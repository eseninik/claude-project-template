# Language Rule Packs

Formalized coding standards per language. Agents reference these when working with specific languages.

## Available Languages

| Language | File | Key Tools |
|----------|------|-----------|
| [Python](python.md) | `python.md` | ruff, black, mypy, pytest |
| [TypeScript](typescript.md) | `typescript.md` | ESLint, Prettier, vitest, Playwright |
| [Go](go.md) | `go.md` | gofmt, golangci-lint, testing |
| [Rust](rust.md) | `rust.md` | rustfmt, clippy, cargo test |

## How to Use

Load via `cat .claude/guides/language-rules/{language}.md` when working with that language.

## Source

Adapted from [everything-claude-code](https://github.com/affaan-m/everything-claude-code) rule packs + our coding standards.
