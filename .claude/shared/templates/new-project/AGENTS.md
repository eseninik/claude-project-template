# AGENTS.md — Project Instructions

> Universal agent context. Read by Codex CLI, Gemini CLI, GitHub Copilot, and other tools.
> Claude Code reads CLAUDE.md which references this file via @AGENTS.md.

## Project

- **Name:** [PROJECT_NAME]
- **Description:** [ONE SENTENCE]
- **Tech Stack:** [Python/Node.js, frameworks, databases]

## Quick Commands

- Install: `[package manager] install`
- Test: `[test command]`
- Lint: `[lint command]`
- Format: `[format command]`
- Typecheck: `[typecheck command]`

## Architecture

- `src/` — source code
- `tests/` — test files
- `docs/` — documentation

### Guardrails

- [Add project-specific architecture rules here]

## Testing Policy

- New behavior requires at least one test (unit or integration)
- Bugfixes require a regression test that fails before the fix
- Tests are IMMUTABLE after approval (Evaluation Firewall)
- Target coverage: [X]%

## Code Review Rubric

Classify findings as:
- **BLOCKER:** Correctness, security, data loss, failing tests, broken API contract
- **IMPORTANT:** Missing tests for new behavior, risky edge cases, performance regressions, missing logging
- **NIT:** Style/readability improvements that materially improve maintainability

When raising a finding:
- Cite file path + line range
- Provide a concrete suggested fix or failing test to add

## Security & Data Handling

- Never hardcode secrets — use environment variables
- Never log sensitive data (passwords, tokens, PII)
- Validate all external inputs
- No network calls during tests unless explicitly mocked

## Cross-Model Verification

Instructions for verifying agents (Codex CLI, Gemini CLI):
1. Run in `read-only` sandbox mode — never modify files during review
2. Focus on: correctness, security, performance, test coverage, logging
3. Use structured JSON output when `--output-schema` is provided
4. Classify findings using the rubric above (BLOCKER/IMPORTANT/NIT)
5. If unsure about a finding, mark confidence < 0.5

## Conventions

- [Add language/framework-specific conventions here]
- Structured logging required (no bare print/console.log)
- Error handling at system boundaries
