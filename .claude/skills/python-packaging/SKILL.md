---
name: python-packaging
version: 1.0.0
description: Use when setting up new Python project, managing dependencies, or preparing for deployment - covers pyproject.toml, dependency management, virtual environments, and modern packaging standards
---

# Python Packaging

## Overview

Modern Python packaging uses `pyproject.toml` as the single source of truth. This skill covers project setup, dependency management, and deployment preparation.

**Core principle:** One config file. Reproducible builds. Minimal dependencies.

## When to Use

**Use for:**
- Starting new Python project
- Adding/updating dependencies
- Setting up CI/CD
- Preparing for deployment
- Converting from requirements.txt

## Project Structure

```
my_bot/
├── pyproject.toml          # Single config file
├── src/
│   └── my_bot/
│       ├── __init__.py
│       ├── __main__.py     # Entry point
│       ├── config.py
│       └── handlers/
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_handlers.py
├── .env.example
├── .gitignore
├── README.md
└── CLAUDE.md
```

## pyproject.toml — Complete Example

```toml
[project]
name = "my-telegram-bot"
version = "0.1.0"
description = "Telegram bot for migration services"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "you@example.com"}
]
keywords = ["telegram", "bot", "aiogram"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

# Main dependencies
dependencies = [
    "aiogram>=3.4.0",
    "aiohttp>=3.9.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.29.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "python-dotenv>=1.0.0",
    "redis>=5.0.0",
]

# Optional dependency groups
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.2.0",
    "mypy>=1.8.0",
    "pre-commit>=3.6.0",
]
prod = [
    "uvloop>=0.19.0",  # Faster event loop (Linux only)
    "orjson>=3.9.0",   # Faster JSON
]

[project.urls]
Homepage = "https://github.com/yourname/my-telegram-bot"
Repository = "https://github.com/yourname/my-telegram-bot"

[project.scripts]
my-bot = "my_bot.__main__:main"

# Build system
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/my_bot"]

# Ruff (linter + formatter)
[tool.ruff]
target-version = "py311"
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
    "ARG",    # flake8-unused-arguments
    "SIM",    # flake8-simplify
]
ignore = [
    "E501",   # line too long (handled by formatter)
    "B008",   # function call in default argument
]

[tool.ruff.lint.isort]
known-first-party = ["my_bot"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

# MyPy
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
plugins = ["pydantic.mypy"]

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

# Pytest
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "-v --tb=short"
filterwarnings = [
    "ignore::DeprecationWarning",
]

# Coverage
[tool.coverage.run]
source = ["src"]
branch = true
omit = ["*/tests/*", "*/__main__.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
]
```

## Dependency Management

### Adding Dependencies

```bash
# Using pip (basic)
pip install aiogram

# Using uv (fast, recommended)
uv add aiogram

# With version constraints
uv add "aiogram>=3.4.0,<4.0.0"

# Dev dependency
uv add --dev pytest
```

### Version Constraints

| Constraint | Meaning | Example |
|------------|---------|---------|
| `>=3.4.0` | At least 3.4.0 | `aiogram>=3.4.0` |
| `>=3.4.0,<4.0.0` | 3.4.0 to 3.x.x | `aiogram>=3.4.0,<4.0.0` |
| `~=3.4.0` | Compatible release (3.4.x) | `aiogram~=3.4.0` |
| `==3.4.0` | Exact version | `aiogram==3.4.0` |

### Lock File

```bash
# Generate lock file
uv lock

# Install from lock file (reproducible)
uv sync

# Update specific package
uv lock --upgrade-package aiogram
```

## Virtual Environments

### Using uv (Recommended)

```bash
# Create venv and install
uv sync

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Run without activating
uv run python -m my_bot
uv run pytest
```

### Using venv (Standard)

```bash
# Create
python -m venv .venv

# Activate
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install
pip install -e ".[dev]"
```

## Entry Points

### __main__.py

```python
# src/my_bot/__main__.py
import asyncio
from my_bot.app import create_bot

def main():
    """Entry point for the bot."""
    asyncio.run(create_bot())

if __name__ == "__main__":
    main()
```

### Running

```bash
# As module
python -m my_bot

# Via script (after install)
my-bot

# Via uv
uv run my-bot
```

## Editable Install

```bash
# Development mode (changes reflect immediately)
pip install -e ".[dev]"

# With uv
uv sync
```

## Building & Publishing

### Build Package

```bash
# Using build
pip install build
python -m build

# Creates:
# dist/my_telegram_bot-0.1.0.tar.gz
# dist/my_telegram_bot-0.1.0-py3-none-any.whl
```

### Publish to PyPI

```bash
pip install twine
twine upload dist/*
```

## Docker Integration

### Dockerfile

```dockerfile
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copy dependency files first (cache layer)
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY src/ ./src/

# Run bot
CMD ["uv", "run", "python", "-m", "my_bot"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  bot:
    build: .
    env_file: .env
    restart: unless-stopped
    depends_on:
      - redis
      - postgres

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: bot_db
      POSTGRES_USER: bot_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  redis_data:
  postgres_data:
```

## .gitignore for Python

```gitignore
# Byte-compiled / optimized
__pycache__/
*.py[cod]
*$py.class

# Virtual environments
.venv/
venv/
ENV/

# Distribution / packaging
build/
dist/
*.egg-info/

# IDE
.idea/
.vscode/
*.swp

# Testing
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/

# Environment
.env
.env.local
*.pem

# Project specific
uploads/
logs/
*.db
```

## Migration from requirements.txt

```bash
# 1. Create pyproject.toml (use template above)

# 2. Convert requirements.txt to dependencies
# Manual: copy each line to [project.dependencies]

# Or use tool:
pip install pip-tools
pip-compile --output-file=requirements.lock pyproject.toml
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Dependencies in setup.py | Use pyproject.toml |
| requirements.txt for app | Use pyproject.toml + lock file |
| No version constraints | Add `>=X.Y.Z` minimum |
| Too strict constraints | Use `>=X.Y.Z,<X+1.0.0` |
| Global pip install | Always use virtual environment |
| Missing `src/` layout | Use src layout for cleaner imports |

## Quick Commands Reference

```bash
# New project setup
mkdir my_bot && cd my_bot
uv init
uv add aiogram sqlalchemy pydantic-settings

# Development
uv sync                    # Install all deps
uv run pytest             # Run tests
uv run ruff check .       # Lint
uv run mypy src           # Type check

# Update
uv lock --upgrade         # Update all
uv lock --upgrade-package aiogram  # Update one

# Build
uv build                  # Create wheel/sdist
```

## Integration with Other Skills

- **telegram-bot-architecture**: Project structure follows this layout
- **security-checklist**: .gitignore protects secrets
- **python-testing-patterns**: pytest config in pyproject.toml
