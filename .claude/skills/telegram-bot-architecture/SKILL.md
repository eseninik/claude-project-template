---
name: telegram-bot-architecture
version: 1.0.0
description: Use when structuring Telegram bot projects with aiogram - covers project structure, routers organization, dependency injection, and clean architecture patterns for bots
---

# Telegram Bot Architecture

## Overview

aiogram 3.x bots benefit from clean architecture patterns. This skill covers project structure, router organization, and separation of concerns for maintainable Telegram bots.

**Core principle:** Handlers should be thin. Business logic belongs in services. Database access belongs in repositories.

## When to Use

**Use for:**
- Starting new bot project
- Refactoring existing bot
- Adding new bot module (department, feature)
- Code review of bot architecture

## Recommended Project Structure

```
telegram_bot/
├── bot/
│   ├── __init__.py
│   ├── __main__.py           # Entry point
│   ├── config.py             # Settings (pydantic-settings)
│   ├── handlers/
│   │   ├── __init__.py       # Router aggregation
│   │   ├── common.py         # /start, /help, errors
│   │   ├── sales/            # Sales department
│   │   │   ├── __init__.py
│   │   │   ├── router.py     # Router setup
│   │   │   ├── handlers.py   # Handler functions
│   │   │   ├── states.py     # FSM states
│   │   │   └── keyboards.py  # Inline/Reply keyboards
│   │   └── execution/        # Execution department
│   │       ├── __init__.py
│   │       ├── router.py
│   │       ├── handlers.py
│   │       ├── states.py
│   │       └── keyboards.py
│   ├── middlewares/
│   │   ├── __init__.py
│   │   ├── database.py       # DB session injection
│   │   ├── logging.py        # Request logging
│   │   └── throttling.py     # Rate limiting
│   ├── filters/
│   │   ├── __init__.py
│   │   └── admin.py          # Admin-only filter
│   └── callbacks/
│       ├── __init__.py
│       └── factories.py      # CallbackData factories
├── services/
│   ├── __init__.py
│   ├── client_service.py     # Business logic for clients
│   ├── document_service.py   # Document processing
│   └── notification_service.py
├── repositories/
│   ├── __init__.py
│   ├── base.py               # Base repository
│   ├── client_repository.py
│   └── document_repository.py
├── models/
│   ├── __init__.py
│   ├── base.py               # SQLAlchemy base
│   ├── client.py
│   └── document.py
├── database/
│   ├── __init__.py
│   └── session.py            # Session factory
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── alembic/                  # Migrations
├── pyproject.toml
├── .env.example
└── CLAUDE.md
```

## Layer Responsibilities

### Handlers (Thin)

```python
# ❌ WRONG: Fat handler with business logic
@router.message(F.text == "/submit")
async def submit_documents(message: Message, state: FSMContext):
    data = await state.get_data()
    
    # Business logic in handler - BAD!
    if not data.get("passport"):
        await message.answer("Загрузите паспорт")
        return
    
    # Database access in handler - BAD!
    async with session() as db:
        client = Client(
            telegram_id=message.from_user.id,
            passport=data["passport"]
        )
        db.add(client)
        await db.commit()
    
    await message.answer("Документы приняты")

# ✅ CORRECT: Thin handler, logic in service
@router.message(F.text == "/submit")
async def submit_documents(
    message: Message,
    state: FSMContext,
    client_service: ClientService,  # Injected via middleware
) -> None:
    data = await state.get_data()
    
    try:
        await client_service.submit_documents(
            telegram_id=message.from_user.id,
            documents=data
        )
        await state.clear()
        await message.answer("Документы приняты!")
    except ValidationError as e:
        await message.answer(f"Ошибка: {e.message}")
```

### Services (Business Logic)

```python
# services/client_service.py
from dataclasses import dataclass
from repositories import ClientRepository, DocumentRepository

@dataclass
class ClientService:
    client_repo: ClientRepository
    document_repo: DocumentRepository
    
    async def submit_documents(
        self,
        telegram_id: int,
        documents: dict,
    ) -> Client:
        """Submit client documents for processing."""
        # Validation
        self._validate_documents(documents)
        
        # Get or create client
        client = await self.client_repo.get_by_telegram_id(telegram_id)
        if not client:
            client = await self.client_repo.create(telegram_id=telegram_id)
        
        # Save documents
        for doc_type, file_id in documents.items():
            await self.document_repo.create(
                client_id=client.id,
                document_type=doc_type,
                telegram_file_id=file_id,
            )
        
        # Update client status
        client.status = ClientStatus.DOCUMENTS_SUBMITTED
        await self.client_repo.update(client)
        
        return client
    
    def _validate_documents(self, documents: dict) -> None:
        required = {"passport", "photo"}
        missing = required - set(documents.keys())
        if missing:
            raise ValidationError(f"Отсутствуют документы: {', '.join(missing)}")
```

### Repositories (Data Access)

```python
# repositories/base.py
from typing import Generic, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: type[T]):
        self.session = session
        self.model = model
    
    async def get(self, id: int) -> T | None:
        return await self.session.get(self.model, id)
    
    async def get_all(self) -> list[T]:
        result = await self.session.execute(select(self.model))
        return list(result.scalars().all())
    
    async def create(self, **kwargs) -> T:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance
    
    async def update(self, instance: T) -> T:
        await self.session.flush()
        return instance
    
    async def delete(self, instance: T) -> None:
        await self.session.delete(instance)
        await self.session.flush()

# repositories/client_repository.py
class ClientRepository(BaseRepository[Client]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Client)
    
    async def get_by_telegram_id(self, telegram_id: int) -> Client | None:
        result = await self.session.execute(
            select(Client).where(Client.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
```

## Dependency Injection via Middleware

```python
# middlewares/database.py
from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable
from aiogram.types import TelegramObject

from services import ClientService, DocumentService
from repositories import ClientRepository, DocumentRepository

class DependencyMiddleware(BaseMiddleware):
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with self.session_factory() as session:
            # Create repositories
            client_repo = ClientRepository(session)
            document_repo = DocumentRepository(session)
            
            # Create services
            data["client_service"] = ClientService(
                client_repo=client_repo,
                document_repo=document_repo,
            )
            data["document_service"] = DocumentService(
                document_repo=document_repo,
            )
            
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
```

## Router Organization

### Multi-Department Structure

```python
# bot/handlers/__init__.py
from aiogram import Router

from .common import router as common_router
from .sales import router as sales_router
from .execution import router as execution_router

def setup_routers() -> Router:
    """Create and configure main router with all sub-routers."""
    router = Router()
    
    # Order matters! First match wins
    router.include_router(common_router)  # /start, /help
    router.include_router(sales_router)   # Sales handlers
    router.include_router(execution_router)  # Execution handlers
    
    return router

# bot/handlers/sales/__init__.py
from aiogram import Router
from .handlers import router

__all__ = ["router"]

# bot/handlers/sales/router.py
from aiogram import Router, F
from aiogram.filters import Command

router = Router(name="sales")

# Apply filters to entire router
router.message.filter(F.chat.type == "private")

# bot/handlers/sales/handlers.py
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from .states import SalesStates
from .keyboards import get_services_keyboard

router = Router()

@router.message(Command("services"))
async def cmd_services(message: Message) -> None:
    await message.answer(
        "Выберите услугу:",
        reply_markup=get_services_keyboard()
    )
```

### FSM States Organization

```python
# bot/handlers/sales/states.py
from aiogram.fsm.state import State, StatesGroup

class ConsultationStates(StatesGroup):
    """States for consultation booking flow."""
    waiting_for_service = State()
    waiting_for_date = State()
    waiting_for_time = State()
    confirmation = State()

class DocumentSubmissionStates(StatesGroup):
    """States for document submission flow."""
    waiting_for_passport = State()
    waiting_for_photo = State()
    waiting_for_additional = State()
    review = State()
```

### Callback Data Factories

```python
# bot/callbacks/factories.py
from aiogram.filters.callback_data import CallbackData

class ServiceCallback(CallbackData, prefix="service"):
    action: str
    service_id: int

class DocumentCallback(CallbackData, prefix="doc"):
    action: str  # "approve", "reject", "request_more"
    client_id: int
    document_id: int | None = None

# Usage in handlers
@router.callback_query(ServiceCallback.filter(F.action == "select"))
async def select_service(
    callback: CallbackQuery,
    callback_data: ServiceCallback,
    client_service: ClientService,
) -> None:
    service = await client_service.get_service(callback_data.service_id)
    await callback.message.edit_text(f"Вы выбрали: {service.name}")
```

## Configuration with pydantic-settings

```python
# bot/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # Bot
    bot_token: str
    admin_ids: list[int] = []
    
    # Database
    database_url: str
    
    # Redis (for FSM storage)
    redis_url: str = "redis://localhost:6379/0"
    
    # Paths
    upload_dir: str = "./uploads"
    
    # Limits
    max_file_size: int = 10 * 1024 * 1024  # 10MB

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

## Entry Point

```python
# bot/__main__.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from bot.config import get_settings
from bot.handlers import setup_routers
from bot.middlewares import DependencyMiddleware
from database import create_session_factory

async def main():
    settings = get_settings()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create bot and dispatcher
    bot = Bot(token=settings.bot_token)
    
    # FSM storage
    redis = Redis.from_url(settings.redis_url)
    storage = RedisStorage(redis=redis)
    
    dp = Dispatcher(storage=storage)
    
    # Setup database
    session_factory = create_session_factory(settings.database_url)
    
    # Register middlewares
    dp.message.middleware(DependencyMiddleware(session_factory))
    dp.callback_query.middleware(DependencyMiddleware(session_factory))
    
    # Register routers
    dp.include_router(setup_routers())
    
    # Start polling
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await redis.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Global db session | Race conditions, connection leaks | Session per request via middleware |
| Business logic in handlers | Untestable, hard to maintain | Extract to services |
| Direct model access in handlers | Tight coupling | Use repositories |
| Hardcoded strings | Hard to maintain | Use enums, constants |
| Fat models | Mixed responsibilities | Separate models and services |
| Circular imports | Import errors | Proper layer separation |

## Testing Architecture

```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_client_service():
    service = AsyncMock(spec=ClientService)
    service.submit_documents.return_value = Client(id=1, status="submitted")
    return service

# tests/unit/test_handlers.py
@pytest.mark.asyncio
async def test_submit_documents(message, mock_client_service):
    # Inject mock service
    await submit_documents(
        message=message,
        state=AsyncMock(),
        client_service=mock_client_service,
    )
    
    mock_client_service.submit_documents.assert_called_once()
    message.answer.assert_called_with("Документы приняты!")
```

## Quick Reference

| Layer | Responsibility | Allowed Dependencies |
|-------|---------------|---------------------|
| Handlers | Request/response, state management | Services, FSMContext |
| Services | Business logic, validation | Repositories |
| Repositories | Data access | Database session |
| Models | Data structure | Nothing |

## Integration with Other Skills

- **async-python-patterns**: All handlers are async
- **python-testing-patterns**: Test each layer independently
- **security-checklist**: Validate input in services
- **test-driven-development**: Write service tests first
