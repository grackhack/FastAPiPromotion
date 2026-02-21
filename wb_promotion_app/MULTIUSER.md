# Мультипользовательский режим WB Promotion App

Приложение теперь поддерживает работу с несколькими пользователями, каждый со своим WB API токеном.

## Архитектура

### База данных

Приложение использует PostgreSQL для хранения пользователей и их API токенов:

- **users** - пользователи системы
- **user_api_tokens** - API токены пользователей для доступа к Wildberries API

### Аутентификация

Аутентификация выполняется через заголовок `X-API-Token`. Каждый запрос к API должен содержать этот заголовок с действительным токеном.

## Настройка

### 1. Создание базы данных

На сервере выполните:

```bash
ssh botuser@195.133.49.121

# Создание БД
sudo -u postgres psql -c "CREATE DATABASE wb_promotion_app;"

# Предоставление прав
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE wb_promotion_app TO bot_user;"
```

### 2. Применение миграций

```bash
cd /home/botuser/FastAPiPromotion/wb_promotion_app

# Применить миграции
alembic upgrade head
```

### 3. Обновление .env файла

Добавьте `DATABASE_URL` в ваш `.env` файл:

```env
WB_API_TOKEN=your_fallback_token
APP_HOST=0.0.0.0
APP_PORT=8001
APP_DEBUG=True
LOG_LEVEL=INFO
DATABASE_URL=postgresql://bot_user:botpwd@localhost:5432/wb_promotion_app
```

## API для управления пользователями

### Создать пользователя

```bash
curl -X POST http://localhost:8001/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "myshop",
    "email": "shop@example.com"
  }'
```

Ответ:
```json
{
  "id": 1,
  "username": "myshop",
  "email": "shop@example.com",
  "is_active": true,
  "created_at": "2026-02-21T10:00:00"
}
```

### Создать токен для пользователя

```bash
curl -X POST http://localhost:8001/api/users/1/tokens \
  -H "Content-Type: application/json" \
  -d '{
    "token": "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjUwOTA0djEiLCJ0eXAiOiJKV1QifQ...",
    "description": "Основной токен для магазина"
  }'
```

Ответ:
```json
{
  "id": 1,
  "user_id": 1,
  "description": "Основной токен для магазина",
  "is_active": true,
  "created_at": "2026-02-21T10:00:00",
  "updated_at": null,
  "token": "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjUwOTA0djEiLCJ0eXAiOiJKV1QifQ..."
}
```

**Важно:** Токен возвращается только при создании! Сохраните его.

### Получить токены пользователя

```bash
curl http://localhost:8001/api/users/1/tokens
```

### Обновить токен

```bash
curl -X PATCH http://localhost:8001/api/users/1/tokens/1 \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false
  }'
```

### Удалить токен

```bash
curl -X DELETE http://localhost:8001/api/users/1/tokens/1
```

## Использование API с токеном

Все эндпоинты теперь требуют заголовок `X-API-Token`:

```bash
# Получить список кампаний
curl http://localhost:8001/api/campaigns/list \
  -H "X-API-Token: eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjUwOTA0djEi..."

# Получить статистику
curl -X POST http://localhost:8001/stats/normquery \
  -H "X-API-Token: eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjUwOTA0djEi..." \
  -H "Content-Type: application/json" \
  -d '{
    "from_date": "2026-02-01",
    "to_date": "2026-02-21",
    "items": [{"advert_id": 123, "nm_id": 456}]
  }'
```

## Схема работы

1. Администратор создаёт пользователя через `/api/users`
2. Для пользователя создаётся токен через `/api/users/{id}/tokens`
3. Пользователь использует полученный токен в заголовке `X-API-Token` для всех запросов
4. Приложение автоматически определяет токен и выполняет запросы от имени пользователя

## Миграции

### Применить миграции

```bash
alembic upgrade head
```

### Откатить миграцию

```bash
alembic downgrade -1
```

### Создать новую миграцию

```bash
alembic revision --autogenerate -m "Description of changes"
```

## Структура файлов

```
wb_promotion_app/
├── models.py           # SQLAlchemy модели (User, UserApiToken)
├── schemas.py          # Pydantic схемы для API
├── config.py           # Конфигурация БД и Session factory
├── dependencies.py     # Зависимости для аутентификации
├── users.py            # Эндпоинты для управления пользователями
├── main.py             # Основные эндпоинты API
├── alembic.ini         # Конфигурация Alembic
└── migrations/         # Миграции базы данных
    ├── env.py
    ├── script.py.mako
    └── versions/
        └── 001_initial.py
```
