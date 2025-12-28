---
name: uv-package-manager
version: 1.0.0
description: Use when managing Python dependencies, creating virtual environments, or running Python commands - uv is 10-100x faster than pip and replaces pip, pip-tools, virtualenv, and pyenv
---

# uv Package Manager

## Overview

uv is an extremely fast Python package manager written in Rust. It replaces pip, pip-tools, virtualenv, and pyenv in a single tool.

**Core principle:** Same commands you know, 10-100x faster.

## When to Use

**Always use uv for:**
- Installing packages
- Creating virtual environments
- Running Python scripts
- Managing Python versions
- Locking dependencies

## Installation

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Via pip (if you must)
pip install uv
```

## Quick Start

```bash
# Initialize new project
uv init my-bot
cd my-bot

# Add dependencies
uv add aiogram sqlalchemy pydantic-settings

# Add dev dependencies
uv add --dev pytest pytest-asyncio ruff

# Run your code
uv run python -m my_bot

# Run tests
uv run pytest
```

## Command Reference

### Project Management

```bash
# Initialize project with pyproject.toml
uv init [project-name]

# Sync dependencies (install from pyproject.toml + lock)
uv sync

# Sync including dev dependencies
uv sync --all-extras

# Sync for production (no dev deps)
uv sync --no-dev
```

### Dependency Management

```bash
# Add package
uv add aiogram

# Add with version constraint
uv add "aiogram>=3.4.0"
uv add "aiogram>=3.4.0,<4.0.0"

# Add dev dependency
uv add --dev pytest

# Add optional dependency group
uv add --optional prod uvloop

# Remove package
uv remove aiogram

# Update lock file
uv lock

# Update specific package
uv lock --upgrade-package aiogram

# Update all packages
uv lock --upgrade
```

### Running Commands

```bash
# Run Python script
uv run python script.py

# Run module
uv run python -m my_bot

# Run installed command
uv run pytest
uv run ruff check .

# Run with specific Python version
uv run --python 3.12 python script.py
```

### Virtual Environments

```bash
# Create venv (automatic with sync)
uv venv

# Create with specific Python
uv venv --python 3.12

# Activate (still needed for some tools)
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Note: `uv run` doesn't need activation!
```

### Python Version Management

```bash
# Install Python version
uv python install 3.12

# List available versions
uv python list

# Use specific version for project
uv python pin 3.12
```

## uv vs pip Comparison

| Task | pip | uv |
|------|-----|-----|
| Install package | `pip install aiogram` | `uv add aiogram` |
| Install from requirements | `pip install -r requirements.txt` | `uv sync` |
| Create venv | `python -m venv .venv` | `uv venv` |
| Run script | `python script.py` | `uv run python script.py` |
| Update package | `pip install --upgrade aiogram` | `uv lock --upgrade-package aiogram` |
| Lock deps | `pip-compile` | `uv lock` |
| Speed | ~30 seconds | ~0.5 seconds |

## Lock File (uv.lock)

uv automatically creates `uv.lock` with exact versions:

```bash
# Generate/update lock file
uv lock

# Install exact versions from lock
uv sync --frozen

# CI should use frozen to ensure reproducibility
```

**Always commit `uv.lock` to git!**

## pyproject.toml Integration

uv reads from standard `pyproject.toml`:

```toml
[project]
name = "my-bot"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "aiogram>=3.4.0",
    "sqlalchemy[asyncio]>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "ruff>=0.2.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "ruff>=0.2.0",
]
```

## CI/CD Usage

### GitHub Actions

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"
      
      - name: Set up Python
        run: uv python install 3.12
      
      - name: Install dependencies
        run: uv sync --frozen
      
      - name: Run tests
        run: uv run pytest
      
      - name: Lint
        run: uv run ruff check .
```

### Docker

```dockerfile
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (cached layer)
RUN uv sync --frozen --no-dev

# Copy source
COPY src/ ./src/

CMD ["uv", "run", "python", "-m", "my_bot"]
```

## Common Workflows

### Start New Project

```bash
# Create and enter directory
mkdir my-telegram-bot && cd my-telegram-bot

# Initialize
uv init

# Add dependencies
uv add aiogram aiohttp sqlalchemy pydantic-settings
uv add --dev pytest pytest-asyncio ruff mypy

# Create src layout
mkdir -p src/my_bot
touch src/my_bot/__init__.py
touch src/my_bot/__main__.py
```

### Clone and Run Existing Project

```bash
git clone https://github.com/user/project.git
cd project

# Install all dependencies from lock file
uv sync

# Run
uv run python -m project
```

### Update Dependencies

```bash
# Update one package
uv lock --upgrade-package aiogram
uv sync

# Update all
uv lock --upgrade
uv sync

# Check what would update
uv lock --upgrade --dry-run
```

### Add Package from Git

```bash
# From GitHub
uv add git+https://github.com/user/repo.git

# Specific branch
uv add git+https://github.com/user/repo.git@main

# Specific tag
uv add git+https://github.com/user/repo.git@v1.0.0
```

## Troubleshooting

### Cache Issues

```bash
# Clear uv cache
uv cache clean

# Clear and reinstall
rm -rf .venv uv.lock
uv sync
```

### Python Version Conflicts

```bash
# Pin Python version
uv python pin 3.12

# Or specify in pyproject.toml
# requires-python = ">=3.11,<3.13"
```

### Package Not Found

```bash
# Check package name on PyPI
uv search package-name

# Some packages have different names
# Example: PIL → pillow
uv add pillow  # not PIL
```

## Quick Reference Card

```bash
# === PROJECT ===
uv init                     # New project
uv sync                     # Install deps
uv sync --frozen            # Install exact versions (CI)

# === DEPENDENCIES ===
uv add <pkg>                # Add dependency
uv add --dev <pkg>          # Add dev dependency
uv remove <pkg>             # Remove
uv lock                     # Update lock file
uv lock --upgrade           # Update all versions

# === RUNNING ===
uv run python <script>      # Run script
uv run pytest               # Run pytest
uv run <command>            # Run any installed command

# === PYTHON ===
uv python install 3.12      # Install Python
uv python pin 3.12          # Use version for project
uv venv --python 3.12       # Create venv with version

# === MAINTENANCE ===
uv cache clean              # Clear cache
uv self update              # Update uv itself
```

## Why uv?

1. **Speed**: 10-100x faster than pip
2. **Reliability**: Deterministic resolution
3. **Simplicity**: One tool replaces many
4. **Compatibility**: Works with existing pyproject.toml
5. **Modern**: Built for Python 3.8+

## Integration with Other Skills

- **python-packaging**: uv reads pyproject.toml
- **telegram-bot-architecture**: Fast dependency installation
- **security-checklist**: Lock file ensures reproducible builds
