---
name: python-testing-patterns
version: 1.0.0
description: Use when writing tests in Python - covers pytest patterns, fixtures, mocking, async testing, and common anti-patterns specific to Python testing
---

# Python Testing Patterns

## Overview

Python testing with pytest has specific patterns that differ from other languages. This skill covers pytest idioms, fixtures, async testing, and avoiding Python-specific testing anti-patterns.

**Core principle:** Good Python tests use pytest fixtures for setup, parametrize for multiple cases, and AsyncMock for async code.

## When to Use

**Always use for:**
- Writing new tests in Python
- Converting unittest to pytest
- Testing async code (aiogram, aiohttp)
- Setting up test fixtures
- Mocking external dependencies

## Essential pytest Patterns

### 1. Fixtures Over Setup/Teardown

```python
# ❌ WRONG: unittest style
class TestUser(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        self.user = User(name="Test")
    
    def tearDown(self):
        self.db.close()

# ✅ CORRECT: pytest fixtures
import pytest

@pytest.fixture
def db():
    database = Database()
    yield database
    database.close()  # Teardown after test

@pytest.fixture
def user():
    return User(name="Test")

def test_user_creation(db, user):
    db.save(user)
    assert db.get(user.id) == user
```

### 2. Fixture Scopes

```python
# Per-test (default) - runs for each test
@pytest.fixture
def fresh_user():
    return User(name="Test")

# Per-module - runs once per module
@pytest.fixture(scope="module")
def db_connection():
    conn = create_connection()
    yield conn
    conn.close()

# Per-session - runs once for entire test run
@pytest.fixture(scope="session")
def app():
    return create_app()
```

### 3. Parametrize for Multiple Cases

```python
# ❌ WRONG: Copy-paste tests
def test_validate_email_valid():
    assert validate_email("user@example.com") is True

def test_validate_email_no_at():
    assert validate_email("userexample.com") is False

def test_validate_email_empty():
    assert validate_email("") is False

# ✅ CORRECT: Parametrize
@pytest.mark.parametrize("email,expected", [
    ("user@example.com", True),
    ("user.name@domain.org", True),
    ("userexample.com", False),
    ("@domain.com", False),
    ("", False),
    (None, False),
])
def test_validate_email(email, expected):
    assert validate_email(email) is expected
```

### 4. Parametrize with IDs

```python
@pytest.mark.parametrize("input_data,expected", [
    pytest.param(
        {"name": "Test", "email": "test@example.com"},
        True,
        id="valid_user"
    ),
    pytest.param(
        {"name": "", "email": "test@example.com"},
        False,
        id="empty_name"
    ),
    pytest.param(
        {"name": "Test", "email": "invalid"},
        False,
        id="invalid_email"
    ),
])
def test_validate_user(input_data, expected):
    assert validate_user(input_data) is expected
```

## Async Testing

### Setup

```bash
pip install pytest-asyncio
```

```python
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"  # or use @pytest.mark.asyncio per test
```

### Async Fixtures

```python
import pytest

@pytest.fixture
async def async_db():
    db = await Database.connect()
    yield db
    await db.close()

@pytest.fixture
async def user_service(async_db):
    return UserService(async_db)

@pytest.mark.asyncio
async def test_get_user(user_service):
    user = await user_service.get(1)
    assert user.name == "Test"
```

### AsyncMock

```python
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_handler():
    # Create async mock
    message = MagicMock()
    message.answer = AsyncMock()
    message.text = "/start"
    
    await cmd_start(message)
    
    message.answer.assert_called_once()
    # Check call args
    assert "Welcome" in message.answer.call_args[0][0]
```

### Patching Async Functions

```python
@pytest.mark.asyncio
async def test_with_patched_async():
    with patch('module.fetch_data', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = {"id": 1, "name": "Test"}
        
        result = await service.get_user_data(1)
        
        mock_fetch.assert_called_once_with(1)
        assert result["name"] == "Test"
```

## aiogram Testing Patterns

### Testing Handlers

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, User, Chat

@pytest.fixture
def telegram_user():
    return User(id=123456, is_bot=False, first_name="Test", language_code="ru")

@pytest.fixture
def telegram_chat():
    return Chat(id=123456, type="private")

@pytest.fixture
def message(telegram_user, telegram_chat):
    msg = MagicMock(spec=Message)
    msg.from_user = telegram_user
    msg.chat = telegram_chat
    msg.answer = AsyncMock()
    msg.reply = AsyncMock()
    return msg

@pytest.mark.asyncio
async def test_start_command(message):
    message.text = "/start"
    
    await cmd_start(message)
    
    message.answer.assert_called_once()
    call_text = message.answer.call_args[0][0]
    assert "Добро пожаловать" in call_text
```

### Testing FSM

```python
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

@pytest.fixture
def storage():
    return MemoryStorage()

@pytest.fixture
async def state(storage, telegram_user, telegram_chat):
    # Create real FSMContext
    return FSMContext(
        storage=storage,
        key=StorageKey(
            bot_id=123,
            chat_id=telegram_chat.id,
            user_id=telegram_user.id
        )
    )

@pytest.mark.asyncio
async def test_registration_flow(message, state):
    # Start registration
    await cmd_register(message, state)
    current_state = await state.get_state()
    assert current_state == RegistrationStates.waiting_for_name
    
    # Enter name
    message.text = "John"
    await process_name(message, state)
    current_state = await state.get_state()
    assert current_state == RegistrationStates.waiting_for_email
    
    # Check saved data
    data = await state.get_data()
    assert data["name"] == "John"
```

### Testing Middleware

```python
@pytest.mark.asyncio
async def test_logging_middleware():
    middleware = LoggingMiddleware()
    
    # Mock handler
    handler = AsyncMock(return_value="result")
    
    # Mock event
    event = MagicMock()
    event.from_user.id = 123
    
    data = {}
    
    result = await middleware(handler, event, data)
    
    assert result == "result"
    handler.assert_called_once_with(event, data)
```

## Mocking Patterns

### Mock vs MagicMock vs AsyncMock

```python
from unittest.mock import Mock, MagicMock, AsyncMock

# Mock - basic mock, raises if attribute accessed without config
mock = Mock()
mock.method()  # OK
mock.attr  # AttributeError (unless spec or configured)

# MagicMock - magic methods work
magic = MagicMock()
len(magic)  # Returns another MagicMock
magic["key"]  # Returns another MagicMock

# AsyncMock - for async functions
async_mock = AsyncMock()
await async_mock()  # Returns another MagicMock
```

### Using `spec` for Type Safety

```python
# ❌ WRONG: Typos not caught
mock_user = MagicMock()
mock_user.nmae = "Test"  # Typo! But no error

# ✅ CORRECT: spec catches typos
from models import User

mock_user = MagicMock(spec=User)
mock_user.nmae = "Test"  # AttributeError: Mock object has no attribute 'nmae'
mock_user.name = "Test"  # OK
```

### Patch Decorators

```python
# Patch specific attribute
@patch('module.service.external_api')
def test_with_patch(mock_api):
    mock_api.return_value = {"status": "ok"}
    result = service.call_api()
    assert result["status"] == "ok"

# Patch multiple
@patch('module.service.api_a')
@patch('module.service.api_b')
def test_multiple(mock_b, mock_a):  # Note: reverse order!
    pass

# Patch as context manager
def test_context_patch():
    with patch('module.service.api') as mock_api:
        mock_api.return_value = "mocked"
        assert service.call() == "mocked"
```

## Common Anti-Patterns

### 1. Testing Implementation, Not Behavior

```python
# ❌ WRONG: Tests implementation details
def test_user_service_calls_repository():
    with patch.object(UserService, '_repository') as mock_repo:
        mock_repo.get.return_value = User(id=1)
        service = UserService()
        service.get_user(1)
        mock_repo.get.assert_called_once_with(1)  # Testing internals!

# ✅ CORRECT: Tests behavior
def test_user_service_returns_user():
    service = UserService(repository=FakeRepository())
    user = service.get_user(1)
    assert user.id == 1
```

### 2. Over-Mocking

```python
# ❌ WRONG: Mock everything
def test_calculator_add():
    mock_math = MagicMock()
    mock_math.add.return_value = 5
    calc = Calculator(math=mock_math)
    assert calc.add(2, 3) == 5  # Tests the mock, not the code!

# ✅ CORRECT: Use real implementation
def test_calculator_add():
    calc = Calculator()
    assert calc.add(2, 3) == 5
```

### 3. Tests With Side Effects

```python
# ❌ WRONG: Uses real database/file/network
def test_save_user():
    db = Database("production_connection_string")  # NO!
    service = UserService(db)
    service.save(User(name="Test"))

# ✅ CORRECT: Use test double or fixture
@pytest.fixture
def test_db():
    db = Database("sqlite:///:memory:")
    db.create_tables()
    yield db
    db.drop_tables()

def test_save_user(test_db):
    service = UserService(test_db)
    service.save(User(name="Test"))
```

### 4. Test Order Dependencies

```python
# ❌ WRONG: Tests depend on order
class TestUserFlow:
    user_id = None
    
    def test_create_user(self):
        TestUserFlow.user_id = service.create(User(name="Test"))
    
    def test_get_user(self):
        user = service.get(TestUserFlow.user_id)  # Fails if run alone!

# ✅ CORRECT: Independent tests with fixtures
@pytest.fixture
def created_user(test_db):
    return service.create(User(name="Test"))

def test_get_user(created_user):
    user = service.get(created_user.id)
    assert user.name == "Test"
```

## Fixture Factories

```python
@pytest.fixture
def make_user():
    """Factory fixture for creating users with custom attributes."""
    def _make_user(name="Test", email="test@example.com", **kwargs):
        return User(name=name, email=email, **kwargs)
    return _make_user

def test_multiple_users(make_user):
    user1 = make_user(name="Alice")
    user2 = make_user(name="Bob", email="bob@example.com")
    assert user1.name != user2.name
```

## Test Organization

```
tests/
├── conftest.py           # Shared fixtures
├── unit/
│   ├── conftest.py       # Unit test fixtures
│   ├── test_models.py
│   └── test_services.py
├── integration/
│   ├── conftest.py       # Integration fixtures (real DB)
│   └── test_api.py
└── e2e/
    └── test_bot_flow.py
```

### conftest.py for Shared Fixtures

```python
# tests/conftest.py
import pytest

@pytest.fixture(scope="session")
def app():
    """Application fixture shared across all tests."""
    return create_app()

@pytest.fixture
def client(app):
    """Test client for each test."""
    return app.test_client()
```

## Quick Reference

| Need | Pattern |
|------|---------|
| Setup/teardown | `@pytest.fixture` with `yield` |
| Multiple test cases | `@pytest.mark.parametrize` |
| Async test | `@pytest.mark.asyncio` + `AsyncMock` |
| Mock sync | `MagicMock(spec=Class)` |
| Mock async | `AsyncMock()` |
| Patch import | `@patch('module.function')` |
| Shared setup | `conftest.py` fixtures |
| Run subset | `pytest -k "test_name"` |

## Verification Checklist

Before marking tests complete:

- [ ] Tests are independent (can run in any order)
- [ ] No hardcoded paths/URLs/credentials
- [ ] Async tests use `@pytest.mark.asyncio`
- [ ] Mocks use `spec=` for type safety
- [ ] Fixtures clean up resources (`yield` + cleanup)
- [ ] Parametrize used for multiple test cases
- [ ] No implementation details tested (only behavior)
