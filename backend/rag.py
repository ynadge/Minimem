"""
RAG (Retrieval-Augmented Generation) module for MiniMem.
Handles vector search against meeting decisions and LLM-based alignment checking.
"""

import json
import os
from typing import Any, Dict, List

import numpy as np
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SIMILARITY_THRESHOLD = 0.75


async def generate_embedding(text: str) -> np.ndarray:
    """Generate an OpenAI embedding vector for the given text."""
    response = await client.embeddings.create(
        model="text-embedding-ada-002",
        input=text,
    )
    return np.array(response.data[0].embedding)


async def find_relevant_context(
    pool, conversation_text: str, top_k: int = 3
) -> List[Dict]:
    """
    Embed the conversation text and find the most semantically similar
    decisions in the database using pgvector cosine similarity.
    Returns top_k decisions with their source meeting info.
    """
    query_embedding = await generate_embedding(conversation_text)

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                d.content                           AS decision,
                m.title                             AS meeting_title,
                m.date                              AS meeting_date,
                1 - (d.embedding <=> $1::vector)    AS similarity
            FROM decisions d
            JOIN meetings m ON d.meeting_id = m.id
            ORDER BY d.embedding <=> $1::vector
            LIMIT $2
            """,
            query_embedding,
            top_k,
        )

    return [
        {
            "decision": row["decision"],
            "meeting_title": row["meeting_title"],
            "meeting_date": str(row["meeting_date"]),
            "similarity": float(row["similarity"]),
        }
        for row in rows
    ]


async def check_alignment(
    pool, conversation_history: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Analyze the recent conversation against stored meeting decisions.

    Steps:
      1. Concatenate the last 4 messages into a query string
      2. Run vector search to find the most relevant decisions
      3. If the best match similarity is below threshold, return aligned
      4. Otherwise, pass conversation + decisions to GPT to judge alignment
      5. Return structured result for the frontend
    """
    recent_msgs = conversation_history[-4:]
    conversation_text = "\n".join(
        f"{msg['sender'].capitalize()}: {msg['content']}" for msg in recent_msgs
    )

    relevant_context = await find_relevant_context(pool, conversation_text, top_k=4)

    # No meaningful context found — treat as aligned
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
        f'- "{ctx["decision"]}" (from "{ctx["meeting_title"]}", {ctx["meeting_date"]})'
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
        temperature=0,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    result = json.loads(raw)

    # Attach vector search metadata
    result["meeting_date"] = relevant_context[0]["meeting_date"]
    result["similarity"] = relevant_context[0]["similarity"]

    return result
