import asyncio
import time
from functools import wraps
from typing import Any, Callable

from loguru import logger


def measure_time(func: Callable) -> Callable:
    """
    Декоратор для измерения времени выполнения функции
    Работает с синхронными и асинхронными функциями
    """

    @wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        start_time = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - start_time
            logger.info(
                f"Функция {func.__name__} выполнилась за {elapsed:.6f} секунд"
            )
        return result

    @wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - start_time
            logger.info(
                f"Функция {func.__name__} выполнилась за {elapsed:.6f} секунд"
            )
        return result

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def exception_handler(func: Callable) -> Callable:
    """
    Декоратор для обработки исключений
    Работает с синхронными и асинхронными функциями
    """

    if asyncio.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any):
            try:
                result = await func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"В функции async {func.__name__} произошло исключение: {e}"
                )
                result = None
            return result

        return async_wrapper
    else:

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any):
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"В функции {func.__name__} произошло исключение: {e}"
                )
                result = None
            return result

        return sync_wrapper


def rate_limiter(max_calls: int, period: float):
    """
    Декоратор для ограничения частоты вызовов функции
    """

    def decorator(func: Callable) -> Callable:
        last_called = 0.0
        calls = 0

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal last_called, calls
            current_time = time.perf_counter()
            if current_time - last_called > period:
                last_called = current_time
                calls = 0
            if calls < max_calls:
                calls += 1
                return await func(*args, **kwargs)
            else:
                logger.warning(
                    f"Функция {func.__name__} превысила лимит вызовов {calls}/{max_calls}, ожидайте сброса лимита через {period - (current_time - last_called):.2f} секунд"
                )
                return None

        return wrapper

    return decorator
