#!/bin/bash
# Скрипт первоначальной настройки сервиса и nginx
# Выполняется один раз пользователем с правами sudo

set -e

PROJECT_USER="botuser"
PROJECT_PATH="/home/botuser/FastAPiPromotion"

echo "🔧 Первоначальная настройка сервиса..."

# 1. Создание директории для user systemd
echo "📁 Создание директории systemd..."
mkdir -p /home/$PROJECT_USER/.config/systemd/user
chown $PROJECT_USER:$PROJECT_USER /home/$PROJECT_USER/.config/systemd/user

# 2. Копирование файла сервиса
echo "📋 Копирование файла сервиса..."
if [ -f "$PROJECT_PATH/wb-promotion-app.service" ]; then
    cp $PROJECT_PATH/wb-promotion-app.service /home/$PROJECT_USER/.config/systemd/user/wb-promotion-app.service
    chown $PROJECT_USER:$PROJECT_USER /home/$PROJECT_USER/.config/systemd/user/wb-promotion-app.service
    echo "✅ Файл сервиса скопирован"
else
    echo "❌ Файл wb-promotion-app.service не найден в $PROJECT_PATH"
    exit 1
fi

# 3. Включение linger для пользователя
echo "🔓 Включение linger для пользователя..."
loginctl enable-linger $PROJECT_USER

# 4. Настройка systemd сервиса
echo "⚙️  Настройка systemd сервиса..."
sudo -u $PROJECT_USER systemctl --user daemon-reload
sudo -u $PROJECT_USER systemctl --user enable wb-promotion-app
sudo -u $PROJECT_USER systemctl --user start wb-promotion-app

# 5. Проверка статуса
echo "📊 Статус сервиса:"
sudo -u $PROJECT_USER systemctl --user status wb-promotion-app --no-pager | head -15

# 6. Настройка nginx
echo "🌐 Настройка nginx..."
if [ -f "$PROJECT_PATH/wb-promotion-nginx.conf" ]; then
    cp $PROJECT_PATH/wb-promotion-nginx.conf /etc/nginx/sites-available/wb-promotion
    nginx -t && systemctl reload nginx
    echo "✅ Nginx настроен"
else
    echo "❌ Файл wb-promotion-nginx.conf не найден в $PROJECT_PATH"
    exit 1
fi

echo ""
echo "🎉 Настройка завершена!"
echo ""
echo "📝 Для управления сервисом используйте:"
echo "   ssh $PROJECT_USER@195.133.49.121"
echo "   systemctl --user status wb-promotion-app"
echo "   systemctl --user restart wb-promotion-app"
echo "   journalctl --user -u wb-promotion-app -f"
echo ""
echo "🌐 Приложение доступно:"
echo "   http://195.133.49.121/promotion/"
echo "   http://195.133.49.121/phrases"
