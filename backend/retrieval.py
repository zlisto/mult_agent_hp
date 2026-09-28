"""Keyword chunk retrieval from harrypotter.db — never load full books into prompts."""

from __future__ import annotations

import re
import sqlite3
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DB_PATH = ROOT / "harrypotter.db"

# ~8–12k tokens of evidence (rough char proxy; ~4 chars/token)
MAX_EVIDENCE_CHARS = 40_000
CHUNK_SIZE = 1_200
CHUNK_OVERLAP = 200
TOP_CHUNKS = 18


def _connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Missing database: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@lru_cache(maxsize=8)
def get_book_meta(book_number: int) -> dict:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT book_number, title, source_pdf, page_count,
                   char_count, token_count, tokenizer
            FROM books WHERE book_number = ?
            """,
            (book_number,),
        ).fetchone()
    if row is None:
        raise ValueError(f"Unknown book_number={book_number}")
    return dict(row)


@lru_cache(maxsize=8)
def _book_text(book_number: int) -> str:
    with _connect() as conn:
        row = conn.execute(
            "SELECT text FROM books WHERE book_number = ?",
            (book_number,),
        ).fetchone()
    if row is None:
        raise ValueError(f"Unknown book_number={book_number}")
    return row["text"]


def _tokenize_query(q: str) -> list[str]:
    words = re.findall(r"[a-zA-Z']{3,}", q.lower())
    stop = {
        "the",
        "and",
        "for",
        "that",
        "with",
        "this",
        "from",
        "what",
        "when",
        "where",
        "which",
        "how",
        "who",
        "are",
        "was",
        "were",
        "did",
        "does",
        "have",
        "has",
        "had",
        "about",
        "into",
        "each",
        "book",
        "harry",
        "potter",
    }
    return [w for w in words if w not in stop]


def _chunk_text(text: str) -> list[tuple[int, str]]:
    chunks: list[tuple[int, str]] = []
    n = len(text)
    i = 0
    idx = 0
    while i < n:
        end = min(i + CHUNK_SIZE, n)
        piece = text[i:end].strip()
        if piece:
            chunks.append((idx, piece))
            idx += 1
        if end >= n:
            break
        i = max(end - CHUNK_OVERLAP, i + 1)
    return chunks


def _score_chunk(chunk: str, terms: list[str]) -> float:
    if not terms:
        return 0.0
    lower = chunk.lower()
    score = 0.0
    for t in terms:
        count = lower.count(t)
        if count:
            # longer rare-ish terms weigh more
            score += count * (1.0 + min(len(t), 12) / 12.0)
    # light boost for phrase-ish pairs
    for a, b in zip(terms, terms[1:]):
        if f"{a} {b}" in lower:
            score += 3.0
    return score


def retrieve_chunks(book_number: int, question: str, max_chars: int = MAX_EVIDENCE_CHARS) -> list[str]:
    """Return the most relevant text chunks for a question from one book."""
    text = _book_text(book_number)
    terms = _tokenize_query(question)
    chunks = _chunk_text(text)
    if not chunks:
        return []

    scored = [( _score_chunk(c, terms), i, c) for i, c in chunks]
    scored.sort(key=lambda x: (-x[0], x[1]))

    # Always keep some top hits even if scores are low
    selected: list[tuple[int, str]] = []
    used = 0
    for score, idx, chunk in scored[:TOP_CHUNKS]:
        if used + len(chunk) > max_chars and selected:
            break
        selected.append((idx, chunk))
        used += len(chunk)

    # If query terms matched nothing, take early narrative slices (still capped)
    if not selected or all(_score_chunk(c, terms) == 0 for _, c in selected):
        selected = []
        used = 0
        for idx, chunk in chunks[:12]:
            if used + len(chunk) > max_chars:
                break
            selected.append((idx, chunk))
            used += len(chunk)

    selected.sort(key=lambda x: x[0])
    return [c for _, c in selected]


def format_evidence(chunks: list[str]) -> str:
    if not chunks:
        return "(No relevant passages retrieved.)"
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(f"[Passage {i}]\n{c}")
    return "\n\n".join(parts)


def list_books() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT book_number, title, page_count, token_count
            FROM books ORDER BY book_number
            """
        ).fetchall()
    return [dict(r) for r in rows]
