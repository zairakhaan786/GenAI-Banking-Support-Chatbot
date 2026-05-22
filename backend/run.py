"""Application entry point — run with: python run.py or uvicorn app.main:app"""

import uvicorn
from backend.app.config import settings

# Note: PYTHONPATH must be set to the root directory for imports to resolve correctly
if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
