from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StoredChunk:
    id: int
    document_id: int
    title: str
    chunk_index: int
    text: str
    embedding: list[float]


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def init_db(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(document_id) REFERENCES documents(id)
                );

                CREATE INDEX IF NOT EXISTS idx_chunks_document_id
                    ON chunks(document_id);

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_messages_session_id_id
                    ON messages(session_id, id);
                """
            )

    def reset_index(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM chunks")
            connection.execute("DELETE FROM documents")

    def insert_document(self, title: str, content: str) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO documents (title, content) VALUES (?, ?)",
                (title, content),
            )
            return int(cursor.lastrowid)

    def insert_chunk(
        self,
        document_id: int,
        title: str,
        chunk_index: int,
        text: str,
        embedding: list[float],
    ) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO chunks
                    (document_id, title, chunk_index, text, embedding)
                VALUES (?, ?, ?, ?, ?)
                """,
                (document_id, title, chunk_index, text, json.dumps(embedding)),
            )
            return int(cursor.lastrowid)

    def fetch_chunks(self) -> list[StoredChunk]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, document_id, title, chunk_index, text, embedding
                FROM chunks
                ORDER BY id
                """
            ).fetchall()

        return [
            StoredChunk(
                id=int(row["id"]),
                document_id=int(row["document_id"]),
                title=str(row["title"]),
                chunk_index=int(row["chunk_index"]),
                text=str(row["text"]),
                embedding=[float(value) for value in json.loads(row["embedding"])],
            )
            for row in rows
        ]

    def count_chunks(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM chunks").fetchone()
            return int(row["count"])

    def append_message(self, session_id: str, role: str, content: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO messages (session_id, role, content)
                VALUES (?, ?, ?)
                """,
                (session_id, role, content),
            )

    def fetch_recent_messages(
        self, session_id: str, pair_limit: int = 5
    ) -> list[ChatMessage]:
        row_limit = pair_limit * 2
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT role, content
                FROM messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, row_limit),
            ).fetchall()

        return [
            ChatMessage(role=str(row["role"]), content=str(row["content"]))
            for row in reversed(rows)
        ]
