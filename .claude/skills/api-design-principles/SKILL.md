---
name: api-design-principles
version: 1.0.0
description: Use when designing REST APIs, webhooks, or any HTTP endpoints - covers URL design, HTTP methods, status codes, error handling, pagination, and versioning
---

# API Design Principles

## Overview

Good API design makes integration easy and errors obvious. This skill covers REST conventions, webhook patterns, and common pitfalls.

**Core principle:** APIs are interfaces for developers. Design for clarity, consistency, and discoverability.

## When to Use

**Use for:**
- Designing new API endpoints
- Adding webhook handlers (Telegram, payments, etc.)
- Reviewing API design
- Debugging integration issues

## REST Fundamentals

### URL Structure

```
https://api.example.com/v1/users/123/orders?status=pending&limit=10
└──────────┬──────────┘└┬┘└──┬──┘└┬┘└──┬──┘└─────────┬────────────┘
         host        version resource id  sub     query params
```

### Resource Naming

```python
# ✅ GOOD: Nouns, plural, lowercase
GET  /users
GET  /users/123
GET  /users/123/orders
POST /orders

# ❌ BAD: Verbs, singular, mixed case
GET  /getUser
GET  /User/123
POST /createOrder
GET  /users/123/getOrders
```

### HTTP Methods

| Method | Purpose | Idempotent | Safe |
|--------|---------|------------|------|
| GET | Read resource | Yes | Yes |
| POST | Create resource | No | No |
| PUT | Replace resource | Yes | No |
| PATCH | Partial update | Yes | No |
| DELETE | Remove resource | Yes | No |

```python
# Resource: /users

GET    /users          # List all users
GET    /users/123      # Get user 123
POST   /users          # Create new user
PUT    /users/123      # Replace user 123
PATCH  /users/123      # Update user 123 partially
DELETE /users/123      # Delete user 123
```

### HTTP Status Codes

```python
# Success (2xx)
200 OK              # GET, PUT, PATCH success
201 Created         # POST success (include Location header)
204 No Content      # DELETE success

# Client Errors (4xx)
400 Bad Request     # Validation failed
401 Unauthorized    # Not authenticated
403 Forbidden       # Authenticated but not allowed
404 Not Found       # Resource doesn't exist
409 Conflict        # Resource state conflict
422 Unprocessable   # Semantic error (valid JSON, invalid data)
429 Too Many Requests  # Rate limited

# Server Errors (5xx)
500 Internal Error  # Unexpected server error
502 Bad Gateway     # Upstream service error
503 Unavailable     # Service temporarily down
```

## Request/Response Design

### Request Body

```python
# ✅ GOOD: Clear field names, consistent types
POST /users
{
    "email": "user@example.com",
    "name": "John Doe",
    "phone": "+1234567890",
    "role": "client"
}

# ❌ BAD: Inconsistent naming, unclear types
POST /users
{
    "Email": "user@example.com",
    "user_name": "John Doe",
    "tel": 1234567890,  # Number instead of string
    "is_admin": 0       # Number instead of boolean
}
```

### Response Body

```python
# Single resource
GET /users/123
{
    "id": 123,
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}

# Collection with pagination
GET /users?page=2&limit=10
{
    "data": [
        {"id": 123, "name": "John"},
        {"id": 124, "name": "Jane"}
    ],
    "pagination": {
        "page": 2,
        "limit": 10,
        "total": 45,
        "pages": 5
    }
}
```

### Error Response

```python
# ✅ GOOD: Structured, actionable errors
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Request validation failed",
        "details": [
            {
                "field": "email",
                "message": "Invalid email format"
            },
            {
                "field": "phone",
                "message": "Phone number required"
            }
        ]
    }
}

# ❌ BAD: Vague, unhelpful
{
    "error": "Bad request"
}
```

## FastAPI Implementation

### Basic CRUD

```python
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr

app = FastAPI()

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    phone: str | None = None

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True

@app.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
)
async def create_user(user: UserCreate):
    # Create user logic
    return created_user

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    user = await user_service.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": f"User {user_id} not found"}
        )
    return user
```

### Error Handling

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

class APIError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code

@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        }
    )

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors()
            }
        }
    )
```

## Webhook Design (for Telegram bots)

### Webhook Endpoint

```python
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import FastAPI, Request

app = FastAPI()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@app.post("/webhook/{bot_token}")
async def telegram_webhook(bot_token: str, request: Request):
    # Verify token matches
    if bot_token != BOT_TOKEN.split(":")[0]:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    # Parse update
    data = await request.json()
    update = Update(**data)
    
    # Process update
    await dp.feed_update(bot, update)
    
    return {"ok": True}
```

### Webhook Security

```python
import hmac
import hashlib

def verify_telegram_hash(data: dict, bot_token: str) -> bool:
    """Verify Telegram webhook data integrity."""
    check_hash = data.pop("hash", None)
    if not check_hash:
        return False
    
    # Create data check string
    data_check = "\n".join(
        f"{k}={v}" for k, v in sorted(data.items())
    )
    
    # Calculate hash
    secret = hashlib.sha256(bot_token.encode()).digest()
    calculated = hmac.new(
        secret,
        data_check.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(check_hash, calculated)
```

### Payment Webhook (Stripe-like)

```python
@app.post("/webhooks/payments")
async def payment_webhook(request: Request):
    # Verify signature
    signature = request.headers.get("X-Signature")
    body = await request.body()
    
    if not verify_signature(body, signature, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse event
    event = json.loads(body)
    
    # Handle event types
    match event["type"]:
        case "payment.success":
            await handle_payment_success(event["data"])
        case "payment.failed":
            await handle_payment_failed(event["data"])
        case _:
            logger.warning(f"Unhandled event type: {event['type']}")
    
    # Always return 200 to acknowledge receipt
    return {"received": True}
```

## Pagination

### Offset Pagination

```python
@app.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    offset = (page - 1) * limit
    users = await user_repo.list(offset=offset, limit=limit)
    total = await user_repo.count()
    
    return {
        "data": users,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    }
```

### Cursor Pagination (for large datasets)

```python
@app.get("/messages")
async def list_messages(
    cursor: str | None = None,
    limit: int = Query(20, ge=1, le=100),
):
    messages, next_cursor = await message_repo.list_after(
        cursor=cursor,
        limit=limit
    )
    
    return {
        "data": messages,
        "pagination": {
            "next_cursor": next_cursor,
            "has_more": next_cursor is not None
        }
    }
```

## Versioning

### URL Versioning (Recommended)

```python
# Version in URL
app_v1 = FastAPI()
app_v2 = FastAPI()

@app_v1.get("/users")
async def list_users_v1():
    # Old format
    pass

@app_v2.get("/users")
async def list_users_v2():
    # New format with additional fields
    pass

# Mount
main_app = FastAPI()
main_app.mount("/v1", app_v1)
main_app.mount("/v2", app_v2)
```

### Header Versioning

```python
from fastapi import Header

@app.get("/users")
async def list_users(api_version: str = Header("1", alias="X-API-Version")):
    if api_version == "2":
        return await list_users_v2()
    return await list_users_v1()
```

## Common Patterns

### Filtering

```python
@app.get("/orders")
async def list_orders(
    status: OrderStatus | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    user_id: int | None = None,
):
    filters = {}
    if status:
        filters["status"] = status
    if created_after:
        filters["created_at__gte"] = created_after
    if created_before:
        filters["created_at__lte"] = created_before
    if user_id:
        filters["user_id"] = user_id
    
    return await order_repo.list(**filters)
```

### Bulk Operations

```python
@app.post("/users/bulk")
async def create_users_bulk(users: list[UserCreate]):
    if len(users) > 100:
        raise HTTPException(400, "Maximum 100 users per request")
    
    results = await user_service.create_many(users)
    
    return {
        "created": len([r for r in results if r.success]),
        "failed": len([r for r in results if not r.success]),
        "results": results
    }
```

## API Documentation

```python
from fastapi import FastAPI

app = FastAPI(
    title="Migration Bot API",
    description="API for migration services Telegram bot",
    version="1.0.0",
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc",    # ReDoc
)

@app.get(
    "/users/{user_id}",
    summary="Get user by ID",
    description="Retrieve a single user by their unique identifier",
    response_description="The user object",
    responses={
        404: {"description": "User not found"},
    }
)
async def get_user(user_id: int):
    ...
```

## Quick Reference

| Need | Pattern |
|------|---------|
| List resources | `GET /resources` |
| Get one | `GET /resources/{id}` |
| Create | `POST /resources` → 201 |
| Update | `PATCH /resources/{id}` → 200 |
| Replace | `PUT /resources/{id}` → 200 |
| Delete | `DELETE /resources/{id}` → 204 |
| Filter | `GET /resources?status=active` |
| Paginate | `GET /resources?page=2&limit=10` |
| Sub-resource | `GET /users/{id}/orders` |

## Integration with Other Skills

- **telegram-bot-architecture**: API endpoints for bot management
- **security-checklist**: Authentication, validation
- **async-python-patterns**: Async endpoint handlers
