#!/usr/bin/env python3
"""
TaskIQ Worker для Wildberries Promotion Manager

Запуск воркера для обработки периодических задач:
    python -m wb_promotion_app.taskiq_worker

Запуск с несколькими воркерами:
    taskiq worker wb_promotion_app.taskiq_config:taskiq_broker --workers 4
"""
import asyncio
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wb_promotion_app.taskiq_config import taskiq_broker


async def main():
    """Запуск воркера"""
    print("🚀 Starting TaskIQ Worker for Wildberries Promotion Manager...")
    print(f"Broker: {taskiq_broker.__class__.__name__}")
    
    # Запускаем воркера
    await taskiq_broker.startup()
    
    print("✅ Worker is ready to process tasks")
    print("Press Ctrl+C to stop")
    
    try:
        # Держим воркера запущенным
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down worker...")
        await taskiq_broker.shutdown()
        print("✅ Worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
