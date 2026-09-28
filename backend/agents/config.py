"""Portkey / model configuration (Lecture 9 pattern)."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
ROOT = BACKEND.parent  # Lecture 10
ZLISTO = ROOT.parent  # test_student/zlisto

load_dotenv(ROOT / ".env")
load_dotenv(ZLISTO / ".env")

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-6-astra").strip() or "gpt-6-astra"
PORTKEY_BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1").rstrip("/")
BOSS_NAME = "Headmaster Labubledore"


def require_api_key() -> str:
    key = os.getenv("PORTKEY_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "PORTKEY_API_KEY is not set. Put it in test_student/zlisto/.env "
            "or Lecture 10/.env (see .env.example)."
        )
    return key


def build_model() -> OpenAIResponsesModel:
    api_key = require_api_key()
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=PORTKEY_BASE_URL,
        default_headers={"x-portkey-api-key": api_key},
    )
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))
