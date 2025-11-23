import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dao import UserDAO
from app.auth.models import User
from app.auth.schemas import SUserAuth, SUserRegister, SUserUpdate
from app.auth.utils import authenticate_user
from app.exceptions import IncorrectLoginOrPasswordException, UserNotFoundException


class AuthService:
    def __init__(self, session: AsyncSession):
        self.users_dao = UserDAO(session)

    async def register_user(self, user_data: SUserRegister) -> User:
        """Регистрирует нового пользователя"""
        new_user = await self.users_dao.add(user_data)
        return new_user

    async def login_user(self, user_data: SUserAuth) -> User:
        """Авторизует пользователя"""
        user = await self.users_dao.find_one_or_none(
            filters={"phone_number": user_data.phone_number}
        )

        if not (
            user
            and await authenticate_user(user=user, password=user_data.password)
        ):
            raise IncorrectLoginOrPasswordException

        return user

    async def update_user_profile(
        self, user_id: str, user_data: SUserUpdate
    ) -> User:
        """Обновляет профиль пользователя"""
        user_uuid = uuid.UUID(str(user_id))
        user = await self.users_dao.find_one_or_none_by_id(user_uuid)
        if not user:
            raise UserNotFoundException

        update_dict = user_data.model_dump(exclude_unset=True, exclude={"id"})
        updated_user = await self.users_dao.update(user.id, **update_dict)

        return updated_user

    async def get_all_users(self) -> list[User]:
        """Возвращает список всех пользователей"""
        return await self.users_dao.find_all_with_relations(User.role)
