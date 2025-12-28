---
name: secret-scanner
version: 1.0.0
description: BACKGROUND SKILL - Automatically scans code for exposed secrets, API keys, passwords, and sensitive data before they can be committed
---

# Secret Scanner (Background Skill)

## Overview

This is a **background skill** that runs automatically to prevent accidental secret exposure. It catches credentials before they reach git.

**Core principle:** Secrets in code = secrets in git history forever.

## Automatic Activation

This skill activates **automatically**:
- When creating/modifying files
- Before git commit
- When .env or config files are touched
- When strings match secret patterns

**No manual loading required.**

## Secret Patterns Detected

### API Keys & Tokens

| Service | Pattern | Example |
|---------|---------|---------|
| Telegram Bot | `\d{8,10}:[A-Za-z0-9_-]{35}` | `123456789:ABCdefGHI...` |
| OpenAI | `sk-[A-Za-z0-9]{48}` | `sk-abc123...` |
| Stripe | `sk_live_[A-Za-z0-9]{24}` | `sk_live_abc123...` |
| AWS Access | `AKIA[0-9A-Z]{16}` | `AKIAIOSFODNN7EXAMPLE` |
| AWS Secret | `[A-Za-z0-9/+=]{40}` | (40 char base64) |
| GitHub | `ghp_[A-Za-z0-9]{36}` | `ghp_abc123...` |
| Google | `AIza[0-9A-Za-z_-]{35}` | `AIzaSyABC...` |

### Passwords & Credentials

```python
# ❌ DETECTED: Hardcoded password
password = "MySecretPass123!"
db_password = "postgres123"
DATABASE_URL = "postgresql://user:password@localhost/db"

# ❌ DETECTED: Connection strings with credentials
REDIS_URL = "redis://:secretpass@localhost:6379"
MONGODB_URI = "mongodb://admin:pass@host:27017"

# ✅ SAFE: Environment variables
password = os.environ["DB_PASSWORD"]
DATABASE_URL = os.environ["DATABASE_URL"]
```

### Private Keys

```python
# ❌ DETECTED: RSA private key
PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEA...
-----END RSA PRIVATE KEY-----"""

# ❌ DETECTED: SSH private key
SSH_KEY = """-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUA...
-----END OPENSSH PRIVATE KEY-----"""
```

### Other Sensitive Data

- JWT secrets: `jwt_secret`, `JWT_SECRET`
- Encryption keys: `ENCRYPTION_KEY`, `secret_key`
- Webhook secrets: `WEBHOOK_SECRET`
- Session secrets: `SESSION_SECRET`, `COOKIE_SECRET`

## Alert Levels

### 🔴 CRITICAL — Block Commit

```python
# These MUST be fixed before commit

BOT_TOKEN = "123456789:ABCdefGHIjklMNO..."  # Telegram bot token
STRIPE_KEY = "sk_live_..."                   # Production Stripe key
AWS_SECRET = "wJalrXUtnFEMI/K7MDENG..."     # AWS secret key
```

### 🟠 WARNING — Review Required

```python
# These should be reviewed

DEBUG_API_KEY = "test_key_123"  # Might be test key, verify
password = "changeme"           # Default password, verify removed in prod
```

### 🟡 NOTICE — Consider Moving

```python
# Not secrets, but should be in config

MAX_RETRIES = 3
TIMEOUT = 30
API_URL = "https://api.example.com"  # Consider .env for flexibility
```

## Response to Detection

When secret detected, Claude will:

1. **Stop** - Don't continue writing code
2. **Alert** - Show what was detected and why it's dangerous
3. **Suggest fix** - Provide environment variable solution
4. **Verify removal** - Ensure secret is gone before proceeding

### Example Response

```markdown
🔴 **SECRET DETECTED**

**File:** `bot/config.py`
**Line 15:** Telegram bot token exposed

```python
# ❌ FOUND
BOT_TOKEN = "123456789:ABCdef..."
```

**Risk:** This token gives full access to your bot. If committed:
- Anyone can read your messages
- Anyone can send messages as your bot
- Token is in git history FOREVER

**Fix:**

1. Add to `.env`:
   ```
   BOT_TOKEN=123456789:ABCdef...
   ```

2. Replace in code:
   ```python
   import os
   BOT_TOKEN = os.environ["BOT_TOKEN"]
   ```

3. Add `.env` to `.gitignore`:
   ```
   .env
   .env.*
   ```

4. If already committed:
   - **Revoke token immediately** in @BotFather
   - Create new token
   - Consider git history cleanup
```

## Safe Patterns

### Using Environment Variables

```python
import os
from dotenv import load_dotenv

load_dotenv()

# ✅ SAFE: From environment
BOT_TOKEN = os.environ["BOT_TOKEN"]
DATABASE_URL = os.environ["DATABASE_URL"]

# ✅ SAFE: With validation
def get_required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required env: {name}")
    return value
```

### Using pydantic-settings

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    bot_token: str
    database_url: str
    redis_url: str = "redis://localhost:6379"
    
    class Config:
        env_file = ".env"

# ✅ SAFE: Loaded from environment
settings = Settings()
```

## Required Files

### .gitignore (MANDATORY)

```gitignore
# Secrets - NEVER commit
.env
.env.*
*.pem
*.key
secrets/
config/local.py

# Common secret files
.secrets
credentials.json
service-account.json
```

### .env.example (Template)

```bash
# Copy to .env and fill in values
BOT_TOKEN=your_bot_token_here
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379
SECRET_KEY=generate_random_string_here
```

## Git Hooks Integration

### Pre-commit hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check for secrets
if grep -rE "(BOT_TOKEN|API_KEY|SECRET).*=.*['\"][^'\"]+['\"]" --include="*.py" .; then
    echo "❌ Potential secrets found! Check files above."
    exit 1
fi
```

### Using detect-secrets

```bash
# Install
pip install detect-secrets

# Create baseline
detect-secrets scan > .secrets.baseline

# Pre-commit check
detect-secrets-hook --baseline .secrets.baseline
```

## Quick Commands

```bash
# Scan current directory
grep -rE "password|secret|token|key" --include="*.py" .

# Check for common patterns
grep -rE "(sk_live_|AKIA|ghp_|\d{8,10}:[A-Za-z0-9_-]{35})" .

# Generate random secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## What to Do If Secret Committed

1. **Revoke immediately** - Change/regenerate the secret
2. **Don't just delete** - It's still in git history
3. **Clean history** (if necessary):
   ```bash
   # Use BFG Repo-Cleaner
   bfg --delete-files .env
   bfg --replace-text passwords.txt
   ```
4. **Force push** - After cleaning (coordinate with team)
5. **Audit access** - Check for unauthorized use

## Integration

This skill triggers:
- **security-checklist** — when secrets found
- **code-reviewer** — adds secret check to review

This skill is triggered by:
- Any file modification
- Git pre-commit
