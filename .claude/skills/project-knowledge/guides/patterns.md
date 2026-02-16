# Паттерны кода

## Назначение
Стандарты и конвенции кода для единообразия и качества.

---

## Naming Conventions

**Файлы:**
- `snake_case.py` для Python модулей
- `PascalCase.py` для классов (опционально)

**Переменные и функции:**
- `snake_case` для переменных и функций
- `PascalCase` для классов
- `UPPER_SNAKE_CASE` для констант

**Примеры:**
```python
# Хорошо
user_name = "John"
def get_user_by_id(user_id: int) -> User:
    pass

class UserService:
    pass

MAX_RETRY_COUNT = 3

# Плохо
userName = "John"  # camelCase
def GetUser():     # PascalCase для функции
```

---

## Организация кода

**Структура модуля:**
```python
# 1. Импорты (stdlib → third-party → local)
import os
from typing import Optional

from aiogram import Router

from src.models import User

# 2. Константы
DEFAULT_TIMEOUT = 30

# 3. Классы/функции
class MyService:
    pass

# 4. Приватные функции (если нужны)
def _helper():
    pass
```

**Принципы:**
- Один класс/сервис = один файл (в большинстве случаев)
- Handlers тонкие - логика в services
- Dependency injection через параметры/middleware
- Избегай circular imports

---

## Обработка ошибок

**Общий подход:**
```python
# Создавай свои исключения для доменных ошибок
class UserNotFoundError(Exception):
    pass

class ValidationError(Exception):
    pass

# Обрабатывай конкретные исключения, не голый except
try:
    user = await user_service.get_by_id(user_id)
except UserNotFoundError:
    await message.answer("Пользователь не найден")
except Exception as e:
    logger.exception("Unexpected error")
    await message.answer("Произошла ошибка")
```

**Логирование ошибок:**
- `logger.exception()` для unexpected errors (включает traceback)
- `logger.error()` для expected errors без traceback
- `logger.warning()` для подозрительных но не критичных ситуаций

---

## Async паттерны

**Используй:**
```python
# async/await для I/O операций
async def fetch_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# gather для параллельных операций
results = await asyncio.gather(
    fetch_users(),
    fetch_orders(),
)
```

**Избегай:**
```python
# НЕ блокируй event loop синхронными вызовами
import requests  # Плохо в async коде
response = requests.get(url)  # Блокирует!

# Используй aiohttp или httpx вместо requests
```

---

## Тестирование

**Naming:**
- `test_<what>_<scenario>_<expected>`
- Например: `test_create_user_with_valid_data_returns_user`

**Структура теста (AAA):**
```python
async def test_get_user_by_id_returns_user():
    # Arrange
    user_id = 1
    expected_user = User(id=1, name="Test")
    mock_repo.get_by_id.return_value = expected_user

    # Act
    result = await service.get_by_id(user_id)

    # Assert
    assert result == expected_user
    mock_repo.get_by_id.assert_called_once_with(user_id)
```

---

## Security Practices

- Никогда не логируй sensitive данные (пароли, токены, PII)
- Используй параметризованные запросы (SQLAlchemy делает это автоматически)
- Валидируй весь пользовательский ввод
- Храни секреты в .env, не в коде
- Маскируй PII в логах: `user_id=123` вместо `phone=+7999...`
