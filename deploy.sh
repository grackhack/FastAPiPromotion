#!/bin/bash
# Скрипт деплоя FastAPI приложения на удалённый сервер

set -e

# Конфигурация
SERVER_USER="botuser"
SERVER_HOST="195.133.49.121"
SERVER_PATH="/home/botuser/FastAPiPromotion"
PROJECT_NAME="FastAPiPromotion"
APP_PORT=8001

echo "🚀 Начало деплоя на $SERVER_HOST..."

# 1. Копирование файлов на сервер
echo "📦 Копирование файлов..."
rsync -avz --exclude='.venv' --exclude='__pycache__' --exclude='.env' --exclude='.git' \
    --exclude='.idea' --exclude='.github' \
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

# 3. Информация о настройке сервиса
echo "🌐 Настройка сервиса и nginx..."
echo ""
echo "⚠️  ПЕРВОНАЧАЛЬНАЯ НАСТРОЙКА (выполняется один раз с sudo):"
echo "   ssh root@195.133.49.121"
echo "   bash /home/botuser/FastAPiPromotion/setup-service-root.sh"
echo ""
echo "📝 Для управления сервисом используйте:"
echo "   ssh $SERVER_USER@$SERVER_HOST"
echo "   systemctl --user status wb-promotion-app"
echo "   systemctl --user restart wb-promotion-app"
echo "   journalctl --user -u wb-promotion-app -f"

echo "🎉 Деплой успешно завершён!"
echo "📝 Приложение доступно на http://$SERVER_HOST/promotion/ и http://$SERVER_HOST/phrases"
