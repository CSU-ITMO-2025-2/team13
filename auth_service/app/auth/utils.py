from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi.responses import Response
from jose import jwt

from app.auth.models import User
from app.config import settings


def create_tokens(data: dict, expires_delta: timedelta = None) -> dict:
    # Текущее время в UTC
    now = datetime.now(timezone.utc)

    # AccessToken - по умолчанию 30 минут, или кастомное время
    if expires_delta:
        access_expire = now + expires_delta
    else:
        access_expire = now + timedelta(minutes=30)
    access_payload = data.copy()
    access_payload.update(
        {"exp": int(access_expire.timestamp()), "type": "access"}
    )
    access_token = jwt.encode(
        access_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    # RefreshToken - 7 дней
    refresh_expire = now + timedelta(days=7)
    refresh_payload = data.copy()
    refresh_payload.update(
        {"exp": int(refresh_expire.timestamp()), "type": "refresh"}
    )
    refresh_token = jwt.encode(
        refresh_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return {"access_token": access_token, "refresh_token": refresh_token}


async def authenticate_user(user, password) -> User | None:
    if not user:
        return None

    if not verify_password(plain_password=password, hashed_password=user.password):
        return None

    return user


def set_tokens(response: Response, user_id: int):
    new_tokens = create_tokens(data={"sub": str(user_id)})
    access_token = new_tokens.get("access_token")
    refresh_token = new_tokens.get("refresh_token")

    response.set_cookie(
        key="user_access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
    )

    response.set_cookie(
        key="user_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
    )


def get_password_hash(password: str) -> str:
    """
    Хеширует пароль с использованием bcrypt.

    Args:
        password: Пароль в виде обычного текста

    Returns:
        Хешированный пароль
    """
    # Преобразуем пароль в байты
    password_bytes = password.encode("utf-8")
    # Генерируем соль и хешируем
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Возвращаем как строку
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие пароля хешу.

    Args:
        plain_password: Пароль в виде обычного текста
        hashed_password: Хешированный пароль

    Returns:
        True если пароли совпадают, иначе False
    """
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)
