#!/bin/bash
# Скрипт настройки SSH-ключа для GitHub Actions на сервере
# Запускать на сервере: bash scripts/setup-github-ssh.sh

set -e

echo "============================================"
echo "Настройка SSH-ключа для GitHub Actions"
echo "============================================"

# Создаём директорию для SSH
SSH_DIR="$HOME/.ssh"
mkdir -p $SSH_DIR
chmod 700 $SSH_DIR

# Генерируем новую пару ключей
echo ""
echo "Генерация новой пары SSH ключей..."
SSH_KEY_FILE="$SSH_DIR/github_actions"
ssh-keygen -t ed25519 -f $SSH_KEY_FILE -N "" -C "github-actions-deploy"

echo ""
echo "✅ Ключи сгенерированы:"
echo "   Приватный: $SSH_KEY_FILE"
echo "   Публичный: ${SSH_KEY_FILE}.pub"

# Добавляем публичный ключ в authorized_keys
echo ""
echo "Добавление публичного ключа в authorized_keys..."
cat ${SSH_KEY_FILE}.pub >> $SSH_DIR/authorized_keys
chmod 600 $SSH_DIR/authorized_keys

# Выводим приватный ключ для добавления в GitHub Secrets
echo ""
echo "============================================"
echo "⚠️  ВАЖНО: Скопируйте приватный ключ ниже"
echo "и добавьте его в GitHub Secrets как SERVER_SSH_KEY"
echo "============================================"
echo ""
cat $SSH_KEY_FILE
echo ""
echo "============================================"
echo ""
echo "Действия:"
echo "1. Скопируйте приведённый выше приватный ключ"
echo "2. Перейдите в репозиторий на GitHub"
echo "3. Settings -> Secrets and variables -> Actions"
echo "4. New repository secret"
echo "   - Name: SERVER_SSH_PRIVATE_KEY"
echo "   - Value: (вставьте скопированный ключ)"
echo ""
echo "Также добавьте следующие секреты:"
echo "   - SERVER_HOST: 195.133.49.121"
echo "   - SERVER_USER: botuser"
echo ""
