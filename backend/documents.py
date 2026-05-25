from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KnowledgeDocument:
    title: str
    content: str


def load_documents(path: Path) -> list[KnowledgeDocument]:
    with path.open("r", encoding="utf-8") as file:
        raw_documents = json.load(file)

    if not isinstance(raw_documents, list):
        raise ValueError("docs.json must contain a list of documents")

    documents: list[KnowledgeDocument] = []
    for index, item in enumerate(raw_documents):
        if not isinstance(item, dict):
            raise ValueError(f"Document {index} must be an object")
        title = str(item.get("title", "")).strip()
        content = str(item.get("content", "")).strip()
        if not title or not content:
            raise ValueError(f"Document {index} must include title and content")
        documents.append(KnowledgeDocument(title=title, content=content))

    return documents
