# Python Coding Rules

> Consolidated coding standards for Python projects. Adapted from ECC rule packs.

## Style & Formatting

- **PEP 8** conventions strictly
- **Type annotations** on ALL function signatures
- **Tooling:** ruff (lint), black (format), isort (imports), mypy (types)
- **Immutable by default:** `@dataclass(frozen=True)`, `NamedTuple`, `tuple` over `list` where possible

## Naming

| Entity | Convention | Example |
|--------|-----------|---------|
| Variables/functions | snake_case | `user_name`, `get_user_by_id()` |
| Classes | PascalCase | `UserService` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES` |
| Private | leading underscore | `_internal_helper()` |
| Booleans | is/has/can prefix | `is_active`, `has_permission` |

## Patterns

### Protocol (Duck Typing)
```python
from typing import Protocol

class Repository(Protocol):
    def find_by_id(self, id: str) -> dict | None: ...
    def save(self, entity: dict) -> dict: ...
```

### Dataclasses as DTOs
```python
@dataclass(frozen=True)
class CreateUserRequest:
    name: str
    email: str
    age: int | None = None
```

### Context Managers for Resources
```python
async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
        data = await response.json()
```

## Testing

- **Framework:** pytest (always)
- **Coverage:** `pytest --cov=src --cov-report=term-missing` — minimum 80%
- **Markers:** `@pytest.mark.unit`, `@pytest.mark.integration`
- **Fixtures:** Use conftest.py, prefer factory fixtures over static data
- **Async tests:** `@pytest.mark.asyncio` with `AsyncMock`

## Error Handling

```python
# Specific exceptions
class UserNotFoundError(Exception):
    def __init__(self, user_id: int):
        super().__init__(f"User {user_id} not found")
        self.user_id = user_id

# Structured logging on errors
except Exception as e:
    logger.error("action=create_user error=%s user_id=%s", e, user_id)
    raise
```

## Security

- **Never** `eval()`, `exec()`, or `pickle.loads()` on user input
- **Always** parameterized queries (SQLAlchemy, asyncpg)
- **Always** validate with Pydantic at boundaries
- **Never** log passwords, tokens, or PII
- **Always** use `secrets` module for token generation (not `random`)

## Logging

```python
import structlog
logger = structlog.get_logger(__name__)

def process_order(order_id: int) -> Order:
    logger.info("action=process_order.start", order_id=order_id)
    # ... work ...
    logger.info("action=process_order.done", order_id=order_id, status=result.status)
    return result
```
