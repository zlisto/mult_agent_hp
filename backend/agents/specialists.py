"""Per-book specialist agents — answer from retrieved chunks only."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from pydantic_ai import Agent
from pydantic_ai.usage import UsageLimits

from models import BOOK_CATALOG
from retrieval import format_evidence, get_book_meta, retrieve_chunks

from .config import build_model

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"
SPECIALIST_BASE = (PROMPTS / "specialist.md").read_text(encoding="utf-8")

_BY_NUM = {b["book_number"]: b for b in BOOK_CATALOG}


def book_label(book_number: int) -> str:
    meta = _BY_NUM.get(book_number) or {}
    db = get_book_meta(book_number)
    title = db.get("title") or meta.get("title") or f"Book {book_number}"
    return f"Book {book_number} Labubu — {title}"


async def run_specialist(book_number: int, question: str) -> dict:
    """Run one book specialist with retrieval-capped evidence."""
    if book_number < 1 or book_number > 7:
        return {
            "book_number": book_number,
            "book_title": "Unknown",
            "agent": f"Book {book_number} Labubu",
            "question": question,
            "reply": "Invalid book_number; use 1–7.",
            "status": "error",
            "passages_used": 0,
        }

    meta = get_book_meta(book_number)
    catalog = _BY_NUM[book_number]
    title = meta["title"]
    agent_name = f"Book {book_number} Labubu"

    chunks = retrieve_chunks(book_number, question)
    evidence = format_evidence(chunks)

    instructions = (
        f"{SPECIALIST_BASE}\n\n"
        f"## Your assignment\n"
        f"- Agent: {agent_name}\n"
        f"- Book: {title}\n"
        f"- Specialty blurb: {catalog['specialty']}\n\n"
        f"## EVIDENCE (from your book only)\n\n{evidence}\n"
    )

    agent: Agent[None, str] = Agent(
        build_model(),
        instructions=instructions,
        output_type=str,
    )

    try:
        result = await agent.run(
            question,
            usage_limits=UsageLimits(request_limit=4),
        )
        reply = (result.output or "").strip()
        status = "done"
    except Exception as exc:
        reply = f"Specialist error ({type(exc).__name__}): {exc}"[:500]
        status = "error"

    return {
        "book_number": book_number,
        "book_title": title,
        "agent": agent_name,
        "question": question,
        "reply": reply,
        "status": status,
        "passages_used": len(chunks),
    }
