from __future__ import annotations

from backend.chunking import chunk_text
from backend.config import get_settings
from backend.documents import load_documents
from backend.embeddings import GeminiEmbeddingClient, prepare_document_for_embedding
from backend.errors import RAGError
from backend.storage import Database


def ingest_documents() -> int:
    settings = get_settings()
    database = Database(settings.database_path)
    embedding_client = GeminiEmbeddingClient(
        api_key=settings.embedding_api_key,
        model=settings.embedding_model,
    )

    documents = load_documents(settings.docs_path)
    database.reset_index()

    chunk_total = 0
    for document in documents:
        document_id = database.insert_document(document.title, document.content)
        for chunk_index, chunk in enumerate(chunk_text(document.content)):
            embedding_input = prepare_document_for_embedding(document.title, chunk)
            embedding = embedding_client.embed_text(embedding_input)
            database.insert_chunk(
                document_id=document_id,
                title=document.title,
                chunk_index=chunk_index,
                text=chunk,
                embedding=embedding,
            )
            chunk_total += 1

    return chunk_total


def main() -> int:
    try:
        chunk_total = ingest_documents()
    except RAGError as exc:
        print(f"Indexing failed: {exc.message}")
        return 1
    except Exception as exc:
        print(f"Indexing failed: {exc}")
        return 1

    print(f"Indexed {chunk_total} chunks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
