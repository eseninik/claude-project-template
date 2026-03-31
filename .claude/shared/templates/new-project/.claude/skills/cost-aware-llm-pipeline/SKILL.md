---
name: cost-aware-llm-pipeline
description: Cost optimization patterns for LLM API usage — model routing by complexity, budget tracking, prompt caching, retry logic. Use when building apps that call LLM APIs. Do NOT use for non-LLM API integrations.
roles: [coder, coder-complex, experimenter]
---

# Cost-Aware LLM Pipeline

## When to Activate

- Building applications that call LLM APIs (Claude, GPT, etc.)
- Processing batches with varying complexity
- Need to stay within API budget
- Optimizing cost without sacrificing quality

## Model Routing by Complexity

```python
def select_model(text_length: int, item_count: int) -> str:
    """Route to cheaper model for simple tasks."""
    if text_length >= 10_000 or item_count >= 30:
        return "claude-sonnet-4-6"   # Complex
    return "claude-haiku-4-5-20251001"  # Simple (3-4x cheaper)
```

## Cost Tracking (Immutable)

```python
@dataclass(frozen=True)
class CostTracker:
    input_tokens: int = 0
    output_tokens: int = 0
    requests: int = 0

    @property
    def total_cost(self) -> float:
        return (self.input_tokens * 0.003 + self.output_tokens * 0.015) / 1000

    def add(self, inp: int, out: int) -> "CostTracker":
        return CostTracker(
            self.input_tokens + inp,
            self.output_tokens + out,
            self.requests + 1,
        )

    def check_budget(self, budget: float) -> bool:
        return self.total_cost <= budget
```

## Prompt Caching

```python
# Use system prompt caching (Claude supports this natively)
# Put static instructions in system prompt, dynamic content in user message
# Cache hit = 90% discount on input tokens

system_prompt = "..."  # Static — cached across requests
user_message = f"Process: {dynamic_data}"  # Dynamic — not cached
```

## Retry with Exponential Backoff

```python
async def call_with_retry(fn, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await fn()
        except RateLimitError:
            wait = 2 ** attempt
            await asyncio.sleep(wait)
    raise MaxRetriesExceeded()
```

## Batch Processing

```python
# Process items in chunks, track cost per chunk
async def process_batch(items, budget=10.0):
    tracker = CostTracker()
    for chunk in chunked(items, size=10):
        if not tracker.check_budget(budget):
            logger.warning("Budget exceeded: $%.2f", tracker.total_cost)
            break
        model = select_model(sum(len(i) for i in chunk), len(chunk))
        result, usage = await process_chunk(chunk, model)
        tracker = tracker.add(usage.input_tokens, usage.output_tokens)
    return results, tracker
```

## Key Rules

1. **Always track cost** — log tokens per request
2. **Route by complexity** — don't use Opus for simple tasks
3. **Cache system prompts** — 90% savings on repeated calls
4. **Set budget limits** — abort gracefully, don't surprise-charge
5. **Batch wisely** — fewer large requests > many small ones

## Related

- [backend-patterns](./../backend-patterns/SKILL.md) — repository/service layers and DB optimization
- [experiment-loop](~/.claude/skills/experiment-loop/SKILL.md) — iterative optimization with quantifiable metrics
