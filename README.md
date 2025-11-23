# HabrParserAI

Микросервисная архитектура для парсинга статей с Habr и их обработки с помощью LLM

## Основные возможности

- **BFF Service** - Backend for Frontend, точка входа для клиентов
- **Auth Service** - Сервис аутентификации и авторизации пользователей
- **Habr Adapter** - Сервис для парсинга и получения контента статей
- **LLM Service** - Сервис интеграции с LLM (Gemini) для анализа текста
- **Async Processing** - Асинхронная обработка задач через RabbitMQ
- **Infrastructure** - Полный стек с PostgreSQL, Redis и RabbitMQ в Docker

## Установка и запуск

1. Создать файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

2. Запустить проект через Docker Compose:
```bash
docker-compose up -d --build
```

Сервисы будут доступны по адресам:
- BFF Service: http://localhost:8000
- Auth Service: http://localhost:5002
- Habr Adapter: http://localhost:5000
- LLM Service: http://localhost:5001
- RabbitMQ UI: http://localhost:15672 (user/password)

## Структура проекта

```
bff/                # Backend for Frontend сервис
auth_service/       # Сервис аутентификации
habr_adapter/       # Сервис парсинга Habr
llm_service/        # Сервис работы с LLM
docker-compose.yaml # Оркестрация контейнеров
logs/               # Логи приложений
```

## Схема взаимодействия сервисов

```mermaid
sequenceDiagram
    participant User
    participant BFF as BFF Service
    participant Auth as Auth Service
    participant DB as PostgreSQL
    participant Redis
    participant Habr as Habr Adapter
    participant RMQ as RabbitMQ
    participant Worker as LLM Consumer
    participant Gemini as Gemini API
    participant LLMAPI as LLM Service API

    Note over User, BFF: 1. Отправка статьи на обработку
    User->>BFF: POST /api/articles/process
    activate BFF
    
    rect rgb(0, 0, 0, 0)
    Note right of BFF: Auth & Cache Check
    BFF->>Redis: Check Token
    opt Token not cached
        BFF->>Auth: Validate Token
        Auth-->>BFF: User Info
        BFF->>Redis: Cache Token
    end
    end

    BFF->>DB: Check Article Exists
    
    alt Article New
        BFF->>Habr: Parse Article
        activate Habr
        Habr-->>BFF: Article Content
        deactivate Habr
        BFF->>RMQ: Publish Task
        BFF->>DB: Save Article
    end
    
    BFF->>DB: Link User to Article
    BFF->>Redis: Check Result Cache
    BFF-->>User: Return task_id
    deactivate BFF

    Note over RMQ, Gemini: 2. Асинхронная обработка
    loop Async Processing
        Worker->>RMQ: Consume Task
        activate Worker
        Worker->>Redis: Set Status "in_progress"
        Worker->>Gemini: Generate Summary
        activate Gemini
        Gemini-->>Worker: Summary JSON
        deactivate Gemini
        Worker->>Redis: Set Status "done" + Result
        deactivate Worker
    end

    Note over User, BFF: 3. Получение результата
    User->>BFF: GET /api/articles/result/{task_id}
    activate BFF
    
    BFF->>DB: Get Article
    
    alt Result in DB
        BFF->>Redis: Cache Result
        BFF-->>User: Result JSON
    else Result not in DB
        BFF->>LLMAPI: GET /api/gemini/tasks/{task_id}
        activate LLMAPI
        LLMAPI->>Redis: Get Result
        Redis-->>LLMAPI: Result JSON
        LLMAPI-->>BFF: Result JSON
        deactivate LLMAPI
        
        opt Status Done
            BFF->>DB: Save Result
            BFF->>Redis: Cache Result
        end
        
        BFF-->>User: Result JSON
    end
    deactivate BFF
```

## Пример использования

### 1. Регистрация пользователя

```bash
curl -X 'POST' \
  'http://localhost:8000/auth/register/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "phone_number": "79991234567",
  "password": "strongpassword123",
  "first_name": "Ivan",
  "last_name": "Ivanov"
}'
```

### 2. Авторизация (получение cookie)

```bash
curl -X 'POST' \
  'http://localhost:8000/auth/login/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "phone_number": "79991234567",
  "password": "strongpassword123"
}' \
  -c cookies.txt
```

### 3. Отправка статьи на обработку

```bash
curl -X 'POST' \
  'http://localhost:8000/api/articles/process' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -b cookies.txt \
  -d '{
  "url": "https://habr.com/ru/companies/selectel/articles/967092"
}'
```

Response:
```json
{
  "task_id": "e79e4b7d-5465-4bc4-b568-fdcd584aecd7",
  "status": "queued"
}
```

### 4. Получение результата

```bash
curl -X 'GET' \
  'http://localhost:8000/api/articles/result/e79e4b7d-5465-4bc4-b568-fdcd584aecd7' \
  -H 'accept: application/json' \
  -b cookies.txt
```

Response:
```json
{
  "status": "done",
  "summary": {
    "title": "Как работают ИИ-агенты...",
    "tldr": "Статья объясняет...",
    ...
  }
}
```