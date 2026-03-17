---
description: Initialize project with template, git, GitHub, and full CI/CD (mandatory)
allowed-tools:
  - Bash(*)
  - Read
  - Edit
  - TodoWrite
  - AskUserQuestion
---

# Instructions

## 0. Create Task Tracking

**Use TodoWrite to create plan:**

```json
[
  {"content": "Проверка окружения", "status": "pending", "activeForm": "Проверка окружения"},
  {"content": "Определение типа проекта", "status": "pending", "activeForm": "Определение типа проекта"},
  {"content": "Подготовка к перемещению (для old проектов)", "status": "pending", "activeForm": "Подготовка к перемещению"},
  {"content": "Перемещение и копирование шаблона", "status": "pending", "activeForm": "Копирование шаблона"},
  {"content": "Объединение .gitignore (для old проектов)", "status": "pending", "activeForm": "Объединение .gitignore"},
  {"content": "Регистрация проекта", "status": "pending", "activeForm": "Регистрация проекта"},
  {"content": "Инициализация git и GitHub", "status": "pending", "activeForm": "Инициализация git и GitHub"},
  {"content": "CI/CD: workflows + secrets + server setup", "status": "pending", "activeForm": "Настройка CI/CD"},
  {"content": "Итоговый отчёт", "status": "pending", "activeForm": "Формирование отчёта"}
]
```

Mark each step as `in_progress` when starting, `completed` when done.

## 1. Check Environment

**EXECUTE git check if .git exists:**

```bash
if [ -d .git ]; then
  git status --porcelain
fi
```

**Handle uncommitted changes:**
- If output not empty: Ask user (Russian):
  ```
  ⚠️ Незакоммиченные изменения:

  [список изменений]

  Что делать?
  1. Закоммитить и продолжить
  2. Продолжить без коммита
  3. Остановить
  ```
  Wait for user choice. If [1] - help commit first. If [3] - STOP.

- If empty or no .git: Continue.

## 2. Determine Project Type

**EXECUTE directory check:**

```bash
ls -A
```

**Analyze output:**
- Empty directory (only .git or completely empty) → **NEW PROJECT** (skip to step 4)
- Has files → **ASK USER** (Russian):
  ```
  Вижу код в папке. Что делать?

  1. Переместить в old/ (миграция старого проекта)
  2. Оставить как есть (рискованно, может перезаписать одноимённые файлы)
  3. Остановить
  ```

**Store user choice** for next steps:
- [1] → `PROJECT_TYPE=OLD`
- [2] → `PROJECT_TYPE=NEW`
- [3] → STOP

## 3. Prepare for Migration (OLD projects only)

**Skip this step if PROJECT_TYPE=NEW.**

If PROJECT_TYPE=OLD and git is initialized:

**Ask user about commit (Russian):**
```
Рекомендую закоммитить перед перемещением в old/
(это сохранит историю старого кода в git).

Закоммитить сейчас?
1. Да
2. Нет (история не сохранится)
```

**If [1] - create commit:**

```bash
git add .
git commit -m "Save old code before migration

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**If [2] - warn user:**
```
⚠️ История старого кода не будет сохранена в git.
Продолжаем...
```

## 4. Move to old/ and Copy Template

**If PROJECT_TYPE=OLD, move files to old/:**

```bash
mkdir old

# Move everything except .git and old/
find . -maxdepth 1 ! -name '.' ! -name '..' ! -name '.git' ! -name 'old' -exec mv {} old/ \;
```

**For all project types, copy template:**

```bash
cp -r ~/.claude/shared/templates/new-project/. .
```

**Verify basic structure:**

```bash
test -d .claude/skills/project-knowledge
```

If check fails, tell user:
```
❌ Ошибка копирования шаблона.
Попробуй вручную: cp -r ~/.claude/shared/templates/new-project/. .
```

## 4.5. Create Python Virtual Environment

**Check if this is a Python project:**

```bash
# Check for Python project indicators
if [ -f pyproject.toml ] || [ -f requirements.txt ] || [ -f setup.py ] || ls *.py 2>/dev/null | head -1 > /dev/null; then
  echo "PYTHON_PROJECT=true"
else
  echo "PYTHON_PROJECT=false"
fi
```

**If PYTHON_PROJECT=true and no .venv exists:**

```bash
if [ ! -d .venv ]; then
  uv venv .venv 2>/dev/null || python -m venv .venv
  echo "✅ .venv создан"
fi
```

**If pyproject.toml or requirements.txt exists, install deps:**

```bash
if [ -f pyproject.toml ]; then
  uv pip install -e ".[dev]" 2>/dev/null || uv pip install -e "." 2>/dev/null || echo "⚠️ Не удалось установить зависимости из pyproject.toml"
elif [ -f requirements.txt ]; then
  uv pip install -r requirements.txt 2>/dev/null || .venv/Scripts/pip install -r requirements.txt 2>/dev/null || echo "⚠️ Не удалось установить зависимости из requirements.txt"
fi
```

**Purpose:** LSP (Pyright) uses `.venv` to resolve imports and provide hover/goToDefinition. Without `.venv`, type information shows as `Unknown`.

## 5. Merge .gitignore (OLD projects only)

**Skip this step if PROJECT_TYPE=NEW.**

**Read both .gitignore files:**
- Read `old/.gitignore` (old project rules)
- Current `.gitignore` is already from template

**Analyze old .gitignore:**

Parse old .gitignore and identify:
1. **Common rules** (already in new .gitignore):
   - Secrets: `.env`, `*.key`, `credentials.json`, `secrets/`
   - Dependencies: `node_modules/`, `venv/`, `__pycache__/`
   - Build outputs: `dist/`, `build/`, `.next/`, `out/`
   - IDE: `.vscode/`, `.idea/`
   - OS: `.DS_Store`
   - Logs: `*.log`, `logs/`

2. **Project-specific rules** (need to add with `old/` prefix):
   - Custom paths like `/public/uploads/`, `/storage/`
   - Config files like `config/database.php`
   - Any other unique patterns

**Create section for old-specific rules:**

Based on analysis, prepare section like:
```gitignore
# Old project specific rules
old/public/uploads/
old/storage/logs/
old/config/database.php
old/cache/
```

**Edit .gitignore:**

Add the old-specific rules section to the end of current `.gitignore`.

Save old .gitignore as backup:
```bash
cp old/.gitignore old/.gitignore.backup
```

**Security check:**

```bash
git status --porcelain
```

Check output for sensitive files that shouldn't be tracked:
- `old/.env*`
- `old/*.key`
- `old/*.pem`
- `old/credentials.json`
- `old/secrets/`

**If found sensitive files:**
- STOP immediately
- Show user the files
- Ask: "В .gitignore не все правила. Добавить эти файлы в .gitignore?"
- If yes - add rules and re-check
- If no - STOP

**If git status is clean or only expected files:**
- Continue to next step

## 6. Register Project

**Determine platform and path:**

```bash
if [[ "$HOME" == "/Users/"* ]]; then
  echo "mac"
elif [[ "$HOME" == "/home/"* ]] || [[ "$HOME" == "/root" ]]; then
  echo "vps"
else
  echo "unknown"
fi

pwd
```

Store PLATFORM and PROJECT_PATH from output.

**Read registry:**

Read `~/.claude/projects-registry.json` using Read tool.

**Check if path exists:**

Search for PROJECT_PATH in any `paths.mac` or `paths.vps` fields.

**If path found:**
- Show matching project entry
- Ask (Russian): "Этот проект уже зарегистрирован. Всё верно?"
- Wait for confirmation

**If path NOT found:**
- Ask (Russian): "Перечисли названия проекта через запятую (например: MyProject, Мой Проект, my-project):"
- Get user input
- Edit `~/.claude/projects-registry.json`:
  - Add new object to `projects` array
  - Set `names` to array from user input (split by comma)
  - Set `paths.mac` or `paths.vps` (based on PLATFORM) to PROJECT_PATH
  - Set other platform path to empty string
  - Set `github` to empty string
- Tell user (Russian): "Проект зарегистрирован! Проверь файл: [projects-registry.json](~/.claude/projects-registry.json)"

## 7. Initialize Git and GitHub

### 7.1. Initialize Git (if needed)

```bash
if [ ! -d .git ]; then
  git init -b main
fi

git branch --show-current
```

**IMPORTANT: Branch MUST be `main`, not `master`.**

If current branch is `master`, rename it:

```bash
git branch -m master main
```

Store current branch name (must be `main`).

### 7.2. Check gh CLI

```bash
command -v gh
gh auth status
```

**Handle results:**
- If gh not installed: STOP with message: "❌ gh CLI не установлен. Установи: `brew install gh` (macOS) или `sudo apt install gh` (Linux), затем: `gh auth login`"
- If not authenticated: STOP with message: "❌ gh не аутентифицирован. Запусти: `gh auth login`"
- If both OK: Continue

### 7.3. Ask for Repository Name

Ask user (Russian):
```
Введи название GitHub репозитория (например: my-project):
```

Store repository name.

### 7.4. Create GitHub Repository

```bash
gh repo create {repository-name} --private --source=. --remote=origin
```

If command fails, tell user:
```
❌ Ошибка создания GitHub репозитория.
Проверь название (возможно, уже существует).
```

### 7.5. Initial Commit and Push

```bash
git add .

git commit -m "Initial commit with AI-First template

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push -u origin main
```

**If push fails with SSH error (Permission denied / publickey):**

Switch remote to HTTPS and retry:
```bash
gh repo view --json url -q .url  # get HTTPS URL
git remote set-url origin https://github.com/{owner}/{repo}.git
git push -u origin main
```

If still fails:
```
❌ Ошибка push в GitHub.
Проверь статус: git status
```

### 7.6. Create Dev Branch

```bash
git checkout -b dev
git push -u origin dev
```

### 7.7. Create Migration Branch (OLD projects only)

**Skip if PROJECT_TYPE=NEW.**

```bash
git checkout -b feature/migration-ai-first dev
git push -u origin feature/migration-ai-first
```

## 8. Pipeline Setup

**Copy pipeline templates to work directory:**

```bash
# Ensure work/ templates are in place (copied from template, verify they exist)
test -f work/PIPELINE.md && echo "PIPELINE template OK" || echo "PIPELINE template MISSING"
```

**If any files missing, copy from shared templates:**

```bash
if [ ! -f work/PIPELINE.md ]; then
  cp .claude/shared/work-templates/PIPELINE-v3.md work/PIPELINE.md
fi
```

**Purpose:** Pipeline infrastructure enables autonomous multi-phase task execution with compaction resilience. See `.claude/guides/autonomous-pipeline.md` for full guide.

## 9. CI/CD Setup (MANDATORY)

**This step is REQUIRED for every new project. Do NOT skip.**

### 9.1. Create GitHub Actions Workflows

Create directories:
```bash
mkdir -p .github/workflows deploy
```

**Create `.github/workflows/deploy.yml`** — auto-deploy on push to main:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    name: Deploy to Contabo VPS
    runs-on: ubuntu-latest

    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            set -e

            cd /root/{project-name}

            export PATH="/root/.local/bin:$PATH"

            echo "=== Pulling latest changes ==="
            git fetch origin main
            git reset --hard origin/main

            echo "=== Installing dependencies ==="
            uv sync --frozen 2>/dev/null || uv sync

            echo "=== Restarting service ==="
            systemctl restart {project-name}

            echo "=== Health check ==="
            sleep 3
            if systemctl is-active --quiet {project-name}; then
              echo "✅ {project-name} is running"
            else
              echo "❌ {project-name} failed to start"
              journalctl -u {project-name} -n 20 --no-pager
              exit 1
            fi
```

Replace `{project-name}` with the actual repository name (e.g. `freelance-bot`).

**Create `.github/workflows/ci.yml`** — CI on push to dev:

```yaml
name: CI

on:
  push:
    branches: [dev]
  pull_request:
    branches: [main]

jobs:
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Set up Python
        run: uv python install 3.12

      - name: Install dependencies
        run: uv sync

      - name: Lint with ruff
        run: uv run ruff check .

      - name: Type check with pyright
        run: uv run pyright
        continue-on-error: true

  test:
    name: Run Tests
    runs-on: ubuntu-latest
    needs: lint

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Set up Python
        run: uv python install 3.12

      - name: Install dependencies
        run: uv sync

      - name: Run tests
        run: uv run pytest -v
        continue-on-error: true
```

### 9.2. Create Systemd Service File

**Create `deploy/{project-name}.service`:**

```ini
[Unit]
Description={Project Name} - Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/{project-name}
Environment=PATH=/root/{project-name}/.venv/bin:/root/.local/bin:/usr/local/bin:/usr/bin:/bin
EnvironmentFile=/root/{project-name}/.env
ExecStart=/root/{project-name}/.venv/bin/python -m src
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 9.3. Set GitHub Secrets

Read SSH connection info from `SSH_CONTABO_CONNECTION.md` in any existing bot project, or use known Contabo server details.

```bash
# Set secrets for the repo
echo "{SERVER_IP}" | gh secret set SERVER_HOST
echo "root" | gh secret set SERVER_USER
gh secret set SERVER_SSH_KEY < ~/.ssh/id_ed25519
```

**Verify:**
```bash
gh secret list
```

Must show: `SERVER_HOST`, `SERVER_USER`, `SERVER_SSH_KEY`.

### 9.4. Setup Server (Contabo VPS)

**Step A: Generate deploy key on server:**

```bash
ssh -o StrictHostKeyChecking=no root@{SERVER_IP} "
  ssh-keygen -t ed25519 -f /root/.ssh/deploy_{project-name} -N '' -C 'deploy-{project-name}'
  cat /root/.ssh/deploy_{project-name}.pub
"
```

**Step B: Add deploy key to GitHub:**

Save the public key to a temp file and add:
```bash
ssh -o StrictHostKeyChecking=no root@{SERVER_IP} "cat /root/.ssh/deploy_{project-name}.pub" > /tmp/deploy_key.pub
gh repo deploy-key add /tmp/deploy_key.pub --title "contabo-deploy"
```

**Step C: Add SSH host alias on server:**

```bash
ssh -o StrictHostKeyChecking=no root@{SERVER_IP} "
cat >> /root/.ssh/config << 'SSHEOF'

Host github-{project-name}
    HostName github.com
    User git
    IdentityFile /root/.ssh/deploy_{project-name}
    StrictHostKeyChecking no
SSHEOF
"
```

**Step D: Clone repo and install service:**

```bash
ssh -o StrictHostKeyChecking=no root@{SERVER_IP} "
  set -e

  # Clone using deploy key
  GIT_SSH_COMMAND='ssh -i /root/.ssh/deploy_{project-name} -o StrictHostKeyChecking=no' \
    git clone git@github.com:{owner}/{project-name}.git /root/{project-name}

  # Set remote to use SSH alias
  cd /root/{project-name}
  git remote set-url origin git@github-{project-name}:{owner}/{project-name}.git
  git config --global --add safe.directory /root/{project-name}

  # Setup uv + venv
  export PATH=\"/root/.local/bin:\$PATH\"
  command -v uv >/dev/null 2>&1 || { curl -LsSf https://astral.sh/uv/install.sh | sh; }
  uv venv .venv 2>/dev/null || true

  # Create .env placeholder
  cp .env.example .env 2>/dev/null || touch .env

  # Install systemd service (create directly, deploy/ may not be in main yet)
  cat > /etc/systemd/system/{project-name}.service << 'SVCEOF'
[Unit]
Description={Project Name} - Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/{project-name}
Environment=PATH=/root/{project-name}/.venv/bin:/root/.local/bin:/usr/local/bin:/usr/bin:/bin
EnvironmentFile=/root/{project-name}/.env
ExecStart=/root/{project-name}/.venv/bin/python -m src
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVCEOF

  systemctl daemon-reload
  systemctl enable {project-name}
  echo '✅ Server setup complete'
"
```

**Step E: Update server repo to main branch:**

```bash
ssh -o StrictHostKeyChecking=no root@{SERVER_IP} "
  cd /root/{project-name}
  git fetch origin
  git checkout main 2>/dev/null || git checkout -b main origin/main
  git branch -D master 2>/dev/null || true
"
```

### 9.5. Commit CI/CD and Push

```bash
git add .github/workflows/ deploy/
git commit -m "feat: add CI/CD pipeline — auto-deploy from main, CI on dev

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin dev
```

Then merge to main so deploy workflow is active:
```bash
git checkout main
git merge dev --no-edit
git push origin main
git checkout dev
```

### 9.6. Verify Deploy Workflow

```bash
gh run list --limit 3
```

Deploy will fail on `uv sync` (no pyproject.toml yet) — this is EXPECTED.
Check that SSH connection and git pull succeed in the logs:

```bash
gh run view {run-id} --log 2>&1 | tail -20
```

If SSH connection works and git pull succeeds → CI/CD is properly configured.

## 10. Final Report

**Get repository URL:**

```bash
gh repo view --json url -q .url
```

**For NEW projects, report (Russian):**

```
✅ Проект инициализирован!

GitHub: {url} (private)
Ветки: main, dev (текущая)

Что создано:
  .claude/              - контекст и настройки проекта
  .github/workflows/    - CI/CD (auto-deploy main, CI on dev)
  deploy/               - systemd service для сервера
  work/                 - папка для фич и задач
  work/STATE.md         - сохранение состояния между сессиями
  work/PIPELINE.md      - шаблон автономного pipeline
  .gitignore            - правила игнорирования
  CLAUDE.md             - настройки для Claude Code

CI/CD:
  - Push в dev → CI (ruff + pytest)
  - Push в main → автодеплой на Contabo ({SERVER_IP})
  - Secrets: SERVER_HOST, SERVER_USER, SERVER_SSH_KEY ✅
  - Deploy key: contabo-deploy ✅
  - Systemd service: {project-name}.service (enabled, ждёт код)
  - Сервер: /root/{project-name}/ (клонирован, .env создан)

Git workflow:
  dev → коммиты и push сюда
  main → ручной merge из dev, автодеплой на сервер

Следующий шаг:
- Запусти project-planning skill для планирования проекта
- Для автономных задач: cat .claude/guides/autonomous-pipeline.md
```

**For OLD projects, report (Russian):**

```
✅ Проект инициализирован с миграцией!

GitHub: {url} (private)
Ветки: main, dev, feature/migration-ai-first (текущая)
Old код: ./old/
State: work/STATE.md (сохранение состояния между сессиями)

CI/CD:
  - Push в main → автодеплой на Contabo ({SERVER_IP})
  - Push в dev → CI (ruff + pytest)
  - Secrets: SERVER_HOST, SERVER_USER, SERVER_SSH_KEY ✅
  - Сервер: /root/{project-name}/ (клонирован, .env создан)

.gitignore:
- Базовые правила (секреты, зависимости, build outputs)
- Специфичные правила из старого проекта (с префиксом old/)

Проверь git status - всё ОК с .gitignore?

Следующий шаг:
- Запусти /old-folder-audit для анализа legacy кода
- Затем /fill-context-from-audit для заполнения контекста
```

# Important Notes

- This command handles both NEW and OLD projects in one workflow
- For OLD projects: preserves history with optional commit, merges .gitignore rules
- Simplified checks: LLM understands context without excessive validation
- Git and GitHub initialization in one flow
- **Branch naming: ALWAYS `main` and `dev`, NEVER `master`**
- **Git workflow: commits on `dev` → manual merge to `main` → auto-deploy from `main`**
- **CI/CD is MANDATORY** — every project gets deploy.yml + ci.yml + GitHub secrets + server setup
- **Deploy pattern: `appleboy/ssh-action` → SSH to Contabo → git pull → uv sync → systemctl restart**
- **Each project gets its own deploy key** on the server (read-only, per-repo isolation)
- All user communication in Russian
- Technical content (code, docs) in English
