#!/usr/bin/env bash
# ao-hybrid.sh — AO (Agent Orchestrator) hybrid spawn workflow helper
# Compatible with Git Bash (msys) on Windows
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SESSIONS_FILE="$PROJECT_ROOT/work/ao-sessions.json"
DEFAULT_PROJECT="claude-project-template-update"

usage() {
  cat <<'USAGE'
ao-hybrid.sh — AO hybrid spawn workflow helper

Usage:
  ao-hybrid.sh spawn   <task-id> <prompt-file> [--project <id>]
  ao-hybrid.sh status  [--project <id>]
  ao-hybrid.sh wait    [--timeout <seconds>]
  ao-hybrid.sh collect <session-id>
  ao-hybrid.sh cleanup [--project <id>]
  ao-hybrid.sh help

Subcommands:
  spawn    Spawn a new AO session for a task and record it
  status   Show status of all tracked sessions
  wait     Block until all sessions reach terminal state
  collect  Print handoff file from a session's worktree
  cleanup  Kill active sessions, run ao cleanup, remove tracking file
  help     Show this help message
USAGE
}

die() { echo "ERROR: $*" >&2; exit 1; }
now_iso() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
has_jq() { command -v jq &>/dev/null; }

get_project() {
  local project="${1:-}"
  if [[ -n "$project" ]]; then echo "$project"; return; fi
  if [[ -f "$SESSIONS_FILE" ]] && has_jq; then
    project=$(jq -r '.project // empty' "$SESSIONS_FILE" 2>/dev/null)
  elif [[ -f "$SESSIONS_FILE" ]]; then
    project=$(grep -o '"project"[[:space:]]*:[[:space:]]*"[^"]*"' "$SESSIONS_FILE" \
      | head -1 | sed 's/.*"project"[[:space:]]*:[[:space:]]*"//' | sed 's/"//')
  fi
  echo "${project:-$DEFAULT_PROJECT}"
}

ensure_sessions_file() {
  if [[ ! -f "$SESSIONS_FILE" ]]; then
    mkdir -p "$(dirname "$SESSIONS_FILE")"
    cat > "$SESSIONS_FILE" <<EOF
{
  "project": "$DEFAULT_PROJECT",
  "created": "$(now_iso)",
  "sessions": []
}
EOF
  fi
}

# --- spawn <task-id> <prompt-file> [--project <id>] ---
cmd_spawn() {
  local task_id="" prompt_file="" project=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --project) project="$2"; shift 2 ;;
      *)
        if [[ -z "$task_id" ]]; then task_id="$1"
        elif [[ -z "$prompt_file" ]]; then prompt_file="$1"
        else die "Unexpected argument: $1"
        fi
        shift ;;
    esac
  done
  [[ -z "$task_id" ]] && die "Missing <task-id>. Usage: ao-hybrid.sh spawn <task-id> <prompt-file>"
  [[ -z "$prompt_file" ]] && die "Missing <prompt-file>. Usage: ao-hybrid.sh spawn <task-id> <prompt-file>"
  [[ ! -f "$prompt_file" ]] && die "Prompt file not found: $prompt_file"

  project=$(get_project "$project")
  ensure_sessions_file

  local output
  output=$(ao spawn "$project" --prompt-file "$prompt_file" 2>&1) || die "ao spawn failed: $output"

  # Extract session id from ao output (e.g. "Session: template-abc123")
  local session_id
  session_id=$(echo "$output" | grep -oiE '[a-z]+-[a-z0-9]{6,}' | head -1)
  [[ -z "$session_id" ]] && session_id=$(echo "$output" | grep -oE '[a-zA-Z0-9_-]{8,}' | tail -1)
  [[ -z "$session_id" ]] && die "Could not parse session ID from ao output: $output"

  local timestamp
  timestamp=$(now_iso)
  if has_jq; then
    local tmp
    tmp=$(jq --arg tid "$task_id" --arg sid "$session_id" --arg ts "$timestamp" \
      '.sessions += [{"task_id": $tid, "session_id": $sid, "status": "spawned", "spawned_at": $ts}]' \
      "$SESSIONS_FILE")
    echo "$tmp" > "$SESSIONS_FILE"
  else
    local entry="{\"task_id\": \"$task_id\", \"session_id\": \"$session_id\", \"status\": \"spawned\", \"spawned_at\": \"$timestamp\"}"
    if grep -q '"sessions": \[\]' "$SESSIONS_FILE"; then
      sed -i "s|\"sessions\": \[\]|\"sessions\": [$entry]|" "$SESSIONS_FILE"
    else
      sed -i "s|\(.*\)\]$|\1, $entry]|" "$SESSIONS_FILE"
    fi
  fi
  echo "Spawned session $session_id for task $task_id"
}

# --- status [--project <id>] ---
cmd_status() {
  local project=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --project) project="$2"; shift 2 ;;
      *) die "Unknown option: $1" ;;
    esac
  done
  project=$(get_project "$project")

  echo "=== AO Sessions (project: $project) ==="
  echo ""
  local output
  output=$(ao session ls 2>&1) || die "ao session ls failed: $output"
  echo "$output"
  echo ""

  # Match actual session status lines with bracketed status indicators [running], [idle], etc.
  # NOT prose like "(no active sessions)" which contains the word "active"
  local total active done_count failed
  total=$(echo "$output" | grep -cE '\[(spawning|running|idle|done|exited|killed|terminated|failed)\]' || true)
  active=$(echo "$output" | grep -cE '\[(spawning|running|idle)\]' || true)
  done_count=$(echo "$output" | grep -cE '\[(done|exited|killed|terminated)\]' || true)
  failed=$(echo "$output" | grep -cE '\[failed\]' || true)
  echo "--- Summary ---"
  echo "Total: $total | Active: $active | Done: $done_count | Failed: $failed"
}

# --- wait [--timeout <seconds>] ---
cmd_wait() {
  local timeout=3600
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --timeout) timeout="$2"; shift 2 ;;
      *) die "Unknown option: $1" ;;
    esac
  done

  local elapsed=0 poll_interval=30
  echo "Waiting for all sessions to reach terminal state (timeout: ${timeout}s)..."
  while (( elapsed < timeout )); do
    local output
    output=$(ao session ls 2>&1) || true
    local active_count
    active_count=$(echo "$output" | grep -cE '\[(spawning|running|idle)\]' || true)
    if (( active_count == 0 )); then
      echo ""
      echo "All sessions completed. (elapsed: ${elapsed}s)"
      exit 0
    fi
    echo "[${elapsed}s] $active_count session(s) still active..."
    sleep "$poll_interval"
    (( elapsed += poll_interval ))
  done
  echo ""
  echo "TIMEOUT: $timeout seconds elapsed with sessions still active."
  exit 1
}

# --- collect <session-id> ---
cmd_collect() {
  local session_id="${1:-}"
  [[ -z "$session_id" ]] && die "Missing <session-id>. Usage: ao-hybrid.sh collect <session-id>"

  local output
  output=$(ao session ls 2>&1) || die "ao session ls failed: $output"

  # Try to extract worktree path from session listing
  local worktree
  worktree=$(echo "$output" | grep "$session_id" | grep -oE '/[^ ]+' | head -1)
  [[ -z "$worktree" ]] && worktree="$PROJECT_ROOT/.claude/worktrees/$session_id"

  local handoff_file="$worktree/work/ao-results/$session_id.md"
  if [[ -f "$handoff_file" ]]; then
    echo "=== Handoff from session $session_id ==="
    cat "$handoff_file"
  else
    die "Handoff file not found: $handoff_file"
  fi
}

# --- cleanup [--project <id>] ---
cmd_cleanup() {
  local project=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --project) project="$2"; shift 2 ;;
      *) die "Unknown option: $1" ;;
    esac
  done
  project=$(get_project "$project")
  echo "Cleaning up sessions for project: $project"

  local output
  output=$(ao session ls 2>&1) || true
  local killed=0
  while IFS= read -r line; do
    if echo "$line" | grep -qE '\[(spawning|running|idle)\]'; then
      local sid
      sid=$(echo "$line" | grep -oE '[a-z]+-[a-z0-9]{6,}' | head -1)
      if [[ -n "$sid" ]]; then
        echo "Killing session: $sid"
        ao session kill "$sid" 2>/dev/null || true
        (( killed++ ))
      fi
    fi
  done <<< "$output"

  echo "Running ao session cleanup..."
  ao session cleanup 2>/dev/null || true
  if [[ -f "$SESSIONS_FILE" ]]; then
    rm -f "$SESSIONS_FILE"
    echo "Removed $SESSIONS_FILE"
  fi
  echo ""
  echo "Cleanup complete. Killed $killed active session(s)."
}

# --- Main dispatch ---
main() {
  local cmd="${1:-help}"
  shift || true
  case "$cmd" in
    spawn)   cmd_spawn "$@" ;;
    status)  cmd_status "$@" ;;
    wait)    cmd_wait "$@" ;;
    collect) cmd_collect "$@" ;;
    cleanup) cmd_cleanup "$@" ;;
    help|-h|--help) usage ;;
    *) die "Unknown command: $cmd. Run 'ao-hybrid.sh help' for usage." ;;
  esac
}

main "$@"
