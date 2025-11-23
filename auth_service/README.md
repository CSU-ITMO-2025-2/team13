# Auth Service

Сервис аутентификации и авторизации пользователей.

## Описание

Auth Service - микросервис для управления пользователями, аутентификацией и авторизацией. Использует JWT токены для аутентификации и PostgreSQL для хранения данных.

## Установка

### 1. Создание виртуального окружения

```bash
# Из корня проекта monorepo
cd auth_service
python -m venv venv
```

### 2. Активация виртуального окружения

**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate
```

**Linux/MacOS:**
```bash
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и настройте параметры:

```bash
copy .env.example .env  # Windows
cp .env.example .env    # Linux/MacOS
```

Отредактируйте `.env`:
```env
DEV_MODE=True
USE_SQLITE=False

SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256

POSTGRES_DB=auth_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_PORT=5432

REDIS_HOST=redis
REDIS_PORT=6379
```

### 5. Запуск базы данных

Убедитесь, что PostgreSQL запущен и доступен. Или используйте Docker:

```bash
# Из корня monorepo
docker-compose up -d db
```

## Запуск

### Локальный запуск

```bash
python run.py
```

Сервис будет доступен по адресу: http://localhost:7000

### Документация API

- Swagger UI: http://localhost:7000/docs
- ReDoc: http://localhost:7000/redoc

## Структура проекта

```
auth_service/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── auth.py          # Эндпоинты аутентификации
│   ├── auth/
│   │   ├── dao.py               # Data Access Objects
│   │   ├── models.py            # SQLAlchemy модели
│   │   ├── schemas.py           # Pydantic модели
│   │   ├── service.py           # Бизнес-логика
│   │   └── utils.py             # Утилиты (JWT, хеширование)
│   ├── core/
│   │   ├── init_db.py           # Инициализация БД
│   │   ├── logging.py           # Настройка логирования
│   │   └── middleware.py        # Middleware
│   ├── dao/
│   │   ├── base.py              # Базовый DAO класс
│   │   └── database.py          # Настройка БД
│   ├── dependencies/
│   │   ├── auth_dep.py          # Зависимости аутентификации
│   │   ├── dao_dep.py           # Зависимости для DAO
│   │   ├── services_dep.py      # Зависимости для сервисов
│   │   └── redis_dep.py         # Redis dependencies
│   ├── config.py                # Конфигурация
│   ├── exceptions.py            # Кастомные исключения
│   └── main.py                  # Точка входа приложения
├── data/
│   └── initial_data.yaml        # Начальные данные (роли)
├── logs/                        # Логи приложения
├── .env.example                 # Пример переменных окружения
├── requirements.txt             # Зависимости
└── run.py                       # Скрипт запуска
```

## Модели данных

### User (Пользователь)
- `id` - уникальный идентификатор
- `phone_number` - номер телефона (логин)
- `email` - электронная почта
- `password` - хешированный пароль
- `first_name` - имя
- `last_name` - фамилия
- `role_id` - ID роли пользователя
- `is_active` - активен ли аккаунт

### Role (Роль)
- `id` - уникальный идентификатор
- `name` - название роли
- `description` - описание

## API Endpoints

### Аутентификация

- **POST** `/api/v1/auth/register/` - Регистрация нового пользователя
- **POST** `/api/v1/auth/login/` - Авторизация пользователя
- **POST** `/api/v1/auth/logout/` - Выход из системы
- **GET** `/api/v1/auth/me/` - Получение информации о текущем пользователе
- **POST** `/api/v1/auth/refresh` - Обновление токенов
- **GET** `/api/v1/auth/all_users/` - Получение списка всех пользователей

## Безопасность

### JWT Токены

Используются два типа токенов:
- **Access Token** - срок жизни 30 минут, используется для доступа к защищенным эндпоинтам
- **Refresh Token** - срок жизни 7 дней, используется для обновления access токена

Токены хранятся в HTTP-only cookies

### Логирование

Логи сохраняются в директории `logs/`:
- `app.log` - все логи приложения
- `errors.log` - только ошибки