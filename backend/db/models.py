"""
SQLAlchemy models for Boola database
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import DeclarativeBase, relationship
from pgvector.sqlalchemy import Vector


# Embedding dimension for BGE-base model
EMBEDDING_DIM = 768


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class Document(Base):
    """
    A crawled document/page.
    Stores the original content and metadata.
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(2048), unique=True, nullable=False, index=True)
    title = Column(String(512), nullable=False)
    content = Column(Text, nullable=False)
    site = Column(String(64), nullable=False, index=True)
    content_hash = Column(String(32), nullable=False)
    crawled_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationship to chunks
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title[:30]}...')>"


class Chunk(Base):
    """
    A chunk of a document for RAG retrieval.
    Stores the text chunk and its vector embedding.
    """
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(EMBEDDING_DIM))  # pgvector column
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationship to document
    document = relationship("Document", back_populates="chunks")

    # Index for vector similarity search
    __table_args__ = (
        Index(
            "ix_chunks_embedding",
            embedding,
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    def __repr__(self):
        return f"<Chunk(id={self.id}, doc_id={self.document_id}, index={self.chunk_index})>"


class Conversation(Base):
    """
    A chat conversation session.
    """
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True)  # UUID
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationship to messages
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """
    A message in a conversation.
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(16), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationship to conversation
    conversation = relationship("Conversation", back_populates="messages")
