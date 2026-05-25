from __future__ import annotations

from dataclasses import dataclass

from backend.embeddings import (
    GeminiEmbeddingClient,
    prepare_query_for_embedding,
)
from backend.llm import GeminiLLMClient
from backend.retrieval import RetrievedChunk, retrieve_chunks
from backend.storage import ChatMessage, Database


INSUFFICIENT_INFORMATION_REPLY = "I do not have enough information to answer that."


@dataclass(frozen=True)
class ChatResult:
    reply: str
    tokens_used: int
    retrieved_chunks: int


class RAGService:
    def __init__(
        self,
        database: Database,
        embedding_client: GeminiEmbeddingClient,
        llm_client: GeminiLLMClient,
        top_k: int = 3,
        similarity_threshold: float = 0.75,
        history_pairs: int = 5,
    ):
        self.database = database
        self.embedding_client = embedding_client
        self.llm_client = llm_client
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.history_pairs = history_pairs

    def chat(self, session_id: str, message: str) -> ChatResult:
        query_embedding = self.embedding_client.embed_text(
            prepare_query_for_embedding(message)
        )
        retrieved = retrieve_chunks(
            query_embedding=query_embedding,
            chunks=self.database.fetch_chunks(),
            top_k=self.top_k,
            threshold=self.similarity_threshold,
        )

        if not retrieved:
            self._store_exchange(
                session_id=session_id,
                user_message=message,
                assistant_message=INSUFFICIENT_INFORMATION_REPLY,
            )
            return ChatResult(
                reply=INSUFFICIENT_INFORMATION_REPLY,
                tokens_used=0,
                retrieved_chunks=0,
            )

        history = self.database.fetch_recent_messages(
            session_id=session_id,
            pair_limit=self.history_pairs,
        )
        prompt = build_prompt(
            retrieved_chunks=retrieved,
            history=history,
            question=message,
        )
        llm_result = self.llm_client.generate(prompt)
        reply = llm_result.text or INSUFFICIENT_INFORMATION_REPLY

        self._store_exchange(
            session_id=session_id,
            user_message=message,
            assistant_message=reply,
        )
        return ChatResult(
            reply=reply,
            tokens_used=llm_result.tokens_used,
            retrieved_chunks=len(retrieved),
        )

    def _store_exchange(
        self, session_id: str, user_message: str, assistant_message: str
    ) -> None:
        self.database.append_message(session_id, "user", user_message)
        self.database.append_message(session_id, "assistant", assistant_message)


def build_prompt(
    retrieved_chunks: list[RetrievedChunk],
    history: list[ChatMessage],
    question: str,
) -> str:
    context = "\n\n".join(
        (
            f"[{index}] Title: {item.chunk.title}\n"
            f"Similarity: {item.score:.3f}\n"
            f"{item.chunk.text}"
        )
        for index, item in enumerate(retrieved_chunks, start=1)
    )
    history_text = _format_history(history)

    return f"""You are a helpful assistant.
Use only the provided context to answer the user's question.
If the context does not contain the answer, say exactly:
{INSUFFICIENT_INFORMATION_REPLY}

Context:
{context}

History:
{history_text}

Question:
{question}

Answer:"""


def _format_history(history: list[ChatMessage]) -> str:
    if not history:
        return "No prior conversation."

    return "\n".join(
        f"{'User' if message.role == 'user' else 'Assistant'}: {message.content}"
        for message in history
    )
