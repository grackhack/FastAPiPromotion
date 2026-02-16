# Настройка CI/CD для автодеплоя

## 1. Добавьте секреты в GitHub

Зайдите в репозиторий → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Добавьте 3 секрета:

| Название | Значение |
|----------|----------|
| `SERVER_HOST` | `195.133.49.121` |
| `SERVER_USER` | `botuser` |
| `SSH_PRIVATE_KEY` | Содержимое файла `~/.ssh/id_ed25519` (ваш приватный SSH ключ) |

### Как получить SSH_PRIVATE_KEY:

**Windows (PowerShell):**
```powershell
Get-Content $env:USERPROFILE\.ssh\id_ed25519 | Set-Clipboard
```

**Linux/Mac:**
```bash
cat ~/.ssh/id_ed25519 | xclip -selection clipboard
```

Вставьте содержимое в поле секрета.

## 2. Проверка работы

После добавления секретов:

1. Сделайте коммит и пуш:
```bash
git push
```

2. Зайдите в **Actions** на GitHub — увидите запущенный workflow

3. Через 1-2 минуты деплой завершится

## 3. Ручной деплой (если CI/CD не работает)

```bash
ssh botuser@195.133.49.121 "cd ~/FastAPiPromotion && git pull && source .venv/bin/activate && pip install -e . && pkill -f 'main:app' && cd wb_promotion_app && ../.venv/bin/python -c \"import subprocess; subprocess.Popen(['../.venv/bin/python', '-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8001'], stdout=open('../app.log', 'w'), stderr=subprocess.STDOUT, start_new_session=True)\""
```

## 4. Мониторинг

- **Логи приложения**: `ssh botuser@195.133.49.121 "tail -f ~/FastAPiPromotion/app.log"`
- **Статус процесса**: `ssh botuser@195.133.49.121 "ps aux | grep uvicorn"`
- **Swagger UI**: http://195.133.49.121/promotion/docs
- **GitHub Actions**: https://github.com/grackhack/FastAPiPromotion/actions
