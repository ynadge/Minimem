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

    async def _init_connection(conn):
        await register_vector(conn)

    app.state.pool = await asyncpg.create_pool(database_url, init=_init_connection)
    print("Database connection pool created")
    yield
    await app.state.pool.close()
    print("Database connection pool closed")


app = FastAPI(title="MiniMem API", lifespan=lifespan)

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
        "You are Alex Chen, a senior software engineer at GrowthCo startup.\n"
        "You're collaborative, enthusiastic, and technically sharp. However, you "
        "don't read meeting notes carefully and often miss recent strategic "
        "decisions from leadership.\n\n"
        "Rules:\n"
        "- Keep replies short: 1 to 3 casual Slack-style sentences\n"
        "- Be friendly and engaged, like a real teammate\n"
        "- Occasionally suggest consumer-facing features, mobile work, or things "
        "that contradict enterprise focus (you genuinely don't know better)\n"
        "- Never reference documents, meetings, or memory — you just don't know\n"
        "- Sound like a real person, not a chatbot"
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
