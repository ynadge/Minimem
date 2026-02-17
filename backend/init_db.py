"""
Database initialization script for MiniMem.
Creates the PostgreSQL schema (tables, indexes, pgvector extension).

Usage:
    python init_db.py
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

SCHEMA_SQL = """
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Meetings table
CREATE TABLE IF NOT EXISTS meetings (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    transcript TEXT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Decisions table (linked to meetings)
CREATE TABLE IF NOT EXISTS decisions (
    id SERIAL PRIMARY KEY,
    meeting_id INTEGER REFERENCES meetings(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Participants table (linked to meetings)
CREATE TABLE IF NOT EXISTS participants (
    id SERIAL PRIMARY KEY,
    meeting_id INTEGER REFERENCES meetings(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(100)
);
"""

INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS meetings_embedding_idx ON meetings USING hnsw (embedding vector_cosine_ops);",
    "CREATE INDEX IF NOT EXISTS decisions_embedding_idx ON decisions USING hnsw (embedding vector_cosine_ops);",
]


async def ensure_database_exists(database_url: str):
    """Create the 'minimem' database if it doesn't already exist."""
    # Connect to the default 'postgres' database to run CREATE DATABASE
    admin_url = database_url.rsplit("/", 1)[0] + "/postgres"
    conn = await asyncpg.connect(admin_url)
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = 'minimem'"
        )
        if not exists:
            await conn.execute("CREATE DATABASE minimem")
            print("Created 'minimem' database.")
        else:
            print("Database 'minimem' already exists.")
    finally:
        await conn.close()


async def init_database():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set in .env")
        return

    # Step 1: Ensure the database exists
    await ensure_database_exists(database_url)

    # Step 2: Connect to minimem and create schema
    print("Connecting to minimem database...")
    conn = await asyncpg.connect(database_url)

    try:
        print("Creating tables...")
        await conn.execute(SCHEMA_SQL)
        print("Tables created successfully.")

        print("Creating HNSW vector indexes...")
        for sql in INDEX_SQL:
            await conn.execute(sql)
        print("Indexes created successfully.")

        # Verify tables exist
        tables = await conn.fetch(
            """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
            """
        )
        print(f"\nDatabase tables: {[t['table_name'] for t in tables]}")
        print("Database initialization complete.")

    except Exception as e:
        print(f"ERROR during initialization: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(init_database())
