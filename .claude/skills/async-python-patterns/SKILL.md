---
name: async-python-patterns
version: 1.0.0
description: Use when working with asyncio, aiohttp, aiogram, or any async Python code - covers proper async/await patterns, concurrent execution, error handling, and testing async code
---

# Async Python Patterns

## Overview

Python's asyncio requires specific patterns to avoid subtle bugs. This skill covers patterns essential for Telegram bots (aiogram), HTTP clients (aiohttp), and general async code.

**Core principle:** Async code looks synchronous but executes differently. Understanding the event loop is mandatory.

## When to Use

**Always use for:**
- aiogram handlers and middlewares
- aiohttp requests
- Database async operations (asyncpg, aiosqlite)
- Any `async def` function
- Concurrent task execution

**Red flags requiring this skill:**
- `RuntimeWarning: coroutine was never awaited`
- `Event loop is closed`
- Tasks silently failing
- Race conditions in handlers

## Core Patterns

### 1. Proper Coroutine Handling

```python
# ❌ WRONG: Coroutine never executed
async def fetch_data():
    return await api.get()

data = fetch_data()  # Returns coroutine object, not result!

# ✅ CORRECT: Await the coroutine
data = await fetch_data()
```

### 2. Concurrent Execution

```python
# ❌ WRONG: Sequential (slow)
result1 = await fetch_user(user_id)
result2 = await fetch_orders(user_id)
result3 = await fetch_balance(user_id)
# Total time: fetch_user + fetch_orders + fetch_balance

# ✅ CORRECT: Concurrent with gather
result1, result2, result3 = await asyncio.gather(
    fetch_user(user_id),
    fetch_orders(user_id),
    fetch_balance(user_id)
)
# Total time: max(fetch_user, fetch_orders, fetch_balance)

# ✅ CORRECT: With error handling
results = await asyncio.gather(
    fetch_user(user_id),
    fetch_orders(user_id),
    return_exceptions=True  # Don't fail all if one fails
)
for result in results:
    if isinstance(result, Exception):
        logger.error(f"Task failed: {result}")
```

### 3. Timeout Handling

```python
# ❌ WRONG: No timeout (can hang forever)
response = await aiohttp_session.get(url)

# ✅ CORRECT: Always set timeouts
async with asyncio.timeout(10):  # Python 3.11+
    response = await aiohttp_session.get(url)

# ✅ CORRECT: For Python 3.10-
try:
    response = await asyncio.wait_for(
        aiohttp_session.get(url),
        timeout=10.0
    )
except asyncio.TimeoutError:
    logger.error("Request timed out")
```

### 4. Resource Cleanup

```python
# ❌ WRONG: Resource leak
session = aiohttp.ClientSession()
# ... use session ...
# Session never closed!

# ✅ CORRECT: Context manager
async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
        data = await response.json()

# ✅ CORRECT: Manual cleanup with try/finally
session = aiohttp.ClientSession()
try:
    # ... use session ...
finally:
    await session.close()
```

### 5. Background Tasks

```python
# ❌ WRONG: Fire and forget (exceptions lost)
asyncio.create_task(send_notification(user_id))

# ✅ CORRECT: Track and handle errors
async def safe_task(coro, name: str):
    try:
        return await coro
    except Exception as e:
        logger.error(f"Background task {name} failed: {e}")
        raise

task = asyncio.create_task(
    safe_task(send_notification(user_id), "notification")
)

# Store reference to prevent garbage collection
background_tasks.add(task)
task.add_done_callback(background_tasks.discard)
```

## aiogram-Specific Patterns

### Handler Pattern

```python
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

router = Router()

# ✅ CORRECT: Async handler with proper typing
@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()  # Always clear state on /start
    await message.answer("Welcome!")

# ✅ CORRECT: Error handling in handler
@router.message(F.text)
async def process_text(message: Message) -> None:
    try:
        result = await process_user_input(message.text)
        await message.answer(result)
    except ValidationError as e:
        await message.answer(f"Invalid input: {e}")
    except Exception as e:
        logger.exception("Unexpected error in handler")
        await message.answer("Something went wrong. Please try again.")
```

### Middleware Pattern

```python
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable

class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, session_pool):
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        async with self.session_pool() as session:
            data["db_session"] = session
            try:
                return await handler(event, data)
            finally:
                # Cleanup happens automatically with context manager
                pass
```

### FSM (Finite State Machine) Pattern

```python
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_email = State()
    waiting_for_phone = State()

@router.message(RegistrationStates.waiting_for_email)
async def process_email(message: Message, state: FSMContext) -> None:
    email = message.text
    
    if not validate_email(email):
        await message.answer("Invalid email. Please try again:")
        return  # Stay in same state
    
    await state.update_data(email=email)
    await state.set_state(RegistrationStates.waiting_for_phone)
    await message.answer("Now enter your phone:")
```

## Testing Async Code

### Basic async test

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_handler_responds():
    # Arrange
    message = AsyncMock()
    message.text = "/start"
    message.answer = AsyncMock()
    
    # Act
    await cmd_start(message)
    
    # Assert
    message.answer.assert_called_once_with("Welcome!")
```

### Testing with fixtures

```python
import pytest
from aiogram.types import Message, User, Chat

@pytest.fixture
def user():
    return User(id=123, is_bot=False, first_name="Test")

@pytest.fixture
def chat():
    return Chat(id=456, type="private")

@pytest.fixture
def message(user, chat):
    msg = MagicMock(spec=Message)
    msg.from_user = user
    msg.chat = chat
    msg.answer = AsyncMock()
    return msg

@pytest.mark.asyncio
async def test_handler_with_fixtures(message):
    message.text = "Hello"
    await process_text(message)
    assert message.answer.called
```

### Testing concurrent code

```python
@pytest.mark.asyncio
async def test_concurrent_fetch():
    # Mock multiple async calls
    with patch('module.fetch_user', new_callable=AsyncMock) as mock_user:
        with patch('module.fetch_orders', new_callable=AsyncMock) as mock_orders:
            mock_user.return_value = {"id": 1, "name": "Test"}
            mock_orders.return_value = [{"id": 1}]
            
            result = await fetch_all_data(user_id=1)
            
            # Both should be called
            mock_user.assert_called_once_with(1)
            mock_orders.assert_called_once_with(1)
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Forgetting `await` | Linter + `RuntimeWarning` check |
| Blocking calls in async | Use `run_in_executor` for sync code |
| `time.sleep()` in async | Use `await asyncio.sleep()` |
| Creating session per request | Reuse session (singleton or middleware) |
| Not handling `CancelledError` | Let it propagate (it's control flow) |
| Catching `Exception` broadly | `CancelledError` is `BaseException` in 3.8+ |

### Blocking code in async

```python
# ❌ WRONG: Blocks event loop
def sync_heavy_computation(data):
    return expensive_operation(data)

async def handler(message: Message):
    result = sync_heavy_computation(message.text)  # Blocks!
    await message.answer(result)

# ✅ CORRECT: Run in executor
import asyncio
from functools import partial

async def handler(message: Message):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,  # Default executor
        partial(sync_heavy_computation, message.text)
    )
    await message.answer(result)
```

## Quick Reference

| Need | Pattern |
|------|---------|
| Run multiple async | `await asyncio.gather(*coros)` |
| With timeout | `async with asyncio.timeout(N):` |
| Background task | `asyncio.create_task()` + store ref |
| Sync → Async | `await loop.run_in_executor(None, func)` |
| Sleep | `await asyncio.sleep(N)` |
| Cancel task | `task.cancel()` + handle `CancelledError` |

## Integration with Other Skills

- **test-driven-development**: Write async tests FIRST
- **condition-based-waiting**: Use for async polling in tests
- **systematic-debugging**: Check for missing `await` first

## Verification Checklist

Before marking async code complete:

- [ ] All coroutines are awaited
- [ ] Timeouts set on external calls
- [ ] Resources cleaned up (sessions, connections)
- [ ] Background tasks tracked
- [ ] Tests use `@pytest.mark.asyncio`
- [ ] No `time.sleep()` (use `asyncio.sleep()`)
- [ ] No blocking calls without `run_in_executor`
