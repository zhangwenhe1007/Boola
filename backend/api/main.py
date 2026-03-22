"""
Boola API - Yale AI Assistant Backend
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from db.connection import get_db, init_db
from db.repository import DocumentRepository, ChunkRepository, ConversationRepository
from rag.service import RAGService, IndexingService
from rag.embeddings import EmbeddingModel
from llm.client import LLMClient

settings = get_settings()

# Initialize shared services (lazy loaded)
_embedding_model: Optional[EmbeddingModel] = None
_llm_client: Optional[LLMClient] = None
_rag_service: Optional[RAGService] = None
_indexing_service: Optional[IndexingService] = None


def get_embedding_model() -> EmbeddingModel:
    """Get or create embedding model singleton"""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel(model_name=settings.embedding_model)
    return _embedding_model


def get_llm_client() -> LLMClient:
    """Get or create LLM client singleton"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient(
            base_url=settings.vllm_base_url,
            api_key=settings.vllm_api_key,
            model=settings.vllm_model,
        )
    return _llm_client


def get_rag_service() -> RAGService:
    """Get or create RAG service singleton"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService(
            embedding_model=get_embedding_model(),
            llm_client=get_llm_client(),
        )
    return _rag_service


def get_indexing_service() -> IndexingService:
    """Get or create indexing service singleton"""
    global _indexing_service
    if _indexing_service is None:
        _indexing_service = IndexingService(
            embedding_model=get_embedding_model(),
        )
    return _indexing_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("Starting Boola API...")
    try:
        await init_db()
        print("Database initialized")
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
        print("Make sure PostgreSQL is running with pgvector extension")

    yield

    # Shutdown
    print("Shutting down Boola API...")


app = FastAPI(
    title="Boola API",
    description="Yale AI Assistant Backend",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== Request/Response Models ==============

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    site_filter: Optional[str] = None  # Filter to specific Yale site


class ChatResponse(BaseModel):
    response: str
    sources: list[dict]
    conversation_id: str


class IndexRequest(BaseModel):
    url: str
    title: str
    content: str
    site: str
    content_hash: str


class IndexResponse(BaseModel):
    success: bool
    document_id: Optional[int] = None
    chunks_created: int
    message: str


class StatsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    status: str


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    llm: str


# ============== Endpoints ==============

@app.get("/", tags=["General"])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Boola API",
        "docs": "/docs",
        "version": "0.1.0",
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint with service status"""
    # Check database
    db_status = "healthy"
    try:
        doc_repo = DocumentRepository(db)
        await doc_repo.count()
    except Exception:
        db_status = "unavailable"

    # Check LLM
    llm_status = "unknown"
    try:
        llm = get_llm_client()
        if await llm.health_check():
            llm_status = "healthy"
        else:
            llm_status = "unavailable"
    except Exception:
        llm_status = "unavailable"

    overall_status = "healthy" if db_status == "healthy" else "degraded"

    return HealthResponse(
        status=overall_status,
        version="0.1.0",
        database=db_status,
        llm=llm_status,
    )


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Main chat endpoint.

    1. Retrieve relevant context from indexed documents
    2. Generate response using LLM with citations
    3. Store conversation history
    """
    # Generate conversation ID if not provided
    conversation_id = request.conversation_id or str(uuid.uuid4())

    # Store user message
    conv_repo = ConversationRepository(db)
    await conv_repo.add_message(conversation_id, "user", request.message)

    # Get RAG response
    rag_service = get_rag_service()
    try:
        result = await rag_service.query(
            session=db,
            query=request.message,
            site_filter=request.site_filter,
        )
        response_text = result.answer
        sources = result.sources
    except Exception as e:
        print(f"RAG error: {e}")
        response_text = (
            "I'm having trouble accessing my knowledge base right now. "
            "Please try again in a moment, or check if the database is properly set up."
        )
        sources = []

    # Store assistant response
    await conv_repo.add_message(conversation_id, "assistant", response_text)

    return ChatResponse(
        response=response_text,
        sources=sources,
        conversation_id=conversation_id,
    )


@app.post("/index", response_model=IndexResponse, tags=["Indexing"])
async def index_document(
    request: IndexRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Index a document for RAG retrieval.

    Creates chunks and generates embeddings for the document.
    """
    indexing_service = get_indexing_service()

    try:
        chunks_created = await indexing_service.index_document(
            session=db,
            url=request.url,
            title=request.title,
            content=request.content,
            site=request.site,
            content_hash=request.content_hash,
        )

        return IndexResponse(
            success=True,
            chunks_created=chunks_created,
            message=f"Successfully indexed document with {chunks_created} chunks",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@app.get("/stats", response_model=StatsResponse, tags=["Admin"])
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get indexing statistics"""
    try:
        doc_repo = DocumentRepository(db)
        chunk_repo = ChunkRepository(db)

        total_docs = await doc_repo.count()
        total_chunks = await chunk_repo.count()

        return StatsResponse(
            total_documents=total_docs,
            total_chunks=total_chunks,
            status="ready" if total_chunks > 0 else "empty",
        )
    except Exception as e:
        return StatsResponse(
            total_documents=0,
            total_chunks=0,
            status=f"error: {str(e)}",
        )


@app.get("/documents", tags=["Admin"])
async def list_documents(
    site: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all indexed documents"""
    doc_repo = DocumentRepository(db)
    docs = await doc_repo.list_all(site=site)

    return {
        "count": len(docs),
        "documents": [
            {
                "id": doc.id,
                "url": doc.url,
                "title": doc.title,
                "site": doc.site,
                "crawled_at": doc.crawled_at.isoformat() if doc.crawled_at else None,
            }
            for doc in docs
        ],
    }


@app.delete("/documents/{doc_id}", tags=["Admin"])
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a document and its chunks"""
    doc_repo = DocumentRepository(db)
    success = await doc_repo.delete(doc_id)

    if not success:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"message": f"Document {doc_id} deleted successfully"}
