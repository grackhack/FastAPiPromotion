# Инструкция по обновлению проекта на сервере

## 1. Подготовка базы данных

```bash
# Подключение к серверу
ssh botuser@195.133.49.121

# Создание БД (нужен пароль sudo)
sudo -u postgres psql -c "CREATE DATABASE wb_promotion_app;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE wb_promotion_app TO bot_user;"
```

## 2. Обновление кода проекта

```bash
cd /home/botuser/FastAPiPromotion

# Если проект в git
git pull origin main

# Или скопируйте файлы вручную
```

## 3. Установка зависимостей

```bash
cd /home/botuser/FastAPiPromotion

# Активация виртуального окружения
source .venv/bin/activate

# Установка новых зависимостей
pip install sqlalchemy psycopg2-binary alembic

# Или обновите через requirements.txt
pip install -r wb_promotion_app/requirements.txt
```

## 4. Обновление .env файла

Добавьте `DATABASE_URL` в `/home/botuser/FastAPiPromotion/.env`:

```bash
cat >> /home/botuser/FastAPiPromotion/.env << EOF

# База данных PostgreSQL
DATABASE_URL=postgresql://bot_user:botpwd@localhost:5432/wb_promotion_app
EOF
```

## 5. Применение миграций

```bash
cd /home/botuser/FastAPiPromotion/wb_promotion_app

# Применение миграций Alembic
alembic upgrade head
```

## 6. Создание первого пользователя

```bash
# Через скрипт инициализации
cd /home/botuser/FastAPiPromotion
source .venv/bin/activate
python wb_promotion_app/init_db.py myshop shop@example.com YOUR_WB_API_TOKEN

# Или через API после запуска сервера
curl -X POST http://localhost:8001/api/users \
  -H "Content-Type: application/json" \
  -d '{"username": "myshop", "email": "shop@example.com"}'

# Затем создайте токен
curl -X POST http://localhost:8001/api/users/1/tokens \
  -H "Content-Type: application/json" \
  -d '{"token": "YOUR_WB_API_TOKEN", "description": "Main token"}'
```

## 7. Перезапуск сервиса

```bash
# Перезапуск systemd сервиса
sudo systemctl restart wb-promotion-app

# Проверка статуса
sudo systemctl status wb-promotion-app

# Просмотр логов
journalctl -u wb-promotion-app -f
```

## 8. Проверка работы

```bash
# Проверка доступности API
curl http://localhost:8001/api/users

# Проверка с токеном
curl -H "X-API-Token: YOUR_TOKEN" http://localhost:8001/api/campaigns/list
```

## API эндпоинты

### Пользователи
- `POST /api/users` - Создать пользователя
- `GET /api/users` - Список пользователей
- `GET /api/users/{id}` - Получить пользователя
- `PATCH /api/users/{id}` - Обновить пользователя
- `DELETE /api/users/{id}` - Удалить пользователя

### Токены
- `POST /api/users/{id}/tokens` - Создать токен
- `GET /api/users/{id}/tokens` - Список токенов
- `GET /api/users/{id}/tokens/{token_id}` - Получить токен
- `PATCH /api/users/{id}/tokens/{token_id}` - Обновить токен
- `DELETE /api/users/{id}/tokens/{token_id}` - Удалить токен

### Wildberries API (требуют X-API-Token)
- `GET /api/campaigns/list` - Список кампаний
- `GET /api/campaigns/count` - Количество кампаний
- `GET /api/campaigns/adverts` - Детали кампаний
- `GET /api/campaigns/media` - Медиакампании
- `POST /search-clusters/*` - Операции с поисковыми кластерами
- `POST /stats/*` - Статистика

## Пример использования

```bash
# 1. Создаём пользователя
USER_ID=$(curl -X POST http://localhost:8001/api/users \
  -H "Content-Type: application/json" \
  -d '{"username": "shop1", "email": "shop1@example.com"}' | jq '.id')

# 2. Создаём токен
TOKEN=$(curl -X POST http://localhost:8001/api/users/${USER_ID}/tokens \
  -H "Content-Type: application/json" \
  -d '{"token": "YOUR_WB_API_TOKEN", "description": "Shop1 token"}' | jq -r '.token')

# 3. Используем токен для запросов
curl -H "X-API-Token: ${TOKEN}" http://localhost:8001/api/campaigns/list
```

## Откат изменений

Если что-то пошло не так:

```bash
# Откат миграции
cd /home/botuser/FastAPiPromotion/wb_promotion_app
alembic downgrade -1

# Или полный откат
alembic downgrade base
```

## Логи

```bash
# Логи приложения
journalctl -u wb-promotion-app -f

# Логи PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-13-main.log
```
