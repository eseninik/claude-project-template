# Priority Ladder

> Conflict resolution framework for competing priorities.
> Higher level ALWAYS wins when priorities conflict.

---

## The Ladder

```
1. SAFETY      — Data loss, harm, irreversible damage?
2. CORRECTNESS — Wrong results, broken logic?
3. SECURITY    — Exploitable? Data leak? Unauthorized access?
4. RELIABILITY — Fails under load? Crashes? Timeouts?
5. SIMPLICITY  — Unnecessarily complex? Hard to maintain?
6. COST        — Expensive to run/maintain/scale?
7. ELEGANCE    — More beautiful solution exists?
```

---

## Resolution Rule

**Higher level wins. Always. No exceptions.**

When two priorities conflict:
1. Identify which level each belongs to
2. The higher-level concern takes precedence
3. Document the trade-off in expert-analysis.md or ADR

### Examples

| Conflict | Winner | Reasoning |
|----------|--------|-----------|
| "Elegant code" vs "Simple code" | SIMPLICITY (5) | Simplicity > Elegance (7) |
| "Fast delivery" vs "Secure code" | SECURITY (3) | Security > Cost (6) |
| "Complex but correct" vs "Simple but approximate" | CORRECTNESS (2) | Correctness > Simplicity (5) |
| "Safe but slow" vs "Fast but risky" | SAFETY (1) | Safety > Reliability (4) |
| "Reliable but complex" vs "Simple but fragile" | RELIABILITY (4) | Reliability > Simplicity (5) |

---

## Tradeoff Matrix Template

Use when comparing approaches in expert panel analysis.

```markdown
| Criterion        | Option A         | Option B         | Option C         |
|------------------|------------------|------------------|------------------|
| SAFETY           | [Low/Med/High]   | [Low/Med/High]   | [Low/Med/High]   |
| CORRECTNESS      | [Low/Med/High]   | [Low/Med/High]   | [Low/Med/High]   |
| SECURITY         | [Low/Med/High]   | [Low/Med/High]   | [Low/Med/High]   |
| RELIABILITY      | [Low/Med/High]   | [Low/Med/High]   | [Low/Med/High]   |
| SIMPLICITY       | [Low/Med/High]   | [Low/Med/High]   | [Low/Med/High]   |
| COST             | [Low/Med/High]   | [Low/Med/High]   | [Low/Med/High]   |
| ELEGANCE         | [Low/Med/High]   | [Low/Med/High]   | [Low/Med/High]   |
| **Verdict**      |                  |                  |                  |
```

Fill Low/Med/High for each. The option that wins on the HIGHEST differing level is the winner.

---

## Failure Mode Table Template

Use when assessing risks in expert panel analysis.

```markdown
| Failure Mode         | Probability | Impact (Ladder Level) | Mitigation          |
|----------------------|-------------|----------------------|---------------------|
| [What can go wrong]  | Low/Med/High| SAFETY/CORRECTNESS/… | [How to prevent]    |
```

Sort by Impact level (highest first), then by Probability (highest first).

---

## When to Use

- Expert Panel: debates between experts with different perspectives
- Architecture decisions: choosing between competing approaches
- Code review: resolving disagreements about implementation
- Any situation where two valid approaches conflict

## Anti-Patterns

- Overriding higher level for lower ("but it's more elegant!") — NEVER
- Treating all levels as equal weight — they are NOT equal
- Skipping levels ("it's safe, so skip to simplicity") — evaluate ALL levels
- Using ladder for non-conflicting decisions — only for conflicts
