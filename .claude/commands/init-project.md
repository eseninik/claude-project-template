---
name: Init Project
description: Полная автоматическая настройка нового проекта (без вопросов)
category: Setup
tags: [init, setup, deploy, cicd]
---

# Init Project - Полностью автоматическая настройка

**Цель**: Настроить CI/CD за одну команду. Без вопросов, без конфигов.

---

## Автоматическое определение параметров

```bash
# 1. Название проекта = название текущей папки
PROJECT_NAME=$(basename "$(pwd)")

# 2. Читаем глобальный конфиг
CONFIG_FILE="$HOME/.claude/deploy.json"

# Если конфига нет — создать с дефолтами и попросить заполнить
if [ ! -f "$CONFIG_FILE" ]; then
  echo "ERROR: Нет конфига $CONFIG_FILE"
  echo "Создай файл с содержимым:"
  echo '{"github_owner":"YOUR_USERNAME","server_host":"YOUR_IP","server_user":"ubuntu","base_path":"/home/ubuntu"}'
  exit 1
fi

# Парсим JSON (работает в bash без jq)
GITHUB_OWNER=$(grep -o '"github_owner"[^,}]*' "$CONFIG_FILE" | cut -d'"' -f4)
SERVER_HOST=$(grep -o '"server_host"[^,}]*' "$CONFIG_FILE" | cut -d'"' -f4)
SERVER_USER=$(grep -o '"server_user"[^,}]*' "$CONFIG_FILE" | cut -d'"' -f4)
BASE_PATH=$(grep -o '"base_path"[^,}]*' "$CONFIG_FILE" | cut -d'"' -f4)

# 3. Путь на сервере = base_path/project_name
PROJECT_PATH="$BASE_PATH/$PROJECT_NAME"

echo "=== Параметры ==="
echo "Project: $PROJECT_NAME"
echo "GitHub: $GITHUB_OWNER/$PROJECT_NAME"
echo "Server: $SERVER_USER@$SERVER_HOST:$PROJECT_PATH"
```

---

## Шаг 1: Проверить prerequisites

```bash
# GitHub CLI
gh --version || echo "STOP: Установи GitHub CLI: winget install GitHub.cli"

# Авторизация
gh auth status || echo "STOP: Авторизуйся: gh auth login"

# SSH к серверу
ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "echo 'SSH OK'" || echo "STOP: Настрой SSH доступ к серверу"
```

---

## Шаг 2: Создать GitHub репозиторий

```bash
# Проверить/создать репо
gh repo view $GITHUB_OWNER/$PROJECT_NAME 2>/dev/null || \
  gh repo create $GITHUB_OWNER/$PROJECT_NAME --private --source=. --remote=origin --push
```

---

## Шаг 3: Настроить GitHub Secrets

```bash
# Читаем локальный SSH ключ (для подключения к серверу)
SSH_KEY=$(cat ~/.ssh/id_ed25519 2>/dev/null || cat ~/.ssh/id_rsa 2>/dev/null)

if [ -z "$SSH_KEY" ]; then
  echo "STOP: Нет SSH ключа. Создай: ssh-keygen -t ed25519"
  exit 1
fi

# Устанавливаем секреты
gh secret set SERVER_HOST --body "$SERVER_HOST"
gh secret set SERVER_USER --body "$SERVER_USER"
gh secret set SERVER_SSH_KEY --body "$SSH_KEY"
gh secret set PROJECT_PATH --body "$PROJECT_PATH"

echo "Секреты установлены"
```

---

## Шаг 4: Настроить сервер

```bash
ssh $SERVER_USER@$SERVER_HOST << REMOTE
  set -e

  # Создать директорию
  mkdir -p $PROJECT_PATH
  cd $PROJECT_PATH

  # Клонировать если пусто
  if [ ! -d ".git" ]; then
    git clone https://github.com/$GITHUB_OWNER/$PROJECT_NAME.git . || true
  fi

  # SSH ключ для GitHub (если нет)
  if [ ! -f ~/.ssh/id_ed25519 ]; then
    ssh-keygen -t ed25519 -C "deploy-$PROJECT_NAME" -f ~/.ssh/id_ed25519 -N ""
  fi

  # GitHub в known_hosts
  grep -q "github.com" ~/.ssh/known_hosts 2>/dev/null || \
    ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null

  # Переключить на SSH
  git remote set-url origin git@github.com:$GITHUB_OWNER/$PROJECT_NAME.git 2>/dev/null || true

  # Вывести публичный ключ
  echo "=== SERVER DEPLOY KEY ==="
  cat ~/.ssh/id_ed25519.pub
  echo "========================="
REMOTE
```

---

## Шаг 5: Добавить Deploy Key в GitHub

```bash
# Получить ключ с сервера
SERVER_KEY=$(ssh $SERVER_USER@$SERVER_HOST "cat ~/.ssh/id_ed25519.pub")

# Сохранить и добавить
echo "$SERVER_KEY" > /tmp/deploy_key_$PROJECT_NAME.pub
gh repo deploy-key add /tmp/deploy_key_$PROJECT_NAME.pub \
  --title "Server Deploy Key" \
  --allow-write 2>/dev/null || echo "Deploy key уже существует"
rm -f /tmp/deploy_key_$PROJECT_NAME.pub
```

---

## Шаг 6: Проверить SSH с сервера к GitHub

```bash
ssh $SERVER_USER@$SERVER_HOST "ssh -T git@github.com 2>&1" | head -1
# Ожидаем: "Hi ...! You've successfully authenticated"
```

---

## Шаг 7: Тестовый деплой

```bash
# Пустой коммит
git commit --allow-empty -m "test: verify CI/CD pipeline" 2>/dev/null || true
git push origin master

# Проверить workflow
sleep 3
gh run list --limit 1
```

---

## Шаг 8: Проверить на сервере

```bash
ssh $SERVER_USER@$SERVER_HOST "cd $PROJECT_PATH && git log -1 --oneline"
```

---

## Финальный вывод

```
✅ Проект $PROJECT_NAME настроен!

GitHub:  https://github.com/$GITHUB_OWNER/$PROJECT_NAME
Server:  $SERVER_USER@$SERVER_HOST:$PROJECT_PATH
Deploy:  git push origin master → auto-deploy

Команда для деплоя:
  git add . && git commit -m "feat: description" && git push origin master
```

---

## Troubleshooting

### "Нет конфига ~/.claude/deploy.json"
```bash
mkdir -p ~/.claude
cat > ~/.claude/deploy.json << 'EOF'
{
  "github_owner": "YOUR_GITHUB_USERNAME",
  "server_host": "YOUR_SERVER_IP",
  "server_user": "ubuntu",
  "base_path": "/home/ubuntu"
}
EOF
```

### "Permission denied" при SSH
- Проверь что ключ добавлен на сервер в `~/.ssh/authorized_keys`

### Deploy Key уже существует
- Это нормально если используешь один ключ для всех проектов
- Можно игнорировать это сообщение
