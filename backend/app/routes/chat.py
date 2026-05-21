"""
Chat Route — POST /chat
"""

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import ChatRequest, ChatResponse, ErrorResponse
from app.services.rag_pipeline import get_rag_pipeline
from app.utils.logger import logger

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Send a message to the banking chatbot",
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a user query through the full RAG pipeline and return a
    context-grounded response with source citations.

    - **query**: The user's banking question
    - **session_id**: Session identifier for conversation memory
    - **top_k**: Number of context chunks to retrieve (default 5)
    """
    logger.info(f"Chat request | session={request.session_id} | query_len={len(request.query)}")

    try:
        pipeline = get_rag_pipeline()
        response = pipeline.chat(
            session_id=request.session_id,
            query=request.query,
            top_k=request.top_k,
        )
        return response

    except ValueError as exc:
        logger.warning(f"Validation error in chat: {exc}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    except Exception as exc:
        logger.error(f"Unexpected error in chat endpoint: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing your request. Please try again.",
        )
