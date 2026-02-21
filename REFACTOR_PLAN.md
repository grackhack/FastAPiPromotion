# План рефакторинга архитектуры

## Цель
Перенести всю бизнес-логику на бэкенд (FastAPI), фронтенд только отображает данные.

## Проблемы текущей архитектуры
- ❌ Токены WB API передаются на клиент
- ❌ Логика обработки ошибок в JavaScript
- ❌ Проверки авторизации на фронте
- ❌ Много API запросов с повторяющейся логикой
- ❌ Токен доступен из DevTools

## Новая архитектура

### 1. Backend (FastAPI)
```
/app
├── api/              # API роуты (только данные)
├── web/              # Web роуты (SSR страницы)
├── core/             # Ядро (авторизация, зависимости)
├── services/         # Бизнес-логика (WB API клиент)
├── models/           # SQLAlchemy модели
├── schemas/          # Pydantic схемы
└── templates/        # Jinja2 шаблоны
```

### 2. Принцип работы
```python
# Веб-страница с SSR
@app.get("/campaigns")
async def campaigns_page(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    # Бэкенд загружает данные
    campaigns = get_campaigns_for_user(user, db)
    return templates.TemplateResponse("campaigns.html", {
        "request": request,
        "campaigns": campaigns,
        "user": user
    })

# API endpoint (для AJAX)
@app.get("/api/campaigns")
async def campaigns_api(
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    # Возвращает JSON
    return get_campaigns_for_user(user, db)
```

### 3. Безопасность
- Токены хранятся только в БД
- Сессионные cookies для аутентификации
- Фронтенд не знает о WB API токенах

## Этапы рефакторинга

### Этап 1: Подготовка ✅
- [x] Создать ветку refactor/ssr-architecture
- [ ] Создать структуру папок
- [ ] Перенести модели и схемы

### Этап 2: Зависимости
- [ ] Создать `core/dependencies.py`
- [ ] `get_current_user()` - из session cookie
- [ ] `require_auth()` - требует авторизации
- [ ] `get_wb_client()` - создаёт клиента для пользователя

### Этап 3: Services
- [ ] Создать `services/wb_client.py`
- [ ] Инкапсулировать работу с WB API
- [ ] Обработка ошибок и retry logic
- [ ] Кэширование запросов

### Этап 4: Web роуты (SSR)
- [ ] `/` - главная с кампаниями
- [ ] `/campaign/{id}` - страница кампании
- [ ] `/profile` - личный кабинет
- [ ] `/login` - вход/выход

### Этап 5: API роуты (для AJAX)
- [ ] `/api/campaigns` - список кампаний
- [ ] `/api/campaigns/{id}` - детали
- [ ] `/api/stats` - статистика
- [ ] Все endpoints без токенов (берут из сессии)

### Этап 6: Templates
- [ ] Базовый layout `base.html`
- [ ] `campaigns.html` - список кампаний
- [ ] `campaign_detail.html` - детали
- [ ] `profile.html` - профиль
- [ ] `login.html` - вход

### Этап 7: Frontend (минимум JS)
- [ ] Удалить apiFetch и всю логику токенов
- [ ] Оставить только UI взаимодействия
- [ ] Модальные окна
- [ ] Формы (отправка на бэкенд)

### Этап 8: Тестирование
- [ ] Unit тесты для services
- [ ] Integration тесты для endpoints
- [ ] Проверка авторизации
- [ ] Проверка SSR

## Структура файлов (новая)
```
wb_promotion_app/
├── __init__.py
├── main.py                 # Точка входа
├── config.py               # Конфигурация
├── database.py             # DB сессии
├── core/
│   ├── __init__.py
│   ├── security.py         # Session management
│   └── dependencies.py     # FastAPI Depends
├── services/
│   ├── __init__.py
│   └── wb_client.py        # WB API сервис
├── api/                    # REST API endpoints
│   ├── __init__.py
│   ├── campaigns.py
│   ├── stats.py
│   └── users.py
├── web/                    # Web endpoints (SSR)
│   ├── __init__.py
│   ├── auth.py
│   ├── campaigns.py
│   └── profile.py
├── models/                 # SQLAlchemy
│   └── ...
├── schemas/                # Pydantic
│   └── ...
├── templates/              # Jinja2
│   ├── base.html
│   ├── campaigns.html
│   └── ...
└── static/                 # CSS, JS
    ├── css/
    └── js/                 # Только UI логика
```

## Критерии готовности
- [ ] Нет `X-API-Token` в JavaScript
- [ ] Все данные загружаются на бэкенде
- [ ] Фронтенд только отображает
- [ ] Токены только в БД
- [ ] Все тесты проходят
- [ ] Деплой работает

## Риски
- ⚠️ Время реализации (2-3 дня)
- ⚠️ Нужно обновить деплой скрипт
- ⚠️ Возможны breaking changes

## Преимущества
- ✅ Безопасно (токены на сервере)
- ✅ Легко поддерживать (вся логика в Python)
- ✅ Быстрая первая загрузка (SSR)
- ✅ SEO-дружелюбно
- ✅ Правильное разделение ответственности
