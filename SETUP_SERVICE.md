# Первоначальная настройка сервиса

Эти команды выполняются **один раз** пользователем с правами sudo для настройки сервиса и nginx.

## 1. Настройка systemd сервиса для пользователя botuser

```bash
# Скопировать файл сервиса в директорию пользователя
cp /home/botuser/FastAPiPromotion/wb-promotion-app.service /home/botuser/.config/systemd/user/wb-promotion-app.service

# Установить права
chown botuser:botuser /home/botuser/.config/systemd/user/wb-promotion-app.service

# Включить linger для пользователя (чтобы сервис работал без активной сессии)
sudo loginctl enable-linger botuser

# Перезапустить демон systemd пользователя
sudo -u botuser systemctl --user daemon-reload
sudo -u botuser systemctl --user enable wb-promotion-app
sudo -u botuser systemctl --user start wb-promotion-app

# Проверить статус
sudo -u botuser systemctl --user status wb-promotion-app
```

## 2. Настройка nginx

```bash
# Скопировать конфигурацию nginx
sudo cp /home/botuser/FastAPiPromotion/wb-promotion-nginx.conf /etc/nginx/sites-available/wb-promotion

# Проверить и перезагрузить nginx
sudo nginx -t
sudo systemctl reload nginx
```

## 3. Проверка работы

```bash
# Проверка что приложение слушает порт 8001
ss -tlnp | grep 8001

# Проверка через curl
curl http://localhost:8001/
curl http://localhost:8001/phrases

# Проверка через nginx (внешний доступ)
curl http://195.133.49.121/promotion/
curl http://195.133.49.121/phrases
```

## 4. Управление сервисом (в дальнейшем от имени botuser)

```bash
# Подключиться как botuser
ssh botuser@195.133.49.121

# Просмотр статуса
systemctl --user status wb-promotion-app

# Перезапуск
systemctl --user restart wb-promotion-app

# Просмотр логов
journalctl --user -u wb-promotion-app -f
```
