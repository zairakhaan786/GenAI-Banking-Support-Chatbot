from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


# ── Chat Schemas ───────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="User's question")
    session_id: str = Field(..., min_length=1, max_length=100, description="Unique session identifier")
    top_k: Optional[int] = Field(5, ge=1, le=20, description="Number of context chunks to retrieve")

    @field_validator("query")
    def query_must_not_be_blank(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be blank or whitespace only")
        return v.strip()

    @field_validator("session_id")
    def session_id_must_be_alphanumeric(cls, v):
        import re
        if not re.match(r"^[a-zA-Z0-9_\-]{1,100}$", v):
            raise ValueError("session_id must be alphanumeric with hyphens/underscores only")
        return v


class SourceChunk(BaseModel):
    content: str
    score: float
    source: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    sources: List[SourceChunk] = []
    model_used: str
    retrieval_count: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"protected_namespaces": ()}


# ── Upload Schemas ─────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    message: str
    filename: str
    chunks_indexed: int
    collection_size: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── Health Schemas ─────────────────────────────────────────────────────────────

class ComponentStatus(BaseModel):
    status: str   # "ok" | "degraded" | "error"
    details: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    components: dict
    collection_documents: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── Session History ────────────────────────────────────────────────────────────

class HistoryMessage(BaseModel):
    role: str   # "user" | "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SessionHistoryResponse(BaseModel):
    session_id: str
    messages: List[HistoryMessage]
    message_count: int


# ── Error ──────────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
