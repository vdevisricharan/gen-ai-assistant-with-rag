from __future__ import annotations

from dataclasses import dataclass

from backend.errors import RAGError, provider_error


@dataclass(frozen=True)
class LLMResult:
    text: str
    tokens_used: int


class GeminiLLMClient:
    def __init__(self, api_key: str | None, model: str, temperature: float = 0.2):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
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

    def generate(self, prompt: str) -> LLMResult:
        try:
            client = self._get_client()
            from google.genai import types

            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=self.temperature),
            )
            text = (getattr(response, "text", None) or "").strip()
            return LLMResult(text=text, tokens_used=_extract_tokens_used(response))
        except Exception as exc:
            raise provider_error(exc) from exc


def _extract_tokens_used(response: object) -> int:
    usage = getattr(response, "usage_metadata", None)
    if usage is None:
        return 0

    if isinstance(usage, dict):
        total = usage.get("total_token_count") or usage.get("total_tokens")
        return int(total or 0)

    total = getattr(usage, "total_token_count", None) or getattr(
        usage, "total_tokens", None
    )
    if total is not None:
        return int(total)

    prompt_tokens = getattr(usage, "prompt_token_count", 0) or 0
    candidate_tokens = getattr(usage, "candidates_token_count", 0) or 0
    return int(prompt_tokens) + int(candidate_tokens)
