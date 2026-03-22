"""
Initialize the database with tables and pgvector extension.
Run this script after starting PostgreSQL.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.connection import init_db, async_engine
from db.models import Base


async def main():
    """Initialize the database"""
    print("Initializing Boola database...")
    print("=" * 50)

    try:
        await init_db()
        print("\nDatabase tables created successfully!")
        print("\nTables:")
        for table in Base.metadata.tables:
            print(f"  - {table}")
        print("\nDatabase is ready to use.")

    except Exception as e:
        print(f"\nError initializing database: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running:")
        print("   docker-compose up -d postgres")
        print("")
        print("2. Check your DATABASE_URL in .env:")
        print("   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/boola")
        print("")
        print("3. Ensure pgvector extension is available:")
        print("   The pgvector/pgvector Docker image includes it by default.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
