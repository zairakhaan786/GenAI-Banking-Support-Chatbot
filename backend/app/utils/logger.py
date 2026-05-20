import sys
from loguru import logger
from backend.app.config import settings


def setup_logger() -> None:
    """Configure loguru with console + rotating file handlers."""
    logger.remove()  # Remove default handler

    # Console handler – coloured, readable
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> – "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # Rotating file handler
    logger.add(
        settings.LOG_FILE,
        level=settings.LOG_LEVEL,
        rotation="10 MB",
        retention="14 days",
        compression="gz",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} – {message}",
        enqueue=True,   # thread-safe writes
    )

    logger.info(f"Logger initialised — level={settings.LOG_LEVEL}")


# Expose logger instance for import across the project
__all__ = ["logger", "setup_logger"]
