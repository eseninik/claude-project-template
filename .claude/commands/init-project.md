---
name: Init Project
description: Полная автоматическая настройка нового проекта (интерактивно)
category: Setup
tags: [init, setup, deploy, cicd]
---

# Init Project - Автоматическая настройка

**Цель**: Настроить полный CI/CD pipeline для нового проекта. Claude спрашивает нужные данные и делает всё сам.

---

## Шаг 1: Собрать информацию у пользователя

**Спросить у пользователя (через чат или AskUserQuestion):**

1. **Название проекта** (для GitHub репозитория)
   - Пример: `my-telegram-bot`

2. **GitHub owner** (username или organization)
   - Пример: `eseninik`

3. **Данные сервера для деплоя:**
   - IP адрес или hostname: `123.45.67.89`
   - SSH пользователь: `ubuntu`
   - Путь для проекта: `/home/ubuntu/my-project`

4. **Название systemd сервиса** (опционально)
   - Пример: `my-bot.service`

**Пример диалога:**
```
Claude: Для настройки проекта мне нужны данные:
1. Как назвать репозиторий на GitHub?
2. Ваш GitHub username?
3. IP сервера для деплоя?
4. SSH пользователь на сервере?
5. Куда на сервере деплоить? (путь)

User: bot-name, eseninik, 1.2.3.4, ubuntu, /home/ubuntu/bot-name
```

---

## Шаг 2: Проверить prerequisites

```bash
# 1. Проверить GitHub CLI
gh --version
# Если нет → попросить установить: winget install GitHub.cli

# 2. Проверить авторизацию
gh auth status
# Если нет → попросить: gh auth login

# 3. Проверить SSH доступ к серверу
ssh -o ConnectTimeout=5 USER@HOST "echo 'SSH OK'"
# Если нет → остановиться и помочь настроить SSH
```

---

## Шаг 3: Создать GitHub репозиторий

```bash
# Проверить существует ли репо
gh repo view OWNER/REPO 2>/dev/null

# Если нет — создать
gh repo create OWNER/REPO --private --source=. --remote=origin --push
```

---

## Шаг 4: Настроить GitHub Secrets

```bash
# Получить приватный ключ для доступа к серверу
# (используем ключ, который уже работает для SSH)
SSH_KEY=$(cat ~/.ssh/id_ed25519)

# Установить все секреты
gh secret set SERVER_HOST --body "IP_ADDRESS"
gh secret set SERVER_USER --body "SSH_USER"
gh secret set SERVER_SSH_KEY --body "$SSH_KEY"
gh secret set PROJECT_PATH --body "/path/on/server"
```

---

## Шаг 5: Настроить сервер

```bash
ssh USER@HOST << 'REMOTE_SCRIPT'
  # Создать директорию если нет
  mkdir -p PROJECT_PATH
  cd PROJECT_PATH

  # Клонировать репозиторий (если пусто)
  if [ ! -d ".git" ]; then
    git clone https://github.com/OWNER/REPO.git .
  fi

  # Создать SSH ключ для GitHub (если нет)
  if [ ! -f ~/.ssh/id_ed25519 ]; then
    ssh-keygen -t ed25519 -C "deploy-key-REPO" -f ~/.ssh/id_ed25519 -N ""
  fi

  # Добавить GitHub в known_hosts
  grep -q "github.com" ~/.ssh/known_hosts 2>/dev/null || ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null

  # Показать публичный ключ для добавления в GitHub
  echo "=== DEPLOY KEY (добавить в GitHub) ==="
  cat ~/.ssh/id_ed25519.pub
  echo "======================================="

  # Переключить remote на SSH
  git remote set-url origin git@github.com:OWNER/REPO.git
REMOTE_SCRIPT
```

---

## Шаг 6: Добавить Deploy Key в GitHub

Получить публичный ключ с сервера и добавить:

```bash
# Получить ключ с сервера
SERVER_PUBLIC_KEY=$(ssh USER@HOST "cat ~/.ssh/id_ed25519.pub")

# Сохранить во временный файл
echo "$SERVER_PUBLIC_KEY" > /tmp/deploy_key.pub

# Добавить в GitHub
gh repo deploy-key add /tmp/deploy_key.pub --title "Server Deploy Key" --allow-write

# Удалить временный файл
rm /tmp/deploy_key.pub
```

---

## Шаг 7: Проверить SSH на сервере

```bash
ssh USER@HOST "ssh -T git@github.com 2>&1 | head -1"
# Ожидаем: "Hi OWNER/REPO! You've successfully authenticated..."
```

---

## Шаг 8: Тестовый деплой

```bash
# Создать тестовый коммит
git commit --allow-empty -m "test: verify CI/CD pipeline"
git push origin main

# Подождать и проверить workflow
sleep 5
gh run list --limit 1
gh run watch
```

---

## Шаг 9: Проверить на сервере

```bash
ssh USER@HOST "cd PROJECT_PATH && git log -1 --oneline"
# Должен показать тестовый коммит
```

---

## Финальный вывод

```
✅ Проект настроен!

GitHub: https://github.com/OWNER/REPO
Server: USER@HOST:PROJECT_PATH
Deploy: push to main → auto-deploy

Для деплоя:
  git add . && git commit -m "feat: description" && git push origin main
```

---

## Troubleshooting

### SSH к серверу не работает
- Проверь что ключ добавлен: `ssh-add -l`
- Проверь права: `chmod 600 ~/.ssh/id_ed25519`

### gh command not found
```bash
# Windows
winget install GitHub.cli
# macOS
brew install gh
# Linux
sudo apt install gh
```

### Deploy Key не работает
- Убедись что ключ добавлен с "Allow write access"
- На сервере: `ssh -T git@github.com` должен работать

### Workflow зелёный но код не обновился
- Проверь PROJECT_PATH в секретах
- На сервере: `git remote -v` должен показывать SSH URL
