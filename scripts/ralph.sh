#!/bin/bash
# Ralph Loop — Fresh-context autonomous pipeline executor
# Usage: ./scripts/ralph.sh [--max-iterations N] [--prompt FILE] [--pipeline FILE]
#
# Spawns fresh `claude -p` processes per pipeline phase.
# Each iteration reads PIPELINE.md, executes current phase, then exits.
# Ralph Loop detects completion or spawns next iteration.

set -euo pipefail

# --- Defaults ---
MAX_ITERATIONS=20
PROMPT_FILE="work/PROMPT.md"
PIPELINE_FILE="work/PIPELINE.md"

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# --- Parse args ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --max-iterations)
      MAX_ITERATIONS="$2"
      shift 2
      ;;
    --prompt)
      PROMPT_FILE="$2"
      shift 2
      ;;
    --pipeline)
      PIPELINE_FILE="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: ./scripts/ralph.sh [--max-iterations N] [--prompt FILE] [--pipeline FILE]"
      echo ""
      echo "Options:"
      echo "  --max-iterations N   Maximum loop iterations (default: 20)"
      echo "  --prompt FILE        Prompt file for claude -p (default: work/PROMPT.md)"
      echo "  --pipeline FILE      Pipeline state file (default: work/PIPELINE.md)"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${RESET}"
      exit 1
      ;;
  esac
done

# --- Validate files ---
if [[ ! -f "$PROMPT_FILE" ]]; then
  echo -e "${RED}Error: Prompt file not found: ${PROMPT_FILE}${RESET}"
  echo "Create it from template: cp .claude/shared/work-templates/PROMPT.md ${PROMPT_FILE}"
  exit 1
fi

if [[ ! -f "$PIPELINE_FILE" ]]; then
  echo -e "${RED}Error: Pipeline file not found: ${PIPELINE_FILE}${RESET}"
  echo "Create it from template: cp .claude/shared/work-templates/PIPELINE.md ${PIPELINE_FILE}"
  exit 1
fi

# --- Main loop ---
echo -e "${BOLD}${CYAN}=== Ralph Loop Started ===${RESET}"
echo -e "Pipeline: ${PIPELINE_FILE}"
echo -e "Prompt:   ${PROMPT_FILE}"
echo -e "Max iterations: ${MAX_ITERATIONS}"
echo ""

for ((i=1; i<=MAX_ITERATIONS; i++)); do
  # Check for completion before each iteration
  if grep -q "PIPELINE_COMPLETE" "$PIPELINE_FILE" 2>/dev/null; then
    echo -e "${GREEN}${BOLD}=== Pipeline Complete! ===${RESET}"
    echo -e "Finished after $((i-1)) iteration(s)."
    exit 0
  fi

  # Extract current phase info
  CURRENT_PHASE=$(grep -n "<- CURRENT" "$PIPELINE_FILE" 2>/dev/null | head -1 || true)
  if [[ -z "$CURRENT_PHASE" ]]; then
    echo -e "${YELLOW}Warning: No <- CURRENT marker found in ${PIPELINE_FILE}${RESET}"
    echo -e "Pipeline may be complete or misconfigured."
    exit 1
  fi

  PHASE_NAME=$(echo "$CURRENT_PHASE" | sed 's/^[0-9]*://' | sed 's/<- CURRENT//' | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')

  echo -e "${BOLD}${CYAN}--- Iteration ${i}/${MAX_ITERATIONS} ---${RESET}"
  echo -e "Current phase: ${YELLOW}${PHASE_NAME}${RESET}"
  echo ""

  # Read prompt content
  PROMPT_CONTENT=$(cat "$PROMPT_FILE")

  # Spawn fresh claude process
  echo -e "Spawning claude -p ..."
  if claude -p "$PROMPT_CONTENT" --verbose; then
    echo -e "${GREEN}Claude exited successfully.${RESET}"
  else
    EXIT_CODE=$?
    echo -e "${RED}Claude exited with code ${EXIT_CODE}.${RESET}"

    # Check if pipeline was marked BLOCKED
    if grep -q "BLOCKED" "$PIPELINE_FILE" 2>/dev/null; then
      echo -e "${RED}${BOLD}Pipeline phase is BLOCKED. Manual intervention required.${RESET}"
      exit 1
    fi

    echo -e "${YELLOW}Retrying on next iteration...${RESET}"
  fi

  # Git checkpoint between phases
  if git diff --quiet 2>/dev/null && git diff --cached --quiet 2>/dev/null; then
    echo -e "${YELLOW}No changes to commit.${RESET}"
  else
    echo -e "Creating git checkpoint..."
    git add -A
    git commit -m "ralph: checkpoint after iteration ${i} — ${PHASE_NAME}" || true
  fi

  echo ""
done

echo -e "${RED}${BOLD}=== Max iterations (${MAX_ITERATIONS}) reached ===${RESET}"
echo -e "Pipeline did not complete. Check ${PIPELINE_FILE} for state."
exit 1
