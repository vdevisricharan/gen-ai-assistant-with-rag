from __future__ import annotations

import re


TOKEN_PATTERN = re.compile(r"\S+")


def count_tokens(text: str) -> int:
    return len(TOKEN_PATTERN.findall(text))


def chunk_text(text: str, chunk_size: int = 420, overlap: int = 50) -> list[str]:
    text = " ".join(text.split())
    if not text:
        return []

    words = text.split()
    if len(words) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = max(end - overlap, start + 1)

    return chunks
