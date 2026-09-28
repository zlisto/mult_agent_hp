"""Headmaster Labubledore — delegates to book specialists via PydanticAI tools."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import UsageLimits

from models import BOOK_CATALOG, ChatResponse, Delegation

from .config import BOSS_NAME, MODEL_NAME, build_model, require_api_key
from .specialists import run_specialist

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"
BOSS_PROMPT = (PROMPTS / "boss.md").read_text(encoding="utf-8")


@dataclass
class BossDeps:
    event_queue: asyncio.Queue[dict[str, Any] | None]
    delegations: list[Delegation] = field(default_factory=list)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def emit(self, event_type: str, **data: Any) -> None:
        await self.event_queue.put({"type": event_type, "data": data})


def _roster_block() -> str:
    lines = []
    for b in BOOK_CATALOG:
        lines.append(
            f"- Book {b['book_number']}: {b['title']} — {b['specialty']}"
        )
    return "\n".join(lines)


def _build_boss_agent() -> Agent[BossDeps, str]:
    require_api_key()
    instructions = (
        f"{BOSS_PROMPT}\n\n"
        f"## Live roster\n{_roster_block()}\n"
    )
    agent: Agent[BossDeps, str] = Agent(
        build_model(),
        deps_type=BossDeps,
        instructions=instructions,
        output_type=str,
    )

    @agent.tool
    async def ask_book_specialist(
        ctx: RunContext[BossDeps],
        book_number: int,
        question: str,
    ) -> dict[str, Any]:
        """Ask one book specialist Labubu a focused question about their novel.

        Args:
            book_number: Integer 1–7 for the Harry Potter book.
            question: Focused sub-question for that book only.
        """
        deps = ctx.deps
        catalog = next(
            (b for b in BOOK_CATALOG if b["book_number"] == book_number),
            None,
        )
        title = catalog["title"] if catalog else f"Book {book_number}"
        agent_name = f"Book {book_number} Labubu"

        delegation = Delegation(
            agent=agent_name,
            book_number=book_number,
            book_title=title,
            question=question,
            reply="",
            status="running",
        )
        async with deps.lock:
            deps.delegations.append(delegation)
            index = len(deps.delegations) - 1

        await deps.emit(
            "specialist_started",
            book_number=book_number,
            book_title=title,
            agent=agent_name,
            question=question,
            index=index,
        )

        result = await run_specialist(book_number, question)

        async with deps.lock:
            deps.delegations[index] = Delegation(
                agent=result["agent"],
                book_number=result["book_number"],
                book_title=result["book_title"],
                question=result["question"],
                reply=result["reply"],
                status=result["status"],  # type: ignore[arg-type]
            )

        await deps.emit(
            "specialist_done",
            book_number=result["book_number"],
            book_title=result["book_title"],
            agent=result["agent"],
            question=result["question"],
            reply=result["reply"],
            status=result["status"],
            passages_used=result.get("passages_used", 0),
            index=index,
        )
        return {
            "agent": result["agent"],
            "book_number": result["book_number"],
            "book_title": result["book_title"],
            "reply": result["reply"],
            "status": result["status"],
        }

    return agent


async def run_boss_chat_stream(message: str) -> AsyncIterator[dict[str, Any]]:
    """Yield progress events, then a final `result` event."""
    queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
    deps = BossDeps(event_queue=queue)

    async def _runner() -> None:
        try:
            await deps.emit("boss_thinking", boss=BOSS_NAME, model=MODEL_NAME)
            agent = _build_boss_agent()
            result = await agent.run(
                message,
                deps=deps,
                usage_limits=UsageLimits(request_limit=16),
            )
            answer = (result.output or "").strip()
            response = ChatResponse(
                answer=answer,
                delegations=list(deps.delegations),
                trace=[],
                boss_name=BOSS_NAME,
            )
            await queue.put(
                {"type": "final", "data": response.model_dump()}
            )
        except Exception as exc:
            detail = f"{type(exc).__name__}: {exc}"[:500]
            response = ChatResponse(
                answer=(
                    f"Sorry — {BOSS_NAME} hit an error and could not finish. "
                    f"({detail})"
                ),
                delegations=list(deps.delegations),
                boss_name=BOSS_NAME,
            )
            await queue.put(
                {
                    "type": "error",
                    "data": {
                        "message": detail,
                        **response.model_dump(),
                    },
                }
            )
        finally:
            await queue.put(None)

    task = asyncio.create_task(_runner())
    try:
        while True:
            event = await queue.get()
            if event is None:
                break
            yield event
    finally:
        await task


async def run_boss_chat(message: str) -> dict[str, Any]:
    """Non-streaming convenience wrapper."""
    final: dict[str, Any] | None = None
    trace: list[dict[str, Any]] = []
    async for event in run_boss_chat_stream(message):
        if event["type"] == "final":
            final = event["data"]
        elif event["type"] == "error":
            final = {
                "answer": event["data"].get("answer", ""),
                "delegations": event["data"].get("delegations", []),
                "boss_name": BOSS_NAME,
                "trace": trace,
            }
            break
        else:
            trace.append(event)
    if final is None:
        final = {
            "answer": "No response produced.",
            "delegations": [],
            "boss_name": BOSS_NAME,
        }
    final["trace"] = trace
    return final
