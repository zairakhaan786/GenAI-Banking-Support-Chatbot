import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # ── Application ────────────────────────────────────────────────────────────
    APP_NAME: str = "GenAI Banking Support Chatbot"
    VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # ── LLM Configuration ──────────────────────────────────────────────────────
    # Supported providers: groq | openai | google | fallback
    LLM_PROVIDER: str = "groq"

    # API Keys (at least one is recommended; fallback mode works without any)
    # The application gracefully handles missing environment variables by falling back to mock components
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    # Model names per provider
    GROQ_MODEL: str = "llama3-8b-8192"
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    GOOGLE_MODEL: str = "gemini-1.5-flash"

    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 1024

    # ── Embeddings ─────────────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # ── ChromaDB ───────────────────────────────────────────────────────────────
    CHROMA_PERSIST_DIR: str = str(BASE_DIR / "chroma_db")
    COLLECTION_NAME: str = "banking_knowledge_base"

    # ── RAG Retrieval ──────────────────────────────────────────────────────────
    TOP_K_RESULTS: int = 5
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 80

    # ── Session Memory ─────────────────────────────────────────────────────────
    MAX_HISTORY_TURNS: int = 8        # message pairs kept in memory
    SESSION_EXPIRY_MINUTES: int = 60

    # ── File Upload ────────────────────────────────────────────────────────────
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    MAX_FILE_SIZE_MB: int = 20
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "txt", "docx"]

    # ── CORS ───────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = ["*"]

    # ── Logging ────────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = str(BASE_DIR / "logs" / "app.log")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


settings = Settings()

# Ensure required directories exist
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(Path(settings.LOG_FILE).parent, exist_ok=True)
