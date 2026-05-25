from backend.retrieval import cosine_similarity, retrieve_chunks
from backend.storage import StoredChunk


def _chunk(chunk_id, embedding):
    return StoredChunk(
        id=chunk_id,
        document_id=1,
        title=f"Doc {chunk_id}",
        chunk_index=0,
        text=f"Chunk {chunk_id}",
        embedding=embedding,
    )


def test_cosine_similarity_scores_identical_vectors_as_one():
    assert cosine_similarity([1, 0, 0], [1, 0, 0]) == 1.0


def test_retrieve_chunks_ranks_and_applies_threshold():
    chunks = [_chunk(1, [1, 0]), _chunk(2, [0, 1])]

    results = retrieve_chunks([1, 0], chunks, top_k=2, threshold=0.75)

    assert len(results) == 1
    assert results[0].chunk.id == 1


def test_retrieve_chunks_returns_empty_when_best_score_is_low():
    chunks = [_chunk(1, [0, 1])]

    results = retrieve_chunks([1, 0], chunks, top_k=1, threshold=0.75)

    assert results == []
