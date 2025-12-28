# Обновлённый шаблон проекта: 30 скиллов для Telegram-ботов

## Что добавлено

### 13 новых скиллов (было 17 → стало 30)

| Скилл | Назначение | Категория |
|-------|------------|-----------|
| `async-python-patterns` | asyncio, aiogram, aiohttp паттерны | Python |
| `python-testing-patterns` | pytest, AsyncMock, fixtures | Python |
| `telegram-bot-architecture` | Структура бота, роутеры, DI | Python |
| `python-packaging` | pyproject.toml, зависимости | Python |
| `python-performance-optimization` | Профилирование, оптимизация | Python |
| `uv-package-manager` | Быстрый менеджер пакетов | Python |
| `security-checklist` | Защита персональных данных | Security |
| `secret-scanner` | Поиск секретов в коде | Security |
| `api-design-principles` | REST API, webhooks, FastAPI | Architecture |
| `architecture-patterns` | Clean Architecture, SOLID, DI | Architecture |
| `code-reviewer` | Автоматическое код-ревью | Quality |
| `test-generator` | Генерация тестов для кода | Quality |

---

## Структура скиллов (итого 30)

```
.claude/skills/
│
├── # MANDATORY (4)
├── systematic-debugging/
├── test-driven-development/
├── verification-before-completion/
├── security-checklist/          ⭐ НОВЫЙ
│
├── # PYTHON-SPECIFIC (6)
├── async-python-patterns/       ⭐ НОВЫЙ
├── python-testing-patterns/     ⭐ НОВЫЙ
├── telegram-bot-architecture/   ⭐ НОВЫЙ
├── python-packaging/            ⭐ НОВЫЙ
├── python-performance-optimization/ ⭐ НОВЫЙ
├── uv-package-manager/          ⭐ НОВЫЙ
│
├── # ARCHITECTURE & API (2)
├── architecture-patterns/       ⭐ НОВЫЙ
├── api-design-principles/       ⭐ НОВЫЙ
│
├── # SECURITY (2)
├── security-checklist/          ⭐ НОВЫЙ
├── secret-scanner/              ⭐ НОВЫЙ
│
├── # TESTING & QUALITY (3)
├── test-generator/              ⭐ НОВЫЙ
├── code-reviewer/               ⭐ НОВЫЙ
├── testing-anti-patterns/
│
├── # SITUATIONAL (4)
├── root-cause-tracing/
├── defense-in-depth/
├── condition-based-waiting/
├── dispatching-parallel-agents/
│
├── # WORKFLOW (4)
├── executing-plans/
├── subagent-driven-development/
├── finishing-a-development-branch/
├── using-git-worktrees/
│
├── # CODE REVIEW (2)
├── requesting-code-review/
├── receiving-code-review/
│
└── # META (4)
    ├── using-superpowers/
    ├── writing-skills/
    ├── testing-skills-with-subagents/
    └── sharing-skills/
```

---

## Установка

### Просто замени папку шаблона:

```bash
# Удали старую папку
rm -rf "C:\Users\Lenovo\Desktop\Боты\Migrator bots\claude-project-template-update"

# Распакуй ZIP в то же место
```

---

## Когда использовать новые скиллы

### Python/aiogram

| Задача | Скиллы |
|--------|--------|
| Новый handler | TDD + async-python-patterns + telegram-bot-architecture |
| Async баг | systematic-debugging + async-python-patterns |
| Написание тестов | python-testing-patterns + TDD |
| Рефакторинг бота | telegram-bot-architecture + architecture-patterns |
| Персональные данные | security-checklist + secret-scanner + TDD |
| FSM flow | telegram-bot-architecture + python-testing-patterns |
| Новый API endpoint | api-design-principles + TDD |
| Проблемы с производительностью | python-performance-optimization |
| Новый проект | python-packaging + uv-package-manager |
| Добавить тесты к существующему коду | test-generator + python-testing-patterns |
| Код-ревью | code-reviewer |

### Security (ОБЯЗАТЕЛЬНО для миграционных ботов)

| Задача | Скиллы |
|--------|--------|
| Работа с паспортами/визами | security-checklist (MANDATORY) |
| Перед коммитом | secret-scanner |
| Загрузка файлов | security-checklist + api-design-principles |

---

## Что покрывает каждый новый скилл

### async-python-patterns
- ✅ Правильный await
- ✅ asyncio.gather для параллелизма
- ✅ Timeouts
- ✅ Background tasks
- ✅ aiogram handlers и middlewares
- ✅ Тестирование async кода

### python-testing-patterns
- ✅ pytest fixtures и scopes
- ✅ @pytest.mark.parametrize
- ✅ AsyncMock для aiogram
- ✅ Тестирование FSM
- ✅ Анти-паттерны тестирования

### telegram-bot-architecture
- ✅ Рекомендуемая структура проекта
- ✅ Thin handlers → thick services
- ✅ Dependency injection через middleware
- ✅ Router организация
- ✅ FSM states
- ✅ Callback factories

### security-checklist
- ✅ Валидация input
- ✅ SQL injection prevention
- ✅ Маскирование PII в логах
- ✅ Шифрование данных
- ✅ Rate limiting
- ✅ .gitignore для секретов

### secret-scanner
- ✅ Поиск API ключей в коде
- ✅ Поиск паролей
- ✅ Pre-commit hooks
- ✅ CI/CD интеграция

### api-design-principles
- ✅ REST naming conventions
- ✅ HTTP methods и status codes
- ✅ Webhook design
- ✅ Идемпотентность
- ✅ Версионирование API
- ✅ Пагинация

### architecture-patterns
- ✅ Clean Architecture layers
- ✅ SOLID principles
- ✅ Repository pattern
- ✅ Dependency Injection
- ✅ Domain-Driven Design basics

### python-packaging
- ✅ pyproject.toml
- ✅ Dependency management
- ✅ Virtual environments
- ✅ CI/CD setup

### python-performance-optimization
- ✅ Profiling (cProfile, py-spy)
- ✅ Memory profiling
- ✅ Async optimization
- ✅ Database query optimization

### uv-package-manager
- ✅ Быстрая установка пакетов
- ✅ Lock файлы
- ✅ Virtual environments
- ✅ Миграция с pip

### test-generator
- ✅ Scaffold тестов для существующего кода
- ✅ pytest структура
- ✅ Fixtures генерация

### code-reviewer
- ✅ Автоматическое ревью
- ✅ Чеклисты качества
- ✅ Security checks

---

## Проверка установки

После установки выполни в Claude Code:

```bash
cat .claude/skills/SKILLS_INDEX.md | head -60
```

Должен увидеть все 30 скиллов в индексе.

---

## Не изменено

- ✅ OpenSpec workflow (proposal → apply → archive)
- ✅ TDD enforcement
- ✅ Verification before completion
- ✅ Git workflow (dev → main → deploy)
- ✅ /init-project command
- ✅ CI/CD setup

---

## Совместимость

- ✅ Совместим с существующими проектами
- ✅ Не ломает OpenSpec workflow
- ✅ Не конфликтует с удалёнными brainstorming/writing-plans
- ✅ Работает с Claude Code из коробки
