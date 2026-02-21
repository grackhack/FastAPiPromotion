# Автодеплой проекта WB Promotion App

## Настройка GitHub Actions

### 1. Сгенерируйте SSH-ключ для деплоя

**На сервере:**
```bash
ssh botuser@195.133.49.121
cd ~/FastAPiPromotion
bash scripts/setup-github-ssh.sh
```

Скопируйте приватный ключ который выведет скрипт.

### 2. Добавьте секреты в GitHub

В репозитории: **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Значение |
|--------|----------|
| `SERVER_HOST` | `195.133.49.121` |
| `SERVER_USER` | `botuser` |
| `SERVER_SSH_PRIVATE_KEY` | Приватный SSH-ключ из шага 1 |

### 3. Настройка на сервере

```bash
# Подключение к серверу
ssh botuser@195.133.49.121

# Создание БД для пользователей
sudo -u postgres psql -c "CREATE DATABASE wb_promotion_app;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE wb_promotion_app TO bot_user;"

# Обновление .env
cat >> ~/FastAPiPromotion/.env << EOF

# База данных PostgreSQL
DATABASE_URL=postgresql://bot_user:botpwd@localhost:5432/wb_promotion_app
EOF
```

### 4. Первый деплой

```bash
# Локально
git add .
git commit -m "Add multiuser support and auto-deploy"
git push origin master
```

GitHub Actions автоматически:
- Заберёт изменения
- Установит зависимости
- Применит миграции БД
- Перезапустит приложение

### 5. Создание первого пользователя

После деплоя создайте пользователя через API:

```bash
curl -X POST http://195.133.49.121:8001/api/users \
  -H "Content-Type: application/json" \
  -d '{"username": "myshop", "email": "shop@example.com"}'

# Создайте токен для пользователя
curl -X POST http://195.133.49.121:8001/api/users/1/tokens \
  -H "Content-Type: application/json" \
  -d '{"token": "YOUR_WB_API_TOKEN", "description": "Main token"}'
```

### 6. Использование API с токеном

```bash
# Все запросы к API требуют заголовок X-API-Token
curl -H "X-API-Token: YOUR_TOKEN" \
  http://195.133.49.121:8001/api/campaigns/list
```

## Структура файлов

```
FastAPIProject1/
├── .github/workflows/
│   └── deploy.yml          # Workflow автодеплоя
├── scripts/
│   └── setup-github-ssh.sh # Скрипт настройки SSH
├── wb_promotion_app/
│   ├── models.py           # SQLAlchemy модели
│   ├── schemas.py          # Pydantic схемы
│   ├── config.py           # Конфигурация БД
│   ├── dependencies.py     # Зависимости аутентификации
│   ├── users.py            # API пользователей
│   ├── main.py             # Основное API
│   ├── init_db.py          # Инициализация БД
│   ├── alembic.ini         # Конфиг Alembic
│   └── migrations/         # Миграции БД
├── DEPLOY_MULTIUSER.md     # Инструкция по деплою
├── GITHUB_ACTIONS_SETUP.md # Настройка GitHub Actions
└── MULTIUSER.md            # Документация мультипользовательского режима
```

## Workflow деплоя

При пуше в `master`/`main`:

1. Checkout кода
2. SSH подключение к серверу
3. `git pull` изменений
4. Установка зависимостей (`pip install`)
5. Применение миграций (`alembic upgrade head`)
6. Перезапуск сервиса (`systemctl --user restart`)
7. Проверка доступности (порт 8001)

## Отладка

### Проверка статуса деплоя
- GitHub → Actions → последний запуск

### Логи на сервере
```bash
journalctl --user -u wb-promotion-app -f
```

### Ручное применение миграций
```bash
cd ~/FastAPiPromotion/wb_promotion_app
source .venv/bin/activate
alembic upgrade head
```

### Проверка БД
```bash
PGPASSWORD=botpwd psql -h localhost -U bot_user -d wb_promotion_app -c "\dt"
```
