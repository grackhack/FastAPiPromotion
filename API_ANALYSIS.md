# Анализ соответствия реализации Wildberries Promotion API

## Обзор

Документ сравнивает текущую реализацию проекта с официальной документацией Wildberries Promotion API (https://dev.wildberries.ru/docs/openapi/promotion).

**Дата анализа:** 17 февраля 2026 г.

---

## 1. Реализованные эндпоинты

### ✅ Полностью реализованные

| Эндпоинт API | Метод | Реализация | Статус |
|--------------|-------|------------|--------|
| `/adv/v1/promotion/count` | GET | `get_campaigns_count()` | ✅ Реализован |
| `/api/advert/v2/adverts` | GET | `get_adverts()` | ✅ Реализован |
| `/adv/v1/adverts` (media) | GET | `get_media_campaigns()` | ✅ Реализован |
| `/adv/v1/count` (media) | GET | `get_media_campaigns_count()` | ✅ Реализован |
| `/adv/v0/normquery/get-bids` | POST | `get_search_cluster_bids()` | ✅ Реализован |
| `/adv/v0/normquery/bids` | POST | `set_search_cluster_bids()` | ✅ Реализован |
| `/adv/v0/normquery/bids` | DELETE | `remove_search_cluster_bids()` | ✅ Реализован |
| `/adv/v0/normquery/get-minus` | POST | `get_minus_phrases()` | ✅ Реализован |
| `/adv/v0/normquery/set-minus` | POST | `set_minus_phrases()` | ✅ Реализован |
| `/adv/v0/normquery/list` | POST | `get_search_cluster_list()` | ✅ Реализован |
| `/adv/v0/normquery/stats` | POST | `get_search_cluster_stats()`, `get_normquery_stats()` | ✅ Реализован |
| `/adv/v3/fullstats` | GET | `get_full_stats()` | ✅ Реализован |

---

## 2. НЕРЕАЛИЗОВАННЫЕ эндпоинты (возможности для расширения)

### 🔴 Кампании - управление

| Эндпоинт API | Метод | Описание | Приоритет |
|--------------|-------|----------|-----------|
| `/api/advert/v1/bids/min` | POST | Минимальные ставки для карточек товаров | 🔴 Высокий |
| `/adv/v2/seacat/save-ad` | POST | **Создать кампанию** | 🔴 Высокий |
| `/adv/v1/supplier/subjects` | GET | Предметы для кампаний | 🟡 Средний |
| `/adv/v2/supplier/nms` | POST | Карточки товаров для кампаний | 🟡 Средний |
| `/adv/v0/delete` | GET | Удаление кампании | 🟡 Средний |
| `/adv/v0/rename` | POST | Переименование кампании | 🟡 Средний |
| `/adv/v0/start` | GET | Запуск кампании | 🟡 Средний |
| `/adv/v0/pause` | GET | Пауза кампании | 🟡 Средний |
| `/adv/v0/stop` | GET | Завершение кампании | 🟡 Средний |
| `/adv/v0/auction/placements` | PUT | Изменение мест размещения | 🟢 Низкий |
| `/api/advert/v1/bids` | PATCH | Изменение ставок в кампаниях | 🟡 Средний |
| `/adv/v0/auction/nms` | PATCH | Изменение списка карточек товаров | 🟢 Низкий |

### 🔴 Финансы

| Эндпоинт API | Метод | Описание | Приоритет |
|--------------|-------|----------|-----------|
| `/adv/v1/balance` | GET | **Баланс счёта** | 🔴 Высокий |
| `/adv/v1/budget` | GET | Бюджет кампании | 🟡 Средний |
| `/adv/v1/budget/deposit` | POST | Пополнение бюджета кампании | 🟢 Низкий |
| `/adv/v1/upd` | GET | История затрат | 🟡 Средний |
| `/adv/v1/payments` | GET | История пополнений счёта | 🟡 Средний |

### 🔴 Медиакампании (расширенно)

| Эндпоинт API | Метод | Описание | Приоритет |
|--------------|-------|----------|-----------|
| `/adv/v1/advert` | GET | Информация о медиакампании | 🟢 Низкий |
| `/adv/v1/stats` | POST | Статистика медиакампаний | 🟡 Средний |

### 🔴 Календарь акций (требуется токен "Цены и скидки")

| Эндпоинт API | Метод | Описание | Приоритет |
|--------------|-------|----------|-----------|
| `/api/v1/calendar/promotions` | GET | Список акций | 🟢 Низкий |
| `/api/v1/calendar/promotions/details` | GET | Детали акций | 🟢 Низкий |
| `/api/v1/calendar/promotions/nomenclatures` | GET | Товары для акции | 🟢 Низкий |
| `/api/v1/calendar/promotions/upload` | POST | Добавить товар в акцию | 🟢 Низкий |

### 🔴 Статистика (расширенно)

| Эндпоинт API | Метод | Описание | Приоритет |
|--------------|-------|----------|-----------|
| `/adv/v1/normquery/stats` | POST | Статистика по кластерам (по дням) | 🟢 Низкий |

---

## 3. Rate Limiting (ограничения API)

### Текущие ограничения (согласно документации WB)

| Эндпоинт | Лимит | Интервал | Всплеск |
|----------|-------|----------|---------|
| `/adv/v1/promotion/count` | 5 запросов | 1 сек | 5 |
| `/api/advert/v2/adverts` | 5 запросов | 1 сек | 5 |
| `/adv/v0/normquery/get-bids` | 5 запросов | 1 сек | 10 |
| `/adv/v0/normquery/bids` (POST) | 2 запроса | 1 сек | 4 |
| `/adv/v0/normquery/bids` (DELETE) | 5 запросов | 1 сек | 10 |
| `/adv/v0/normquery/get-minus` | 5 запросов | 1 сек | 10 |
| `/adv/v0/normquery/set-minus` | 5 запросов | 1 сек | 10 |
| `/adv/v0/normquery/list` | 5 запросов | 1 сек | 10 |
| `/adv/v0/normquery/stats` | 10 запросов | 1 мин | 20 |
| `/adv/v3/fullstats` | 3 запроса | 1 мин | 1 |
| `/adv/v1/balance` | 1 запрос | 1 сек | 5 |
| `/adv/v1/adverts` (media) | 10 запросов | 1 сек | 10 |
| `/adv/v1/count` (media) | 10 запросов | 1 сек | 10 |

### ⚠️ Рекомендации по rate limiting

**В проекте НЕ реализовано** автоматическое управление rate limiting. Рекомендуется добавить:

1. **Rate Limiter** (например, `pyrate-limiter` или `aiolimiter`)
2. **Retry logic** с экспоненциальной задержкой для HTTP 429
3. **Queue** для пакетных операций

---

## 4. Синхронизация данных

Согласно документации WB:

| Данные | Частота обновления |
|--------|-------------------|
| Общая синхронизация с базой | Раз в 3 минуты |
| Статусы кампаний | Раз в 1 минуту |
| Ставки кампаний | Раз в 30 секунд |

**Рекомендация:** Добавить кэширование с TTL для часто вызываемых методов.

---

## 5. Проблемы и замечания

### ⚠️ Критические

1. **Отсутствие обработки HTTP 429** (Too Many Requests)
   - API возвращает 429 при превышении лимита
   - Требуется retry logic

2. **Нет валидации токена**
   - Токен проверяется только на наличие
   - Нет проверки на истечение срока действия

3. **Относится к балансy**
   - Нет метода проверки баланса
   - Невозможно контролировать расходы

### ⚠️ Средние

1. **Неполная типизация**
   - Некоторые методы возвращают `Dict[str, Any]` вместо строгих моделей
   - Усложняет поддержку и тестирование

2. **Отсутствие unit-тестов**
   - Файл `test_app.py` существует, но не покрыты все методы

3. **Нет логирования запросов к API**
   - Полезно для отладки и аудита

### ℹ️ Минорные

1. **Дублирование базового URL**
   - В `api_client.py` жёстко задан `self.base_url`
   - Для медиакампаний используется отдельный URL, но это не конфигурируется

2. **Разные форматы дат**
   - В некоторых местах используется `date`, в других `datetime`
   - Требуется унификация

---

## 6. Рекомендации по расширению

### Приоритет 1 (Высокий)

```python
# 1. Добавить метод получения баланса
def get_balance(self) -> BalanceResponse:
    """
    Получить баланс счёта продвижения
    
    GET /adv/v1/balance
    
    Returns:
        BalanceResponse: {
            "balance": int,      # Основной баланс
            "net": int,          # Бонусный баланс
            "bonus": int,        # Бонусы
            "cashbacks": [...]   # Список кэшбэков
        }
    """
    endpoint = "/adv/v1/balance"
    return self._make_request("GET", endpoint)

# 2. Добавить метод создания кампании
def create_campaign(
    self,
    name: str,
    nm_ids: List[int],
    bid_type: str = "manual",
    payment_type: str = "cpm",
    placement_types: List[str] = None
) -> int:
    """
    Создать новую рекламную кампанию
    
    POST /adv/v2/seacat/save-ad
    
    Args:
        name: Название кампании
        nm_ids: Список артикулов WB (макс. 50)
        bid_type: "manual" или "unified"
        payment_type: "cpm" или "cpc"
        placement_types: ["search"], ["recommendations"], или оба
    
    Returns:
        int: ID созданной кампании
    """
    endpoint = "/adv/v2/seacat/save-ad"
    payload = {
        "name": name,
        "nms": nm_ids,
        "bid_type": bid_type,
        "payment_type": payment_type,
        "placement_types": placement_types or ["search"]
    }
    return self._make_request("POST", endpoint, payload)

# 3. Добавить методы управления кампаниями
def start_campaign(self, campaign_id: int) -> None:
    """Запустить кампанию (GET /adv/v0/start)"""
    
def pause_campaign(self, campaign_id: int) -> None:
    """Приостановить кампанию (GET /adv/v0/pause)"""
    
def stop_campaign(self, campaign_id: int) -> None:
    """Завершить кампанию (GET /adv/v0/stop)"""
    
def delete_campaign(self, campaign_id: int) -> None:
    """Удалить кампанию (GET /adv/v0/delete)"""
    
def rename_campaign(self, campaign_id: int, new_name: str) -> None:
    """Переименовать кампанию (POST /adv/v0/rename)"""
```

### Приоритет 2 (Средний)

```python
# 4. Rate Limiter
from pyrate_limiter import Duration, Rate, Limiter

RATES = [
    Rate(limit=5, interval=Duration.SECOND),  # Для большинства эндпоинтов
    Rate(limit=2, interval=Duration.SECOND),  # Для set-bids
    Rate(limit=10, interval=Duration.MINUTE), # Для stats
]

limiter = Limiter(*RATES)

# 5. Retry logic
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True
)
def _make_request(self, method: str, endpoint: str, payload: Optional[Dict] = None):
    # ... existing code ...
    if response.status_code == 429:
        raise Exception("Rate limit exceeded")
```

### Приоритет 3 (Низкий)

```python
# 6. Кэширование
from functools import lru_cache
from datetime import timedelta

# Кэширование на 3 минуты (синхронизация данных WB)
@cache(ttl=timedelta(minutes=3))
def get_campaigns_count(self):
    # ...
```

---

## 7. Новые модели данных

```python
# schemas.py - новые схемы

class BalanceResponse(BaseModel):
    """Ответ эндпоинта /adv/v1/balance"""
    balance: int = Field(..., description="Основной баланс (копейки)")
    net: int = Field(0, description="Бонусный баланс")
    bonus: int = Field(0, description="Бонусы")
    cashbacks: List[CashbackItem] = Field(default_factory=list)


class CashbackItem(BaseModel):
    """Элемент кэшбэка"""
    sum: int
    percent: int
    expiration_date: datetime


class CreateCampaignRequest(BaseModel):
    """Запрос создания кампании"""
    name: str = Field(..., max_length=100)
    nm_ids: List[int] = Field(..., max_items=50)
    bid_type: Literal["manual", "unified"] = "manual"
    payment_type: Literal["cpm", "cpc"] = "cpm"
    placement_types: List[Literal["search", "recommendations"]] = ["search"]


class CampaignActionResponse(BaseModel):
    """Ответ действий с кампанией"""
    success: bool
    message: str
    campaign_id: Optional[int] = None


class MinBidsRequest(BaseModel):
    """Запрос минимальных ставок"""
    advert_id: int
    nm_ids: List[int] = Field(..., max_items=100)
    payment_type: Literal["cpm", "cpc"]
    placement_types: List[Literal["combined", "search", "recommendation"]]


class MinBidsResponse(BaseModel):
    """Ответ минимальных ставок"""
    bids: List[NMBidItem]


class NMBidItem(BaseModel):
    """Ставка для товара"""
    nm_id: int
    bids: List[BidTypeItem]


class BidTypeItem(BaseModel):
    """Ставка по типу размещения"""
    type: Literal["combined", "search", "recommendation"]
    value: int  # в копейках
```

---

## 8. Сводная таблица покрытия API

| Категория | Всего эндпоинтов | Реализовано | Процент |
|-----------|-----------------|-------------|---------|
| Кампании (списки) | 2 | 2 | 100% |
| Кампании (управление) | 10 | 0 | 0% |
| Поисковые кластеры | 6 | 6 | 100% |
| Статистика | 3 | 2 | 67% |
| Финансы | 5 | 0 | 0% |
| Медиакампании | 3 | 2 | 67% |
| Календарь акций | 4 | 0 | 0% |
| **ИТОГО** | **33** | **12** | **36%** |

---

## 9. Выводы

### Текущее состояние
Проект реализует **36%** доступного функционала API Wildberries Promotion.

### Сильные стороны
✅ Полная реализация работы с поисковыми кластерами  
✅ Рабочие методы получения статистики  
✅ Правильная структура проекта  
✅ Наличие веб-интерфейса  

### Зоны роста
🔴 **Управление кампаниями** — создание, запуск, пауза, удаление  
🔴 **Финансы** — баланс, история операций  
🟡 **Rate limiting** — защита от превышения лимитов API  
🟡 **Кэширование** — оптимизация запросов  

### Рекомендуемый порядок реализации
1. Метод получения баланса (`/adv/v1/balance`)
2. Методы управления статусом кампаний (start/pause/stop/delete)
3. Rate limiter для всех запросов
4. Метод создания кампании
5. Методы работы с минимальными ставками
