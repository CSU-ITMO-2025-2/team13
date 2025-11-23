from pathlib import Path

import aiofiles
import yaml
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Base as AuthBase
from app.auth.models import Role
from app.dao.database import async_session_maker

# --- ЗАГРУЗКА КОНФИГА ---


async def load_initial_data(file_path: Path) -> dict:
    """Загружает данные инициализации из YAML-файла"""
    try:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            data = await f.read()
            data = yaml.safe_load(data)
            if not isinstance(data, dict):
                raise ValueError(
                    "YAML-файл должен содержать корневой объект (словарь)"
                )
            return data
    except FileNotFoundError:
        logger.error(f"Файл данных не найден по пути: {file_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Ошибка парсинга YAML файла: {e}")
        raise
    except ValueError as e:
        logger.error(f"Ошибка формата данных в YAML файле: {e}")
        raise


# --- ИНИЦИАЛИЗАЦИЯ БД ---


async def init_roles(session: AsyncSession, roles_data: list):
    """Инициализирует роли пользователей"""
    result = await session.execute(select(Role).limit(1))
    if not result.scalar_one_or_none():
        logger.info("Создание записей в Role")
        roles = [Role(**data) for data in roles_data]
        session.add_all(roles)
        logger.info(f"Добавлено {len(roles)} ролей")
    else:
        logger.info("Роли уже существуют, пропуск инициализации")


async def init_default_admin(session: AsyncSession, admin_data: dict):
    """Инициализирует пользователя-администратора по умолчанию"""
    from app.auth.models import User
    from app.auth.utils import get_password_hash

    # Проверяем существование админа
    result = await session.execute(
        select(User).filter_by(email=admin_data["email"])
    )
    existing_admin = result.scalar_one_or_none()

    if not existing_admin:
        logger.info("Создание администратора по умолчанию")

        # Хешируем пароль
        hashed_password = get_password_hash(admin_data["password"])

        # Создаем пользователя
        admin = User(
            email=admin_data["email"],
            phone_number=admin_data["phone_number"],
            password=hashed_password,
            first_name=admin_data["first_name"],
            last_name=admin_data["last_name"],
            role_id=admin_data["role_id"],
            is_active=True,
        )

        session.add(admin)
        logger.info(
            f"Администратор создан: {admin_data['email']} "
            f"(phone: {admin_data['phone_number']})"
        )
    else:
        logger.info(
            f"Администратор уже существует: {admin_data['email']}, пропуск"
        )


async def init_database(
    session: AsyncSession = async_session_maker(),
    data_file_path: str = "initial_data.yaml",
    create_tables: bool = True,
) -> None:
    """
    Инициализирует базу данных, загружая начальные данные из YAML-файла
    """
    if create_tables:
        logger.info("Создание таблиц базы данных")
        if hasattr(session, "bind"):
            engine_to_use = session.bind
        else:
            engine_to_use = session.get_bind()

        async with engine_to_use.begin() as conn:
            await conn.run_sync(AuthBase.metadata.create_all)

        logger.info("Таблицы базы данных созданы")

    logger.info(f"Загрузка начальных данных из файла: {data_file_path}")
    data = await load_initial_data(Path(data_file_path))

    if isinstance(session, AsyncSession):
        try:
            logger.info("Начало инициализации данных в базе данных")

            await init_roles(session, data.get("roles", []))

            # Инициализируем дефолтного администратора
            if "default_admin_user" in data:
                await init_default_admin(session, data["default_admin_user"])

            await session.commit()
            logger.info("База данных успешно инициализирована начальными данными")
        except Exception as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}")
            await session.rollback()
            raise
    else:
        async with async_session_maker() as session:
            try:
                logger.info("Начало инициализации данных в базе данных")

                await init_roles(session, data.get("roles", []))

                # Инициализируем дефолтного администратора
                if "default_admin_user" in data:
                    await init_default_admin(session, data["default_admin_user"])

                await session.commit()
                logger.info(
                    "База данных успешно инициализирована начальными данными"
                )
            except Exception as e:
                logger.error(f"Ошибка при инициализации базы данных: {e}")
                await session.rollback()
                raise
            finally:
                await session.close()
                logger.info("Завершение операции инициализации базы данных")
