from backend.chunking import chunk_text, count_tokens


def test_short_text_returns_single_chunk():
    chunks = chunk_text("one two three", chunk_size=5, overlap=1)

    assert chunks == ["one two three"]


def test_long_text_chunks_with_overlap():
    text = " ".join(f"word{i}" for i in range(10))

    chunks = chunk_text(text, chunk_size=4, overlap=1)

    assert chunks == [
        "word0 word1 word2 word3",
        "word3 word4 word5 word6",
        "word6 word7 word8 word9",
    ]
    assert all(count_tokens(chunk) <= 4 for chunk in chunks)
