#!/usr/bin/env python3
"""
Скрипт проверки подключения к базе данных
"""

import sys
import os
import codecs

if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wb_promotion_app.config import engine, SessionLocal
from wb_promotion_app.models import Base
from sqlalchemy import inspect


def check_db():
    print("=" * 50)
    print("ПРОВЕРКА ПОДКЛЮЧЕНИЯ К БАЗЕ ДАННЫХ")
    print("=" * 50)
    
    # Проверка подключения
    print(f"\n1. URL подключения: {engine.url}")
    
    try:
        conn = engine.connect()
        print("2. Статус подключения: OK")
        conn.close()
    except Exception as e:
        print(f"2. Статус подключения: ОШИБКА - {e}")
        return
    
    # Проверка таблиц в БД
    print("\n3. Таблицы в базе данных:")
    inspector = inspect(engine)
    db_tables = inspector.get_table_names()
    
    if db_tables:
        for table in db_tables:
            print(f"   - {table}")
        print(f"\n   Всего таблиц: {len(db_tables)}")
    else:
        print("   Таблиц не найдено!")
    
    # Проверка таблиц в модели
    print("\n4. Таблицы в модели SQLAlchemy:")
    model_tables = Base.metadata.sorted_tables
    for table in model_tables:
        print(f"   - {table.name}")
    print(f"\n   Всего в модели: {len(model_tables)}")
    
    # Сравнение
    print("\n5. Сверка:")
    model_names = {t.name for t in model_tables}
    db_names = set(db_tables)
    
    if model_names == db_names:
        print("   [OK] Все таблицы модели созданы в БД")
    else:
        missing = model_names - db_names
        extra = db_names - model_names
        if missing:
            print(f"   [WARN] Не созданы в БД: {missing}")
        if extra:
            print(f"   [INFO] Лишние в БД: {extra}")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    check_db()
