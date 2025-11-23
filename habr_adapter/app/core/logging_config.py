import sys
from pathlib import Path

from config import settings
from loguru import logger


def setup_logging():
    """
    Настраивает логгер loguru для вывода в консоль и файлы.
    """
    logger.remove()

    # Консоль
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>",
        level=settings.CONSOLE_LOG_LEVEL,
    )

    # Директория с логами
    log_dir = Path(settings.LOGS_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Общий лог
    logger.add(
        log_dir / "app.log",
        level="DEBUG",
        rotation="10 MB",
        retention=5,
        enqueue=True,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )

    logger.info("Логгер успешно настроен")
