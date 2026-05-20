"""
FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from backend.app.config import settings
from api import chat, health, upload
from rag_pipeline.rag_pipeline import get_rag_pipeline
from backend.app.utils.logger import logger, setup_logger

# ── Lifespan ───────────────────────────────────────────────────────────────────

def init_kb():
    """Initialise all singletons and load the knowledge base in the background."""
    try:
        pipeline = get_rag_pipeline()
        chunks = pipeline.bootstrap_knowledge_base()
        logger.info(f"Startup complete — knowledge base: {chunks} chunks ready")
    except Exception as exc:
        logger.error(f"Startup error (non-fatal): {exc}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialise logger, warm up services, bootstrap KB. Shutdown: cleanup."""
    setup_logger()
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")

    # Warm-up: load the knowledge base in a background thread to prevent
    # blocking the event loop and causing port binding timeouts on Render.
    asyncio.create_task(asyncio.to_thread(init_kb))

    yield  # Application is running

    logger.info("Shutting down — goodbye")


# ── Application ────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "A production-ready AI Banking Support Chatbot powered by RAG "
        "(Retrieval-Augmented Generation). Supports PDF/TXT document ingestion, "
        "semantic retrieval via ChromaDB, and context-aware response generation."
    ),
    version=settings.VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routers ────────────────────────────────────────────────────────────────

app.include_router(chat.router,   prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(health.router, prefix="/api")

# ── Static Frontend ────────────────────────────────────────────────────────────

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        file_path = FRONTEND_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIR / "index.html"))
