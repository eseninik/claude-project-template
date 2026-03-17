# Coder Agent Memory

> Persistent memory for coder agents. First 200 lines auto-injected at startup.

## Patterns That Work

- Always add structured logging (entry/exit/error) per logging-standards.md
- Run verification-before-completion before claiming done
- Check existing code patterns before implementing new ones

## Patterns That Fail

- Skipping tests after code changes
- Bare print()/console.log() instead of structured logging
- Hardcoded values (URLs, paths, credentials)

## Project-Specific Knowledge

- Python projects use uv for package management
- Test framework: pytest + AsyncMock
- Follow Clean Architecture patterns

## Recent History

| Date | Task | Outcome | Learning |
|------|------|---------|----------|
