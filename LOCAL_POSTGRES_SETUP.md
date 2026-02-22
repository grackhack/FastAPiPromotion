# Настройка локального PostgreSQL для разработки

## 1. Установка PostgreSQL (если не установлен)

### Windows
1. Скачайте с [postgresql.org](https://www.postgresql.org/download/windows/)
2. Установите, запомните пароль пользователя `postgres`
3. Порт по умолчанию: `5432`

### Проверка установки
```bash
psql --version
```

## 2. Создание базы данных

### Вариант А: Через pgAdmin
1. Откройте pgAdmin 4
2. Подключитесь к серверу PostgreSQL
3. ПКМ на "Databases" → "Create" → "Database"
4. Имя: `wb_promotion_app`
5. Owner: `postgres`
6. Encoding: `UTF8`

### Вариант Б: Через командную строку
```bash
# Windows (PowerShell от имени администратора)
cd "C:\Program Files\PostgreSQL\16\bin"
.\psql -U postgres -c "CREATE DATABASE wb_promotion_app WITH OWNER = postgres ENCODING = 'UTF8';"
```

### Вариант В: Выполнить SQL скрипт
```bash
cd C:\Users\Admin\PycharmProjects\FastAPIProject1
psql -U postgres -f create_db.sql
```

## 3. Проверка подключения

```bash
# Windows
psql -U postgres -d wb_promotion_app -h localhost

# Если запросит пароль, введите пароль пользователя postgres
```

## 4. Инициализация базы данных (создание таблиц)

```bash
# Из корня проекта
.venv\Scripts\python.exe scripts\init_db.py

# Или через Python напрямую
python scripts\init_db.py
```

Это создаст таблицы:
- `users` - пользователи
- `user_api_tokens` - API токены

## 5. Запуск приложения

```bash
# Установка зависимостей (если не сделано)
.venv\Scripts\pip.exe install -e .

# Запуск сервера
.venv\Scripts\uvicorn.exe wb_promotion_app.main:app --reload --host 0.0.0.0 --port 8000

# Или через скрипт
.venv\Scripts\python.exe wb_promotion_app/run_server.py
```

## 6. Проверка работы

Откройте в браузере:
- Веб-интерфейс: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

## Решение проблем

### Ошибка подключения "connection refused"
- Проверьте, запущен ли PostgreSQL сервис
- Windows: `services.msc` → "postgresql-x64-16" должен быть "Running"

### Ошибка аутентификации
- Убедитесь, что пароль в `.env` совпадает с паролем пользователя postgres
- Или измените `.env`: `DATABASE_URL=postgresql://postgres:ВАШ_ПАРОЛЬ@localhost:5432/wb_promotion_app`

### Ошибка "database does not exist"
- Выполните шаг 2 для создания базы данных
