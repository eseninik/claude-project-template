---
name: mcp-integration
description: |
  Calls MCP servers on-demand via mcp-cli for external services (search, scraping, documentation).
  Avoids loading tool descriptions into context by invoking mcp-cli through Bash only when needed.
  Activate when the task requires web search, library documentation, web scraping, or external API access.
  Does NOT apply to local file operations, git commands, or standard CLI tools.
---

# MCP Integration (On-Demand)

Call MCP servers via `mcp-cli` through Bash. Each call invokes the server directly instead of loading tool descriptions into context (~2000-6000 tokens per server saved).

## Available Servers

| Server | Purpose | Use When |
|--------|---------|----------|
| perplexity | AI-powered web search | Need current/recent information, technology research |
| context7 | Library documentation with context | Need API docs, code examples for a specific library |
| firecrawl | Web scraping and content extraction | Need to parse a web page or extract structured data |
| ref | Reference/documentation search | Need to search reference materials |
| exa | Semantic web search | Need AI-powered semantic search across the web |

## Workflow: Discover, Inspect, Call

### Step 1: Find the right tool

```bash
# List all servers and tools
mcp-cli

# Search by pattern
mcp-cli grep "*search*"

# Tools for a specific server
mcp-cli info perplexity
```

### Step 2: Inspect schema (parameters)

```bash
# Schema for a specific tool
mcp-cli info perplexity search

# With descriptions
mcp-cli info perplexity -d
```

### Step 3: Call the tool

```bash
# Inline JSON arguments
mcp-cli call perplexity search '{"query": "mcp server best practices"}'

# No arguments
mcp-cli call todoist list_projects

# Via stdin
echo '{"url": "https://example.com"}' | mcp-cli call firecrawl scrape
```

## Examples

### Web search (perplexity)

```bash
mcp-cli call perplexity search '{"query": "latest python 3.13 features 2025"}'
```

### Library docs (context7)

```bash
mcp-cli call context7 search '{"query": "aiogram 3 router setup"}'
```

### Web scraping (firecrawl)

```bash
mcp-cli call firecrawl scrape '{"url": "https://docs.example.com/api"}'
```

### Semantic search (exa)

```bash
mcp-cli call exa search '{"query": "telegram bot architecture best practices", "numResults": 5}'
```

## Platform Notes

| Platform | Mode | Latency |
|----------|------|---------|
| Windows | Direct (no daemon, Unix sockets unavailable) | 2-10s per call |
| Linux/macOS | Daemon (auto-starts, connection pooling) | ~100ms after first call |

Windows direct mode is acceptable for research tasks but not for batch operations.

## Configuration

Config file: `~/.config/mcp/mcp_servers.json`

Format compatible with Claude Desktop. API keys via environment variables:

```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "package-name"],
      "env": {
        "API_KEY": "${ENV_VAR_NAME}"
      }
    }
  }
}
```

Config search order:
1. `MCP_CONFIG_PATH` env var or `-c` flag
2. `./mcp_servers.json` (current directory)
3. `~/.mcp_servers.json`
4. `~/.config/mcp/mcp_servers.json`

## Installation

```bash
# Windows (via Bun)
bun install -g @philschmid/mcp-cli

# Linux
curl -fsSL https://raw.githubusercontent.com/philschmid/mcp-cli/main/install.sh | bash
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `command not found: mcp-cli` | Install: `bun install -g @philschmid/mcp-cli` |
| `Config not found` | Create `~/.config/mcp/mcp_servers.json` |
| `Environment variable not set` | Export the API key: `export VAR_NAME=value` |
| `Connection timeout` | Check internet, try `mcp-cli info server` |
| `Daemon socket error` (Windows) | Expected -- runs in direct mode on Windows |

## Edge Cases

- If mcp-cli is not installed, inform the user and provide installation command
- If a server returns empty results, try rephrasing the query or using a different server
- If config file is missing, guide the user to create it at `~/.config/mcp/mcp_servers.json`

## Related
- ← tasks requiring external data — web search, scraping, docs lookup
- (standalone — no direct skill dependencies)
