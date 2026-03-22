"""
RAG service that combines retrieval and generation
"""
from typing import Optional
from dataclasses import dataclass
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from .embeddings import EmbeddingModel
from db.repository import ChunkRepository, DocumentRepository
from llm.client import LLMClient


@dataclass
class RetrievedContext:
    """Context retrieved for a query"""
    content: str
    url: str
    title: str
    site: str
    score: float


@dataclass
class RAGResponse:
    """Response from the RAG pipeline"""
    answer: str
    sources: list[dict]
    context_used: list[RetrievedContext]


class RAGService:
    """
    Service that orchestrates the RAG pipeline:
    1. Embed the query
    2. Retrieve relevant chunks from the database
    3. Generate a response using the LLM
    """

    def __init__(
        self,
        embedding_model: Optional[EmbeddingModel] = None,
        llm_client: Optional[LLMClient] = None,
        top_k: int = 5,
    ):
        """
        Initialize RAG service.

        Args:
            embedding_model: Model for generating embeddings
            llm_client: Client for LLM generation
            top_k: Number of chunks to retrieve
        """
        self.embedding_model = embedding_model or EmbeddingModel()
        self.llm_client = llm_client or LLMClient()
        self.top_k = top_k

    async def query(
        self,
        session: AsyncSession,
        query: str,
        site_filter: Optional[str] = None,
    ) -> RAGResponse:
        """
        Execute a RAG query.

        Args:
            session: Database session
            query: User's question
            site_filter: Optional site to filter results

        Returns:
            RAGResponse with answer and sources
        """
        # Step 1: Embed the query
        query_embedding = self.embedding_model.embed_query(query)

        # Step 2: Retrieve relevant chunks
        chunk_repo = ChunkRepository(session)
        results = await chunk_repo.search_similar(
            query_embedding=query_embedding,
            top_k=self.top_k,
            site_filter=site_filter,
        )

        # Convert to context objects
        contexts = []
        for chunk, score in results:
            contexts.append(
                RetrievedContext(
                    content=chunk.content,
                    url=getattr(chunk, "url", ""),
                    title=getattr(chunk, "title", ""),
                    site=getattr(chunk, "site", ""),
                    score=score,
                )
            )

        # Step 3: Format context for LLM
        context_for_llm = [
            {
                "content": ctx.content,
                "url": ctx.url,
                "title": ctx.title,
            }
            for ctx in contexts
        ]

        # Step 4: Generate response
        try:
            answer = await self.llm_client.generate(
                query=query,
                context=context_for_llm,
            )
        except Exception as e:
            # Fallback if LLM is unavailable
            answer = self._generate_fallback_response(query, contexts)

        # Step 5: Extract sources from response
        sources = [
            {"url": ctx.url, "title": ctx.title}
            for ctx in contexts
            if ctx.url  # Only include if URL exists
        ]

        return RAGResponse(
            answer=answer,
            sources=sources,
            context_used=contexts,
        )

    def _generate_fallback_response(
        self,
        query: str,
        contexts: list[RetrievedContext],
    ) -> str:
        """Generate a fallback response when LLM is unavailable"""
        if not contexts:
            return (
                "I couldn't find any relevant information for your question. "
                "Please try rephrasing or ask about a different topic."
            )

        # Return the most relevant context with a note
        top_context = contexts[0]
        return (
            f"Based on my sources, here's what I found:\n\n"
            f"{top_context.content[:500]}...\n\n"
            f"Sources:\n[1] {top_context.url} - {top_context.title}\n\n"
            f"(Note: LLM service is currently unavailable. This is a direct excerpt.)"
        )


class IndexingService:
    """
    Service for indexing documents into the RAG system
    """

    def __init__(
        self,
        embedding_model: Optional[EmbeddingModel] = None,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
    ):
        """
        Initialize indexing service.

        Args:
            embedding_model: Model for generating embeddings
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks
        """
        self.embedding_model = embedding_model or EmbeddingModel()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def index_document(
        self,
        session: AsyncSession,
        url: str,
        title: str,
        content: str,
        site: str,
        content_hash: str,
    ) -> int:
        """
        Index a document: store it and create chunks with embeddings.

        Args:
            session: Database session
            url: Document URL
            title: Document title
            content: Document content
            site: Site category
            content_hash: Hash of content for change detection

        Returns:
            Number of chunks created
        """
        doc_repo = DocumentRepository(session)
        chunk_repo = ChunkRepository(session)

        # Check if document already exists
        existing = await doc_repo.get_by_url(url)
        if existing:
            # Check if content changed
            if existing.content_hash == content_hash:
                return 0  # No update needed

            # Content changed - delete old chunks and update
            await chunk_repo.delete_by_document(existing.id)
            await doc_repo.update_content(existing.id, content, content_hash)
            doc_id = existing.id
        else:
            # Create new document
            doc = await doc_repo.create(
                url=url,
                title=title,
                content=content,
                site=site,
                content_hash=content_hash,
            )
            doc_id = doc.id

        # Chunk the content
        chunks = self._chunk_text(content)

        # Generate embeddings for all chunks
        embeddings = self.embedding_model.embed_documents(chunks)

        # Store chunks with embeddings
        chunk_data = [
            (i, chunk, embeddings[i])
            for i, chunk in enumerate(chunks)
        ]
        await chunk_repo.create_many(doc_id, chunk_data)

        return len(chunks)

    def _chunk_text(self, text: str) -> list[str]:
        """Split text into chunks"""
        # Simple paragraph-based chunking
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # Keep overlap
                overlap = current_chunk[-self.chunk_overlap:] if current_chunk else ""
                current_chunk = overlap + " " + para if overlap else para
            else:
                current_chunk = current_chunk + "\n\n" + para if current_chunk else para

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks if chunks else [text[:self.chunk_size]]
