#!/usr/bin/env bash
# Codex cross-model review — runs on Stop hook
# Blocks Claude completion if BLOCKER issues found
set -euo pipefail

# Read hook input from stdin
payload="$(cat)"

# Guard: prevent infinite loop
stop_hook_active="$(echo "$payload" | jq -r '.stop_hook_active // false')"
if [[ "$stop_hook_active" == "true" ]]; then
  exit 0
fi

# Check if codex is installed
if ! command -v codex &>/dev/null; then
  echo "codex CLI not installed, skipping cross-model review" >&2
  exit 0
fi

project_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}"
schema="$project_dir/.codex/review-schema.json"
out_dir="$project_dir/.codex/reviews"
mkdir -p "$out_dir"

# Skip if no schema configured
if [[ ! -f "$schema" ]]; then
  exit 0
fi

# Risk classifier: skip trivial changes
changed_files="$(git diff --name-only HEAD 2>/dev/null || git diff --name-only 2>/dev/null || echo "")"
if [[ -z "$changed_files" ]]; then
  exit 0
fi

# Check if only low-risk files changed
high_risk=false
while IFS= read -r file; do
  case "$file" in
    *.md|*.css|*.json|*.txt|*.yml|*.yaml|*.toml|*.cfg|*.ini|*.gitignore)
      ;; # low risk, skip
    *auth*|*payment*|*migration*|*security*|*crypto*|*token*|*secret*)
      high_risk=true
      break
      ;;
    *.py|*.js|*.ts|*.tsx|*.jsx|*.go|*.rs|*.java|*.rb)
      high_risk=true
      break
      ;;
    *)
      high_risk=true
      break
      ;;
  esac
done <<< "$changed_files"

if [[ "$high_risk" == "false" ]]; then
  exit 0
fi

ts="$(date +%Y%m%d-%H%M%S)"
out_file="$out_dir/review-$ts.json"
latest="$out_dir/latest.json"

# Run Codex review in read-only mode
set +e
codex exec \
  "Review the current working tree changes. Focus on correctness, security, performance, and missing tests. Use AGENTS.md rubric if present. Return JSON matching the schema." \
  --sandbox read-only \
  --ask-for-approval never \
  --output-schema "$schema" \
  -o "$out_file" \
  2>/tmp/codex-review-stderr.log
status=$?
set -e

# If Codex failed (network, auth, rate limit), don't block Claude
if [[ $status -ne 0 ]]; then
  echo "Codex review failed (exit $status), skipping gate" >&2
  exit 0
fi

cp -f "$out_file" "$latest"

# Check for blockers
has_blockers="$(jq -r '.summary.has_blockers // false' "$out_file" 2>/dev/null || echo "false")"
if [[ "$has_blockers" == "true" ]]; then
  blocker_count="$(jq '[.findings[] | select(.severity=="BLOCKER")] | length' "$out_file" 2>/dev/null || echo "0")"
  blocker_details="$(jq -r '.findings[] | select(.severity=="BLOCKER") | "  - [\(.location.path):\(.location.line_start)] \(.title): \(.explanation)"' "$out_file" 2>/dev/null || echo "  (details unavailable)")"

  # Output JSON to block stop
  jq -n \
    --arg reason "Codex cross-model review found $blocker_count BLOCKER issue(s). Read .codex/reviews/latest.json, fix blockers, re-run review.
$blocker_details" \
    '{ "decision": "block", "reason": $reason }'
  exit 0
fi

# No blockers — let Claude finish
verdict_status="$(jq -r '.verdict.status // "unknown"' "$out_file" 2>/dev/null || echo "unknown")"
important_count="$(jq '[.findings[] | select(.severity=="IMPORTANT")] | length' "$out_file" 2>/dev/null || echo "0")"

if [[ "$important_count" -gt 0 ]]; then
  echo "Codex review: $verdict_status ($important_count IMPORTANT issues). See .codex/reviews/latest.json" >&2
fi

exit 0
