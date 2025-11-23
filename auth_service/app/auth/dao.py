from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.auth.models import Role, User
from app.auth.schemas import SUserAddDB, SUserRegister
from app.auth.utils import get_password_hash
from app.dao.base import BaseDAO
from app.exceptions import UserAlreadyExistsException


class UserDAO(BaseDAO):
    model = User

    async def find_one_or_none_by_id(self, data_id):
        """Переопределяем для загрузки с ролью"""
        try:
            query = (
                select(self.model)
                .options(selectinload(self.model.role))
                .filter_by(id=data_id)
            )
            result = await self._session.execute(query)
            record = result.scalar_one_or_none()
            log_message = f"Запись {self.model.__name__} с ID {data_id} {'найдена' if record else 'не найдена'}."
            logger.info(log_message)
            return record
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске записи с ID {data_id}: {e}")
            raise

    async def add(self, values: SUserRegister):
        """Добавляет нового пользователя в БД с проверкой на уникальность и хэшированием пароля"""
        existing_by_email = await self.find_one_or_none(
            filters={"email": values.email}
        )
        if existing_by_email:
            raise UserAlreadyExistsException

        existing_by_phone = await self.find_one_or_none(
            filters={"phone_number": values.phone_number}
        )
        if existing_by_phone:
            raise UserAlreadyExistsException

        values_dict = values.model_dump(exclude_unset=True)

        plain_password = values_dict.pop("password")
        values_dict["password"] = get_password_hash(plain_password)

        values_dict.pop("confirm_password", None)

        hashed_values = SUserAddDB(**values_dict)
        return await super().add(hashed_values)

    async def update(self, user_id: int, **kwargs):
        """Обновляет пользователя по ID"""
        await super().update(filters={"id": user_id}, values=kwargs)
        return await self.find_one_or_none_by_id(user_id)

    async def delete(self, user_id: int):
        """Удаляет пользователя по ID"""
        return await super().delete(filters={"id": user_id})


class RoleDAO(BaseDAO):
    model = Role
