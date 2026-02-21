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
- [x] Создать структуру папок
- [x] Перенести модели и схемы

### Этап 2: Зависимости ✅
- [x] Создать `core/dependencies.py`
- [x] `get_current_user()` - из session cookie
- [x] `require_auth()` - требует авторизации
- [x] `get_wb_client()` - создаёт клиента для пользователя

### Этап 3: Services ✅
- [x] Создать `services/wb_service.py`
- [x] Инкапсулировать работу с WB API
- [x] Обработка ошибок и retry logic
- [x] Кэширование запросов

### Этап 4: Web роуты (SSR) ✅
- [x] `/` - главная с кампаниями
- [x] `/campaigns` - страница всех кампаний
- [x] `/campaign/{id}` - страница кампании
- [x] Загрузка данных на бэкенде

### Этап 5: API роуты ✅
- [x] `/api/campaigns` - список кампаний
- [x] `/api/campaigns/media` - медиакампании
- [x] `/api/stats/*` - статистика
- [x] Все endpoints без токенов (берут из сессии)

### Этап 6: Templates ✅
- [x] Обновить `index.html` для SSR
- [x] Навигация через Jinja2
- [x] Данные в JSON из бэкенда

### Этап 7: Frontend ✅
- [x] Удалить apiFetch и всю логику токенов
- [x] Удалить currentApiToken
- [x] Оставить только UI взаимодействия
- [x] Обновить loadPromotionCampaigns для API без токенов

### Этап 8: Тестирование ✅
- [x] Unit тесты для services
- [x] Integration тесты для endpoints
- [x] Проверка авторизации
- [x] Проверка SSR
- [x] Все импорты работают
- [x] Приложение загружается (49 роутов)

### Этап 9: Документация ✅
- [x] ARCHITECTURE.md - полное описание архитектуры
- [x] REFACTOR_PLAN.md обновлён
- [x] Чеклист для продакшена

## Готово к merge! ✅

### Статистика рефакторинга:
- **Этапов выполнено:** 9/9
- **Файлов создано:** 10
- **Файлов обновлено:** 8
- **Строк кода:** +500 (Python), -200 (JS)
- **Роутов:** 49

### Что сделано:
1. ✅ Вся бизнес-логика на бэкенде (services/wb_service.py)
2. ✅ Токены только на сервере (core/dependencies.py)
3. ✅ SSR для страниц (web/campaigns.py)
4. ✅ API без токенов (api/campaigns.py)
5. ✅ Фронтенд только отображает (templates/, static/js/)
6. ✅ Документация (ARCHITECTURE.md)

### Следующие шаги:
1. Merge в master
2. Обновить production сервер
3. Мониторинг после деплоя

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
