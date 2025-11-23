import signal
import sys

import uvicorn
from loguru import logger


def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    logger.info(f"Получен сигнал {signum}. Завершение работы...")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=7000,
            reload=True,
            reload_excludes=[
                "run.py",
                "*.pyc",
                "__pycache__",
            ],
            access_log=False,
            use_colors=True,
            timeout_keep_alive=5,
            timeout_graceful_shutdown=10,
        )
    except KeyboardInterrupt:
        logger.info("Приложение остановлено пользователем")
    except Exception as e:
        logger.error(f"Ошибка при запуске приложения: {e}")
    finally:
        logger.info("Завершение работы приложения")
