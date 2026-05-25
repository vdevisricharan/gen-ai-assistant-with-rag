from backend.llm import LLMResult
from backend.rag import INSUFFICIENT_INFORMATION_REPLY, RAGService, build_prompt
from backend.retrieval import RetrievedChunk
from backend.storage import ChatMessage, Database, StoredChunk


class FakeEmbeddingClient:
    def __init__(self, embedding):
        self.embedding = embedding

    def embed_text(self, _text):
        return self.embedding


class FakeLLMClient:
    def __init__(self, text="grounded answer"):
        self.text = text
        self.prompts = []

    def generate(self, prompt):
        self.prompts.append(prompt)
        return LLMResult(text=self.text, tokens_used=12)


def test_build_prompt_includes_context_history_and_question():
    chunk = StoredChunk(1, 1, "Reset Password", 0, "Reset from Settings.", [1.0])

    prompt = build_prompt(
        retrieved_chunks=[RetrievedChunk(chunk=chunk, score=0.91)],
        history=[ChatMessage(role="user", content="hello")],
        question="How do I reset it?",
    )

    assert "Reset from Settings." in prompt
    assert "User: hello" in prompt
    assert "How do I reset it?" in prompt


def test_chat_returns_insufficient_information_when_no_chunk_matches(tmp_path):
    database = Database(tmp_path / "rag.sqlite3")
    document_id = database.insert_document("Other", "Other")
    database.insert_chunk(document_id, "Other", 0, "Other", [0.0, 1.0])
    service = RAGService(
        database=database,
        embedding_client=FakeEmbeddingClient([1.0, 0.0]),
        llm_client=FakeLLMClient(),
        top_k=1,
        similarity_threshold=0.75,
    )

    result = service.chat("s1", "unknown")

    assert result.reply == INSUFFICIENT_INFORMATION_REPLY
    assert result.retrieved_chunks == 0


def test_chat_uses_llm_when_chunk_matches(tmp_path):
    database = Database(tmp_path / "rag.sqlite3")
    document_id = database.insert_document("Reset Password", "Reset")
    database.insert_chunk(document_id, "Reset Password", 0, "Reset content", [1.0, 0.0])
    llm = FakeLLMClient("Use Settings > Security.")
    service = RAGService(
        database=database,
        embedding_client=FakeEmbeddingClient([1.0, 0.0]),
        llm_client=llm,
        top_k=1,
        similarity_threshold=0.75,
    )

    result = service.chat("s1", "How do I reset my password?")

    assert result.reply == "Use Settings > Security."
    assert result.tokens_used == 12
    assert result.retrieved_chunks == 1
    assert "Reset content" in llm.prompts[0]
