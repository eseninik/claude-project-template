#!/usr/bin/env bash
# Prepared judge invocations for the observability DUAL_TEAMS run.
# Fire one per pair once BOTH sides complete.

set -u
mkdir -p work/observability/verdicts

judge_pair() {
  local task_id="$1"
  local spec="work/observability/tasks/${task_id}.md"
  local claude_wt="worktrees/observability/claude/${task_id}"
  local codex_wt="worktrees/observability/codex/${task_id}"
  local out="work/observability/verdicts/${task_id}-verdict.json"

  echo "=== Judging: ${task_id} ==="
  py -3 .claude/scripts/judge.py \
    --task "${spec}" \
    --claude-worktree "${claude_wt}" \
    --codex-worktree "${codex_wt}" \
    --output "${out}" \
    --per-timeout 180 \
    --base HEAD
  echo "--- verdict: ${out} ---"
  cat "${out}" 2>/dev/null | python -m json.tool | head -40 || true
}

case "${1:-all}" in
  T-A) judge_pair "task-T-A-dual-status" ;;
  T-B) judge_pair "task-T-B-codex-health" ;;
  T-C) judge_pair "task-T-C-pipeline-status" ;;
  all)
    judge_pair "task-T-A-dual-status"
    judge_pair "task-T-B-codex-health"
    judge_pair "task-T-C-pipeline-status"
    ;;
  *) echo "usage: $0 [T-A|T-B|T-C|all]"; exit 2 ;;
esac
