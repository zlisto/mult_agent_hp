"""Shared API / agent result models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


BOOK_CATALOG: list[dict[str, Any]] = [
    {
        "book_number": 1,
        "title": "Harry Potter and the Sorcerer's Stone",
        "short": "Sorcerer's Stone",
        "specialty": (
            "Year 1 at Hogwarts: the Philosopher's/Sorcerer's Stone, "
            "Nicolas Flamel, Quirrell, and Voldemort's first return."
        ),
        "accent": "#c41e3a",
        "house_hint": "Gryffindor scarlet",
    },
    {
        "book_number": 2,
        "title": "Harry Potter and the Chamber of Secrets",
        "short": "Chamber of Secrets",
        "specialty": (
            "Year 2: the Chamber, the basilisk, Tom Riddle's diary "
            "(a Horcrux), and Ginny Weasley."
        ),
        "accent": "#1a472a",
        "house_hint": "Slytherin green",
    },
    {
        "book_number": 3,
        "title": "Harry Potter and the Prisoner of Azkaban",
        "short": "Prisoner of Azkaban",
        "specialty": (
            "Year 3: Sirius Black, Remus Lupin, the Marauders, "
            "the Time-Turner, and Pettigrew's reveal."
        ),
        "accent": "#946b2d",
        "house_hint": "amber / time",
    },
    {
        "book_number": 4,
        "title": "Harry Potter and the Goblet of Fire",
        "short": "Goblet of Fire",
        "specialty": (
            "Year 4: Triwizard Tournament, Barty Crouch Jr., "
            "Voldemort's rebirth in the graveyard, Priori Incantatem."
        ),
        "accent": "#0e1a40",
        "house_hint": "Ravenclaw navy",
    },
    {
        "book_number": 5,
        "title": "Harry Potter and the Order of the Phoenix",
        "short": "Order of the Phoenix",
        "specialty": (
            "Year 5: Umbridge, the Order, the Department of Mysteries, "
            "the prophecy, and Sirius's fate."
        ),
        "accent": "#eeba30",
        "house_hint": "Hufflepuff gold",
    },
    {
        "book_number": 6,
        "title": "Harry Potter and the Half-Blood Prince",
        "short": "Half-Blood Prince",
        "specialty": (
            "Year 6: Slughorn's memories, Horcrux lore explained, "
            "the locket, the cave, and Dumbledore's death."
        ),
        "accent": "#5d4e6d",
        "house_hint": "prince purple",
    },
    {
        "book_number": 7,
        "title": "Harry Potter and the Deathly Hallows",
        "short": "Deathly Hallows",
        "specialty": (
            "Final book: Horcrux hunt and destruction, the Hallows, "
            "the Battle of Hogwarts, and Voldemort's end."
        ),
        "accent": "#111111",
        "house_hint": "Deathly black",
    },
]


class Delegation(BaseModel):
    agent: str
    book_number: int
    book_title: str
    question: str
    reply: str = ""
    status: Literal["pending", "running", "done", "error"] = "pending"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    answer: str
    delegations: list[Delegation] = Field(default_factory=list)
    trace: list[dict[str, Any]] = Field(default_factory=list)
    boss_name: str = "Headmaster Labubledore"


class ProgressEvent(BaseModel):
    type: str
    data: dict[str, Any] = Field(default_factory=dict)
