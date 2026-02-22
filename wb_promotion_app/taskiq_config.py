"""
TaskIQ брокер и планировщик для периодических задач
Использует PostgreSQL как брокер и бэкенд результатов
"""
import os
from taskiq import TaskiqScheduler, AsyncBroker
from taskiq.cli.scheduler.args import SchedulerArgs
from taskiq.cli.scheduler.run import run_scheduler
from taskiq_postgresql import PostgresqlBroker, PostgresqlResultBackend, PostgresqlSchedulerSource
from taskiq.schedule_sources import LabelScheduleSource

from .config import DATABASE_URL

# TaskIQ брокер
taskiq_broker: AsyncBroker = PostgresqlBroker(
    dsn=DATABASE_URL,
    queue_name="wb_promotion_tasks",
).with_result_backend(
    PostgresqlResultBackend(
        dsn=DATABASE_URL,
    )
)

# Планировщик
scheduler_source = PostgresqlSchedulerSource(
    dsn=DATABASE_URL,
    table_name="taskiq_schedules",
)

scheduler = TaskiqScheduler(
    broker=taskiq_broker,
    sources=[scheduler_source, LabelScheduleSource(taskiq_broker)],
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
