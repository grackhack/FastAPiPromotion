# Описание проекта FastAPIProject1

## Общая информация

**Название:** Wildberries Promotion API Manager  
**Версия:** 1.0.0  
**Описание:** API для управления рекламными кампаниями Wildberries, включая работу с поисковыми кластерами  
**Python:** >=3.9  

## Сервер

- **Хост:** 195.133.49.121
- **Пользователь:** botuser
- **Порт приложения:** 8001
- **Путь на сервере:** /home/botuser/FastAPiPromotion

## Структура файлов

```
FastAPIProject1/
├── .env.example                    # Шаблон переменных окружения
├── .gitignore                      # Git ignore файл
├── .github/
│   └── workflows/
│       └── deploy.yml              # GitHub Actions workflow для автодеплоя
├── DEPLOY.md                       # Инструкция по настройке CI/CD
├── deploy.sh                       # Скрипт деплоя на сервер
├── pyproject.toml                  # Зависимости проекта (poetry/pip)
├── README.md                       # Основная документация
├── SETUP_SERVICE.md                # (не прочитан)
├── setup-service-root.sh           # Скрипт первоначальной настройки сервиса (требует sudo)
├── start.sh                        # (не прочитан)
├── wb-promotion.service            # Systemd сервис для приложения
├── wb-promotion-nginx.conf         # Конфигурация nginx
├── wb_promotion_app/               # Основной пакет приложения
│   ├── __init__.py
│   ├── api_client.py               # Клиент Wildberries Advert API
│   ├── API_DOCS.md                 # Полная документация API
│   ├── config.py                   # Конфигурация приложения
│   ├── example_usage.py            # Примеры использования
│   ├── main.py                     # Точка входа FastAPI
│   ├── models.py                   # Dataclass модели данных
│   ├── README.md                   # Документация модуля
│   ├── requirements.txt            # Зависимости (альтернатива pyproject.toml)
│   ├── run_server.py               # Скрипт запуска сервера
│   ├── schemas.py                  # Pydantic схемы для валидации
│   ├── test_app.py                 # Тесты
│   ├── utils.py                    # Вспомогательные функции
│   ├── static/                     # Статические файлы
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       ├── campaign-detail.js
│   │       └── campaigns-list.js
│   └── templates/                  # HTML шаблоны Jinja2
│       ├── campaign-detail.html    # Страница настройки кампании
│       ├── campaigns.html          # Страница списка кампаний
│       ├── index.html              # Главная страница
│       └── phrases.html            # Страница управления минус-фразами
└── PROJECT_STRUCTURE.md            # Этот файл
```

## Зависимости (pyproject.toml)

```toml
fastapi>=0.100.0
uvicorn>=0.23.0
python-dotenv>=1.0.0
jinja2>=3.1.0
requests>=2.31.0
```

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `WB_API_TOKEN` | Токен API Wildberries (категория "Продвижение") | - |
| `APP_HOST` | Хост для прослушивания | `0.0.0.0` |
| `APP_PORT` | Порт приложения | `8000` |
| `APP_DEBUG` | Режим отладки | `False` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |

## Архитектура приложения

### Основные модули

#### 1. `main.py` - Точка входа FastAPI
- Инициализация FastAPI приложения
- Настройка статических файлов и шаблонов Jinja2
- Определение всех API эндпоинтов
- Инициализация клиента WB API

#### 2. `api_client.py` - WB Promotions Client
Класс `WBPromotionClient` для взаимодействия с API Wildberries:
- `get_campaigns_count()` - получить список ID кампаний по группам
- `get_adverts()` - получить подробную информацию о кампаниях
- `get_media_campaigns()` - получить список медиакампаний
- `get_media_campaigns_count()` - получить количество медиакампаний
- `get_campaigns()` - комбинированный метод получения всех кампаний
- `get_search_cluster_bids()` - получить ставки поисковых кластеров
- `set_search_cluster_bids()` - установить ставки кластеров
- `remove_search_cluster_bids()` - удалить ставки кластеров
- `get_search_cluster_stats()` - получить статистику по кластерам
- `get_minus_phrases()` - получить минус-фразы
- `set_minus_phrases()` - установить минус-фразы
- `get_search_cluster_list()` - получить список активных/неактивных кластеров
- `get_normquery_stats()` - получить статистику по нормализованным запросам
- `get_full_stats()` - получить полную статистику по кампаниям

#### 3. `schemas.py` - Pydantic схемы
Схемы для валидации данных API:
- `CampaignInfo` - информация о кампании
- `CampaignCountResponseSchema` - ответ /adv/v1/promotion/count
- `PromotionCampaignSchema` - подробная информация о кампании
- `PromotionAdvertsResponseSchema` - ответ /api/advert/v2/adverts
- `MediaCampaignSchema` - медиакампания
- `MediaCampaignCountResponseSchema` - ответ /adv/v1/count
- `SearchClusterBid` - ставка поискового кластера
- `MinusPhraseRequest` - запрос минус-фраз
- `SearchClusterStats` - статистика кластеров
- `SearchClusterListResponse` - список кластеров
- `StatsRequest/StatsResponse` - запрос/ответ статистики
- `FullStatsRequest/FullStatsResponse` - полная статистика

#### 4. `models.py` - Dataclass модели
Модели данных для внутренней логики (аналогичны схемам, но как dataclass)

#### 5. `config.py` - Конфигурация
Загрузка и валидация переменных окружения

#### 6. `utils.py` - Утилиты
- `setup_logging()` - настройка логирования
- `validate_token()` - проверка токена
- `format_response()` - форматирование ответа
- `handle_api_error()` - обработка ошибок API
- `clean_query()` - очистка поискового запроса

## API Endpoints

### Веб-интерфейс (HTML)
| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/` | Главная страница |
| GET | `/campaigns` | Страница просмотра кампаний |
| GET | `/campaign/{campaign_id}` | Страница настройки кампании |
| GET | `/phrases` | Страница управления минус-фразами |

### API (JSON)
| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/campaigns/list` | Получить список кампаний |
| GET | `/campaigns/count` | Получить количество кампаний по группам |
| GET | `/campaigns/adverts` | Получить подробную информацию о кампаниях |
| GET | `/campaigns/media` | Получить список медиакампаний |
| GET | `/campaigns/media/count` | Получить количество медиакампаний |
| POST | `/search-clusters/bids` | Получить ставки кластеров |
| POST | `/search-clusters/set-bids` | Установить ставки кластеров |
| DELETE | `/search-clusters/remove-bids` | Удалить ставки кластеров |
| POST | `/search-clusters/stats` | Получить статистику кластеров |
| POST | `/search-clusters/minus-phrases` | Получить минус-фразы |
| POST | `/search-clusters/set-minus-phrases` | Установить минус-фразы |
| POST | `/search-clusters/list` | Получить список кластеров |
| POST | `/stats/normquery` | Получить статистику по запросам |
| POST | `/stats/full` | Получить полную статистику |

## Статусы кампаний Wildberries

### Обычные кампании (promotion)
| Код | Описание |
|-----|----------|
| -1 | Удалена |
| 4 | Готова к запуску |
| 7 | Завершена |
| 8 | Отменена |
| 9 | Активна |
| 11 | На паузе |

### Медиакампании
| Код | Описание |
|-----|----------|
| 1 | Черновик |
| 2 | Модерация |
| 3 | Отклонена |
| 4 | Готова к запуску |
| 5 | Запланирована |
| 6 | На показах |
| 7 | Завершена |
| 8 | Отменена |
| 9 | Приостановлена продавцом |
| 10 | Пауза по дневному лимиту |
| 11 | Пауза |

## Развёртывание

### Локальная разработка
```bash
pip install -e .
uvicorn wb_promotion_app.main:app --reload --host 0.0.0.0 --port 8000
```

### Деплой на сервер
```bash
./deploy.sh
```


### Управление сервисом
```bash

systemctl --user status wb-promotion-app
systemctl --user restart wb-promotion-app
journalctl --user -u wb-promotion-app -f
```

### CI/CD
Автоматический деплой при пуше в ветку `master` через GitHub Actions.

## Доступ к API

- **Swagger UI:** http://195.133.49.121:8001/docs
- **ReDoc:** http://195.133.49.121:8001/redoc
- **OpenAPI JSON:** http://195.133.49.121:8001/openapi.json
- **Веб-интерфейс:** http://195.133.49.121/promotion/

## Ограничения API Wildberries

| Эндпоинт | Лимит |
|----------|-------|
| `/adv/v0/normquery/get-bids` | 5 запросов/сек |
| `/adv/v0/normquery/bids` (POST) | 2 запроса/сек |
| `/adv/v0/normquery/bids` (DELETE) | 5 запросов/сек |
| `/adv/v0/normquery/get-minus` | 5 запросов/сек |
| `/adv/v0/normquery/set-minus` | 5 запросов/сек |
| `/adv/v0/normquery/list` | 5 запросов/сек |
| `/adv/v0/normquery/stats` | 10 запросов/мин |

## Тестирование

```bash
pytest wb_promotion_app/test_app.py
```
