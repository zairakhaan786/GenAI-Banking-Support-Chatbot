"""
RAG Pipeline
------------
Orchestrates the full Retrieval-Augmented Generation flow:
  1. Contextual query building (uses conversation memory)
  2. Semantic retrieval from ChromaDB
  3. Prompt construction
  4. LLM / fallback response generation
  5. Session memory update
"""

from pathlib import Path
from typing import List, Tuple

from langchain_core.documents import Document

from app.config import settings
from app.models.schemas import ChatResponse, SourceChunk
from app.services.document_processor import DocumentProcessor
from app.services.embeddings import get_embedding_service
from app.services.llm_service import get_llm_service
from app.services.memory import get_memory_service
from app.services.vector_store import get_vector_store
from app.utils.logger import logger

# Path to the built-in banking knowledge base
KNOWLEDGE_BASE_PATH = Path(__file__).resolve().parents[3] / "data" / "banking_knowledge_base.txt"


class RAGPipeline:
    def __init__(self):
        self._processor = DocumentProcessor()
        self._vector_store = get_vector_store()
        self._memory = get_memory_service()
        self._llm = get_llm_service()
        self._embedding_service = get_embedding_service()

    # ── Knowledge Base Bootstrapping ───────────────────────────────────────────

    def bootstrap_knowledge_base(self) -> int:
        """
        Load the built-in banking knowledge base into ChromaDB on first run.
        Skips if the collection is already populated.
        """
        if self._vector_store.collection_exists_and_populated():
            count = self._vector_store.get_document_count()
            logger.info(f"Knowledge base already indexed ({count} chunks). Skipping bootstrap.")
            return count

        if not KNOWLEDGE_BASE_PATH.exists():
            logger.warning(f"Knowledge base file not found: {KNOWLEDGE_BASE_PATH}")
            return 0

        logger.info("Bootstrapping banking knowledge base...")
        raw_text = KNOWLEDGE_BASE_PATH.read_text(encoding="utf-8")
        chunks = self._processor.process_text_directly(raw_text, source="banking_knowledge_base.txt")
        indexed = self._vector_store.add_documents(chunks)
        logger.info(f"Knowledge base bootstrapped: {indexed} chunks indexed")
        return indexed

    # ── Core Chat Flow ─────────────────────────────────────────────────────────

    def chat(self, session_id: str, query: str, top_k: int = None) -> ChatResponse:
        """
        Full RAG pipeline for a single user turn.
        Returns a ChatResponse with answer + source citations.
        """
        top_k = top_k or settings.TOP_K_RESULTS

        # 1. Build contextual query (resolves pronouns using history)
        contextual_query = self._memory.build_contextual_query(session_id, query)
        logger.debug(f"[{session_id}] Contextual query: {contextual_query[:120]}")

        # 2. Semantic retrieval
        retrieved: List[Tuple[Document, float]] = self._vector_store.similarity_search(
            query=contextual_query,
            k=top_k,
        )
        logger.info(f"[{session_id}] Retrieved {len(retrieved)} chunks for query")

        # 3. Build prompt
        prompt = self._build_prompt(
            query=query,
            history_text=self._memory.get_history_as_text(session_id),
            context_docs=retrieved,
        )

        # 4. Generate response
        answer = self._llm.generate(prompt=prompt, query=query, context_docs=retrieved)

        # 5. Update session memory
        self._memory.add_message(session_id, "user", query)
        self._memory.add_message(session_id, "assistant", answer)

        # 6. Build source citations
        sources = [
            SourceChunk(
                content=doc.page_content[:300],
                score=round(score, 4),
                source=doc.metadata.get("source", "knowledge_base"),
            )
            for doc, score in retrieved
        ]

        return ChatResponse(
            answer=answer,
            session_id=session_id,
            sources=sources,
            model_used=self._llm.model_name,
            retrieval_count=len(retrieved),
        )

    # ── Prompt Construction ────────────────────────────────────────────────────

    def _build_prompt(
        self,
        query: str,
        history_text: str,
        context_docs: List[Tuple[Document, float]],
    ) -> str:
        context_blocks = []
        for i, (doc, score) in enumerate(context_docs, 1):
            source = doc.metadata.get("source", "knowledge_base")
            context_blocks.append(
                f"[Chunk {i} | Source: {source} | Relevance: {score:.2f}]\n{doc.page_content}"
            )
        context_str = "\n\n".join(context_blocks) if context_blocks else "No relevant context found."

        history_section = ""
        if history_text:
            history_section = f"""
Conversation History:
{history_text}

"""

        prompt = f"""You are BankBot, a professional and helpful AI banking assistant.
Answer the customer's question using ONLY the provided context below.
If the context does not contain enough information, acknowledge this politely and suggest contacting customer support.
Keep your answer concise, accurate, and well-structured. Use bullet points when listing multiple items.

{history_section}Context:
{context_str}

Question: {query}

Answer:"""

        return prompt

    # ── Document Ingestion ─────────────────────────────────────────────────────

    def ingest_document(self, file_path: str) -> Tuple[int, int]:
        """
        Process and index an uploaded document.
        Returns (chunks_indexed, collection_total).
        """
        chunks, char_count = self._processor.process_file(file_path)
        indexed = self._vector_store.add_documents(chunks)
        total = self._vector_store.get_document_count()
        logger.info(f"Ingested '{file_path}': {indexed} chunks, collection total={total}")
        return indexed, total


# Singleton
_rag_pipeline: RAGPipeline = None


def get_rag_pipeline() -> RAGPipeline:
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline
