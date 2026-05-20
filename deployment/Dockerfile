# ── Build Stage ────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Runtime Stage ──────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy project files
COPY backend /app/backend
COPY frontend /app/frontend
COPY data /app/data

# Switch to backend directory for runtime
WORKDIR /app/backend

# Create required directories
RUN mkdir -p chroma_db uploads logs .cache/huggingface
ENV HF_HOME=/app/backend/.cache/huggingface

# Non-root user for security
RUN useradd -r -u 1001 bankbot && chown -R bankbot:bankbot /app
USER bankbot

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
