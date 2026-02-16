#!/bin/bash
# Скрипт деплоя FastAPI приложения на удалённый сервер

set -e

# Конфигурация
SERVER_USER="botuser"
SERVER_HOST="195.133.49.121"
SERVER_PATH="/home/botuser/FastAPiPromotion"
PROJECT_NAME="FastAPiPromotion"

echo "🚀 Начало деплоя на $SERVER_HOST..."

# 1. Копирование файлов на сервер
echo "📦 Копирование файлов..."
rsync -avz --exclude='.venv' --exclude='__pycache__' --exclude='.env' --exclude='.git' \
    ./ $SERVER_USER@$SERVER_HOST:~/tmp_deploy/

# 2. Подготовка на сервере
echo "🔧 Настройка на сервере..."
ssh $SERVER_USER@$SERVER_HOST << 'EOF'
    # Создание директории проекта
    mkdir -p ~/FastAPiPromotion
    
    # Перемещение файлов
    mv ~/tmp_deploy/* ~/FastAPiPromotion/ 2>/dev/null || true
    rm -rf ~/tmp_deploy
    
    cd ~/FastAPiPromotion
    
    # Создание виртуального окружения
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
    fi
    
    # Активация и установка зависимостей
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -e .
    
    # Копирование .env если не существует
    if [ ! -f ".env" ]; then
        cp .env.example .env 2>/dev/null || echo "Создайте .env файл вручную"
    fi
    
    echo "✅ Деплой завершён"
EOF

echo "🎉 Деплой успешно завершён!"
echo "📝 Для запуска выполните: ssh $SERVER_USER@$SERVER_HOST 'cd $SERVER_PATH && source .venv/bin/activate && uvicorn wb_promotion_app.main:app --host 0.0.0.0 --port 8000'"
