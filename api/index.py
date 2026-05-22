"""
Vercel Serverless Entrypoint — GenAI Banking Support Chatbot

Vercel's Python runtime requires an ASGI `app` object at the module level
of a file inside the `api/` directory. This shim patches sys.path so the
backend package is importable, then re-exports the FastAPI app.
"""

import os
import sys
from pathlib import Path

# ── Path patch ─────────────────────────────────────────────────────────────────
# Make `backend/` importable as a package root inside Vercel's build sandbox.
ROOT = Path(__file__).resolve().parent.parent       # repo root
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

# ── Vercel environment defaults ────────────────────────────────────────────────
# /tmp is the only writable path in Vercel serverless functions.
os.environ.setdefault("CHROMA_PERSIST_DIR", "/tmp/chroma_db")
os.environ.setdefault("UPLOAD_DIR", "/tmp/uploads")
os.environ.setdefault("LOG_FILE", "/tmp/app.log")
os.environ.setdefault("LLM_PROVIDER", "fallback")
os.environ.setdefault("DEBUG", "false")

# ── App import ────────────────────────────────────────────────────────────────
# Import AFTER env vars are set so Settings() picks them up on construction.
from app.main import app  # noqa: E402

# Vercel detects `app` as the ASGI handler automatically.
