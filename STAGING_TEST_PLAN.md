# Staging Testing Plan

## Цель
Протестировать новую архитектуру на staging окружении перед merge в master.

## Окружения

### Production (текущее)
- URL: http://195.133.49.121:8001
- Ветка: master
- Статус: Работает стабильно

### Staging (новое)
- URL: http://195.133.49.121:8002 (новый порт)
- Ветка: refactor/ssr-architecture
- Статус: Требуется настройка

## План тестирования

### 1. Подготовка staging окружения

```bash
# На сервере
cd ~/FastAPiPromotion

# Создать копию для staging
cp -r . ~/FastAPiPromotion-staging
cd ~/FastAPiPromotion-staging

# Переключиться на новую ветку
git fetch origin
git checkout refactor/ssr-architecture

# Установить зависимости (если есть новые)
source .venv/bin/activate
pip install -e .

# Проверить что приложение запускается
python -m uvicorn wb_promotion_app.main:app --host 0.0.0.0 --port 8002
```

### 2. Настройка systemd сервиса для staging

```bash
# Создать сервис
cat > ~/FastAPiPromotion-staging/wb-promotion-staging.service << EOF
[Unit]
Description=FastAPI Wildberries Promotion App (Staging)
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/botuser/FastAPiPromotion-staging
Environment="PATH=/home/botuser/FastAPiPromotion-staging/.venv/bin"
ExecStart=/home/botuser/FastAPiPromotion-staging/.venv/bin/python -m uvicorn wb_promotion_app.main:app --host 0.0.0.0 --port 8002
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=wb-promotion-app-staging

[Install]
WantedBy=multi-user.target
EOF

# Установить сервис
ln -sf ~/FastAPiPromotion-staging/wb-promotion-staging.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable wb-promotion-staging
systemctl --user start wb-promotion-staging

# Проверить статус
systemctl --user status wb-promotion-staging
```

### 3. Чеклист тестирования

#### Базовая функциональность
- [ ] Приложение запускается на порту 8002
- [ ] Главная страница `/` загружается (200 OK)
- [ ] Страница `/login` доступна
- [ ] Страница `/profile` требует авторизации

#### Аутентификация
- [ ] Вход через `/login` работает
- [ ] Session cookie устанавливается
- [ ] `/auth/me` возвращает данные пользователя
- [ ] `/logout` корректно завершает сессию

#### Кампании (SSR)
- [ ] `/` загружает кампании через SSR
- [ ] Данные кампаний в JSON в шаблоне
- [ ] `/campaigns` отображает список
- [ ] `/campaign/{id}` отображает детали

#### API Endpoints
- [ ] `GET /api/campaigns` возвращает список
- [ ] `GET /api/campaigns/media` возвращает медиа
- [ ] `POST /api/stats/normquery` возвращает статистику
- [ ] `POST /api/search-clusters/minus-phrases` работает

#### Личный кабинет
- [ ] `/profile` отображает информацию
- [ ] Добавление токена работает
- [ ] Удаление токена работает
- [ ] Список токенов отображается

#### Безопасность
- [ ] `/api/*` без авторизации → 401
- [ ] `/` без авторизации → показывает сообщение
- [ ] Токены не передаются на фронтенд
- [ ] Session cookie httponly

#### Производительность
- [ ] Время загрузки главной < 2с
- [ ] Время загрузки кампании < 1с
- [ ] API ответы < 500мс

### 4. Автоматические тесты

```bash
# Запустить тесты (если есть)
cd ~/FastAPiPromotion-staging
source .venv/bin/activate
pytest -v

# Или проверить через curl
# Главная страница
curl -s http://localhost:8002/ | grep -o '<title>.*</title>'

# API без авторизации (должен быть 401)
curl -s -o /dev/null -w '%{http_code}' http://localhost:8002/api/campaigns

# Логин
curl -s -X POST http://localhost:8002/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"testuser"}' \
  -c /tmp/staging_cookies.txt

# API с авторизацией
curl -s -b /tmp/staging_cookies.txt http://localhost:8002/api/campaigns | head -c 100
```

### 5. Мониторинг

```bash
# Логи staging
journalctl --user -u wb-promotion-staging -f

# Проверка ошибок
journalctl --user -u wb-promotion-staging -n 100 | grep -i error

# Использование ресурсов
ps aux | grep uvicorn | grep 8002
```

### 6. Критерии успеха

**Staging готов к production, если:**
- ✅ Все endpoints работают
- ✅ Аутентификация работает
- ✅ SSR загружает данные
- ✅ API возвращает JSON
- ✅ Нет ошибок в логах
- ✅ Производительность в норме
- ✅ Безопасность проверена

### 7. Rollback план

Если что-то пошло не так:

```bash
# Остановить staging
systemctl --user stop wb-promotion-staging

# Production не затронут, работает на порту 8001
# Можно спокойно исправлять ошибки

# После исправлений
systemctl --user start wb-promotion-staging
```

### 8. Timeline

| Этап | Время | Статус |
|------|-------|--------|
| Подготовка staging | 30 мин | ⏳ |
| Настройка сервиса | 15 мин | ⏳ |
| Базовое тестирование | 30 мин | ⏳ |
| Полное тестирование | 1 час | ⏳ |
| Исправление ошибок | ? | ⏳ |
| Финальная проверка | 30 мин | ⏳ |
| **Итого** | **~3 часа** | |

## Команды для быстрого тестирования

```bash
# 1. Проверка что staging работает
curl http://localhost:8002/ | grep -o '<title>.*</title>'

# 2. Проверка API
curl http://localhost:8002/api/campaigns

# 3. Проверка SSR
curl http://localhost:8002/ | grep 'campaigns-data'

# 4. Проверка авторизации
curl -X POST http://localhost:8002/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"myebox"}' \
  -c /tmp/staging.txt

curl -b /tmp/staging.txt http://localhost:8002/api/campaigns | head -c 200
```

## Контакты

При возникновении проблем:
- Проверить логи: `journalctl --user -u wb-promotion-staging -f`
- Проверить порт: `ss -tlnp | grep 8002`
- Перезапустить: `systemctl --user restart wb-promotion-staging`
