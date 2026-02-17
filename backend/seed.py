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
        "title": "Q1 All-Hands: The Pivot to B2B",
        "date": "2025-01-15",
        "transcript": (
            'Sarah Fisher (CEO): Okay team, big news. We\'ve been burning runway on the '
            'consumer app and frankly the App Store keeps pulling us for "privacy concerns" '
            "— which, for the record, is totally overblown. Anyway. We're pivoting. B2B "
            "only in Q1. Enterprise security firms, insurance companies, private gated "
            "communities. That's our customer now.\n\n"
            "Mike Rodriguez (CTO): This means we are pausing the consumer-facing GoodBad "
            "Score app entirely. No new features, no bug fixes, no nothing. All engineering "
            "goes to the enterprise SDK and the API dashboard.\n\n"
            "Sarah Fisher: Our goal is three signed enterprise pilots by end of March. "
            "Three. That's it. One of them is basically done — TrustGuard Security is very "
            "interested. But we need the enterprise dashboard live and we need SSO because "
            "their IT guy won't shut up about it.\n\n"
            "Alex Chen (Senior Eng): What about the explainability feature? Legal said we "
            "might need it.\n\n"
            "Sarah Fisher: Legal says a lot of things. That goes on the backlog. Focus on "
            "the dashboard and SSO. If we don't close these pilots we don't make it to "
            "Q2.\n\n"
            "Mike Rodriguez: To be crystal clear: no consumer features. The GoodBad Score "
            "app is frozen. Anyone working on it without explicit sign-off is wasting time "
            "we don't have."
        ),
        "decisions": [
            "Pivot entirely to B2B enterprise in Q1 — consumer app is frozen",
            "GoodBad Score consumer app gets zero engineering resources this quarter",
            "Top priorities: enterprise SDK, API dashboard, SSO integration",
            "Target: 3 signed enterprise pilots by March 31st",
            "TrustGuard Security is the lead prospect — close them first",
            "Explainability feature goes to backlog — not a Q1 priority",
            "No consumer features without explicit CEO sign-off",
        ],
        "participants": [
            {"name": "Sarah Fisher", "role": "CEO"},
            {"name": "Mike Rodriguez", "role": "CTO"},
            {"name": "Alex Chen", "role": "Senior Engineer"},
            {"name": "Priya Nair", "role": "Head of Product"},
            {"name": "Jordan Lee", "role": "Sales Lead"},
        ],
    },
    {
        "title": "Engineering Standup — Sprint Planning",
        "date": "2025-02-10",
        "transcript": (
            "Mike Rodriguez (CTO): Alright. SSO is the number one blocker. TrustGuard's "
            "IT team will not proceed without it. Alex, how long?\n\n"
            "Alex Chen: A week if nothing blows up. Maybe less. The enterprise dashboard "
            "is mostly done, I just need to wire up the org-level admin controls.\n\n"
            "Mike Rodriguez: Good. Do SSO first, then admin controls. In that order. Do "
            "not get distracted by anything else.\n\n"
            "Alex Chen: What about the accuracy drift we're seeing on the BAD detection "
            "model? It's been flagging more false positives this week.\n\n"
            "Mike Rodriguez: Known issue. Data science is looking at it. That is not your "
            "problem this sprint. Your problem is SSO and admin controls. That's it.\n\n"
            "Alex Chen: Understood.\n\n"
            "Mike Rodriguez: Also — and I shouldn't have to say this — the GoodBad Score "
            "app is frozen. I saw a PR open for a new onboarding flow. Close it. We are "
            "not doing consumer onboarding flows in Q1."
        ),
        "decisions": [
            "SSO integration is the single highest priority — blocks TrustGuard deal",
            "Enterprise admin controls come after SSO, not before",
            "Model accuracy drift is a data science issue — not engineering's concern this sprint",
            "Consumer app PRs should be closed immediately — GoodBad Score app is frozen",
            "Sprint order is strictly: SSO → admin controls → nothing else",
        ],
        "participants": [
            {"name": "Mike Rodriguez", "role": "CTO"},
            {"name": "Alex Chen", "role": "Senior Engineer"},
        ],
    },
    {
        "title": "Product Sync — TrustGuard Feedback",
        "date": "2025-02-12",
        "transcript": (
            "Priya Nair (Head of Product): So I got off a call with TrustGuard. Good news "
            'and annoying news. Good news: they love the core detection product. Their '
            'words were "genuinely unsettling how accurate it is," which I\'m choosing to '
            "interpret as a compliment.\n\n"
            "Sarah Fisher (CEO): It is a compliment. What's the annoying news?\n\n"
            "Priya Nair: They want audit logs. Every classification event needs a timestamp, "
            "location, confidence score, and operator ID. For compliance reasons apparently.\n\n"
            "Sarah Fisher: How hard is that?\n\n"
            "Mike Rodriguez (CTO): Not hard. A week of work, maybe less. It's mostly a "
            "logging pipeline.\n\n"
            "Sarah Fisher: Okay add it to the sprint. But SSO still comes first. The audit "
            "logs are a pilot requirement but TrustGuard said they can start the pilot "
            "without them as long as SSO is done.\n\n"
            "Priya Nair: One more thing — they asked if we'd ever consider a mobile app "
            "for their field agents. Like a handheld version.\n\n"
            "Sarah Fisher: Tell them it's on the roadmap. Don't tell them when. We are not "
            "building a consumer-facing anything until Q2 at the earliest. Mobile is not "
            "happening in Q1.\n\n"
            "Mike Rodriguez: Agreed. No mobile, no consumer surface, nothing that isn't "
            "the enterprise dashboard."
        ),
        "decisions": [
            "Audit logging pipeline added to sprint — lower priority than SSO",
            "TrustGuard can begin pilot once SSO is complete — audit logs can follow",
            "Mobile app for field agents is NOT happening in Q1",
            "Any mobile or consumer-facing feature requests get pushed to Q2 roadmap",
            "SSO remains the critical path item — nothing changes that",
        ],
        "participants": [
            {"name": "Sarah Fisher", "role": "CEO"},
            {"name": "Mike Rodriguez", "role": "CTO"},
            {"name": "Priya Nair", "role": "Head of Product"},
        ],
    },
    {
        "title": "Investor Update Prep — a16z Check-in",
        "date": "2025-02-14",
        "transcript": (
            "Sarah Fisher (CEO): Okay so the a16z check-in is in two weeks. Here's what "
            "the narrative is: we pivoted fast, we have a hot enterprise prospect, and we "
            "are laser focused. I cannot walk into that meeting and tell them we split "
            "engineering between consumer and enterprise. That is a death sentence.\n\n"
            "Jordan Lee (Sales): TrustGuard is close. If I had to bet I'd say we get the "
            "LOI by end of February.\n\n"
            "Sarah Fisher: That's the story. One focused bet, enterprise only, one serious "
            "prospect about to sign. Mike, is there anything in the codebase that looks "
            "like we've been doing consumer work?\n\n"
            "Mike Rodriguez (CTO): There was a PR. I closed it. We're clean.\n\n"
            "Sarah Fisher: Good. The company narrative for a16z is: PreCrime.ai is the "
            "enterprise infrastructure play for physical security teams. We are not a "
            "consumer app. We are not a social credit score. We are a B2B API. Say it "
            "back to me.\n\n"
            "Jordan Lee: B2B API for enterprise physical security teams.\n\n"
            "Sarah Fisher: Perfect. Alex, I need the enterprise dashboard looking polished "
            "for a screen share demo. That is priority one after SSO.\n\n"
            "Alex Chen (Senior Eng): Got it. I can have it looking sharp in a few days.\n\n"
            "Sarah Fisher: Great. No consumer work, nothing experimental, nothing that "
            "isn't directly connected to closing TrustGuard or impressing a16z."
        ),
        "decisions": [
            "Company narrative: B2B API for enterprise physical security — not a consumer app",
            "All work must connect directly to closing TrustGuard or the a16z demo",
            "Enterprise dashboard needs to be polished and demo-ready after SSO",
            "No experimental features, no consumer work, nothing off-script before the investor meeting",
            "Jordan Lee to close TrustGuard LOI by end of February",
        ],
        "participants": [
            {"name": "Sarah Fisher", "role": "CEO"},
            {"name": "Mike Rodriguez", "role": "CTO"},
            {"name": "Alex Chen", "role": "Senior Engineer"},
            {"name": "Jordan Lee", "role": "Sales Lead"},
        ],
    },
    {
        "title": "Weekly Retro — What's Slowing Us Down",
        "date": "2025-02-15",
        "transcript": (
            "Mike Rodriguez (CTO): Quick retro. What's blocking people?\n\n"
            "Alex Chen (Senior Eng): Honestly the SSO implementation is going fine. My "
            "only concern is we keep getting Slack messages asking for small consumer "
            "features — the GoodBad Score leaderboard, the shareable profile cards thing. "
            "I don't know where those are coming from but it's distracting.\n\n"
            "Priya Nair (Head of Product): That's me, sorry. I was triaging old user "
            "requests from before the pivot. I'll stop.\n\n"
            "Mike Rodriguez: Please. We have one job right now.\n\n"
            "Alex Chen: Also — and I know this is not my call — but the model is "
            "classifying bald men as BAD at a rate that seems statistically notable.\n\n"
            "Mike Rodriguez: ...I'll flag that to data science.\n\n"
            "Sarah Fisher (CEO): Moving on. Jordan, where are we on TrustGuard?\n\n"
            "Jordan Lee (Sales): Demo is Tuesday. If SSO is live by Monday I think we "
            "close.\n\n"
            "Sarah Fisher: Alex, SSO by Monday.\n\n"
            "Alex Chen: It'll be done Sunday.\n\n"
            "Sarah Fisher: Good. Everything else is noise until TrustGuard signs. "
            "Leaderboards, profile cards, shareable badges, consumer onboarding — all "
            "of it is noise. We can revisit in Q2 if we're still alive."
        ),
        "decisions": [
            "Ignore all incoming consumer feature requests until Q2 — they are noise",
            "GoodBad Score leaderboard is not being built in Q1",
            "Shareable profile cards feature is not being built in Q1",
            "SSO must be live by Monday for TrustGuard demo on Tuesday",
            "Everything that is not SSO or TrustGuard prep is deprioritized until the deal closes",
        ],
        "participants": [
            {"name": "Sarah Fisher", "role": "CEO"},
            {"name": "Mike Rodriguez", "role": "CTO"},
            {"name": "Alex Chen", "role": "Senior Engineer"},
            {"name": "Priya Nair", "role": "Head of Product"},
            {"name": "Jordan Lee", "role": "Sales Lead"},
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
