# Hour 2: RAG Pipeline + API Endpoints

## Context
Backend foundation is complete. Database has 3 meetings, 12 decisions, 7 participants with 1536-dim embeddings. AsyncOpenAI client and pgvector are working. HNSW indexes are in place.

This ticket builds:
1. The RAG pipeline in `rag.py` (vector search + alignment analysis)
2. Three API endpoints in `main.py` (/api/chat, /api/analyze, /api/meetings)

---

## Task 1: Implement `backend/rag.py`

Replace the placeholder with the full implementation:

```python
from openai import AsyncOpenAI
import os
import json
from typing import List, Dict, Any

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_embedding(text: str) -> list:
    """Generate OpenAI embedding for a given text string."""
    response = await client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding


async def find_relevant_context(pool, conversation_text: str, top_k: int = 3) -> List[Dict]:
    """
    Embed the conversation text and find the most semantically similar
    decisions in the database using pgvector cosine similarity.
    Returns top_k decisions with their source meeting info.
    """
    query_embedding = await generate_embedding(conversation_text)

    rows = await pool.fetch(
        """
        SELECT
            d.content         AS decision,
            m.title           AS meeting_title,
            m.date            AS meeting_date,
            1 - (d.embedding <=> $1::vector) AS similarity
        FROM decisions d
        JOIN meetings m ON d.meeting_id = m.id
        ORDER BY d.embedding <=> $1::vector
        LIMIT $2
        """,
        query_embedding,
        top_k
    )

    return [
        {
            "decision":      row["decision"],
            "meeting_title": row["meeting_title"],
            "meeting_date":  str(row["meeting_date"]),
            "similarity":    float(row["similarity"]),
        }
        for row in rows
    ]


async def check_alignment(pool, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Analyze the recent conversation against stored meeting decisions.

    Steps:
      1. Concatenate the last 4 messages into a query string
      2. Run vector search to find the most relevant decisions
      3. If the best match similarity is below threshold, return aligned (no relevant context)
      4. Otherwise, pass conversation + decisions to GPT to judge alignment
      5. Return structured result for the frontend

    Returns a dict with keys:
      - aligned (bool)
      - issue (str | None)
      - relevant_decision (str | None)
      - meeting_title (str | None)
      - meeting_date (str | None)
      - similarity (float)
      - severity ("low" | "medium" | "high" | None)
    """
    # Build query from the last 4 messages
    recent_msgs = conversation_history[-4:]
    conversation_text = "\n".join(
        f"{msg['sender'].capitalize()}: {msg['content']}"
        for msg in recent_msgs
    )

    # Vector search
    relevant_context = await find_relevant_context(pool, conversation_text, top_k=4)

    # No meaningful context found — treat as aligned
    SIMILARITY_THRESHOLD = 0.75
    if not relevant_context or relevant_context[0]["similarity"] < SIMILARITY_THRESHOLD:
        return {
            "aligned": True,
            "issue": None,
            "relevant_decision": None,
            "meeting_title": None,
            "meeting_date": None,
            "similarity": relevant_context[0]["similarity"] if relevant_context else 0.0,
            "severity": None,
        }

    # Format context for the LLM prompt
    context_lines = "\n".join(
        f"- \"{ctx['decision']}\" (from \"{ctx['meeting_title']}\", {ctx['meeting_date']})"
        for ctx in relevant_context
    )

    prompt = f"""You are an organizational alignment checker for a startup.

Your job: determine whether the recent conversation CONTRADICTS any of the company's recorded decisions.

## Recent Conversation
{conversation_text}

## Recorded Company Decisions
{context_lines}

## Instructions
- Only flag a contradiction if the conversation is actively suggesting work or direction that goes against a decision.
- Do NOT flag if the conversation is simply mentioning or acknowledging a past decision.
- Do NOT flag neutral or unrelated conversation.

Respond ONLY with valid JSON (no markdown, no explanation) in this exact shape:
{{
  "aligned": true,
  "issue": null,
  "relevant_decision": null,
  "meeting_title": null,
  "severity": null
}}

or if misaligned:
{{
  "aligned": false,
  "issue": "One sentence describing the contradiction",
  "relevant_decision": "The exact decision text that is being contradicted",
  "meeting_title": "The meeting it came from",
  "severity": "low | medium | high"
}}"""

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,  # Deterministic for alignment checks
        response_format={"type": "json_object"}
    )

    raw = response.choices[0].message.content
    result = json.loads(raw)

    # Attach vector search metadata to the response
    result["meeting_date"] = relevant_context[0]["meeting_date"]
    result["similarity"]   = relevant_context[0]["similarity"]

    return result
```

---

## Task 2: Add API Endpoints to `backend/main.py`

Add the following imports at the top of `main.py` (after existing imports):

```python
from pydantic import BaseModel
from typing import List
from rag import check_alignment, generate_embedding
from openai import AsyncOpenAI

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

Add these Pydantic models:

```python
class ChatMessageModel(BaseModel):
    sender: str       # "user" | "alex" | "minimem"
    content: str
    timestamp: str    # ISO string, e.g. "2025-02-16T14:32:00"

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessageModel]
```

Add these three endpoints:

### Endpoint 1: `/api/chat` — Teammate AI (Alex)

```python
@app.post("/api/chat")
async def chat_with_teammate(request: ChatRequest):
    """
    Alex is an enthusiastic engineer who doesn't know about recent strategic decisions.
    He might suggest work that contradicts company direction — that's intentional.
    """
    system_prompt = """You are Alex Chen, a senior software engineer at GrowthCo startup.
You're collaborative, enthusiastic, and technically sharp. However, you don't read meeting notes carefully and often miss recent strategic decisions from leadership.

Rules:
- Keep replies short: 1 to 3 casual Slack-style sentences
- Be friendly and engaged, like a real teammate
- Occasionally suggest consumer-facing features, mobile work, or things that contradict enterprise focus (you genuinely don't know better)
- Never reference documents, meetings, or memory — you just don't know
- Sound like a real person, not a chatbot"""

    messages = [{"role": "system", "content": system_prompt}]

    # Add last 6 messages as conversation history
    for msg in request.history[-6:]:
        if msg.sender in ("user",):
            messages.append({"role": "user", "content": msg.content})
        elif msg.sender == "alex":
            messages.append({"role": "assistant", "content": msg.content})
        # Skip minimem messages — Alex shouldn't "see" the bot alerts

    messages.append({"role": "user", "content": request.message})

    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.8,  # Some personality variation
    )

    return {
        "content": response.choices[0].message.content,
        "sender": "alex"
    }
```

### Endpoint 2: `/api/analyze` — MiniMem Alignment Check

```python
@app.post("/api/analyze")
async def analyze_alignment(request: ChatRequest):
    """
    MiniMem analyzes the conversation for misalignment with recorded decisions.
    Called after every user message. Returns alignment status + context.
    """
    history = [
        {"sender": msg.sender, "content": msg.content}
        for msg in request.history
        if msg.sender in ("user", "alex")  # Only analyze human conversation, not bot messages
    ]

    result = await check_alignment(request.app.state.pool, history)
    return result
```

**Important**: `request.app.state.pool` won't work with Pydantic models directly. 
Fix this by injecting the pool via FastAPI's `Request` object instead:

```python
from fastapi import Request

@app.post("/api/analyze")
async def analyze_alignment(request: Request, body: ChatRequest):
    history = [
        {"sender": msg.sender, "content": msg.content}
        for msg in body.history
        if msg.sender in ("user", "alex")
    ]
    result = await check_alignment(request.app.state.pool, history)
    return result

@app.post("/api/chat")
async def chat_with_teammate(request: Request, body: ChatRequest):
    # ... use body.message, body.history
    # same pattern for consistency
```

### Endpoint 3: `/api/meetings` — Fetch All Meetings

```python
@app.get("/api/meetings")
async def get_meetings(request: Request):
    """
    Returns all meetings with their decisions and participants.
    Used by frontend to populate context panel / meeting sidebar.
    """
    rows = await request.app.state.pool.fetch(
        """
        SELECT
            m.id,
            m.title,
            m.date,
            m.transcript,
            ARRAY_AGG(DISTINCT d.content)  AS decisions,
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
            "id":           row["id"],
            "title":        row["title"],
            "date":         str(row["date"]),
            "transcript":   row["transcript"],
            "decisions":    [d for d in row["decisions"]   if d],
            "participants": [p for p in row["participants"] if p],
        }
        for row in rows
    ]
```

---

## Task 3: Manual Testing

With the server running (`uvicorn main:app --reload`), test each endpoint:

### Test `/api/meetings`
```bash
curl http://localhost:8000/api/meetings | python3 -m json.tool
```
Expected: Array of 3 meetings, each with decisions and participants arrays.

### Test `/api/chat` (Alex responds)
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hey Alex, should we work on the mobile app redesign this sprint?",
    "history": []
  }'
```
Expected: Alex responds enthusiastically, likely agreeing with mobile work (he lacks context).

### Test `/api/analyze` (misalignment detection)
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "message": "",
    "history": [
      {"sender": "user",    "content": "should we work on the mobile app?",       "timestamp": "2025-02-16T10:00:00"},
      {"sender": "alex",    "content": "Yeah totally! Let'\''s prioritize it.",     "timestamp": "2025-02-16T10:00:01"}
    ]
  }'
```
Expected: `aligned: false`, with relevant_decision pointing to the Q1 all-hands mobile pause decision.

### Test `/api/analyze` (aligned conversation)
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "message": "",
    "history": [
      {"sender": "user", "content": "Let'\''s focus on the SSO integration this sprint.", "timestamp": "2025-02-16T10:00:00"},
      {"sender": "alex", "content": "Yes! SSO is critical for the enterprise deals.",     "timestamp": "2025-02-16T10:00:01"}
    ]
  }'
```
Expected: `aligned: true`, no issue flagged.

---

## Success Criteria
- [ ] `/api/meetings` returns 3 meetings with decisions and participants
- [ ] `/api/chat` returns Alex's response in 1-3 casual sentences
- [ ] `/api/analyze` returns `aligned: false` for mobile app discussion
- [ ] `/api/analyze` returns `aligned: true` for SSO/enterprise discussion
- [ ] Similarity scores are present in all `/api/analyze` responses
- [ ] No unhandled exceptions in the uvicorn logs