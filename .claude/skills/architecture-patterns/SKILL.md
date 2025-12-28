---
name: architecture-patterns
version: 1.0.0
description: Use when designing application architecture, refactoring code structure, or implementing design patterns - covers Clean Architecture, Repository pattern, Dependency Injection, and SOLID principles for Python projects
---

# Architecture Patterns

## Overview

Good architecture separates concerns and makes code testable. This skill covers patterns essential for maintainable Python applications, especially Telegram bots with business logic.

**Core principle:** Dependencies should point inward. Business logic should not depend on frameworks, databases, or external services.

## When to Use

**Always use for:**
- Starting new project from scratch
- Major refactoring
- Adding new bounded context (department, module)
- Code review of structural changes

**Red flags requiring this skill:**
- Business logic in handlers/controllers
- Database queries scattered everywhere
- Circular imports
- "God classes" doing everything
- Can't test without real database

## Clean Architecture Layers

```
┌─────────────────────────────────────────────┐
│           Handlers / Controllers            │  ← Thin, only I/O
├─────────────────────────────────────────────┤
│              Application Services           │  ← Orchestration
├─────────────────────────────────────────────┤
│              Domain / Business Logic        │  ← Core rules
├─────────────────────────────────────────────┤
│              Repositories / Gateways        │  ← Data access
└─────────────────────────────────────────────┘
        ↑ Dependencies point INWARD ↑
```

### Layer Responsibilities

| Layer | Responsibility | Knows About | Example |
|-------|---------------|-------------|---------|
| **Handlers** | Parse input, format output | Services | aiogram handlers |
| **Services** | Orchestrate use cases | Domain, Repos | ClientService |
| **Domain** | Business rules | Nothing external | Client entity |
| **Repositories** | Data persistence | Database | ClientRepository |

## SOLID Principles

### S - Single Responsibility

```python
# ❌ WRONG: Class does everything
class ClientManager:
    def create_client(self, data): ...
    def send_welcome_email(self, client): ...
    def generate_invoice(self, client): ...
    def export_to_excel(self, clients): ...

# ✅ CORRECT: Each class has one job
class ClientService:
    def create_client(self, data): ...

class NotificationService:
    def send_welcome_email(self, client): ...

class InvoiceService:
    def generate_invoice(self, client): ...
```

### O - Open/Closed

```python
# ❌ WRONG: Must modify class to add new behavior
class DocumentProcessor:
    def process(self, doc_type: str, file: bytes):
        if doc_type == "passport":
            return self._process_passport(file)
        elif doc_type == "visa":
            return self._process_visa(file)
        # Must add new elif for each type!

# ✅ CORRECT: Open for extension, closed for modification
from abc import ABC, abstractmethod

class DocumentProcessor(ABC):
    @abstractmethod
    def process(self, file: bytes) -> ProcessedDocument: ...

class PassportProcessor(DocumentProcessor):
    def process(self, file: bytes) -> ProcessedDocument: ...

class VisaProcessor(DocumentProcessor):
    def process(self, file: bytes) -> ProcessedDocument: ...

# Registry pattern
processors: dict[str, DocumentProcessor] = {
    "passport": PassportProcessor(),
    "visa": VisaProcessor(),
}
```

### D - Dependency Inversion

```python
# ❌ WRONG: High-level depends on low-level
class ClientService:
    def __init__(self):
        self.db = PostgresDatabase()  # Concrete dependency!

# ✅ CORRECT: Depend on abstractions
class ClientRepository(ABC):
    @abstractmethod
    async def get(self, id: int) -> Client | None: ...

class ClientService:
    def __init__(self, repo: ClientRepository):
        self.repo = repo  # Abstract dependency
```

## Repository Pattern

### Base Repository

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")

class Repository(ABC, Generic[T]):
    @abstractmethod
    async def get(self, id: int) -> T | None: ...
    
    @abstractmethod
    async def list(self, offset: int = 0, limit: int = 100) -> list[T]: ...
    
    @abstractmethod
    async def create(self, entity: T) -> T: ...
    
    @abstractmethod
    async def update(self, entity: T) -> T: ...
    
    @abstractmethod
    async def delete(self, id: int) -> bool: ...
```

### SQLAlchemy Implementation

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class SQLAlchemyRepository(Repository[T]):
    def __init__(self, session: AsyncSession, model: type[T]):
        self.session = session
        self.model = model
    
    async def get(self, id: int) -> T | None:
        return await self.session.get(self.model, id)
    
    async def create(self, entity: T) -> T:
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
```

## Dependency Injection

### aiogram Middleware DI

```python
from aiogram import BaseMiddleware

class DIMiddleware(BaseMiddleware):
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    async def __call__(self, handler, event, data):
        async with self.session_factory() as session:
            # Build dependency tree
            client_repo = SQLAlchemyClientRepository(session)
            client_service = ClientService(repo=client_repo)
            
            # Inject into handler
            data["client_service"] = client_service
            
            try:
                return await handler(event, data)
            finally:
                await session.commit()
```

### FastAPI Dependency Injection

```python
from fastapi import Depends

async def get_db_session():
    async with async_session_factory() as session:
        yield session

async def get_client_service(
    session: AsyncSession = Depends(get_db_session),
) -> ClientService:
    repo = SQLAlchemyClientRepository(session)
    return ClientService(repo=repo)

@router.get("/clients/{id}")
async def get_client(
    id: int,
    service: ClientService = Depends(get_client_service),
):
    return await service.get(id)
```

## Domain-Driven Design Basics

### Entity vs Value Object

```python
from dataclasses import dataclass

# Entity: Has identity, mutable
@dataclass
class Client:
    id: int
    telegram_id: int
    name: str
    status: str
    
    def approve(self):
        if self.status != "pending":
            raise DomainError("Can only approve pending clients")
        self.status = "approved"

# Value Object: No identity, immutable
@dataclass(frozen=True)
class Money:
    amount: int  # cents
    currency: str
    
    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise DomainError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
```

### Domain Events

```python
@dataclass
class DomainEvent:
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ClientApproved(DomainEvent):
    client_id: int
    approved_by: int

class EventBus:
    def __init__(self):
        self._handlers: dict[type, list[Callable]] = {}
    
    def subscribe(self, event_type: type, handler: Callable):
        self._handlers.setdefault(event_type, []).append(handler)
    
    async def publish(self, event: DomainEvent):
        for handler in self._handlers.get(type(event), []):
            await handler(event)
```

## Project Structure

```
project/
├── bot/                    # Presentation layer (aiogram)
│   ├── handlers/
│   ├── middlewares/
│   └── keyboards/
├── application/            # Application services
│   └── services/
├── domain/                 # Business logic (no dependencies!)
│   ├── entities/
│   ├── value_objects/
│   └── exceptions.py
├── infrastructure/         # External implementations
│   ├── database/
│   │   ├── models.py
│   │   └── repositories/
│   └── external/
└── tests/
```

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **Anemic Domain** | Entities just data | Put behavior in entities |
| **God Class** | One class does all | Split by responsibility |
| **Circular Deps** | A → B → A | Extract to third module |
| **Service Locator** | Global registry | Constructor injection |

## Verification Checklist

- [ ] Handlers are thin (< 20 lines)
- [ ] Business logic in domain/services
- [ ] Dependencies point inward
- [ ] No circular imports
- [ ] Repositories behind interfaces
- [ ] Can test services without real DB
- [ ] SOLID principles followed
