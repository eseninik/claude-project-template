#!/bin/bash
# Ralph Loop v2 — Fresh context per pipeline phase
# Eliminates compaction by giving each phase a clean 200K context
#
# Usage:
#   ./scripts/ralph.sh
#   ./scripts/ralph.sh --max-iterations 10
#   ./scripts/ralph.sh --pipeline work/PIPELINE.md --prompt work/PROMPT.md
#   ./scripts/ralph.sh --dry-run

set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────
MAX_ITERATIONS=20
PIPELINE_FILE="work/PIPELINE.md"
PROMPT_FILE="work/PROMPT.md"
DRY_RUN=false
MODEL_FLAG=""

# ── Parse arguments ───────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case $1 in
    --max-iterations) MAX_ITERATIONS="$2"; shift 2 ;;
    --pipeline)       PIPELINE_FILE="$2";  shift 2 ;;
    --prompt)         PROMPT_FILE="$2";    shift 2 ;;
    --model)          MODEL_FLAG="--model $2"; shift 2 ;;
    --dry-run)        DRY_RUN=true;        shift ;;
    -h|--help)
      echo "Usage: ralph.sh [--max-iterations N] [--pipeline FILE] [--prompt FILE] [--model MODEL] [--dry-run]"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 3 ;;
  esac
done

# ── Validate inputs ──────────────────────────────────────────
if [ ! -f "$PIPELINE_FILE" ]; then
  echo "ERROR: Pipeline file not found: $PIPELINE_FILE"
  exit 3
fi

if [ ! -f "$PROMPT_FILE" ]; then
  echo "ERROR: Prompt file not found: $PROMPT_FILE"
  exit 3
fi

echo "╔══════════════════════════════════════════╗"
echo "║         Ralph Loop v2 Starting           ║"
echo "╠══════════════════════════════════════════╣"
echo "║ Pipeline:  $PIPELINE_FILE"
echo "║ Prompt:    $PROMPT_FILE"
echo "║ Max iter:  $MAX_ITERATIONS"
echo "║ Dry run:   $DRY_RUN"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── Main loop ────────────────────────────────────────────────
for i in $(seq 1 "$MAX_ITERATIONS"); do
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "[Iteration $i/$MAX_ITERATIONS] Checking pipeline status..."

  # Check for completion
  if grep -q "PIPELINE_COMPLETE" "$PIPELINE_FILE"; then
    echo ""
    echo "Pipeline COMPLETE after $((i - 1)) iterations."
    exit 0
  fi

  # Check for blocked state
  if grep -q "Status: BLOCKED" "$PIPELINE_FILE"; then
    echo ""
    echo "Pipeline BLOCKED. Check $PIPELINE_FILE for details."
    exit 1
  fi

  # Extract current phase name for logging
  CURRENT_PHASE=$(grep -oP '(?<=Phase \d+: ).*?(?= <-\s*CURRENT)' "$PIPELINE_FILE" 2>/dev/null || echo "unknown")
  echo "[Iteration $i] Current phase: $CURRENT_PHASE"

  if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] Would execute: claude -p \"\$(cat $PROMPT_FILE)\" --dangerously-skip-permissions $MODEL_FLAG"
    echo "[DRY RUN] Skipping..."
    continue
  fi

  # Execute one phase with fresh context
  echo "[Iteration $i] Spawning fresh claude -p process..."
  set +e
  # shellcheck disable=SC2086
  claude -p "$(cat "$PROMPT_FILE")" --dangerously-skip-permissions $MODEL_FLAG
  EXIT_CODE=$?
  set -e

  if [ $EXIT_CODE -ne 0 ]; then
    echo "[Iteration $i] WARNING: claude -p exited with code $EXIT_CODE"
    echo "Continuing to next iteration (agent may have partially updated state)..."
  fi

  # Git checkpoint
  echo "[Iteration $i] Creating git checkpoint..."
  git add -A
  git commit -m "pipeline: checkpoint iteration $i — phase: $CURRENT_PHASE" --allow-empty
  git tag -f "pipeline-iter-$i"

  echo "[Iteration $i] Checkpoint created: pipeline-iter-$i"
  echo ""
done

echo ""
echo "Max iterations ($MAX_ITERATIONS) reached without pipeline completion."
echo "Check $PIPELINE_FILE for current state."
exit 2
