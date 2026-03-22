"""
Database repository for document and chunk operations
"""
from typing import Optional
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np

from .models import Document, Chunk, Conversation, Message


class DocumentRepository:
    """Repository for document operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        url: str,
        title: str,
        content: str,
        site: str,
        content_hash: str,
    ) -> Document:
        """Create a new document"""
        doc = Document(
            url=url,
            title=title,
            content=content,
            site=site,
            content_hash=content_hash,
        )
        self.session.add(doc)
        await self.session.commit()
        await self.session.refresh(doc)
        return doc

    async def get_by_url(self, url: str) -> Optional[Document]:
        """Get document by URL"""
        result = await self.session.execute(
            select(Document).where(Document.url == url)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, doc_id: int) -> Optional[Document]:
        """Get document by ID"""
        result = await self.session.execute(
            select(Document).where(Document.id == doc_id)
        )
        return result.scalar_one_or_none()

    async def update_content(
        self,
        doc_id: int,
        content: str,
        content_hash: str,
    ) -> Optional[Document]:
        """Update document content"""
        doc = await self.get_by_id(doc_id)
        if doc:
            doc.content = content
            doc.content_hash = content_hash
            await self.session.commit()
            await self.session.refresh(doc)
        return doc

    async def delete(self, doc_id: int) -> bool:
        """Delete document and its chunks"""
        doc = await self.get_by_id(doc_id)
        if doc:
            await self.session.delete(doc)
            await self.session.commit()
            return True
        return False

    async def list_all(self, site: Optional[str] = None) -> list[Document]:
        """List all documents, optionally filtered by site"""
        query = select(Document)
        if site:
            query = query.where(Document.site == site)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self) -> int:
        """Count total documents"""
        result = await self.session.execute(select(func.count(Document.id)))
        return result.scalar() or 0


class ChunkRepository:
    """Repository for chunk operations with vector search"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        document_id: int,
        chunk_index: int,
        content: str,
        embedding: np.ndarray,
    ) -> Chunk:
        """Create a new chunk with embedding"""
        chunk = Chunk(
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            embedding=embedding.tolist(),
        )
        self.session.add(chunk)
        await self.session.commit()
        await self.session.refresh(chunk)
        return chunk

    async def create_many(
        self,
        document_id: int,
        chunks: list[tuple[int, str, np.ndarray]],
    ) -> list[Chunk]:
        """Create multiple chunks for a document"""
        chunk_objects = [
            Chunk(
                document_id=document_id,
                chunk_index=idx,
                content=content,
                embedding=embedding.tolist(),
            )
            for idx, content, embedding in chunks
        ]
        self.session.add_all(chunk_objects)
        await self.session.commit()
        return chunk_objects

    async def delete_by_document(self, document_id: int) -> int:
        """Delete all chunks for a document"""
        result = await self.session.execute(
            select(Chunk).where(Chunk.document_id == document_id)
        )
        chunks = result.scalars().all()
        count = len(chunks)
        for chunk in chunks:
            await self.session.delete(chunk)
        await self.session.commit()
        return count

    async def search_similar(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        site_filter: Optional[str] = None,
    ) -> list[tuple[Chunk, float]]:
        """
        Search for similar chunks using cosine similarity.
        Returns chunks with their similarity scores.
        """
        # Build the query using pgvector's cosine distance
        # Note: pgvector uses <=> for cosine distance (1 - similarity)
        embedding_str = str(query_embedding.tolist())

        if site_filter:
            query = text("""
                SELECT c.*, d.url, d.title, d.site,
                       1 - (c.embedding <=> :embedding) as similarity
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
                WHERE d.site = :site
                ORDER BY c.embedding <=> :embedding
                LIMIT :limit
            """)
            result = await self.session.execute(
                query,
                {"embedding": embedding_str, "site": site_filter, "limit": top_k}
            )
        else:
            query = text("""
                SELECT c.*, d.url, d.title, d.site,
                       1 - (c.embedding <=> :embedding) as similarity
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
                ORDER BY c.embedding <=> :embedding
                LIMIT :limit
            """)
            result = await self.session.execute(
                query,
                {"embedding": embedding_str, "limit": top_k}
            )

        rows = result.fetchall()

        # Convert to Chunk objects with scores
        results = []
        for row in rows:
            chunk = Chunk(
                id=row.id,
                document_id=row.document_id,
                chunk_index=row.chunk_index,
                content=row.content,
            )
            # Attach document info as attributes for convenience
            chunk.url = row.url
            chunk.title = row.title
            chunk.site = row.site
            results.append((chunk, row.similarity))

        return results

    async def count(self) -> int:
        """Count total chunks"""
        result = await self.session.execute(select(func.count(Chunk.id)))
        return result.scalar() or 0


class ConversationRepository:
    """Repository for conversation operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, conversation_id: str) -> Conversation:
        """Create a new conversation"""
        conv = Conversation(id=conversation_id)
        self.session.add(conv)
        await self.session.commit()
        await self.session.refresh(conv)
        return conv

    async def get(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        result = await self.session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
    ) -> Message:
        """Add a message to a conversation"""
        # Ensure conversation exists
        conv = await self.get(conversation_id)
        if not conv:
            conv = await self.create(conversation_id)

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def get_messages(self, conversation_id: str) -> list[Message]:
        """Get all messages in a conversation"""
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        return list(result.scalars().all())
