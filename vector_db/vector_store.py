"""
Vector Store Service
--------------------
ChromaDB-backed persistent vector store.
Provides add, search, and metadata operations.
"""

from typing import List, Tuple, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_core.documents import Document
from langchain_chroma import Chroma

from backend.app.config import settings
from rag_pipeline.embeddings import get_embedding_service
from backend.app.utils.logger import logger


class VectorStoreService:
    def __init__(self):
        self._embedding_service = get_embedding_service()
        self._client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._vectorstore: Optional[Chroma] = None
        self._init_vectorstore()

    # ── Initialisation ─────────────────────────────────────────────────────────

    def _init_vectorstore(self) -> None:
        """Connect to (or create) the ChromaDB collection."""
        try:
            self._vectorstore = Chroma(
                collection_name=settings.COLLECTION_NAME,
                embedding_function=self._embedding_service.get_langchain_embeddings(),
                client=self._client,
                persist_directory=settings.CHROMA_PERSIST_DIR,
            )
            count = self.get_document_count()
            logger.info(f"Vector store ready — collection='{settings.COLLECTION_NAME}', docs={count}")
        except Exception as exc:
            logger.error(f"Failed to initialise vector store: {exc}")
            raise

    # ── Write ──────────────────────────────────────────────────────────────────

    def add_documents(self, documents: List[Document]) -> int:
        """Index a list of LangChain Documents. Returns number of chunks added."""
        if not documents:
            logger.warning("add_documents called with empty list")
            return 0
        try:
            self._vectorstore.add_documents(documents)
            logger.info(f"Indexed {len(documents)} chunks into vector store")
            return len(documents)
        except Exception as exc:
            logger.error(f"Error adding documents to vector store: {exc}")
            raise

    # ── Read ───────────────────────────────────────────────────────────────────

    def similarity_search(
        self,
        query: str,
        k: int = None,
        score_threshold: float = 0.0,
    ) -> List[Tuple[Document, float]]:
        """
        Returns top-k (document, score) pairs ordered by relevance.
        score is cosine similarity in [0, 1].
        """
        k = k or settings.TOP_K_RESULTS
        try:
            results = self._vectorstore.similarity_search_with_relevance_scores(
                query=query,
                k=k,
            )
            # Filter by threshold and sort descending
            filtered = [(doc, score) for doc, score in results if score >= score_threshold]
            filtered.sort(key=lambda x: x[1], reverse=True)
            logger.debug(f"Retrieval: query_len={len(query)}, hits={len(filtered)}/{k}")
            return filtered
        except Exception as exc:
            logger.error(f"Similarity search failed: {exc}")
            return []

    def get_document_count(self) -> int:
        try:
            collection = self._client.get_collection(settings.COLLECTION_NAME)
            return collection.count()
        except Exception:
            return 0

    def collection_exists_and_populated(self) -> bool:
        return self.get_document_count() > 0


# Singleton
_vector_store_service: Optional[VectorStoreService] = None


def get_vector_store() -> VectorStoreService:
    global _vector_store_service
    if _vector_store_service is None:
        _vector_store_service = VectorStoreService()
    return _vector_store_service
