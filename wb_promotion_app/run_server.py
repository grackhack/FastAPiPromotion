#!/usr/bin/env python3
"""
Скрипт для запуска Wildberries Promotion API Manager
"""

import uvicorn
import sys
import os

# Добавляем родительскую директорию в путь для корректных импортов
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wb_promotion_app.config import APP_HOST, APP_PORT, APP_DEBUG


def main():
    print("Запуск Wildberries Promotion API Manager...")
    print(f"Адрес: http://{APP_HOST}:{APP_PORT}")
    print(f"Режим отладки: {APP_DEBUG}")

    uvicorn.run(
        "wb_promotion_app.main:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=APP_DEBUG,
        log_level="info"
    )


if __name__ == "__main__":
    main()