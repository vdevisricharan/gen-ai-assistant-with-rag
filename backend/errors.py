from __future__ import annotations


class RAGError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def provider_error(exc: Exception) -> RAGError:
    if isinstance(exc, RAGError):
        return exc

    text = str(exc).lower()
    if (
        "api key" in text
        or "apikey" in text
        or "unauthenticated" in text
        or "permission denied" in text
        or "401" in text
        or "403" in text
    ):
        return RAGError("Invalid API key", 401)

    if (
        "rate limit" in text
        or "resource_exhausted" in text
        or "quota" in text
        or "429" in text
    ):
        return RAGError("Rate limit exceeded", 429)

    if "timeout" in text or "timed out" in text or "deadline" in text:
        return RAGError("Request timeout", 504)

    return RAGError("LLM provider request failed", 502)
