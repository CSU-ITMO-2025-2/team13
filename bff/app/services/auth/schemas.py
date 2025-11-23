import re
from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    computed_field,
    field_validator,
    model_validator,
)


class EmailModel(BaseModel):
    email: EmailStr = Field(description="Электронная почта")
    model_config = ConfigDict(from_attributes=True)


class PhoneModel(BaseModel):
    phone_number: str = Field(
        description="Номер телефона в международном формате, начинающийся с '+'"
    )
    model_config = ConfigDict(from_attributes=True)


class UserBase(EmailModel, PhoneModel):
    first_name: str = Field(
        min_length=3, max_length=50, description="Имя, от 3 до 50 символов"
    )
    last_name: str = Field(
        min_length=3, max_length=50, description="Фамилия, от 3 до 50 символов"
    )

    @field_validator("phone_number")
    def validate_phone_number(cls, value: str) -> str:
        if not re.match(r"^\+\d{5,15}$", value):
            raise ValueError(
                'Номер телефона должен начинаться с "+" и содержать от 5 до 15 цифр'
            )
        return value


class SUserRegister(UserBase):
    password: str = Field(
        min_length=5, max_length=50, description="Пароль, от 5 до 50 знаков"
    )
    confirm_password: str = Field(
        min_length=5, max_length=50, description="Повторите пароль"
    )

    @model_validator(mode="after")
    def check_password(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("Пароли не совпадают")
        return self


class SUserAuth(PhoneModel):
    password: str = Field(
        min_length=5, max_length=50, description="Пароль, от 5 до 50 знаков"
    )


class RoleModel(BaseModel):
    id: int = Field(description="Идентификатор роли")
    name: str = Field(description="Название роли")
    model_config = ConfigDict(from_attributes=True)


class SUserInfo(UserBase):
    id: str = Field(description="Идентификатор пользователя (UUID)")
    role: RoleModel | None = Field(default=None, exclude=True)

    @computed_field
    def role_name(self) -> str:
        return self.role.name if self.role else "Неизвестно"

    @computed_field
    def role_id(self) -> int:
        return self.role.id if self.role else 0
