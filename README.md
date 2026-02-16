# Wildberries Promotion API Manager

API для управления рекламными кампаниями Wildberries

## Быстрый старт

### Локальная разработка

```bash
# Установка зависимостей
pip install -e .

# Запуск
uvicorn wb_promotion_app.main:app --reload --host 0.0.0.0 --port 8000
```

### Деплой на сервер

1. **Клонирование на сервер:**
```bash
ssh botuser@195.133.49.121
git clone git@github.com:grackhack/FastAPiPromotion.git ~/FastAPiPromotion
cd ~/FastAPiPromotion
```

2. **Настройка окружения:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
# Отредактируйте .env и укажите ваш WB_API_TOKEN
nano .env
```

3. **Запуск приложения:**
```bash
# Порт 8000 может быть занят, используем 8001
cd wb_promotion_app
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8001 > ../app.log 2>&1 &
```

4. **Проверка:**
```bash
# Проверка логов
cat ~/FastAPiPromotion/app.log

# Проверка API
curl http://localhost:8001/docs
```

## Доступ к API

- **Swagger UI**: http://195.133.49.121:8001/docs
- **ReDoc**: http://195.133.49.121:8001/redoc
- **OpenAPI JSON**: http://195.133.49.121:8001/openapi.json

## Управление процессом

```bash
# Остановить приложение
pkill -f "uvicorn main:app"

# Перезапустить
cd ~/FastAPiPromotion/wb_promotion_app && source ../.venv/bin/activate && \
    nohup python -m uvicorn main:app --host 0.0.0.0 --port 8001 > ../app.log 2>&1 &

# Просмотр логов
tail -f ~/FastAPiPromotion/app.log
```

## Обновление из GitHub

```bash
cd ~/FastAPiPromotion
git pull
source .venv/bin/activate
pip install -e .
pkill -f "uvicorn main:app"
cd wb_promotion_app && nohup python -m uvicorn main:app --host 0.0.0.0 --port 8001 > ../app.log 2>&1 &
```

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `WB_API_TOKEN` | Токен API Wildberries | - |
| `APP_HOST` | Хост для прослушивания | `0.0.0.0` |
| `APP_PORT` | Порт приложения | `8000` |
| `APP_DEBUG` | Режим отладки | `False` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |

## Структура проекта

```
FastAPiPromotion/
├── wb_promotion_app/
│   ├── main.py           # Точка входа FastAPI
│   ├── api_client.py     # Клиент WB API
│   ├── schemas.py        # Pydantic схемы
│   ├── config.py         # Конфигурация
│   ├── utils.py          # Утилиты
│   ├── templates/        # HTML шаблоны
│   └── static/           # Статические файлы
├── .env.example          # Пример переменных окружения
├── pyproject.toml        # Зависимости проекта
├── deploy.sh             # Скрипт деплоя
└── wb-promotion.service  # Systemd сервис
```
