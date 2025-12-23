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
  echo '{"github_owner":"YOUR_USERNAME","server_host":"YOUR_IP","server_user":"ubuntu","base_path":"/home/ubuntu","ssh_key":"PATH_TO_KEY","ssh_config":"PATH_TO_CONFIG"}'
  exit 1
fi

# Парсим JSON (работает в bash без jq)
GITHUB_OWNER=$(grep -o '"github_owner"[^,}]*' "$CONFIG_FILE" | cut -d'"' -f4)
SERVER_HOST=$(grep -o '"server_host"[^,}]*' "$CONFIG_FILE" | cut -d'"' -f4)
SERVER_USER=$(grep -o '"server_user"[^,}]*' "$CONFIG_FILE" | cut -d'"' -f4)
BASE_PATH=$(grep -o '"base_path"[^,}]*' "$CONFIG_FILE" | cut -d'"' -f4)
SSH_KEY=$(grep -o '"ssh_key"[^,}]*' "$CONFIG_FILE" | cut -d'"' -f4)
SSH_CONFIG=$(grep -o '"ssh_config"[^,}]*' "$CONFIG_FILE" | cut -d'"' -f4)

# 3. Путь на сервере = base_path/project_name
PROJECT_PATH="$BASE_PATH/$PROJECT_NAME"

# 4. SSH команда с правильными путями (для Windows с кириллицей)
SSH_CMD="ssh -F \"$SSH_CONFIG\""

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

# SSH к серверу (используем SSH_CMD из конфига)
$SSH_CMD $SERVER_USER@$SERVER_HOST "echo 'SSH OK'" || echo "STOP: Настрой SSH доступ к серверу"
```

---

## Шаг 2: Создать GitHub репозиторий с двумя ветками

```bash
# Проверить существует ли репо
if ! gh repo view $GITHUB_OWNER/$PROJECT_NAME 2>/dev/null; then
  # Создаём репо и пушим в dev (рабочая ветка)
  git checkout -b dev 2>/dev/null || git branch -M dev
  gh repo create $GITHUB_OWNER/$PROJECT_NAME --private --source=. --remote=origin --push

  # Создаём main ветку (продакшн) и пушим
  git checkout -b main
  git push -u origin main

  # Возвращаемся в dev для работы
  git checkout dev

  # Устанавливаем main как default branch в GitHub
  gh repo edit $GITHUB_OWNER/$PROJECT_NAME --default-branch main
fi
```

---

## Шаг 3: Настроить GitHub Secrets

```bash
# Читаем локальный SSH ключ (для подключения к серверу)
SSH_KEY_CONTENT=$(cat "$SSH_KEY" 2>/dev/null)

if [ -z "$SSH_KEY_CONTENT" ]; then
  echo "STOP: Нет SSH ключа по пути $SSH_KEY"
  exit 1
fi

# Устанавливаем секреты (только 3 - PROJECT_PATH не нужен, см. ниже)
gh secret set SERVER_HOST --body "$SERVER_HOST"
gh secret set SERVER_USER --body "$SERVER_USER"
gh secret set SERVER_SSH_KEY --body "$SSH_KEY_CONTENT"

echo "Секреты установлены"
```

---

## Шаг 3.1: Обновить deploy.yml с реальным путём

```bash
# Заменить PROJECT_NAME на реальное имя проекта в workflow
sed -i "s|/home/ubuntu/PROJECT_NAME|$PROJECT_PATH|g" .github/workflows/deploy.yml
git add .github/workflows/deploy.yml
git commit -m "chore: set project path in deploy workflow"
git push origin dev

# Синхронизируем main с dev для деплоя
git checkout main
git merge dev -m "chore: sync main with dev"
git push origin main
git checkout dev
```

---

## Шаг 4: Настроить сервер

**ВАЖНО:** Каждый репозиторий требует УНИКАЛЬНЫЙ deploy key!

```bash
$SSH_CMD $SERVER_USER@$SERVER_HOST << REMOTE
  set -e

  # Создать директорию
  mkdir -p $PROJECT_PATH

  # Создать УНИКАЛЬНЫЙ SSH ключ для этого проекта
  KEY_FILE=~/.ssh/deploy_$PROJECT_NAME
  if [ ! -f "\$KEY_FILE" ]; then
    ssh-keygen -t ed25519 -C "deploy-$PROJECT_NAME" -f "\$KEY_FILE" -N ""
  fi

  # GitHub в known_hosts
  grep -q "github.com" ~/.ssh/known_hosts 2>/dev/null || \
    ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null

  # Настроить SSH config с алиасом для этого репозитория
  if ! grep -q "Host github-$PROJECT_NAME" ~/.ssh/config 2>/dev/null; then
    cat >> ~/.ssh/config << EOF

Host github-$PROJECT_NAME
  HostName github.com
  User git
  IdentityFile ~/.ssh/deploy_$PROJECT_NAME
  IdentitiesOnly yes
EOF
  fi

  # Клонировать репозиторий (ветка main) используя алиас
  cd $PROJECT_PATH
  if [ ! -d ".git" ]; then
    git clone -b main git@github-$PROJECT_NAME:$GITHUB_OWNER/$PROJECT_NAME.git . || true
  fi

  # Настроить remote на алиас
  git remote set-url origin git@github-$PROJECT_NAME:$GITHUB_OWNER/$PROJECT_NAME.git 2>/dev/null || true

  # Вывести публичный ключ
  echo "=== SERVER DEPLOY KEY ==="
  cat "\${KEY_FILE}.pub"
  echo "========================="
REMOTE
```

---

## Шаг 5: Добавить Deploy Key в GitHub

```bash
# Получить УНИКАЛЬНЫЙ ключ с сервера
SERVER_KEY=$($SSH_CMD $SERVER_USER@$SERVER_HOST "cat ~/.ssh/deploy_$PROJECT_NAME.pub")

# Сохранить и добавить
echo "$SERVER_KEY" > /tmp/deploy_key_$PROJECT_NAME.pub
gh repo deploy-key add /tmp/deploy_key_$PROJECT_NAME.pub \
  --title "Server Deploy Key" \
  --allow-write
rm -f /tmp/deploy_key_$PROJECT_NAME.pub
```

---

## Шаг 6: Проверить SSH с сервера к GitHub

```bash
$SSH_CMD $SERVER_USER@$SERVER_HOST "ssh -T git@github-$PROJECT_NAME 2>&1" | head -1
# Ожидаем: "Hi ...! You've successfully authenticated"
```

---

## Шаг 7: Тестовый деплой

```bash
# Пустой коммит в dev
git commit --allow-empty -m "test: verify CI/CD pipeline" 2>/dev/null || true
git push origin dev

# Мержим в main для деплоя
git checkout main
git merge dev
git push origin main
git checkout dev

# Проверить workflow
sleep 3
gh run list --limit 1
```

---

## Шаг 8: Проверить на сервере

```bash
$SSH_CMD $SERVER_USER@$SERVER_HOST "cd $PROJECT_PATH && git log -1 --oneline"
```

---

## Финальный вывод

```
✅ Проект $PROJECT_NAME настроен!

GitHub:  https://github.com/$GITHUB_OWNER/$PROJECT_NAME
Server:  $SERVER_USER@$SERVER_HOST:$PROJECT_PATH

Ветки:
  dev  — рабочая ветка (все изменения коммитятся сюда)
  main — продакшн ветка (автодеплой на сервер)

Workflow:
  1. Работа: git add . && git commit -m "feat: description" && git push origin dev
  2. Деплой: git checkout main && git merge dev && git push origin main && git checkout dev

Или попросить Claude: "мержи и деплой"
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
