"""
LLM Service
-----------
Multi-provider LLM wrapper (Groq → OpenAI → Google → Fallback).
Provider is selected based on LLM_PROVIDER env var and API key availability.
Fallback mode constructs a coherent response from retrieved context without an LLM.
"""

from typing import List, Optional, Tuple

from langchain_core.documents import Document

from backend.app.config import settings
from backend.app.utils.logger import logger


class LLMService:
    def __init__(self):
        self._llm = None
        self._provider = "fallback"
        self._model_name = "context-formatter"
        self._initialize()

    # ── Initialisation ─────────────────────────────────────────────────────────

    def _initialize(self) -> None:
        provider = settings.LLM_PROVIDER.lower()

        if provider == "groq" and settings.GROQ_API_KEY:
            self._try_groq()
        elif provider == "openai" and settings.OPENAI_API_KEY:
            self._try_openai()
        elif provider == "google" and settings.GOOGLE_API_KEY:
            self._try_google()
        else:
            # Auto-detect: try each provider in order
            if settings.GROQ_API_KEY:
                self._try_groq()
            elif settings.OPENAI_API_KEY:
                self._try_openai()
            elif settings.GOOGLE_API_KEY:
                self._try_google()

        if self._llm is None:
            logger.warning(
                "No LLM API key detected — running in smart fallback mode. "
                "Set GROQ_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY for full LLM support."
            )

    def _try_groq(self) -> None:
        try:
            from langchain_groq import ChatGroq
            self._llm = ChatGroq(
                api_key=settings.GROQ_API_KEY,
                model_name=settings.GROQ_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
            )
            self._provider = "groq"
            self._model_name = settings.GROQ_MODEL
            logger.info(f"LLM initialised: Groq ({settings.GROQ_MODEL})")
        except Exception as exc:
            logger.warning(f"Groq init failed: {exc}")

    def _try_openai(self) -> None:
        try:
            from langchain_openai import ChatOpenAI
            self._llm = ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
            )
            self._provider = "openai"
            self._model_name = settings.OPENAI_MODEL
            logger.info(f"LLM initialised: OpenAI ({settings.OPENAI_MODEL})")
        except Exception as exc:
            logger.warning(f"OpenAI init failed: {exc}")

    def _try_google(self) -> None:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            self._llm = ChatGoogleGenerativeAI(
                google_api_key=settings.GOOGLE_API_KEY,
                model=settings.GOOGLE_MODEL,
                temperature=settings.LLM_TEMPERATURE,
            )
            self._provider = "google"
            self._model_name = settings.GOOGLE_MODEL
            logger.info(f"LLM initialised: Google ({settings.GOOGLE_MODEL})")
        except Exception as exc:
            logger.warning(f"Google GenAI init failed: {exc}")

    # ── Generation ─────────────────────────────────────────────────────────────

    def generate(self, prompt: str, query: str, context_docs: List[Tuple[Document, float]]) -> str:
        """Generate a response using LLM or fallback."""
        if self._llm is not None:
            return self._llm_generate(prompt)
        return self._fallback_generate(query, context_docs)

    def _llm_generate(self, prompt: str) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage
        try:
            system_msg = SystemMessage(content=(
                "You are BankBot, a knowledgeable and professional AI banking assistant. "
                "Answer customer queries accurately using only the provided context. "
                "If the context does not contain enough information, say so politely and "
                "suggest contacting customer support. Keep answers clear and structured."
            ))
            human_msg = HumanMessage(content=prompt)
            response = self._llm.invoke([system_msg, human_msg])
            return response.content.strip()
        except Exception as exc:
            logger.error(f"LLM generation failed: {exc}. Falling back to context formatter.")
            return self._fallback_generate_from_prompt(prompt)

    def _fallback_generate(self, query: str, context_docs: List[Tuple[Document, float]]) -> str:
        """
        Smart fallback: formats retrieved chunks into a structured, readable answer.
        Works without any LLM API key.
        """
        if not context_docs:
            return (
                "I'm sorry, I couldn't find specific information about your query in our knowledge base. "
                "Please contact our customer support team at 1800-XXX-XXXX or visit your nearest branch for assistance."
            )

        query_lower = query.lower()
        intro = self._generate_intro(query_lower)

        content_parts = []
        for doc, score in context_docs[:3]:
            chunk = doc.page_content.strip()
            if chunk and len(chunk) > 30:
                content_parts.append(chunk)

        body = "\n\n".join(content_parts)

        outro = (
            "\n\nFor personalised assistance or more details, "
            "please visit your nearest branch or call our 24/7 helpline."
        )

        return f"{intro}\n\n{body}{outro}"

    def _generate_intro(self, query: str) -> str:
        if any(w in query for w in ["loan", "borrow", "credit", "emi", "interest"]):
            return "Here is the relevant information about banking loan products and policies:"
        if any(w in query for w in ["card", "credit card", "debit card"]):
            return "Here is what you need to know about our card services:"
        if any(w in query for w in ["account", "savings", "deposit", "fd", "fixed"]):
            return "Here is the relevant information about our account and deposit products:"
        if any(w in query for w in ["kyc", "document", "open", "apply"]):
            return "Here are the requirements and process details:"
        if any(w in query for w in ["fraud", "block", "stolen", "security"]):
            return "Here is important information about banking security and fraud prevention:"
        return "Based on our banking knowledge base, here is the relevant information:"

    def _fallback_generate_from_prompt(self, prompt: str) -> str:
        # Last-resort: extract context section from the prompt
        if "Context:" in prompt:
            ctx = prompt.split("Context:")[1].split("Question:")[0].strip()
            return f"Based on our records:\n\n{ctx[:800]}\n\nFor more help, contact customer support."
        return "I encountered an issue generating a response. Please try again or contact customer support."

    @property
    def model_name(self) -> str:
        return f"{self._provider}/{self._model_name}"

    @property
    def provider(self) -> str:
        return self._provider


# Singleton
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
