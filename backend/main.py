"""
MiniMem API — FastAPI backend for organizational memory demo.
"""

from contextlib import asynccontextmanager

from typing import List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI
import asyncpg
import os
from dotenv import load_dotenv
from pgvector.asyncpg import register_vector
from rag import check_alignment

load_dotenv()

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ChatMessageModel(BaseModel):
    sender: str       # "user" | "alex" | "minimem"
    content: str
    timestamp: str    # ISO string, e.g. "2025-02-16T14:32:00"


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessageModel]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown of the database connection pool."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    # Railway injects postgres:// — asyncpg requires postgresql://
    database_url = database_url.replace("postgres://", "postgresql://", 1)

    # Railway requires SSL; local Postgres typically does not
    is_local = "localhost" in database_url or "127.0.0.1" in database_url
    ssl_mode = None if is_local else "require"

    async def _init_connection(conn):
        await register_vector(conn)

    app.state.pool = await asyncpg.create_pool(
        database_url, init=_init_connection, ssl=ssl_mode
    )
    print("Database connection pool created")
    yield
    await app.state.pool.close()
    print("Database connection pool closed")


app = FastAPI(title="MiniMem API", lifespan=lifespan)

# CORS — env-driven so the Vercel production URL can be added in Railway
cors_origins_raw = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001")
cors_origins = [origin.strip() for origin in cors_origins_raw.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "MiniMem API is running"}


@app.get("/health")
async def health_check():
    try:
        async with app.state.pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/chat")
async def chat_with_teammate(request: Request, body: ChatRequest):
    """
    Alex is an enthusiastic engineer who doesn't know about recent strategic
    decisions. He might suggest work that contradicts company direction.
    """
    system_prompt = (
        "You are Alex Chen, a senior software engineer at PreCrime.ai.\n"
        "You are collaborative and enthusiastic, but you don't read meeting notes "
        "and miss recent strategic decisions.\n\n"
        "Rules:\n"
        "- MAXIMUM 2 sentences per response. Never exceed this.\n"
        "- Casual Slack tone — like texting a coworker, not writing an email\n"
        "- You genuinely don't know about recent all-hands decisions or strategic pivots\n"
        "- You might naturally suggest consumer features, mobile work, or UI redesigns "
        "without realizing they're paused\n"
        '- Never use the words "certainly", "absolutely", "of course", or "great question"\n'
        '- Never start a message with "I"\n'
        '- Avoid em dashes and emojis unless they are part of the conversation\n'
        "- Sound like a real person, not a chatbot or assistant"
    )

    messages = [{"role": "system", "content": system_prompt}]

    for msg in body.history[-6:]:
        if msg.sender == "user":
            messages.append({"role": "user", "content": msg.content})
        elif msg.sender == "alex":
            messages.append({"role": "assistant", "content": msg.content})
        # Skip minimem messages — Alex shouldn't "see" the bot alerts

    messages.append({"role": "user", "content": body.message})

    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.8,
    )

    return {
        "content": response.choices[0].message.content,
        "sender": "alex",
    }


@app.post("/api/analyze")
async def analyze_alignment(request: Request, body: ChatRequest):
    """
    MiniMem analyzes the conversation for misalignment with recorded decisions.
    Called after every user message. Returns alignment status + context.
    """
    history = [
        {"sender": msg.sender, "content": msg.content}
        for msg in body.history
        if msg.sender in ("user", "alex")
    ]

    result = await check_alignment(request.app.state.pool, history)
    return result


@app.get("/api/meetings")
async def get_meetings(request: Request):
    """
    Returns all meetings with their decisions and participants.
    Used by frontend to populate context panel / meeting sidebar.
    """
    async with request.app.state.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                m.id,
                m.title,
                m.date,
                m.transcript,
                ARRAY_AGG(DISTINCT d.content) AS decisions,
                ARRAY_AGG(DISTINCT p.name || ' (' || p.role || ')') AS participants
            FROM meetings m
            LEFT JOIN decisions    d ON d.meeting_id = m.id
            LEFT JOIN participants p ON p.meeting_id = m.id
            GROUP BY m.id, m.title, m.date, m.transcript
            ORDER BY m.date DESC
            """
        )

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "date": str(row["date"]),
            "transcript": row["transcript"],
            "decisions": [d for d in row["decisions"] if d],
            "participants": [p for p in row["participants"] if p],
        }
        for row in rows
    ]
