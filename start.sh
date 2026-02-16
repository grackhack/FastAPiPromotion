#!/bin/bash
# Скрипт запуска приложения

cd /home/botuser/FastAPiPromotion

# Активация виртуального окружения
source .venv/bin/activate

# Запуск приложения
cd wb_promotion_app
python -m uvicorn main:app --host 0.0.0.0 --port 8000
