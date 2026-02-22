#!/usr/bin/env python3
"""
Скрипт инициализации базы данных
Создаёт все таблицы SQLAlchemy в базе данных
"""

import sys
import os
import codecs

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Устанавливаем кодировку UTF-8 для Windows
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from wb_promotion_app.config import engine, get_db
from wb_promotion_app.models import Base


def init_db():
    """Создать все таблицы в базе данных"""
    print("Инициализация базы данных...")
    print(f"Подключение: {engine.url}")
    
    # Создаём все таблицы
    Base.metadata.create_all(bind=engine)
    
    print("[OK] Таблицы успешно созданы!")
    print("\nСозданные таблицы:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")


if __name__ == "__main__":
    init_db()
