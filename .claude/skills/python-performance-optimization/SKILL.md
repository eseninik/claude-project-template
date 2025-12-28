---
name: python-performance-optimization
version: 1.0.0
description: Use when code is slow, needs profiling, or requires optimization - covers profiling tools, common bottlenecks, async optimization, memory management, and database query optimization
---

# Python Performance Optimization

## Overview

Premature optimization is the root of all evil, but ignorant optimization is worse. This skill covers how to measure, identify, and fix actual performance problems.

**Core principle:** Measure first. Optimize what matters. Verify improvement.

## When to Use

**Use for:**
- Response time too slow
- High memory usage
- Database queries taking too long
- Bot handlers timing out
- Need to handle more concurrent users

**Do NOT use for:**
- Code that works fine (premature optimization)
- "It might be slow someday"
- Making code "cleaner" (that's refactoring)

## The Optimization Process

```
NEVER SKIP STEPS:

1. MEASURE current performance (get baseline)
2. IDENTIFY the bottleneck (profile, don't guess)
3. OPTIMIZE only the bottleneck
4. VERIFY improvement (compare to baseline)
5. REPEAT if still slow

Skipping to step 3? That's guessing. Stop.
```

## Profiling Tools

### cProfile — CPU Time

```python
import cProfile
import pstats

# Profile a function
cProfile.run('my_function()', 'output.prof')

# Analyze results
stats = pstats.Stats('output.prof')
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

### line_profiler — Line by Line

```bash
pip install line_profiler
```

```python
# Add decorator to function
@profile
def slow_function():
    result = []
    for i in range(10000):      # Line 4: 0.001s
        result.append(i ** 2)    # Line 5: 0.234s  <-- BOTTLENECK
    return sum(result)           # Line 6: 0.002s
```

```bash
kernprof -l -v script.py
```

### memory_profiler — Memory Usage

```bash
pip install memory_profiler
```

```python
from memory_profiler import profile

@profile
def memory_hungry():
    data = [i for i in range(1000000)]  # +38.1 MiB
    return sum(data)
```

### py-spy — Production Profiling

```bash
pip install py-spy

# Profile running process
py-spy top --pid 12345

# Generate flame graph
py-spy record -o profile.svg --pid 12345
```

## Common Bottlenecks & Fixes

### 1. String Concatenation

```python
# ❌ SLOW: O(n²) - creates new string each time
result = ""
for item in items:
    result += str(item)

# ✅ FAST: O(n) - joins once at the end
result = "".join(str(item) for item in items)
```

### 2. List Operations

```python
# ❌ SLOW: O(n) for each insert at beginning
for item in items:
    result.insert(0, item)

# ✅ FAST: O(1) for each append, then reverse
result = []
for item in items:
    result.append(item)
result.reverse()

# ✅ BETTER: Use deque for frequent insert/pop at both ends
from collections import deque
result = deque()
result.appendleft(item)  # O(1)
```

### 3. Dictionary Lookups in Loops

```python
# ❌ SLOW: Repeated attribute lookup
for item in items:
    result.append(some_dict.get(item.key))

# ✅ FAST: Cache the method
dict_get = some_dict.get
for item in items:
    result.append(dict_get(item.key))
```

### 4. Unnecessary Object Creation

```python
# ❌ SLOW: Creates new list each iteration
for i in range(1000):
    temp = [x for x in data if x > threshold]
    process(temp)

# ✅ FAST: Use generator (lazy evaluation)
for i in range(1000):
    temp = (x for x in data if x > threshold)
    process(temp)
```

### 5. Global Variable Access

```python
# ❌ SLOW: Global lookup each time
MULTIPLIER = 2

def calculate(values):
    return [v * MULTIPLIER for v in values]

# ✅ FAST: Local variable (cached)
def calculate(values, multiplier=MULTIPLIER):
    return [v * multiplier for v in values]
```

## Async Optimization (for aiogram)

### 1. Concurrent I/O

```python
# ❌ SLOW: Sequential requests
async def get_user_data(user_id: int):
    profile = await api.get_profile(user_id)      # 100ms
    orders = await api.get_orders(user_id)        # 150ms
    balance = await api.get_balance(user_id)      # 80ms
    return profile, orders, balance               # Total: 330ms

# ✅ FAST: Concurrent requests
async def get_user_data(user_id: int):
    profile, orders, balance = await asyncio.gather(
        api.get_profile(user_id),
        api.get_orders(user_id),
        api.get_balance(user_id),
    )
    return profile, orders, balance               # Total: 150ms (max)
```

### 2. Connection Pooling

```python
# ❌ SLOW: New connection per request
async def fetch_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# ✅ FAST: Reuse session (connection pool)
class ApiClient:
    def __init__(self):
        self._session: aiohttp.ClientSession | None = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=100)
            self._session = aiohttp.ClientSession(connector=connector)
        return self._session
    
    async def fetch_data(self, url: str):
        session = await self.get_session()
        async with session.get(url) as response:
            return await response.json()
```

### 3. Semaphore for Rate Limiting

```python
# ❌ BAD: Overwhelm external API
async def fetch_all(urls: list[str]):
    return await asyncio.gather(*[fetch(url) for url in urls])

# ✅ GOOD: Limit concurrent requests
async def fetch_all(urls: list[str], max_concurrent: int = 10):
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def fetch_limited(url: str):
        async with semaphore:
            return await fetch(url)
    
    return await asyncio.gather(*[fetch_limited(url) for url in urls])
```

## Database Optimization

### 1. N+1 Query Problem

```python
# ❌ SLOW: N+1 queries
users = await db.execute(select(User))  # 1 query
for user in users:
    orders = await db.execute(
        select(Order).where(Order.user_id == user.id)
    )  # N queries

# ✅ FAST: Join or eager loading
from sqlalchemy.orm import selectinload

users = await db.execute(
    select(User).options(selectinload(User.orders))
)  # 2 queries total
```

### 2. Index Missing

```python
# ❌ SLOW: Full table scan
await db.execute(
    select(User).where(User.telegram_id == 123456)
)

# ✅ FAST: Add index
class User(Base):
    telegram_id: Mapped[int] = mapped_column(index=True)  # Index!
```

### 3. Select Only Needed Columns

```python
# ❌ SLOW: Fetches all columns
users = await db.execute(select(User))

# ✅ FAST: Fetch only needed columns
users = await db.execute(
    select(User.id, User.name, User.telegram_id)
)
```

### 4. Batch Operations

```python
# ❌ SLOW: Insert one by one
for user_data in users_data:
    user = User(**user_data)
    db.add(user)
    await db.commit()  # Commits 1000 times!

# ✅ FAST: Bulk insert
db.add_all([User(**data) for data in users_data])
await db.commit()  # Single commit
```

## Memory Optimization

### 1. Generators Instead of Lists

```python
# ❌ HIGH MEMORY: Creates full list in memory
def get_all_users():
    return [process(user) for user in fetch_million_users()]

# ✅ LOW MEMORY: Yields one at a time
def get_all_users():
    for user in fetch_million_users():
        yield process(user)
```

### 2. __slots__ for Many Objects

```python
# ❌ HIGH MEMORY: Dict per instance (~300 bytes overhead)
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

# ✅ LOW MEMORY: Fixed attributes (~50 bytes overhead)
class Point:
    __slots__ = ['x', 'y']
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
```

### 3. Delete Large Objects

```python
# Process large data
large_data = load_huge_file()
result = process(large_data)

# Free memory immediately
del large_data
gc.collect()  # Force garbage collection if needed
```

## Caching

### 1. functools.lru_cache

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_computation(n: int) -> int:
    # Called once per unique n
    return sum(i ** 2 for i in range(n))
```

### 2. Async Caching

```python
from aiocache import cached, Cache

@cached(ttl=300, cache=Cache.MEMORY)  # 5 min TTL
async def get_user_profile(user_id: int):
    return await api.fetch_profile(user_id)
```

### 3. Redis for Distributed Cache

```python
from redis.asyncio import Redis

redis = Redis.from_url("redis://localhost")

async def get_cached_data(key: str):
    cached = await redis.get(key)
    if cached:
        return json.loads(cached)
    
    data = await fetch_expensive_data()
    await redis.setex(key, 300, json.dumps(data))  # 5 min TTL
    return data
```

## Quick Wins Checklist

Before deep optimization, check these:

- [ ] Using `__slots__` for data classes with many instances?
- [ ] Database queries have proper indexes?
- [ ] Using `asyncio.gather()` for parallel I/O?
- [ ] Connection pooling enabled?
- [ ] Caching frequently accessed data?
- [ ] Using generators for large datasets?
- [ ] Avoiding N+1 queries?
- [ ] String concatenation using `join()`?

## Verification Template

```markdown
## Performance Optimization Report

**Problem:** [What was slow]
**Baseline:** [Measured time/memory before]

**Bottleneck:** [What profiler showed]
**Solution:** [What was changed]

**Result:** [Measured time/memory after]
**Improvement:** [X% faster / Y% less memory]
```

## Integration with Other Skills

- **async-python-patterns**: Proper async before optimizing async
- **python-testing-patterns**: Benchmark tests to prevent regression
- **systematic-debugging**: Find performance bugs systematically
