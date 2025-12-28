---
name: test-generator
version: 1.0.0
description: BACKGROUND SKILL - Automatically generates test scaffolds when new functions or classes are created, ensuring TDD compliance by creating test files alongside implementation
---

# Test Generator (Background Skill)

## Overview

This is a **background skill** that creates test scaffolds automatically when you write new code. It ensures every function has a corresponding test.

**Core principle:** No function without a test. Scaffold first, implement second.

## Automatic Activation

This skill activates **automatically** when:
- New function/method created
- New class created
- New file created in `src/`
- Handler added to router

**No manual loading required.**

## Generated Test Structure

### For Functions

When you create:
```python
# src/services/client_service.py
async def register_client(telegram_id: int, name: str) -> Client:
    ...
```

Generator creates:
```python
# tests/unit/test_client_service.py
import pytest
from services.client_service import register_client

class TestRegisterClient:
    """Tests for register_client function."""
    
    @pytest.mark.asyncio
    async def test_register_client_success(self):
        """Test successful client registration."""
        # Arrange
        telegram_id = 123456
        name = "Test User"
        
        # Act
        result = await register_client(telegram_id, name)
        
        # Assert
        assert result is not None
        # TODO: Add specific assertions
        pytest.fail("Test not implemented")
    
    @pytest.mark.asyncio
    async def test_register_client_duplicate_fails(self):
        """Test registration fails for existing client."""
        # TODO: Implement test
        pytest.fail("Test not implemented")
    
    @pytest.mark.asyncio
    async def test_register_client_invalid_input(self):
        """Test registration fails with invalid input."""
        # TODO: Implement test
        pytest.fail("Test not implemented")
```

### For Classes

When you create:
```python
# src/services/document_service.py
class DocumentService:
    def __init__(self, repo: DocumentRepository):
        self.repo = repo
    
    async def upload_document(self, client_id: int, file_id: str) -> Document:
        ...
    
    async def get_documents(self, client_id: int) -> list[Document]:
        ...
```

Generator creates:
```python
# tests/unit/test_document_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from services.document_service import DocumentService

class TestDocumentService:
    """Tests for DocumentService class."""
    
    @pytest.fixture
    def mock_repo(self):
        """Create mock repository."""
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_repo):
        """Create service instance with mocked dependencies."""
        return DocumentService(repo=mock_repo)
    
    class TestUploadDocument:
        """Tests for upload_document method."""
        
        @pytest.mark.asyncio
        async def test_upload_document_success(self, service, mock_repo):
            """Test successful document upload."""
            # Arrange
            client_id = 1
            file_id = "abc123"
            mock_repo.add.return_value = Document(id=1, client_id=client_id)
            
            # Act
            result = await service.upload_document(client_id, file_id)
            
            # Assert
            assert result is not None
            mock_repo.add.assert_called_once()
            pytest.fail("Test not implemented - add specific assertions")
    
    class TestGetDocuments:
        """Tests for get_documents method."""
        
        @pytest.mark.asyncio
        async def test_get_documents_returns_list(self, service, mock_repo):
            """Test getting documents for client."""
            # TODO: Implement test
            pytest.fail("Test not implemented")
```

### For aiogram Handlers

When you create:
```python
# src/bot/handlers/registration.py
@router.message(Command("register"))
async def cmd_register(message: Message, state: FSMContext) -> None:
    ...
```

Generator creates:
```python
# tests/unit/handlers/test_registration.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, User, Chat
from bot.handlers.registration import cmd_register

class TestCmdRegister:
    """Tests for /register command handler."""
    
    @pytest.fixture
    def user(self):
        """Create test user."""
        return User(id=123456, is_bot=False, first_name="Test")
    
    @pytest.fixture
    def chat(self):
        """Create test chat."""
        return Chat(id=123456, type="private")
    
    @pytest.fixture
    def message(self, user, chat):
        """Create test message."""
        msg = MagicMock(spec=Message)
        msg.from_user = user
        msg.chat = chat
        msg.text = "/register"
        msg.answer = AsyncMock()
        msg.reply = AsyncMock()
        return msg
    
    @pytest.fixture
    def state(self):
        """Create test FSM state."""
        state = AsyncMock()
        state.get_data.return_value = {}
        state.get_state.return_value = None
        return state
    
    @pytest.mark.asyncio
    async def test_register_new_user(self, message, state):
        """Test registration for new user."""
        # Act
        await cmd_register(message, state)
        
        # Assert
        message.answer.assert_called_once()
        # TODO: Add specific assertions about response
        pytest.fail("Test not implemented")
    
    @pytest.mark.asyncio
    async def test_register_existing_user(self, message, state):
        """Test registration for already registered user."""
        # TODO: Implement test
        pytest.fail("Test not implemented")
```

## Test Categories Generated

### Happy Path
- Function works with valid input
- Expected output returned
- Side effects occur correctly

### Edge Cases
- Empty input
- Boundary values (0, max int, etc.)
- None/null values

### Error Cases
- Invalid input types
- Missing required data
- Dependency failures

### Async-Specific
- Concurrent calls
- Timeout handling
- Cancellation

## Generated File Locations

```
src/                          tests/
├── services/                 ├── unit/
│   ├── client_service.py     │   ├── test_client_service.py
│   └── document_service.py   │   └── test_document_service.py
├── repositories/             ├── unit/repositories/
│   └── client_repo.py        │   └── test_client_repo.py
└── bot/                      └── unit/handlers/
    └── handlers/                 └── test_registration.py
        └── registration.py
```

## Fixture Templates

### Database Session

```python
@pytest.fixture
async def db_session():
    """Create test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
```

### Fake Repository

```python
@pytest.fixture
def fake_client_repo():
    """Create fake client repository."""
    from repositories.fake import FakeClientRepository
    return FakeClientRepository()
```

### Service with Dependencies

```python
@pytest.fixture
def client_service(fake_client_repo, fake_document_repo):
    """Create service with fake repositories."""
    return ClientService(
        client_repo=fake_client_repo,
        document_repo=fake_document_repo,
    )
```

## pytest.fail() Convention

All generated tests include `pytest.fail("Test not implemented")`:

```python
async def test_something(self):
    # TODO: Implement test
    pytest.fail("Test not implemented")
```

This ensures:
1. Test is visible in test run
2. Test fails until implemented (TDD red phase)
3. No false "all tests pass" when tests empty

## Integration with TDD

This skill supports TDD workflow:

```
1. Write function signature (no body)
   ↓
2. [TEST-GENERATOR] Creates test scaffold
   ↓
3. Implement test assertions (RED)
   ↓
4. Run test → FAILS (expected)
   ↓
5. Implement function body (GREEN)
   ↓
6. Run test → PASSES
   ↓
7. Refactor (stay GREEN)
```

## Customization

### Skip Test Generation

```python
# test-generator: skip
def internal_helper():
    """Helper function, doesn't need direct test."""
    pass
```

### Custom Test Template

Add to `CLAUDE.md`:

```markdown
## Test Generation

### Additional Fixtures
All handler tests should include:
- `mock_client_service` fixture
- `authorized_user` fixture

### Required Test Cases
All service methods must test:
- Success case
- Not found case
- Validation error case
```

## Quick Reference

| Created | Generated Test |
|---------|----------------|
| `async def func()` | `test_func_success`, `test_func_error` |
| `class Service` | Test class with fixtures |
| `@router.message()` | Handler test with message mock |
| `class Model` | Model validation tests |

## This Skill Triggers

- **test-driven-development** — tests are TDD-compliant
- **python-testing-patterns** — follows pytest conventions
- **async-python-patterns** — async tests properly structured
