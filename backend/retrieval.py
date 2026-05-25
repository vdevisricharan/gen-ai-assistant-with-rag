from __future__ import annotations

import math
from dataclasses import dataclass

from backend.storage import StoredChunk


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: StoredChunk
    score: float


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0

    dot_product = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0

    return dot_product / (left_norm * right_norm)


def retrieve_chunks(
    query_embedding: list[float],
    chunks: list[StoredChunk],
    top_k: int = 3,
    threshold: float = 0.75,
) -> list[RetrievedChunk]:
    ranked = sorted(
        (
            RetrievedChunk(
                chunk=chunk,
                score=cosine_similarity(query_embedding, chunk.embedding),
            )
            for chunk in chunks
        ),
        key=lambda item: item.score,
        reverse=True,
    )

    top_results = ranked[:top_k]
    if not top_results or top_results[0].score < threshold:
        return []

    return [result for result in top_results if result.score >= threshold]
