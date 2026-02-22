"""
TaskIQ брокер и планировщик для периодических задач
Использует PostgreSQL как брокер и бэкенд результатов
"""
from taskiq import TaskiqScheduler, AsyncBroker
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_postgresql import PostgresqlBroker, PostgresqlResultBackend

from .config import DATABASE_URL

# TaskIQ брокер
taskiq_broker: AsyncBroker = PostgresqlBroker(
    dsn=DATABASE_URL,
    channel_name="wb_promotion_tasks",
    run_migrations=True,  # Автоматически создавать таблицы
).with_result_backend(
    PostgresqlResultBackend(
        dsn=DATABASE_URL,
    )
)

# Планировщик с LabelScheduleSource (расписание из декораторов @task)
scheduler = TaskiqScheduler(
    broker=taskiq_broker,
    sources=[LabelScheduleSource(taskiq_broker)],
)


def get_broker() -> AsyncBroker:
    """Получить брокер TaskIQ"""
    return taskiq_broker


async def start_scheduler():
    """Запустить планировщик"""
    await scheduler.startup()


async def stop_scheduler():
    """Остановить планировщик"""
    await scheduler.shutdown()
