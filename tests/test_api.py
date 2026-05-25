from fastapi.testclient import TestClient

from backend.main import app, get_database, get_service
from backend.rag import ChatResult


class FakeDatabase:
    path = "memory"

    def __init__(self, chunks=0):
        self.chunks = chunks

    def count_chunks(self):
        return self.chunks


class FakeService:
    def chat(self, session_id, message):
        assert session_id == "abc123"
        assert message == "How can I reset my password?"
        return ChatResult(
            reply="Users can reset their password from Settings > Security.",
            tokens_used=120,
            retrieved_chunks=3,
        )


def test_health_reports_indexed_chunk_count():
    app.dependency_overrides[get_database] = lambda: FakeDatabase(chunks=4)
    client = TestClient(app)

    response = client.get("/health")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["indexedChunks"] == 4


def test_chat_endpoint_returns_response_shape():
    app.dependency_overrides[get_service] = lambda: FakeService()
    client = TestClient(app)

    response = client.post(
        "/api/chat",
        json={
            "sessionId": "abc123",
            "message": "How can I reset my password?",
        },
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {
        "reply": "Users can reset their password from Settings > Security.",
        "tokensUsed": 120,
        "retrievedChunks": 3,
    }


def test_chat_endpoint_rejects_empty_message():
    client = TestClient(app)

    response = client.post(
        "/api/chat",
        json={
            "sessionId": "abc123",
            "message": "",
        },
    )

    assert response.status_code == 422
