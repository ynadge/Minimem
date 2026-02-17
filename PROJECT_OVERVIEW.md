# MiniMem - Organizational Memory Demo

## Project Purpose
MiniMem is a demo application showcasing how AI can prevent organizational misalignment as companies scale. Built to demonstrate technical capabilities for Sentra.

## Core Concept
A Slack-like interface where:
1. **Alex (Teammate AI)** - An engineer colleague who is talking to you about next sprint priorities because he does not have context
2. **You (User)** - Chatting with Alex about next sprint priorities  
3. **MiniMem (Memory Bot)** - AI guardian that posts alerts when conversation contradicts recent strategic decisions

## The Demo Flow
Alex asks about work-related priorities → You suggest something (e.g., mobile app work) → MiniMem detects this contradicts a recent all-hands decision (focus on enterprise) → Posts alert in chat with meeting context → You  course-correct

## Architecture

```
Frontend (Next.js + React + TypeScript + Tailwind)
  ↓ HTTP/WebSocket
Python Backend (FastAPI)
  ├── /api/chat → Teammate AI responses
  ├── /api/analyze → MiniMem alignment detection
  ├── /api/meetings → Get meeting data
  └── /ws/chat → WebSocket for real-time updates
  ↓
PostgreSQL Database
  ├── meetings (id, title, date, transcript, embedding vector)
  ├── decisions (id, meeting_id, content, embedding vector)
  └── participants (id, meeting_id, name, role)
  ↓
Vector Search (pgvector extension)
  └── Semantic similarity search on embeddings
```

## Key Technical Features
1. **RAG (Retrieval-Augmented Generation)**: Vector embeddings to find relevant meeting context
2. **Multi-AI Orchestration**: Two AI instances (teammate + guardian) working together
3. **Real-time Updates**: WebSocket for live chat experience
4. **Production Patterns**: Async operations, connection pooling, proper error handling

## Visual Design
- Realistic laptop frame (MacBook style)
- Pixel-perfect Slack clone UI
- Three participants: User, Alex, MiniMem bot
- MiniMem alerts appear as bot messages with special styling (warning/success states)

## Tech Stack
- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python), asyncpg, WebSockets
- **Database**: PostgreSQL 15 with pgvector extension
- **AI**: OpenAI GPT-4o-mini + text-embedding-ada-002
- **Styling**: Tailwind CSS, custom Slack-like components

## Success Criteria
Demonstrates:
- Full-stack development (React + Python)
- SQL database design and querying
- Vector embeddings and RAG implementation
- Beautiful, intuitive UI design
- Product thinking (solving Sentra's core problem)
