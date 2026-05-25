from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    docs_path: Path
    database_path: Path
    llm_api_key: str | None
    embedding_api_key: str | None
    llm_model: str
    embedding_model: str
    similarity_threshold: float
    top_k: int
    history_pairs: int
    llm_temperature: float


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    return float(value)


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


@lru_cache
def get_settings() -> Settings:
    load_dotenv(BASE_DIR / ".env")

    llm_api_key = (
        os.getenv("LLM_API_KEY")
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )
    embedding_api_key = os.getenv("EMBEDDING_API_KEY") or llm_api_key

    database_path = Path(os.getenv("DATABASE_PATH", "./rag.sqlite3"))
    if not database_path.is_absolute():
        database_path = BASE_DIR / database_path

    return Settings(
        docs_path=BASE_DIR / "backend" / "docs.json",
        database_path=database_path,
        llm_api_key=llm_api_key,
        embedding_api_key=embedding_api_key,
        llm_model=os.getenv("LLM_MODEL", "gemini-2.5-flash"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "gemini-embedding-2"),
        similarity_threshold=_get_float("SIMILARITY_THRESHOLD", 0.75),
        top_k=_get_int("TOP_K", 3),
        history_pairs=_get_int("HISTORY_PAIRS", 5),
        llm_temperature=_get_float("LLM_TEMPERATURE", 0.2),
    )
