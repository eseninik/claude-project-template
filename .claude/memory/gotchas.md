# Project Gotchas

> Known pitfalls and warnings. Auto-updated after each session.
> Format: one bullet per gotcha. Duplicates are removed automatically.

---

## Environment Gotchas
<!-- OS-specific, tooling issues -->

### OpenRouter requires HTTP-Referer header (2026-02-19)
- OpenRouter API returns 401 "User not found" if requests lack `HTTP-Referer` header
- Symptom: Graphiti search/add_memory fails with 401, but API key is valid on dashboard
- Root cause: graphiti_core's AsyncOpenAI client doesn't send custom headers
- Fix: patch factories.py to create AsyncOpenAI with `default_headers={"HTTP-Referer": "http://localhost:8000", "X-Title": "Graphiti MCP"}`
- File: `~/graphiti/mcp_server/src/services/factories.py` (mounted as Docker volume)
- After patching: restart container with `docker compose -f docker-compose-falkordb.yml restart graphiti-mcp`

### Docker Desktop on Windows (Auto-Generated)
- Docker Desktop on Windows may hang on "Starting Engine" -- fix: `wsl --shutdown` + restart
- Verified: 2026-02-18

## Code Gotchas
<!-- Non-obvious behaviors, tricky APIs, common mistakes -->

## Build/Deploy Gotchas
<!-- CI/CD quirks, deployment issues -->
