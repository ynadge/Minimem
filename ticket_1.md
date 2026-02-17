# Hour 1: Backend Foundation + Database Setup

## Objective
Set up the Python FastAPI backend with PostgreSQL database, pgvector extension, and seed data with embeddings.

## Tasks

### 1. Project Structure Setup
Create the following directory structure:
```
minimem/
├── backend/
│   ├── main.py
│   ├── rag.py
│   ├── seed.py
│   ├── requirements.txt
│   └── .env
├── frontend/  (will create later)
└── README.md
```

### 2. Install Dependencies
Create `backend/requirements.txt`:
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
asyncpg==0.29.0
openai==1.10.0
python-dotenv==1.0.0
websockets==12.0
```

Create `backend/.env`:
```
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql://postgres:password@localhost/minimem
```

### 3. PostgreSQL Database Setup
Run these SQL commands to create database and schema:

```sql
-- Create database
CREATE DATABASE minimem;

-- Connect to minimem database, then:
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE meetings (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    transcript TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI ada-002 dimension
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE decisions (
    id SERIAL PRIMARY KEY,
    meeting_id INTEGER REFERENCES meetings(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE participants (
    id SERIAL PRIMARY KEY,
    meeting_id INTEGER REFERENCES meetings(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(100)
);

-- Vector similarity search indexes
CREATE INDEX ON meetings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX ON decisions USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### 4. Create FastAPI Application (`backend/main.py`)

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="MiniMem API")

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection pool
@app.on_event("startup")
async def startup():
    database_url = os.getenv("DATABASE_URL")
    app.state.pool = await asyncpg.create_pool(database_url)
    print("✅ Database connection pool created")

@app.on_event("shutdown")
async def shutdown():
    await app.state.pool.close()
    print("👋 Database connection pool closed")

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
```

### 5. Create Seed Script (`backend/seed.py`)

```python
import asyncio
import asyncpg
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MEETINGS = [
    {
        "title": "Q1 All-Hands: Strategic Pivot",
        "date": "2025-01-15",
        "transcript": """Sarah (CEO): Team, we're making a major strategic shift. After analyzing our metrics and talking to investors, we're pausing all consumer features in Q1 to focus entirely on enterprise expansion. This is critical for our runway.

Mike (CTO): Specifically, this means the mobile app redesign is on hold. We need all engineering effort redirected to enterprise dashboard, SSO integration, and admin controls.

Sarah: Our goal is to sign 5 enterprise customers by end of March. Everything else is secondary. I know this is a big change, but it's the right move for the company.

Alex (Senior Eng): Makes sense. I'll shift my focus to the enterprise features.

Mike: Thank you everyone. Let's make Q1 count.""",
        "decisions": [
            "Pause all consumer features in Q1 to focus on enterprise",
            "Mobile app redesign is on hold indefinitely",
            "Target: Sign 5 enterprise customers by March 31st",
            "All engineering resources redirected to enterprise features",
            "Top priorities: SSO integration, enterprise dashboard, admin controls"
        ],
        "participants": [
            {"name": "Sarah Chen", "role": "CEO"},
            {"name": "Mike Rodriguez", "role": "CTO"},
            {"name": "Alex Chen", "role": "Senior Engineer"},
        ]
    },
    {
        "title": "Engineering Standup - Feb Sprint Planning",
        "date": "2025-02-14",
        "transcript": """Mike (CTO): Quick updates on enterprise track. We have two major deals waiting on SSO integration. This is our highest priority blocker.

Alex: I can pick that up. Should take about a week with testing.

Mike: Perfect. Also, enterprise customers are reporting the dashboard is slow with large datasets. We need performance optimization.

Alex: I'll add that to the backlog after SSO.

Mike: Good. And reminder - no consumer feature work this quarter per the all-hands decision.""",
        "decisions": [
            "SSO integration is top priority - blocking two enterprise deals",
            "Dashboard performance optimization needed for large datasets",
            "Alex to lead SSO implementation (1 week estimate)",
            "No consumer features this quarter - strict enforcement"
        ],
        "participants": [
            {"name": "Mike Rodriguez", "role": "CTO"},
            {"name": "Alex Chen", "role": "Senior Engineer"},
        ]
    },
    {
        "title": "Product Team Sync - Customer Feedback",
        "date": "2025-02-10",
        "transcript": """Sarah (CEO): I wanted to share feedback from enterprise prospects. They love the core product but need better admin controls and audit logging.

Mike: We can prioritize admin panel improvements. The audit logging will take a bit more time.

Sarah: That's fine. Also, a few asked about our mobile app. I told them it's not in our roadmap right now given our enterprise focus.

Mike: Correct. Mobile is on hold per our Q1 strategy.""",
        "decisions": [
            "Prioritize admin panel improvements for enterprise customers",
            "Audit logging feature needed - medium priority",
            "Mobile app explicitly not in roadmap due to enterprise focus"
        ],
        "participants": [
            {"name": "Sarah Chen", "role": "CEO"},
            {"name": "Mike Rodriguez", "role": "CTO"},
        ]
    }
]

async def generate_embedding(text: str) -> list:
    """Generate OpenAI embedding for text"""
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding

async def seed_database():
    """Seed database with meeting data and embeddings"""
    database_url = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(database_url)
    
    print("🌱 Starting database seed...")
    
    # Clear existing data
    await conn.execute("DELETE FROM participants")
    await conn.execute("DELETE FROM decisions")
    await conn.execute("DELETE FROM meetings")
    print("🗑️  Cleared existing data")
    
    for idx, meeting in enumerate(MEETINGS, 1):
        print(f"\n📝 Processing meeting {idx}/{len(MEETINGS)}: {meeting['title']}")
        
        # Generate embedding for full transcript
        print("   ⚙️  Generating transcript embedding...")
        embedding = await generate_embedding(meeting["transcript"])
        
        # Insert meeting
        meeting_id = await conn.fetchval(
            """
            INSERT INTO meetings (title, date, transcript, embedding)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            meeting["title"],
            meeting["date"],
            meeting["transcript"],
            embedding
        )
        print(f"   ✅ Meeting inserted (ID: {meeting_id})")
        
        # Insert decisions with embeddings
        print(f"   ⚙️  Processing {len(meeting['decisions'])} decisions...")
        for decision in meeting["decisions"]:
            decision_embedding = await generate_embedding(decision)
            await conn.execute(
                """
                INSERT INTO decisions (meeting_id, content, embedding)
                VALUES ($1, $2, $3)
                """,
                meeting_id,
                decision,
                decision_embedding
            )
        print(f"   ✅ {len(meeting['decisions'])} decisions inserted")
        
        # Insert participants
        for participant in meeting["participants"]:
            await conn.execute(
                """
                INSERT INTO participants (meeting_id, name, role)
                VALUES ($1, $2, $3)
                """,
                meeting_id,
                participant["name"],
                participant["role"]
            )
        print(f"   ✅ {len(meeting['participants'])} participants inserted")
    
    # Verify data
    meeting_count = await conn.fetchval("SELECT COUNT(*) FROM meetings")
    decision_count = await conn.fetchval("SELECT COUNT(*) FROM decisions")
    participant_count = await conn.fetchval("SELECT COUNT(*) FROM participants")
    
    print(f"\n✨ Seed complete!")
    print(f"   📊 {meeting_count} meetings")
    print(f"   📊 {decision_count} decisions")
    print(f"   📊 {participant_count} participants")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
```

## Testing & Verification

### Run the backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Visit http://localhost:8000/docs to see FastAPI auto-generated docs.

### Seed the database:
```bash
python seed.py
```

### Verify in PostgreSQL:
```sql
-- Check meetings
SELECT id, title, date FROM meetings;

-- Check decisions
SELECT d.content, m.title 
FROM decisions d 
JOIN meetings m ON d.meeting_id = m.id;

-- Verify embeddings exist
SELECT id, title, array_length(embedding, 1) as embedding_dim 
FROM meetings;
```

## Expected Output
- FastAPI server running on http://localhost:8000
- Database with 3 meetings, ~12 decisions, ~6 participants
- All records have vector embeddings (1536 dimensions)
- Health check endpoint returning "healthy"

## Common Issues & Fixes

**Issue**: pgvector extension not found
**Fix**: 
```bash
# On Mac with Homebrew Postgres
brew install pgvector

# Then in psql:
CREATE EXTENSION vector;
```

**Issue**: asyncpg connection fails
**Fix**: Check DATABASE_URL in .env matches your Postgres setup

**Issue**: OpenAI API errors
**Fix**: Verify OPENAI_API_KEY in .env is valid

## Success Criteria
- [ ] FastAPI server starts without errors
- [ ] /health endpoint returns "healthy"
- [ ] Database has 3 meetings with embeddings
- [ ] All decisions have embeddings
- [ ] Can query vector similarity (we'll test this in Hour 2)