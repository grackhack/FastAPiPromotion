# Настройка автодеплоя через GitHub Actions

## Шаг 1: Генерация SSH-ключа

### Вариант А: Через скрипт на сервере

```bash
# Подключитесь к серверу
ssh botuser@195.133.49.121

# Перейдите в директорию проекта
cd ~/FastAPiPromotion

# Запустите скрипт настройки
bash scripts/setup-github-ssh.sh
```

Скрипт сгенерирует ключ и выведет приватный ключ для копирования.

### Вариант Б: Вручную

```bash
# На локальной машине
ssh-keygen -t ed25519 -f ~/.ssh/github_actions -C "github-actions-deploy"

# Копируем публичный ключ на сервер
ssh-copy-id -i ~/.ssh/github_actions.pub botuser@195.133.49.121

# Или вручную добавляем в authorized_keys на сервере
cat ~/.ssh/github_actions.pub | ssh botuser@195.133.49.121 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

## Шаг 2: Добавление секретов в GitHub

1. Перейдите в репозиторий на GitHub
2. **Settings** → **Secrets and variables** → **Actions**
3. **New repository secret**

Добавьте следующие секреты:

| Secret Name | Value |
|-------------|-------|
| `SERVER_HOST` | `195.133.49.121` |
| `SERVER_USER` | `botuser` |
| `SERVER_SSH_PRIVATE_KEY` | Приватный ключ из шага 1 (начинается с `-----BEGIN OPENSSH PRIVATE KEY-----`) |

### Как получить приватный ключ:

```bash
# На локальной машине
cat ~/.ssh/github_actions

# Или на сервере если генерировали там
ssh botuser@195.133.49.121 "cat ~/.ssh/github_actions"
```

## Шаг 3: Проверка workflow

Workflow файл находится в `.github/workflows/deploy.yml`

Триггеры:
- Пуш в ветку `master`
- Пуш в ветку `main`

## Шаг 4: Тестирование

Сделайте пуш в репозиторий:

```bash
git add .
git commit -m "Test auto-deploy"
git push origin master
```

Проверьте статус деплоя:
- Перейдите в **Actions** на GitHub
- Выберите запущенный workflow
- Проверьте логи выполнения

## Шаг 5: Что делает workflow

1. **Checkout** — загружает код из репозитория
2. **SSH на сервер** — подключается к серверу
3. **Git pull** — загружает последние изменения
4. **Install dependencies** — устанавливает зависимости
5. **Database migrations** — применяет миграции Alembic
6. **Restart service** — перезапускает приложение через systemd
7. **Health check** — проверяет что приложение доступно на порту 8001

## Структура workflow

```yaml
name: Deploy to Production
on:
  push:
    branches: [master, main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - Checkout code
      - Deploy via SSH
        - Pull changes
        - Install dependencies
        - Run migrations
        - Restart service
        - Health check
```

## Отладка

### Если деплой не работает:

1. **Проверьте логи GitHub Actions**
   - Вкладка Actions → последний запуск → посмотреть логи

2. **Проверьте подключение к серверу**
   ```bash
   ssh -i ~/.ssh/github_actions botuser@195.133.49.121
   ```

3. **Проверьте права на ключ**
   ```bash
   chmod 600 ~/.ssh/github_actions
   ```

4. **Проверьте логи приложения на сервере**
   ```bash
   ssh botuser@195.133.49.121
   journalctl --user -u wb-promotion-app -n 50
   ```

### Ручной деплой

Если нужно развернуть вручную:

```bash
ssh botuser@195.133.49.121

cd ~/FastAPiPromotion
git pull
source .venv/bin/activate
pip install -e .
pip install -r wb_promotion_app/requirements.txt

cd wb_promotion_app
alembic upgrade head

systemctl --user restart wb-promotion-app
systemctl --user status wb-promotion-app
```

## Безопасность

- Приватный SSH-ключ хранится только в GitHub Secrets
- Ключ имеет тип ed25519 (современный и безопасный)
- Доступ к серверу только для пользователя `botuser` (не root)
- Workflow запускается только при пуше в защищённые ветки

## Дополнительные настройки

### Деплой только из определённой папки

```yaml
on:
  push:
    branches: [master]
    paths:
      - 'wb_promotion_app/**'
      - '.github/workflows/**'
```

### Уведомления о деплое

Добавьте в workflow:

```yaml
- name: Notify on success
  if: success()
  run: |
    curl -X POST ${{ secrets.TELEGRAM_WEBHOOK }} \
      -d "text=✅ Деплой успешен!"

- name: Notify on failure
  if: failure()
  run: |
    curl -X POST ${{ secrets.TELEGRAM_WEBHOOK }} \
      -d "text=❌ Деплой не удался!"
```
