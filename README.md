# MiniMem

> *What happens when a company loses itself?*

A demo exploring organizational memory — built to show how AI can prevent the misalignment that quietly kills startups as they scale.

**[→ Try the live demo](https://minimem-flame.vercel.app)**

---

## The Problem

Growing startups make dozens of decisions every week. Strategic pivots, priority calls, things that are explicitly off the table. Those decisions live in meeting notes, Slack threads, and the heads of whoever was in the room.

Two weeks later, an engineer who missed the all-hands is suggesting exactly the work leadership decided to pause. Not out of malice — out of information decay. The company is misaligned with itself.

This is what Sentra is building against. MiniMem is my attempt to prototype one slice of that problem: **what if an AI teammate could catch misalignment the moment it enters a conversation?**

---

## The Demo

MiniMem puts you inside a Slack-like group chat at **PreCrime.ai** — a (fictional, satirical) startup building an AI camera app that classifies strangers as GOOD 🟢 or BAD 🔴 using computer vision and vibes. They recently pivoted hard to enterprise B2B. Their engineer Alex did not get the memo.

**The game:**
1. Alex opens the conversation and asks what you should work on
2. The pinned meeting notes show you exactly what leadership decided
3. Try suggesting something off-agenda — watch MiniMem catch it in real time
4. Course-correct — watch MiniMem confirm you're aligned

The point isn't the game. The point is experiencing what organizational memory actually *feels* like when it works.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Next.js Frontend                      │
│         Slack-like UI · TypeScript · Tailwind            │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP (parallel requests)
          ┌──────────────┴──────────────┐
          ▼                             ▼
┌─────────────────┐          ┌──────────────────────┐
│   /api/chat     │          │    /api/analyze       │
│                 │          │                       │
│  Alex (teammate │          │  MiniMem (guardian    │
│  AI) responds   │          │  AI) checks alignment │
└────────┬────────┘          └──────────┬────────────┘
         │                              │
         │              ┌───────────────┘
         │              ▼
         │    ┌─────────────────────┐
         │    │    RAG Pipeline     │
         │    │                     │
         │    │  1. Embed query     │
         │    │  2. Vector search   │
         │    │  3. LLM analysis    │
         │    └──────────┬──────────┘
         │               │
         └───────────────┼──────────────┐
                         ▼              ▼
              ┌─────────────────────────────────┐
              │    PostgreSQL + pgvector         │
              │                                  │
              │  meetings  (transcript, embedding)│
              │  decisions (content, embedding)   │
              │  participants                     │
              └─────────────────────────────────┘
```

### Two AI instances, one purpose

The most interesting architectural decision: two separate LLM calls fire in parallel on every user message.

**Alex (the teammate)** runs with a system prompt that makes him enthusiastic but context-blind. He doesn't know about recent decisions. He'll happily agree to build the consumer leaderboard, work on the mobile app, or anything else that's been explicitly frozen. Temperature 0.8 — he has personality.

**MiniMem (the guardian)** never sees Alex's response. It independently analyzes the conversation against the decision database using vector similarity search. Temperature 0 — it needs to be deterministic.

The two AIs are completely unaware of each other. MiniMem isn't reacting to Alex — it's reacting to the conversation's *direction*. This is the right design: in production, you'd want the memory layer to be orthogonal to the communication layer.

### RAG implementation

Meeting transcripts and decisions are embedded at seed time using `text-embedding-ada-002` (1536 dimensions) and stored in PostgreSQL via the `pgvector` extension with HNSW indexes.

On each message, MiniMem:
1. Embeds the last 4 messages of conversation as a single query string
2. Runs cosine similarity search against the decisions table
3. If the best match exceeds a 0.75 similarity threshold, passes the conversation + top matches to `gpt-4o-mini` for alignment judgment
4. Returns structured JSON: `{ aligned, issue, relevant_decision, meeting_title, severity }`

The 0.75 threshold is doing real work here. Below it, there's not enough semantic overlap to make a confident claim — better to stay quiet than false-positive. In the test data, genuine misalignments score 0.80+.

### Why HNSW over IVFFlat

IVFFlat requires a minimum number of rows before you can create the index — annoying during development when you're re-seeding constantly. HNSW works on empty tables and has better recall at the cost of slightly higher memory usage. For a dataset of this size the tradeoff is trivially in HNSW's favor.

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | Next.js 16, React, TypeScript | App Router, strong typing, fast iteration |
| Styling | Tailwind CSS | Utility-first, no context switching |
| Backend | FastAPI (Python) | Async-native, automatic OpenAPI docs, familiar in ML contexts |
| Database | PostgreSQL 17 | Reliable, great ecosystem, pgvector support |
| Vector search | pgvector (HNSW index) | No separate vector DB needed for this scale |
| Embeddings | text-embedding-ada-002 | 1536-dim, strong semantic understanding |
| LLM | gpt-4o-mini | Fast, cheap, good enough for structured JSON output |
| Frontend hosting | Vercel | Zero-config Next.js deployment |
| Backend hosting | Railway | Native pgvector support, stays warm, simple env management |

---

## Running Locally

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with pgvector extension
- OpenAI API key

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # add your OPENAI_API_KEY and DATABASE_URL

python init_db.py     # creates tables and indexes
python seed.py        # seeds meetings with embeddings
uvicorn main:app --reload
```

API docs available at `http://localhost:8000/docs`

### Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local  # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

---

## Project Structure

```
minimem/
├── backend/
│   ├── main.py          # FastAPI app, endpoints, Alex's system prompt
│   ├── rag.py           # Embedding generation, vector search, alignment analysis
│   ├── seed.py          # Meeting data + embedding pipeline
│   ├── init_db.py       # Schema creation (tables + HNSW indexes)
│   └── requirements.txt
│
└── frontend/
    └── src/
        ├── app/
        │   └── page.tsx              # Main orchestration, game state, API calls
        ├── components/
        │   ├── ChatMessage.tsx        # User / Alex / MiniMem message rendering
        │   ├── MeetingNotesPanel.tsx  # Collapsible pinned agenda
        │   ├── GamePrompt.tsx         # Stage-driven user nudges
        │   ├── SlackSidebar.tsx       # Workspace chrome
        │   ├── LaptopFrame.tsx        # Monitor bezel wrapper
        │   └── TypingIndicator.tsx    # Animated typing dots
        └── types/
            └── index.ts              # Shared TypeScript interfaces
```

---

## What I'd Build Next

This demo deliberately scopes down to one core interaction. In a production system:

**Broader ingestion** — real Slack threads, Notion docs, email chains, Jira tickets. The pipeline is the same (chunk → embed → store) but the surface area of organizational memory is much larger.

**Smarter chunking** — right now entire meeting transcripts are embedded as single vectors. In practice you'd chunk by speaker turn or topic, embed each chunk separately, and retrieve at chunk granularity. Better recall, more precise citations.

**Longitudinal context** — decisions decay and get superseded. The system should understand that a January decision can be overridden by a March decision, and weight recency accordingly. Right now it just finds the most semantically similar decision, not the most *current* one.

**Multi-tenant isolation** — the schema is ready for it (adding `org_id` foreign keys), but the API layer doesn't enforce it yet. Real product needs row-level security.

**Proactive surfacing** — right now MiniMem only fires reactively (when someone says something wrong). The more interesting product moment is proactive: "Based on last week's all-hands, here's context you might want before this meeting."

---

## Why I Built This

I came across Sentra after your funding announcement and the problem immediately resonated. I've watched fast-growing teams lose their own context — decisions made in week 3 that contradict decisions from week 1, engineers building things leadership explicitly paused, new hires operating on stale mental models of what the company is doing.

MiniMem is my attempt to make that problem tangible and interactive. It's also an honest signal of what I'd bring to the role: I can scope a problem, design a system, and ship something end-to-end that demonstrates the core value prop.

I'd love to talk about what you're building.

---

*Built by [Your Name] · [your@email.com] · [linkedin.com/in/yourprofile]*
