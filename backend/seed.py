"""
Seed script for MiniMem database.
Populates meetings, decisions, and participants with OpenAI embeddings.

Usage:
    python seed.py
"""

import asyncio
import datetime
import os

import asyncpg
import numpy as np
from openai import AsyncOpenAI
from pgvector.asyncpg import register_vector
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MEETINGS = [
    {
        "title": "Q1 All-Hands: Strategic Pivot",
        "date": "2025-01-15",
        "transcript": (
            "Sarah (CEO): Team, we're making a major strategic shift. After analyzing "
            "our metrics and talking to investors, we're pausing all consumer features "
            "in Q1 to focus entirely on enterprise expansion. This is critical for our "
            "runway.\n\n"
            "Mike (CTO): Specifically, this means the mobile app redesign is on hold. "
            "We need all engineering effort redirected to enterprise dashboard, SSO "
            "integration, and admin controls.\n\n"
            "Sarah: Our goal is to sign 5 enterprise customers by end of March. "
            "Everything else is secondary. I know this is a big change, but it's the "
            "right move for the company.\n\n"
            "Alex (Senior Eng): Makes sense. I'll shift my focus to the enterprise "
            "features.\n\n"
            "Mike: Thank you everyone. Let's make Q1 count."
        ),
        "decisions": [
            "Pause all consumer features in Q1 to focus on enterprise",
            "Mobile app redesign is on hold indefinitely",
            "Target: Sign 5 enterprise customers by March 31st",
            "All engineering resources redirected to enterprise features",
            "Top priorities: SSO integration, enterprise dashboard, admin controls",
        ],
        "participants": [
            {"name": "Sarah Chen", "role": "CEO"},
            {"name": "Mike Rodriguez", "role": "CTO"},
            {"name": "Alex Chen", "role": "Senior Engineer"},
        ],
    },
    {
        "title": "Engineering Standup - Feb Sprint Planning",
        "date": "2025-02-14",
        "transcript": (
            "Mike (CTO): Quick updates on enterprise track. We have two major deals "
            "waiting on SSO integration. This is our highest priority blocker.\n\n"
            "Alex: I can pick that up. Should take about a week with testing.\n\n"
            "Mike: Perfect. Also, enterprise customers are reporting the dashboard is "
            "slow with large datasets. We need performance optimization.\n\n"
            "Alex: I'll add that to the backlog after SSO.\n\n"
            "Mike: Good. And reminder - no consumer feature work this quarter per the "
            "all-hands decision."
        ),
        "decisions": [
            "SSO integration is top priority - blocking two enterprise deals",
            "Dashboard performance optimization needed for large datasets",
            "Alex to lead SSO implementation (1 week estimate)",
            "No consumer features this quarter - strict enforcement",
        ],
        "participants": [
            {"name": "Mike Rodriguez", "role": "CTO"},
            {"name": "Alex Chen", "role": "Senior Engineer"},
        ],
    },
    {
        "title": "Product Team Sync - Customer Feedback",
        "date": "2025-02-10",
        "transcript": (
            "Sarah (CEO): I wanted to share feedback from enterprise prospects. They "
            "love the core product but need better admin controls and audit logging.\n\n"
            "Mike: We can prioritize admin panel improvements. The audit logging will "
            "take a bit more time.\n\n"
            "Sarah: That's fine. Also, a few asked about our mobile app. I told them "
            "it's not in our roadmap right now given our enterprise focus.\n\n"
            "Mike: Correct. Mobile is on hold per our Q1 strategy."
        ),
        "decisions": [
            "Prioritize admin panel improvements for enterprise customers",
            "Audit logging feature needed - medium priority",
            "Mobile app explicitly not in roadmap due to enterprise focus",
        ],
        "participants": [
            {"name": "Sarah Chen", "role": "CEO"},
            {"name": "Mike Rodriguez", "role": "CTO"},
        ],
    },
]


async def generate_embedding(text: str) -> np.ndarray:
    """Generate an OpenAI embedding vector for the given text."""
    response = await client.embeddings.create(
        model="text-embedding-ada-002",
        input=text,
    )
    return np.array(response.data[0].embedding)


async def seed_database():
    """Seed the database with meeting data and vector embeddings."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set in .env")
        return

    conn = await asyncpg.connect(database_url)
    await register_vector(conn)

    print("Starting database seed...")

    # Clear existing data (order respects foreign keys)
    await conn.execute("DELETE FROM participants")
    await conn.execute("DELETE FROM decisions")
    await conn.execute("DELETE FROM meetings")
    print("Cleared existing data")

    for idx, meeting in enumerate(MEETINGS, 1):
        print(f"\nProcessing meeting {idx}/{len(MEETINGS)}: {meeting['title']}")

        # Generate embedding for transcript
        print("  Generating transcript embedding...")
        transcript_embedding = await generate_embedding(meeting["transcript"])

        # Insert meeting
        meeting_id = await conn.fetchval(
            """
            INSERT INTO meetings (title, date, transcript, embedding)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            meeting["title"],
            datetime.date.fromisoformat(meeting["date"]),
            meeting["transcript"],
            transcript_embedding,
        )
        print(f"  Meeting inserted (ID: {meeting_id})")

        # Insert decisions with embeddings
        print(f"  Processing {len(meeting['decisions'])} decisions...")
        for decision_text in meeting["decisions"]:
            decision_embedding = await generate_embedding(decision_text)
            await conn.execute(
                """
                INSERT INTO decisions (meeting_id, content, embedding)
                VALUES ($1, $2, $3)
                """,
                meeting_id,
                decision_text,
                decision_embedding,
            )
        print(f"  {len(meeting['decisions'])} decisions inserted")

        # Insert participants
        for participant in meeting["participants"]:
            await conn.execute(
                """
                INSERT INTO participants (meeting_id, name, role)
                VALUES ($1, $2, $3)
                """,
                meeting_id,
                participant["name"],
                participant["role"],
            )
        print(f"  {len(meeting['participants'])} participants inserted")

    # Verify seeded data
    meeting_count = await conn.fetchval("SELECT COUNT(*) FROM meetings")
    decision_count = await conn.fetchval("SELECT COUNT(*) FROM decisions")
    participant_count = await conn.fetchval("SELECT COUNT(*) FROM participants")

    print(f"\nSeed complete!")
    print(f"  {meeting_count} meetings")
    print(f"  {decision_count} decisions")
    print(f"  {participant_count} participants")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(seed_database())
