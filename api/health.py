"""
Health Route — GET /health
"""

from fastapi import APIRouter

from backend.app.config import settings
from app.models.schemas import ComponentStatus, HealthResponse
from rag_pipeline.memory import get_memory_service
from vector_db.vector_store import get_vector_store
from backend.app.utils.logger import logger

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=HealthResponse,
    summary="Check service health and component status",
)
async def health_check() -> HealthResponse:
    """
    Returns the operational status of all system components:
    vector store, embedding model, LLM, and session memory.
    """
    components: dict = {}

    # Vector store
    try:
        vs = get_vector_store()
        doc_count = vs.get_document_count()
        components["vector_store"] = ComponentStatus(
            status="ok", details=f"ChromaDB online, {doc_count} documents indexed"
        ).dict()
    except Exception as exc:
        components["vector_store"] = ComponentStatus(status="error", details=str(exc)).dict()
        doc_count = 0

    # Session memory
    try:
        mem = get_memory_service()
        active = mem.get_session_count()
        components["session_memory"] = ComponentStatus(
            status="ok", details=f"{active} active session(s)"
        ).dict()
    except Exception as exc:
        components["session_memory"] = ComponentStatus(status="error", details=str(exc)).dict()

    # LLM provider
    try:
        from rag_pipeline.llm_service import get_llm_service
        llm = get_llm_service()
        components["llm"] = ComponentStatus(
            status="ok", details=f"Provider: {llm.model_name}"
        ).dict()
    except Exception as exc:
        components["llm"] = ComponentStatus(status="degraded", details=str(exc)).dict()

    overall = "healthy" if all(c["status"] == "ok" for c in components.values()) else "degraded"

    return HealthResponse(
        status=overall,
        version=settings.VERSION,
        components=components,
        collection_documents=doc_count,
    )
