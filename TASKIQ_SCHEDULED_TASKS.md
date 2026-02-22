# TaskIQ - Периодические задачи для Wildberries Promotion

## 📌 Назначение

Система периодических задач для:
- 📊 Автоматического сбора статистики кампаний
- 📈 Расчета дополнительных метрик
- 🤖 Автоматического управления кампаниями по правилам

---

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install -e .
```

### 2. Инициализация таблиц

```bash
.venv\Scripts\python.exe scripts\init_db.py
```

Будут созданы таблицы:
- `campaign_stats_history` - История статистики
- `auto_rules` - Правила авто-управления
- `scheduled_tasks` - Расписания задач
- `taskiq_queue` - Очередь задач (TaskIQ)
- `taskiq_results` - Результаты задач (TaskIQ)
- `taskiq_schedules` - Расписания TaskIQ

### 3. Запуск воркера

**Вариант А: Прямой запуск**
```bash
.venv\Scripts\python.exe wb_promotion_app/taskiq_worker.py
```

**Вариант Б: Через TaskIQ CLI (рекомендуется)**
```bash
.venv\Scripts\taskiq.exe worker wb_promotion_app.taskiq_config:taskiq_broker --workers 2
```

### 4. Запуск планировщика (отдельный процесс)

```bash
.venv\Scripts\taskiq.exe scheduler wb_promotion_app.taskiq_config:scheduler
```

---

## 📋 Предопределенные задачи

### 1. `collect_campaign_stats` - Сбор статистики

Собирает статистику кампании за указанный период и сохраняет в историю.

**Параметры:**
- `campaign_id` (int) - ID кампании
- `nm_id` (int, опционально) - ID товара
- `days_back` (int) - За сколько дней собирать (по умолчанию 1)
- `user_id` (int) - ID пользователя для токена

**Пример вызова:**
```python
from wb_promotion_app.tasks import collect_campaign_stats

# Отправить задачу
task = await collect_campaign_stats.kiq(
    campaign_id=123,
    nm_id=456,
    days_back=1,
    user_id=1
)

# Получить результат
result = await task.wait_result()
```

### 2. `check_auto_rules` - Проверка правил

Проверяет правила авто-управления и выполняет действия при срабатывании.

**Параметры:**
- `user_id` (int, опционально) - ID пользователя

**Пример:**
```python
from wb_promotion_app.tasks import check_auto_rules

task = await check_auto_rules.kiq(user_id=1)
result = await task.wait_result()
```

### 3. `calculate_campaign_metrics` - Расчет метрик

Рассчитывает дополнительные метрики на основе истории:
- Средний дневной расход
- CTR, CR, CPC за 7 дней
- Прогноз расхода на месяц

**Параметры:**
- `campaign_id` (int, опционально) - ID кампании
- `user_id` (int) - ID пользователя

### 4. `scheduled_collect_all_stats` - Плановый сбор статистики

Автоматически запускается каждые 6 часов (cron: `0 */6 * * *`).
Собирает статистику для всех активных расписаний.

### 5. `scheduled_check_rules` - Плановая проверка правил

Автоматически запускается каждые 2 часа (cron: `0 */2 * * *`).

---

## 🔧 API Endpoints

### Управление расписаниями

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/tasks/scheduled` | Список расписаний |
| POST | `/api/tasks/scheduled` | Создать расписание |
| PATCH | `/api/tasks/scheduled/{id}` | Обновить расписание |
| DELETE | `/api/tasks/scheduled/{id}` | Удалить расписание |

**Пример создания расписания:**
```bash
curl -X POST http://localhost:8000/api/tasks/scheduled \
  -H "Content-Type: application/json" \
  -H "Cookie: session_id=..." \
  -d '{
    "task_type": "collect_stats",
    "campaign_id": 123,
    "cron_schedule": "0 */6 * * *"
  }'
```

### Управление правилами

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/tasks/rules` | Список правил |
| POST | `/api/tasks/rules` | Создать правило |
| PATCH | `/api/tasks/rules/{id}` | Обновить правило |
| DELETE | `/api/tasks/rules/{id}` | Удалить правило |
| POST | `/api/tasks/rules/{id}/test` | Тестировать правило |

**Пример создания правила:**
```bash
curl -X POST http://localhost:8000/api/tasks/rules \
  -H "Content-Type: application/json" \
  -H "Cookie: session_id=..." \
  -d '{
    "name": "Остановить при расходе > 1000₽",
    "campaign_id": 123,
    "condition_type": "spend_limit",
    "condition_operator": ">",
    "condition_value": 1000,
    "action_type": "pause_campaign"
  }'
```

### Типы условий

| condition_type | Описание |
|----------------|----------|
| `spend_limit` | Лимит расхода (₽) |
| `ctr_low` | Низкий CTR (%) |
| `views_limit` | Лимит просмотров |
| `clicks_limit` | Лимит кликов |
| `cpc_high` | Высокий CPC (₽) |

### Типы действий

| action_type | Описание |
|-------------|----------|
| `pause_campaign` | Остановить кампанию |
| `delete_phrase` | Удалить минус-фразу |
| `reduce_bid` | Уменьшить ставку |

### История статистики

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/tasks/stats-history` | История статистики |

**Параметры:**
- `campaign_id` (int) - Фильтр по кампании
- `days` (int) - За сколько дней (по умолчанию 7)

### Ручной запуск задач

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/tasks/collect-stats` | Сбор статистики |
| POST | `/api/tasks/check-rules` | Проверка правил |
| POST | `/api/tasks/calculate-metrics` | Расчет метрик |

---

## 📊 Cron расписания

### Примеры cron выражений

```
# Каждые 6 часов
0 */6 * * *

# Каждый день в 9:00
0 9 * * *

# Каждые 30 минут
*/30 * * * *

# Каждый понедельник в 10:00
0 10 * * 1

# 1 числа каждого месяца в 00:00
0 0 1 * *
```

### Формат cron
```
┌───────────── минут (0-59)
│ ┌───────────── часов (0-23)
│ │ ┌───────────── дня месяца (1-31)
│ │ │ ┌───────────── месяца (1-12)
│ │ │ │ ┌───────────── дня недели (0-6)
│ │ │ │ │
* * * * *
```

---

## 🗄️ Модель данных

### CampaignStatsHistory
```python
{
    "id": int,
    "campaign_id": int,
    "nm_id": int | null,
    "views": int,
    "clicks": int,
    "orders": int,
    "atbs": int,
    "shks": int,
    "canceled": int,
    "spend": float,
    "sum_price": float,
    "ctr": float,
    "cr": float,
    "cpc": float,
    "cpm": float,
    "period_from": datetime,
    "period_to": datetime,
    "collected_at": datetime,
    "is_auto": bool
}
```

### AutoRule
```python
{
    "id": int,
    "user_id": int,
    "campaign_id": int,
    "nm_id": int | null,
    "name": str,
    "condition_type": str,
    "condition_operator": str,
    "condition_value": float,
    "action_type": str,
    "action_params": dict | null,
    "is_active": bool,
    "last_checked_at": datetime | null,
    "last_triggered_at": datetime | null
}
```

### ScheduledTask
```python
{
    "id": int,
    "user_id": int,
    "task_type": str,
    "campaign_id": int | null,
    "nm_id": int | null,
    "cron_schedule": str,
    "task_params": dict | null,
    "is_active": bool,
    "last_run_at": datetime | null,
    "next_run_at": datetime | null
}
```

---

## 🎯 Примеры использования

### 1. Настройка автоматического сбора статистики

```python
# POST /api/tasks/scheduled
{
    "task_type": "collect_stats",
    "campaign_id": 34000580,
    "cron_schedule": "0 */6 * * *"
}
```

Теперь статистика кампании будет собираться каждые 6 часов.

### 2. Создание правила остановки кампании

```python
# POST /api/tasks/rules
{
    "name": "Остановить при расходе > 500₽",
    "campaign_id": 34000580,
    "condition_type": "spend_limit",
    "condition_operator": ">",
    "condition_value": 500,
    "action_type": "pause_campaign"
}
```

### 3. Просмотр истории статистики

```bash
GET /api/tasks/stats-history?campaign_id=34000580&days=7
```

### 4. Тестирование правила

```bash
POST /api/tasks/rules/1/test
```

Ответ:
```json
{
    "rule_id": 1,
    "rule_name": "Остановить при расходе > 500₽",
    "condition": "spend_limit > 500",
    "current_value": 450.5,
    "triggered": false,
    "action_would_be": "pause_campaign"
}
```

---

## 🔍 Мониторинг

### Проверка статуса воркера

```bash
# В логах ищите сообщения:
🚀 Starting TaskIQ Worker...
✅ Worker is ready to process tasks
```

### Просмотр выполненных задач

```sql
SELECT * FROM taskiq_results 
ORDER BY created_at DESC 
LIMIT 10;
```

### Просмотр очереди задач

```sql
SELECT * FROM taskiq_queue 
ORDER BY created_at DESC;
```

---

## ⚠️ Troubleshooting

### Воркер не запускается

1. Проверьте зависимости:
```bash
pip install -e .
```

2. Проверьте подключение к БД:
```bash
.venv\Scripts\python.exe scripts\check_db.py
```

### Задачи не выполняются

1. Убедитесь, что воркер запущен
2. Проверьте логи воркера
3. Проверьте таблицу `taskiq_results` на ошибки

### Планировщик не работает

1. Убедитесь, что запущен отдельный процесс планировщика
2. Проверьте таблицу `taskiq_schedules`
3. Проверьте cron выражения

---

## 📝 Следующие шаги

1. ✅ Настройка автоматического сбора статистики
2. ✅ Создание правил авто-управления
3. ⏳ Реализация действий (pause_campaign, delete_phrase, reduce_bid)
4. ⏳ Уведомления о срабатывании правил
5. ⏳ Дашборд с историей и метриками
