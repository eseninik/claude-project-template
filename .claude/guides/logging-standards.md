# Logging Standards

> Mandatory guide for all code written by agents. Every function, endpoint, and process must have structured logging.
> Load: `cat .claude/guides/logging-standards.md`

---

## Why This Is Mandatory

Without logging, debugging requires:
1. Reproducing the issue (often impossible in production)
2. Adding logs retroactively (time-consuming, risky)
3. Guessing what happened (unreliable)

With logging from day 1: read logs → understand issue → fix.

**Rule: No code ships without logging. This is a HARD CONSTRAINT, not a suggestion.**

---

## Core Principles

### 1. Log at Boundaries
Every entry/exit point must be logged:
- Function entry with key parameters
- Function exit with result summary
- External calls (API, DB, file I/O)
- User actions and state transitions

### 2. Log Levels Have Meaning

| Level | When to Use | Example |
|-------|-------------|---------|
| **DEBUG** | Variable values, data transformations, loop iterations | `DEBUG: Processing item 5/100, payload_size=1.2KB` |
| **INFO** | Business flow events, successful operations | `INFO: User login successful, user_id=123` |
| **WARNING** | Recoverable issues, degraded behavior, retries | `WARNING: API rate limited, retry in 5s (attempt 2/3)` |
| **ERROR** | Failed operations that need attention | `ERROR: Payment processing failed, order_id=456, reason=timeout` |
| **CRITICAL** | System-level failures, data corruption risk | `CRITICAL: Database connection pool exhausted, 0/10 available` |

### 3. Structured Over Freeform
Always use key=value pairs or structured format. Never just `print("something happened")`.

### 4. Context Is Everything
Every log entry should answer: **Who? What? When? Where? Why?**
- Who: user_id, request_id, session_id
- What: the action being performed
- When: timestamp (automatic via logger)
- Where: module, function, line (automatic via logger)
- Why: relevant parameters, state

---

## Python Logging Standards

### Setup Pattern
```python
import logging
import structlog  # preferred if available, fallback to stdlib

logger = structlog.get_logger(__name__)
# OR for stdlib:
logger = logging.getLogger(__name__)
```

### Function Logging Pattern
```python
async def process_lead(lead_id: int, source: str) -> dict:
    logger.info("processing_lead_started", lead_id=lead_id, source=source)

    try:
        lead_data = await fetch_lead(lead_id)
        logger.debug("lead_data_fetched", lead_id=lead_id, fields=list(lead_data.keys()))

        result = await transform_lead(lead_data)
        logger.info("processing_lead_completed", lead_id=lead_id, result_status=result["status"])
        return result

    except LeadNotFoundError:
        logger.warning("lead_not_found", lead_id=lead_id, source=source)
        raise
    except Exception as e:
        logger.error("processing_lead_failed", lead_id=lead_id, error=str(e), error_type=type(e).__name__)
        raise
```

### API Endpoint Logging Pattern
```python
@router.post("/api/leads")
async def create_lead(request: LeadCreateRequest):
    request_id = str(uuid4())
    logger.info("api_request_received",
                endpoint="/api/leads", method="POST",
                request_id=request_id, payload_size=len(request.json()))

    try:
        result = await lead_service.create(request)
        logger.info("api_request_completed",
                    request_id=request_id, status=201, lead_id=result.id)
        return result

    except ValidationError as e:
        logger.warning("api_validation_failed",
                      request_id=request_id, errors=e.errors())
        raise HTTPException(400, detail=e.errors())
    except Exception as e:
        logger.error("api_request_failed",
                    request_id=request_id, error=str(e), error_type=type(e).__name__)
        raise
```

### Database Operation Logging Pattern
```python
async def get_contacts(filters: dict, limit: int = 100) -> list[Contact]:
    logger.debug("db_query_started", table="contacts", filters=filters, limit=limit)

    start = time.monotonic()
    result = await db.execute(query)
    elapsed = time.monotonic() - start

    logger.info("db_query_completed",
                table="contacts", rows_returned=len(result),
                elapsed_ms=round(elapsed * 1000, 2))

    if elapsed > 1.0:
        logger.warning("db_query_slow", table="contacts", elapsed_ms=round(elapsed * 1000, 2), filters=filters)

    return result
```

### Background Task / Worker Logging Pattern
```python
async def sync_worker(batch_size: int = 50):
    logger.info("worker_started", worker="sync", batch_size=batch_size)

    processed, errors = 0, 0
    async for batch in get_batches(batch_size):
        logger.debug("batch_processing", batch_num=processed // batch_size + 1, items=len(batch))

        for item in batch:
            try:
                await process_item(item)
                processed += 1
            except Exception as e:
                errors += 1
                logger.error("item_processing_failed", item_id=item.id, error=str(e))

        logger.info("batch_completed", processed=processed, errors=errors)

    logger.info("worker_completed", worker="sync", total_processed=processed, total_errors=errors)
```

### External API Call Logging Pattern
```python
async def call_amocrm_api(method: str, endpoint: str, data: dict = None) -> dict:
    logger.info("external_api_call_started", service="amocrm", method=method, endpoint=endpoint)

    start = time.monotonic()
    try:
        response = await client.request(method, endpoint, json=data)
        elapsed = time.monotonic() - start

        logger.info("external_api_call_completed",
                    service="amocrm", endpoint=endpoint,
                    status=response.status_code, elapsed_ms=round(elapsed * 1000, 2))

        if response.status_code >= 400:
            logger.warning("external_api_error_response",
                          service="amocrm", endpoint=endpoint,
                          status=response.status_code, body=response.text[:500])

        return response.json()

    except httpx.TimeoutException:
        elapsed = time.monotonic() - start
        logger.error("external_api_timeout", service="amocrm", endpoint=endpoint, elapsed_ms=round(elapsed * 1000, 2))
        raise
    except Exception as e:
        logger.error("external_api_failed", service="amocrm", endpoint=endpoint, error=str(e))
        raise
```

---

## Node.js / TypeScript Logging Standards

### Setup Pattern
```typescript
import pino from 'pino';  // preferred
// OR: import winston from 'winston';

const logger = pino({ name: 'module-name' });
// OR for simple projects:
const logger = console;  // acceptable for scripts, not for services
```

### Function Logging Pattern
```typescript
async function processWebhook(payload: WebhookPayload): Promise<void> {
  logger.info({ event: 'webhook_processing_started', type: payload.type, id: payload.id });

  try {
    const result = await handlePayload(payload);
    logger.info({ event: 'webhook_processing_completed', id: payload.id, result: result.status });
  } catch (error) {
    logger.error({ event: 'webhook_processing_failed', id: payload.id, error: error.message, stack: error.stack });
    throw error;
  }
}
```

### Express/Fastify Middleware Logging Pattern
```typescript
app.use((req, res, next) => {
  const requestId = req.headers['x-request-id'] || randomUUID();
  const start = Date.now();

  logger.info({ event: 'request_received', method: req.method, path: req.path, requestId });

  res.on('finish', () => {
    const elapsed = Date.now() - start;
    logger.info({
      event: 'request_completed', method: req.method, path: req.path,
      status: res.statusCode, elapsedMs: elapsed, requestId
    });

    if (elapsed > 1000) {
      logger.warn({ event: 'slow_request', path: req.path, elapsedMs: elapsed, requestId });
    }
  });

  next();
});
```

---

## What MUST Be Logged (Checklist for Implementers)

Every piece of code you write MUST include logging for:

- [ ] **Function entry** — key parameters (not sensitive data)
- [ ] **Function exit** — result summary or status
- [ ] **External API calls** — service name, endpoint, status, elapsed time
- [ ] **Database queries** — table/collection, operation type, row count, elapsed time
- [ ] **File I/O** — file path, operation (read/write), size
- [ ] **State transitions** — from_state → to_state, trigger
- [ ] **Error handling** — every catch block must log the error with context
- [ ] **Retry attempts** — attempt number, max attempts, reason for retry
- [ ] **Background tasks** — start, progress (periodic), completion with stats
- [ ] **Configuration loading** — what was loaded, from where (not secret values)
- [ ] **Authentication/authorization** — success/failure, user identifier (not credentials)

---

## What MUST NOT Be Logged

- Passwords, tokens, API keys, secrets
- Full credit card numbers, SSN, personal health data
- Request/response bodies with PII (log size/hash instead)
- High-frequency loop iterations at INFO level (use DEBUG)

### Safe Logging of Sensitive Data
```python
# BAD
logger.info("api_call", token=api_token)

# GOOD
logger.info("api_call", token_prefix=api_token[:8] + "...")

# BAD
logger.info("user_data", email=user.email, phone=user.phone)

# GOOD
logger.info("user_data", user_id=user.id, has_email=bool(user.email))
```

---

## QA Logging Review Checklist

QA reviewers MUST check these for every code change:

| Check | Pass Criteria |
|-------|---------------|
| **Entry/exit logging** | Every public function has INFO log at entry and exit |
| **Error logging** | Every catch/except block logs error with context |
| **External call logging** | Every API/DB/file call has timing + result logging |
| **No bare prints** | No `print()`, `console.log()` used instead of logger |
| **No sensitive data** | No tokens, passwords, PII in log messages |
| **Structured format** | All logs use key=value or structured JSON, not freeform strings |
| **Appropriate levels** | DEBUG for details, INFO for flow, WARNING for issues, ERROR for failures |
| **Request tracing** | Request-scoped operations have request_id or correlation_id |

### Severity of Missing Logging

| What's Missing | QA Severity |
|----------------|-------------|
| No logging at all in new code | **CRITICAL** |
| Missing error logging in catch blocks | **CRITICAL** |
| Missing logging on external API calls | **IMPORTANT** |
| Missing timing on slow operations | **IMPORTANT** |
| Using print() instead of logger | **IMPORTANT** |
| Missing DEBUG logs for data transformations | **MINOR** |
| Missing request_id propagation | **MINOR** |

---

## Logger Setup Templates

### Python — Quick Setup
```python
# In project root or config module
import logging
import sys

def setup_logging(level: str = "INFO"):
    """Call once at application startup."""
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

# In each module
logger = logging.getLogger(__name__)
```

### Python — Structlog Setup (recommended)
```python
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer(),  # dev
        # structlog.processors.JSONRenderer(),  # production
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)
```

### Node.js — Pino Setup (recommended)
```typescript
import pino from 'pino';

export const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  transport: process.env.NODE_ENV === 'development'
    ? { target: 'pino-pretty' }
    : undefined,
});
```

---

## Integration with Development System

### For Implementers (coder agents)
- Step 3 in coder.md: after writing code, verify logging coverage using the checklist above
- If existing code you're modifying lacks logging → add logging to the functions you touch
- Match the project's existing logging library and patterns

### For QA Reviewers
- Use the QA Logging Review Checklist above during code review
- Missing logging in new code = CRITICAL finding
- Missing error logging in catch blocks = CRITICAL finding

### For Verification
- Logging is part of the quality checklist in verification-before-completion
- "No logging in new functions" = verification FAILS
