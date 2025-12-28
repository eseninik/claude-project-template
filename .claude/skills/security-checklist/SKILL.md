---
name: security-checklist
version: 1.0.0
description: Use when working with personal data, API keys, authentication, or any code that handles sensitive information - MANDATORY for migration bots handling personal documents and data
---

# Security Checklist

## Overview

Telegram bots for migration services handle extremely sensitive personal data: passports, visas, personal documents, financial information. Security is not optional.

**Core principle:** Every piece of personal data is a liability. Minimize collection, encrypt storage, log access, delete when done.

## When to Use

**MANDATORY for:**
- Any code handling personal documents (passports, visas, IDs)
- User authentication and sessions
- File uploads/downloads
- Database operations with personal data
- API integrations with third-party services
- Deployment and configuration

**Red flags requiring immediate review:**
- Hardcoded credentials in code
- Personal data in logs
- Unencrypted file storage
- Missing input validation
- Broad exception handlers hiding errors

## Pre-Implementation Security Review

### Before writing ANY code:

```
SECURITY DECISION TREE:

Does this feature handle personal data?
├─ Yes → Complete this checklist BEFORE coding
└─ No  → Still review data flow for indirect exposure

Does this feature involve authentication?
├─ Yes → Use established patterns (no custom crypto)
└─ No  → Verify no auth bypass possible

Does this feature accept user input?
├─ Yes → Input validation MANDATORY
└─ No  → Verify input can't be injected upstream
```

## Critical Security Patterns

### 1. Secret Management

```python
# ❌ CRITICAL VULNERABILITY: Hardcoded secrets
BOT_TOKEN = "123456:ABC-DEF1234..."
DATABASE_URL = "postgresql://user:password@localhost/db"

# ✅ CORRECT: Environment variables
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]  # Fails if missing (good!)
DATABASE_URL = os.environ["DATABASE_URL"]

# ✅ CORRECT: With validation
def get_required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

BOT_TOKEN = get_required_env("BOT_TOKEN")
```

### 2. Input Validation

```python
# ❌ WRONG: Trust user input
async def save_document(message: Message):
    filename = message.document.file_name
    await message.document.download(destination=f"/uploads/{filename}")

# ✅ CORRECT: Validate everything
import re
from pathlib import Path
import uuid

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

async def save_document(message: Message) -> Path:
    doc = message.document
    
    # Validate size
    if doc.file_size > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {doc.file_size} bytes")
    
    # Validate extension
    original_name = doc.file_name or "unknown"
    ext = Path(original_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type not allowed: {ext}")
    
    # Generate safe filename (never use user input!)
    safe_filename = f"{uuid.uuid4()}{ext}"
    destination = UPLOAD_DIR / safe_filename
    
    await message.document.download(destination=destination)
    return destination
```

### 3. SQL Injection Prevention

```python
# ❌ CRITICAL VULNERABILITY: SQL injection
async def get_user(user_id: str):
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    return await db.execute(query)

# ✅ CORRECT: Parameterized queries
async def get_user(user_id: int):
    query = "SELECT * FROM users WHERE id = $1"
    return await db.fetchrow(query, user_id)

# ✅ CORRECT: With ORM (SQLAlchemy)
async def get_user(user_id: int) -> User | None:
    async with session() as db:
        return await db.get(User, user_id)
```

### 4. Personal Data in Logs

```python
# ❌ WRONG: Logging sensitive data
logger.info(f"Processing user: {user.passport_number}, email: {user.email}")

# ✅ CORRECT: Mask sensitive data
def mask_passport(number: str) -> str:
    if len(number) < 4:
        return "***"
    return f"***{number[-4:]}"

def mask_email(email: str) -> str:
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    return f"{local[0]}***@{domain}"

logger.info(f"Processing user: {mask_passport(user.passport_number)}, "
            f"email: {mask_email(user.email)}")
# Output: "Processing user: ***1234, email: j***@example.com"

# ✅ BETTER: Don't log PII at all
logger.info(f"Processing user_id={user.id}")
```

### 5. File Upload Security

```python
import magic  # python-magic
from pathlib import Path

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}

async def validate_uploaded_file(file_path: Path) -> bool:
    """Validate file by content, not extension."""
    mime = magic.from_file(str(file_path), mime=True)
    
    if mime not in ALLOWED_MIME_TYPES:
        # Delete suspicious file immediately
        file_path.unlink()
        raise ValueError(f"Invalid file type: {mime}")
    
    return True

# ✅ Full upload flow
async def handle_document(message: Message) -> str:
    # 1. Basic validation
    doc = message.document
    if doc.file_size > MAX_FILE_SIZE:
        raise ValueError("File too large")
    
    # 2. Download to temp location
    temp_path = TEMP_DIR / f"{uuid.uuid4()}.tmp"
    await doc.download(destination=temp_path)
    
    try:
        # 3. Validate content type
        await validate_uploaded_file(temp_path)
        
        # 4. Move to permanent storage with safe name
        ext = Path(doc.file_name or "").suffix.lower() or ".bin"
        final_path = UPLOAD_DIR / f"{uuid.uuid4()}{ext}"
        temp_path.rename(final_path)
        
        return str(final_path)
    except Exception:
        # Clean up on any error
        temp_path.unlink(missing_ok=True)
        raise
```

### 6. Rate Limiting

```python
from aiogram import BaseMiddleware
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: int = 10, per_seconds: int = 60):
        self.rate_limit = rate_limit
        self.per_seconds = per_seconds
        self.requests: dict[int, list[datetime]] = defaultdict(list)
    
    async def __call__(self, handler, event, data):
        user_id = event.from_user.id
        now = datetime.now()
        
        # Clean old requests
        cutoff = now - timedelta(seconds=self.per_seconds)
        self.requests[user_id] = [
            t for t in self.requests[user_id] if t > cutoff
        ]
        
        # Check limit
        if len(self.requests[user_id]) >= self.rate_limit:
            await event.answer("Слишком много запросов. Подождите минуту.")
            return
        
        self.requests[user_id].append(now)
        return await handler(event, data)
```

### 7. Data Encryption at Rest

```python
from cryptography.fernet import Fernet
import base64
import os

# Generate key once and store securely
# key = Fernet.generate_key()

def get_encryption_key() -> bytes:
    key = os.environ.get("ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("ENCRYPTION_KEY not set")
    return base64.b64decode(key)

def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data before storing in database."""
    f = Fernet(get_encryption_key())
    return f.encrypt(data.encode()).decode()

def decrypt_sensitive_data(encrypted: str) -> str:
    """Decrypt sensitive data when reading from database."""
    f = Fernet(get_encryption_key())
    return f.decrypt(encrypted.encode()).decode()

# Usage in model
class UserDocument(Base):
    __tablename__ = "user_documents"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)
    document_type: Mapped[str]
    # Encrypted fields
    _passport_number: Mapped[str] = mapped_column("passport_number")
    
    @property
    def passport_number(self) -> str:
        return decrypt_sensitive_data(self._passport_number)
    
    @passport_number.setter
    def passport_number(self, value: str):
        self._passport_number = encrypt_sensitive_data(value)
```

### 8. Secure Session Management

```python
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

# ✅ CORRECT: Use Redis with encryption and TTL
redis = Redis(
    host=os.environ["REDIS_HOST"],
    password=os.environ["REDIS_PASSWORD"],
    ssl=True,  # Always use SSL in production
)

storage = RedisStorage(
    redis=redis,
    state_ttl=3600,  # 1 hour session timeout
    data_ttl=3600,
)

# Configure session cleanup
async def cleanup_old_sessions():
    """Run periodically to ensure sessions expire."""
    # Redis TTL handles this, but audit periodically
    pass
```

## .gitignore Security

```gitignore
# Secrets - NEVER commit
.env
.env.*
*.pem
*.key
secrets/
config/local.py

# Uploads with personal data
uploads/
temp/

# Database files
*.db
*.sqlite

# Logs that might contain PII
logs/
*.log
```

## Pre-Commit Security Check

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
  
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
```

## Security Checklist Before Deploy

### Code Review

- [ ] No hardcoded secrets (use `detect-secrets`)
- [ ] All user input validated
- [ ] SQL queries parameterized
- [ ] File uploads validated by content type
- [ ] Personal data encrypted at rest
- [ ] Personal data masked in logs
- [ ] Rate limiting implemented
- [ ] Session timeouts configured

### Infrastructure

- [ ] HTTPS/TLS everywhere
- [ ] Database connections encrypted
- [ ] Secrets in environment variables or vault
- [ ] Minimal file permissions
- [ ] Regular backups (encrypted)
- [ ] Monitoring for suspicious activity

### Compliance (for personal data)

- [ ] Data retention policy defined
- [ ] User consent documented
- [ ] Data deletion procedure exists
- [ ] Access logging enabled
- [ ] Breach notification plan ready

## Quick Reference

| Threat | Protection |
|--------|------------|
| Hardcoded secrets | Environment variables + detect-secrets |
| SQL injection | Parameterized queries / ORM |
| Path traversal | UUID filenames, validate paths |
| XSS in responses | Escape output, Content-Type headers |
| Brute force | Rate limiting, account lockout |
| Data breach | Encryption at rest, minimal collection |
| Session hijacking | Secure cookies, short TTL, Redis |

## Integration with Other Skills

- **test-driven-development**: Write security tests FIRST
- **systematic-debugging**: Check security implications of fixes
- **verification-before-completion**: Include security checklist
