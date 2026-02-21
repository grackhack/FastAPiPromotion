# Архитектура WB Promotion App (SSR)

## Обзор

После рефакторинга приложение использует **Server-Side Rendering (SSR)** архитектуру с правильной сепарацией ответственности.

## Архитектурные принципы

1. **Бэкенд (FastAPI)** - вся бизнес-логика, работа с WB API, аутентификация
2. **Фронтенд (Jinja2 + JS)** - только отображение данных и UI взаимодействия
3. **Токены** - хранятся только на сервере, фронтенд не знает о них

## Структура проекта

```
wb_promotion_app/
├── main.py                 # Точка входа, подключение роутов
├── config.py               # Конфигурация (БД, настройки)
├── models.py               # SQLAlchemy модели (User, UserApiToken)
├── schemas.py              # Pydantic схемы (DTO)
├── auth.py                 # Session management
├── dependencies.py         # [DEPRECATED] старые зависимости
│
├── core/                   # Ядро приложения
│   ├── __init__.py
│   └── dependencies.py     # FastAPI Depends (auth, token, wb_client)
│
├── services/               # Бизнес-логика
│   ├── __init__.py
│   └── wb_service.py       # WB API сервис (инкапсуляция)
│
├── api/                    # REST API endpoints
│   ├── __init__.py
│   └── campaigns.py        # API для AJAX запросов (без токенов)
│
├── web/                    # Web endpoints (SSR)
│   ├── __init__.py
│   └── campaigns.py        # SSR endpoints для страниц
│
├── templates/              # Jinja2 шаблоны
│   ├── index.html          # Главная (SSR с данными)
│   ├── campaigns.html      # Все кампании
│   ├── campaign-detail.html # Детали кампании
│   ├── profile.html        # Личный кабинет
│   └── login.html          # Вход
│
└── static/                 # Статические файлы
    ├── css/
    │   └── style.css
    └── js/                 # Только UI логика
        ├── campaigns-list.js
        └── campaign-detail.js
```

## Поток данных

### SSR (Web endpoints)

```
1. Пользователь → GET /
2. FastAPI → get_current_user() → User из session cookie
3. FastAPI → get_wb_client() → WBService с токеном пользователя
4. WBService → WB API → данные
5. FastAPI → templates.TemplateResponse → HTML с данными
6. Браузер → отображает HTML + JSON данные
```

### API (AJAX запросы)

```
1. Фронтенд → GET /api/campaigns
2. FastAPI → require_auth() → User из session cookie
3. FastAPI → get_wb_client() → WBService с токеном
4. WBService → WB API → JSON
5. Фронтенд → отображает JSON
```

## Ключевые компоненты

### 1. Core Dependencies (`core/dependencies.py`)

```python
# Получить текущего пользователя (или None)
user = await get_current_user(request, db)

# Требовать авторизацию (401 или редирект)
user = await require_auth(request, db)

# Требовать токен (403 или редирект на профиль)
token = await require_token(request, user, db)

# Создать WB клиент для пользователя
wb = get_wb_client(token)
```

### 2. WB Service (`services/wb_service.py`)

```python
class WBService:
    """Инкапсулирует работу с WB API"""
    
    def get_campaigns(self) -> List[Dict]:
        """Получить кампании, конвертировать в dict"""
        
    def get_stats(self, from_date, to_date, items) -> Dict:
        """Получить статистику"""
```

### 3. API Endpoints (`api/campaigns.py`)

```python
@router.get("/campaigns")
async def get_campaigns(
    user: User = Depends(require_auth),
    wb: WBService = Depends(get_wb_client)
):
    return wb.get_campaigns()
```

### 4. Web Endpoints (`web/campaigns.py`)

```python
@app.get("/")
async def campaigns_page(
    request: Request,
    user: User = Depends(get_current_user),
    wb: WBService = Depends(get_wb_client)
):
    campaigns = wb.get_campaigns()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "campaigns": campaigns
    })
```

## Безопасность

### Хранение токенов
- ✅ Токены в БД (user_api_tokens таблица)
- ✅ Доступ только через сессию
- ✅ Фронтенд не получает токен

### Аутентификация
- ✅ Session cookies (httponly, samesite=lax)
- ✅ 7 дней срок действия
- ✅ Проверка в БД при каждом запросе

### API защита
- ✅ require_auth() для всех endpoints
- ✅ require_token() для WB API endpoints
- ✅ 401/403 для неавторизованных

## Миграция со старой архитектуры

### Было (неправильно):
```javascript
// Фронтенд знает о токенах
const response = await fetch('/campaigns/adverts', {
    headers: { 'X-API-Token': currentApiToken }
});
```

### Стало (правильно):
```javascript
// Фронтенд просто вызывает API
const response = await fetch('/api/campaigns');
// Бэкенд сам берёт токен из сессии
```

## Тестирование

### Unit тесты (services)
```python
def test_wb_service_get_campaigns():
    client = MockWBClient()
    service = WBService(client)
    campaigns = service.get_campaigns()
    assert len(campaigns) > 0
```

### Integration тесты (endpoints)
```python
def test_api_campaigns_requires_auth(client):
    response = client.get("/api/campaigns")
    assert response.status_code == 401
```

## Развёртывание

### Переменные окружения
```env
DATABASE_URL=postgresql://user:pass@localhost/db
WB_API_TOKEN=fallback_token  # Для старых endpoints
```

### Миграции БД
```bash
alembic upgrade head
```

### Перезапуск
```bash
systemctl --user restart wb-promotion-app
```

## Преимущества новой архитектуры

| Характеристика | Было | Стало |
|---------------|------|-------|
| Токены на клиенте | ❌ | ✅ Нет |
| Бизнес-логика | ❌ JS | ✅ Python |
| SSR | ❌ | ✅ Да |
| Безопасность | ⚠️ | ✅ Высокая |
| Поддержка | ❌ Сложно | ✅ Легко |
| Тестирование | ❌ Сложно | ✅ Unit-тесты |

## Чеклист для продакшена

- [ ] Все endpoints используют новые зависимости
- [ ] Удалены старые API endpoints с токенами
- [ ] Фронтенд не содержит логики токенов
- [ ] Session cookies настроены правильно
- [ ] Логи не содержат токены
- [ ] Unit-тесты написаны
- [ ] Integration-тесты проходят
- [ ] Документация обновлена
