from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.config import BASE_DIR, get_settings
from backend.embeddings import GeminiEmbeddingClient
from backend.errors import RAGError
from backend.llm import GeminiLLMClient
from backend.rag import RAGService
from backend.storage import Database


FRONTEND_DIR = BASE_DIR / "frontend"


class ChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(alias="sessionId")
    message: str

    @field_validator("session_id", "message")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("must not be empty")
        return value.strip()


class ChatResponse(BaseModel):
    reply: str
    tokensUsed: int
    retrievedChunks: int


@lru_cache
def get_database() -> Database:
    return Database(get_settings().database_path)


@lru_cache
def get_service() -> RAGService:
    settings = get_settings()
    return RAGService(
        database=get_database(),
        embedding_client=GeminiEmbeddingClient(
            api_key=settings.embedding_api_key,
            model=settings.embedding_model,
        ),
        llm_client=GeminiLLMClient(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
        ),
        top_k=settings.top_k,
        similarity_threshold=settings.similarity_threshold,
        history_pairs=settings.history_pairs,
    )


app = FastAPI(title="GenAI RAG Chatbot")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.exception_handler(RAGError)
async def rag_error_handler(_: Request, exc: RAGError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.message})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return await request_validation_exception_handler(request, exc)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(Path(FRONTEND_DIR) / "index.html")


@app.get("/health")
def health(database: Database = Depends(get_database)) -> dict[str, object]:
    return {
        "status": "ok",
        "indexedChunks": database.count_chunks(),
        "database": str(database.path),
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    service: RAGService = Depends(get_service),
) -> ChatResponse:
    result = service.chat(session_id=request.session_id, message=request.message)
    return ChatResponse(
        reply=result.reply,
        tokensUsed=result.tokens_used,
        retrievedChunks=result.retrieved_chunks,
    )
