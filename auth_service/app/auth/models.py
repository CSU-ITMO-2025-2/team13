import uuid

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.dao.database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, comment="Уникальный идентификатор роли")
    name = Column(String(50), unique=True, nullable=False, comment="Название роли")
    description = Column(String(255), comment="Описание роли")

    users = relationship("User", back_populates="role")

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}', description='{self.description}')>"


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Уникальный идентификатор пользователя",
    )
    email = Column(
        String(255), unique=True, nullable=False, comment="Email пользователя"
    )
    phone_number = Column(
        String(20), unique=True, nullable=False, comment="Номер телефона"
    )
    password = Column(
        String(255), nullable=False, comment="Хэш пароля пользователя"
    )
    first_name = Column(String(100), nullable=False, comment="Имя пользователя")
    last_name = Column(String(100), nullable=False, comment="Фамилия пользователя")
    avatar_url = Column(
        String(2048), comment="Ссылка на изображение профиля пользователя"
    )
    role_id = Column(
        Integer,
        ForeignKey("roles.id"),
        default=1,
        nullable=False,
        comment="ID роли пользователя",
    )
    is_active = Column(Boolean, default=True, comment="Флаг активности аккаунта")

    role = relationship("Role", back_populates="users")

    def __repr__(self):
        return f"<User(id={self.id}, phone='{self.phone_number}', name='{self.first_name} {self.last_name}')>"
