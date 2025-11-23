import logging
import os
import sys

from loguru import logger

from app.config import settings


class InterceptHandler(logging.Handler):
    """Перехватчик для стандартных логов Python в Loguru"""

    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging():
    """Настройка логирования для всего приложения."""

    logs_dir = settings.LOGS_DIR
    app_log_path = os.path.join(logs_dir, "app.log")
    errors_log_path = os.path.join(logs_dir, "errors.log")

    logger.remove()

    # Вывод в консоль
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>",
        level="DEBUG",
        colorize=True,
        enqueue=True,
        backtrace=True,
        diagnose=True,
        catch=True,
    )

    # Добавляем запись в файл
    logger.add(
        app_log_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="INFO",
        rotation="1 day",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
    )

    # Отдельный файл для ошибок
    logger.add(
        errors_log_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="ERROR",
        rotation="1 week",
        retention="60 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
    )

    # Перехватываем стандартные логи Python
    if not any(
        isinstance(handler, InterceptHandler) for handler in logging.root.handlers
    ):
        logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

        for logger_name in [
            "uvicorn",
            "uvicorn.error",
            "uvicorn.access",
            "fastapi",
        ]:
            logging_logger = logging.getLogger(logger_name)
            logging_logger.handlers = [InterceptHandler()]
            logging_logger.setLevel(logging.INFO)

    logger.info("Логирование настроено с Loguru")
