# Документация Wildberries Promotion API Manager

## Обзор

Wildberries Promotion API Manager - это мини-приложение, позволяющее управлять рекламными кампаниями Wildberries, включая работу с поисковыми кластерами.

## Установка и запуск

1. Клонируйте репозиторий
2. Установите зависимости: `pip install -r requirements.txt`
3. Настройте переменные окружения в файле `.env`
4. Запустите приложение: `uvicorn main:app --reload`

## Переменные окружения

- `WB_API_TOKEN` - токен API Wildberries (обязательно)
- `APP_HOST` - хост для запуска приложения (по умолчанию 0.0.0.0)
- `APP_PORT` - порт для запуска приложения (по умолчанию 8000)
- `APP_DEBUG` - режим отладки (по умолчанию False)
- `LOG_LEVEL` - уровень логирования (по умолчанию INFO)

## Структура проекта

```
wb_promotion_app/
├── main.py              # Основное приложение FastAPI
├── api_client.py        # Клиент для взаимодействия с API Wildberries
├── models.py            # Модели данных
├── schemas.py           # Схемы Pydantic для валидации данных
├── config.py            # Конфигурационные параметры
├── utils.py             # Вспомогательные функции
├── requirements.txt     # Зависимости проекта
├── .env                 # Файл переменных окружения
├── README.md            # Основная документация
├── example_usage.py     # Пример использования API
└── test_app.py          # Тесты для приложения
```

## Доступные эндпоинты

### GET /

Главная страница приложения

**Ответ:**
```json
{
  "message": "Wildberries Promotion API Manager"
}
```

### GET /campaigns

Получить список рекламных кампаний

**Ответ:**
```json
[
  {
    "id": 123456,
    "name": "Название кампании",
    "status": "active",
    "type": "search",
    "daily_budget": 1000.0,
    "total_budget": 10000.0
  }
]
```

### POST /search-clusters/bids

Получить ставки поисковых кластеров для указанных товаров в кампаниях

**Тело запроса:**
```json
[
  {
    "advert_id": 123456,
    "nm_id": 789012,
    "norm_query": "поисковый запрос",
    "bid": 1000
  }
]
```

**Ответ:**
```json
{
  "bids": [
    {
      "advert_id": 123456,
      "bid": 700,
      "nm_id": 983512347,
      "norm_query": "Фраза 1"
    }
  ]
}
```

### POST /search-clusters/set-bids

Установить ставки для поисковых кластеров

**Тело запроса:**
```json
[
  {
    "advert_id": 123456,
    "nm_id": 789012,
    "norm_query": "поисковый запрос",
    "bid": 1500
  }
]
```

**Ответ:**
```json
{
  "result": "success"
}
```

### DELETE /search-clusters/remove-bids

Удалить ставки с поисковых кластеров

**Тело запроса:**
```json
[
  {
    "advert_id": 123456,
    "nm_id": 789012,
    "norm_query": "поисковый запрос",
    "bid": 1000
  }
]
```

**Ответ:**
```json
{
  "result": "success"
}
```

### POST /search-clusters/stats

Получить статистику по поисковым кластерам за указанный период

**Тело запроса:**
```json
{
  "from_date": "2023-01-01",
  "to_date": "2023-01-31",
  "items": [
    {
      "advert_id": 123456,
      "nm_id": 789012,
      "norm_query": "поисковый запрос",
      "bid": 1000
    }
  ]
}
```

**Ответ:**
```json
{
  "stats": [
    {
      "advert_id": 1825035,
      "nm_id": 983512347,
      "stats": [
        {
          "atbs": 68,
          "avg_pos": 3.6,
          "clicks": 2090,
          "cpc": 471,
          "cpm": 813,
          "ctr": 107.23,
          "norm_query": "Фраза 1",
          "orders": 19,
          "views": 1949
        }
      ]
    }
  ]
}
```

### POST /search-clusters/minus-phrases

Получить список минус-фраз для товаров в кампаниях

**Тело запроса:**
```json
[
  {
    "advert_id": 123456,
    "nm_id": 789012
  }
]
```

**Ответ:**
```json
{
  "items": [
    {
      "advert_id": 1825035,
      "nm_id": 983512347,
      "norm_queries": [
        "Фраза 1"
      ]
    }
  ]
}
```

### POST /search-clusters/set-minus-phrases

Установить минус-фразы для товара в кампании

**Тело запроса:**
```json
{
  "advert_id": 123456,
  "nm_id": 789012,
  "norm_queries": [
    "поисковый запрос"
  ]
}
```

**Ответ:**
```json
{
  "result": "success"
}
```

### POST /search-clusters/list

Получить списки активных и неактивных поисковых кластеров

**Тело запроса:**
```json
[
  {
    "advert_id": 123456,
    "nm_id": 789012
  }
]
```

**Ответ:**
```json
{
  "items": [
    {
      "advertId": 123456,
      "nmId": 789012,
      "normQueries": {
        "active": null,
        "excluded": [
          "бест трикотаж",
          "горы футболка для мужчин",
          "одежда для моря",
          "одежда на море",
          "поло мужское"
        ]
      }
    }
  ]
}
```

## Запуск тестов

Для запуска тестов используйте команду:

```bash
pytest test_app.py
```

## Пример использования

Смотрите файл `example_usage.py` для примера использования API.

## Ограничения API Wildberries

1. **Токен**: Для доступа к методам требуется токен для категории "Продвижение"
2. **Типы кампаний**: Методы работают только с кампаниями с ручной ставкой и моделью оплаты CPM
3. **Ограничения по количеству**: 
   - До 100 элементов в одном запросе
   - До 1000 минус-фраз для одного товара
4. **Частотные ограничения**:
   - `/adv/v0/normquery/get-bids`: 5 запросов в секунду
   - `/adv/v0/normquery/bids` (POST): 2 запроса в секунду
   - `/adv/v0/normquery/bids` (DELETE): 5 запросов в секунду
   - `/adv/v0/normquery/get-minus`: 5 запросов в секунду
   - `/adv/v0/normquery/set-minus`: 5 запросов в секунду
   - `/adv/v0/normquery/list`: 5 запросов в секунду
   - `/adv/v0/normquery/stats`: 10 запросов в минуту