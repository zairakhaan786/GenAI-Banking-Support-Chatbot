"""
Embedding Service
-----------------
Wraps sentence-transformers (local, free, no API key needed).
Provides a singleton instance to avoid reloading the model on every request.
"""

from functools import lru_cache
from typing import List
import os

# Fix for macOS 'meta tensor' bug with PyTorch/Transformers
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings
from app.utils.logger import logger


class EmbeddingService:
    """Wraps HuggingFace sentence-transformer embeddings."""

    def __init__(self):
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info("Embedding model loaded successfully")

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query string."""
        return self.embeddings.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of document strings."""
        return self.embeddings.embed_documents(texts)

    def get_langchain_embeddings(self):
        """Return the raw LangChain embeddings object (for ChromaDB integration)."""
        return self.embeddings


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """Singleton factory – model is loaded once at first call."""
    return EmbeddingService()
