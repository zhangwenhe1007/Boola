"""
Database connection and session management
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator

from api.config import get_settings

settings = get_settings()

# Convert postgresql:// to postgresql+asyncpg:// for async
async_database_url = settings.database_url.replace(
    "postgresql://", "postgresql+asyncpg://"
)

# Sync engine (for migrations and setup)
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async engine (for API requests)
async_engine = create_async_engine(async_database_url, echo=settings.debug)
AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    Automatically closes the session when done.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    Initialize database with required extensions and tables.
    Creates the pgvector extension if it doesn't exist.
    """
    from .models import Base

    async with async_engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    print("Database initialized successfully")


async def drop_db():
    """Drop all tables (use with caution)"""
    from .models import Base

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    print("Database tables dropped")
