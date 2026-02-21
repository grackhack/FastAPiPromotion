#!/bin/bash
# Скрипт развёртывания staging окружения
# Запуск на сервере: bash scripts/deploy-staging.sh

set -e

echo "=========================================="
echo "Развёртывание staging окружения"
echo "=========================================="

# Переходим в домашнюю директорию
cd ~

# Проверяем что есть исходный репозиторий
if [ ! -d "FastAPiPromotion" ]; then
    echo "❌ Репозиторий FastAPiPromotion не найден!"
    exit 1
fi

echo "✓ Репозиторий найден"

# Создаём staging директорию
STAGING_DIR=~/FastAPiPromotion-staging

if [ -d "$STAGING_DIR" ]; then
    echo "⚠️  Staging директория уже существует"
    read -p "Удалить и создать заново? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$STAGING_DIR"
        echo "✓ Удалено старое staging окружение"
    else
        echo "Отмена"
        exit 0
    fi
fi

# Копируем репозиторий
echo "📦 Копирование репозитория..."
cp -r FastAPiPromotion "$STAGING_DIR"
cd "$STAGING_DIR"

# Переключаемся на ветку рефакторинга
echo "🔄 Переключение на ветку refactor/ssr-architecture..."
git fetch origin
git checkout refactor/ssr-architecture

echo "✓ Ветка переключена"

# Проверяем виртуальное окружение
if [ ! -d ".venv" ]; then
    echo "⚠️  Виртуальное окружение не найдено"
    echo "Создайте его вручную:"
    echo "  cd $STAGING_DIR"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -e ."
    exit 1
fi

echo "✓ Виртуальное окружение найдено"

# Активируем виртуальное окружение
source .venv/bin/activate

# Устанавливаем зависимости
echo "📦 Установка зависимостей..."
pip install -e . --quiet
echo "✓ Зависимости установлены"

# Проверяем что приложение запускается
echo "🧪 Проверка запуска приложения..."
python -c "from wb_promotion_app.main import app; print('✓ Приложение загружается, роутов:', len(app.routes))"

# Создаём systemd сервис
echo "📝 Создание systemd сервиса..."

SERVICE_FILE="$STAGING_DIR/wb-promotion-staging.service"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=FastAPI Wildberries Promotion App (Staging)
After=network.target

[Service]
Type=simple
WorkingDirectory=$STAGING_DIR
Environment="PATH=$STAGING_DIR/.venv/bin"
ExecStart=$STAGING_DIR/.venv/bin/python -m uvicorn wb_promotion_app.main:app --host 0.0.0.0 --port 8002
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=wb-promotion-app-staging

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Сервис создан: $SERVICE_FILE"

# Устанавливаем сервис
echo "🔧 Установка сервиса..."
mkdir -p ~/.config/systemd/user/
ln -sf "$SERVICE_FILE" ~/.config/systemd/user/wb-promotion-staging.service
systemctl --user daemon-reload

echo "✓ Сервис установлен"

# Запускаем сервис
echo "🚀 Запуск сервиса..."
systemctl --user enable wb-promotion-staging
systemctl --user start wb-promotion-staging

# Ждём запуска
sleep 3

# Проверяем статус
echo "📊 Проверка статуса..."
if systemctl --user is-active --quiet wb-promotion-staging; then
    echo "✅ Сервис запущен"
else
    echo "❌ Сервис не запустился"
    echo "Проверьте логи:"
    echo "  journalctl --user -u wb-promotion-staging -n 50"
    exit 1
fi

# Проверяем что приложение доступно
echo "🌐 Проверка доступности..."
sleep 2

if curl -s http://localhost:8002/ > /dev/null; then
    echo "✅ Приложение доступно на http://localhost:8002"
else
    echo "❌ Приложение недоступно"
    exit 1
fi

# Финальная информация
echo ""
echo "=========================================="
echo "✅ Staging окружение развёрнуто!"
echo "=========================================="
echo ""
echo "URL: http://localhost:8002"
echo "Внешний URL: http://195.133.49.121:8002"
echo ""
echo "Команды управления:"
echo "  systemctl --user status wb-promotion-staging"
echo "  systemctl --user restart wb-promotion-staging"
echo "  systemctl --user stop wb-promotion-staging"
echo ""
echo "Логи:"
echo "  journalctl --user -u wb-promotion-staging -f"
echo ""
echo "Тестирование:"
echo "  curl http://localhost:8002/"
echo "  curl http://localhost:8002/api/campaigns"
echo ""
echo "=========================================="
