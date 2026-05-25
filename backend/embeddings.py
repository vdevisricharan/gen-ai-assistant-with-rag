from __future__ import annotations

from backend.errors import RAGError, provider_error


def prepare_document_for_embedding(title: str, text: str) -> str:
    safe_title = title.strip() or "none"
    return f"title: {safe_title} | text: {text.strip()}"


def prepare_query_for_embedding(query: str) -> str:
    return f"task: question answering | query: {query.strip()}"


class GeminiEmbeddingClient:
    def __init__(self, api_key: str | None, model: str):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if not self.api_key:
            raise RAGError("Invalid API key", 401)
        if self._client is None:
            try:
                from google import genai
            except ImportError as exc:
                raise RAGError(
                    "Gemini SDK is not installed. Run pip install -r requirements.txt.",
                    500,
                ) from exc
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def embed_text(self, text: str) -> list[float]:
        try:
            result = self._get_client().models.embed_content(
                model=self.model,
                contents=text,
            )
            embedding = result.embeddings[0]
            return [float(value) for value in embedding.values]
        except Exception as exc:
            raise provider_error(exc) from exc
