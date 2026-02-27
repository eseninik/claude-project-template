#!/usr/bin/env python3
"""spawn-agent.py — One-command teammate spawning with auto-type detection.

Auto-detects agent type from task description keywords, generates complete
prompt with embedded skills and memory context. Replaces manual multi-step
teammate creation with a single command.

Internally imports generate-prompt.py — no code duplication.

Usage:
  python .claude/scripts/spawn-agent.py --task "Implement login" --team feat --name dev-1
  python .claude/scripts/spawn-agent.py --task "Review code changes" -o work/prompt.md
  python .claude/scripts/spawn-agent.py --task "Debug test failure" --detect-only
  python .claude/scripts/spawn-agent.py --task "Sync files" --type template-syncer  # override
"""

import argparse
import importlib.util
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Import generate-prompt module (same directory)
# ---------------------------------------------------------------------------

def load_generator():
    """Import generate-prompt.py from the same directory."""
    gen_path = Path(__file__).resolve().parent / "generate-prompt.py"
    if not gen_path.is_file():
        print(f"ERROR: generate-prompt.py not found at {gen_path}", file=sys.stderr)
        sys.exit(1)
    spec = importlib.util.spec_from_file_location("generate_prompt", gen_path)
    if spec is None or spec.loader is None:
        print(f"ERROR: Could not load generate-prompt.py as module", file=sys.stderr)
        sys.exit(1)
    try:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as e:
        print(f"ERROR: Failed to import generate-prompt.py: {e}", file=sys.stderr)
        sys.exit(1)
    return mod


# ---------------------------------------------------------------------------
# Type auto-detection engine
# ---------------------------------------------------------------------------

# Rules ordered from most specific to most general.
# Each rule: (type, keywords, anti_keywords, boost_words)
# Score = +2 per keyword match, -1 per anti match, +0.5 per boost match
# Highest score wins. Ties: first in list wins.

TYPE_RULES = [
    # --- Highly specific types first ---
    ('coder-complex', {
        'keywords': [
            'refactor', 'redesign', 'migrate', 'architect', 'complex',
            'multi-module', 'cross-cutting', 'system-wide',
            'рефакторинг', 'редизайн', 'миграция', 'архитектур',
        ],
        'anti': [],
        'boost': ['architecture', 'system', 'multiple files', 'breaking change'],
    }),
    ('ao-hybrid-coordinator', {
        'keywords': [
            'ao hybrid', 'ao-hybrid', 'ao spawn', 'full context agent',
        ],
        'anti': [],
        'boost': ['worktree', 'parallel', 'full claude'],
    }),
    ('fleet-orchestrator', {
        'keywords': [
            'fleet', 'all bots', 'all projects', 'cross-project', 'multi-repo',
            'все боты', 'все проекты', 'флот',
        ],
        'anti': [],
        'boost': ['sync', 'deploy', 'migrate'],
    }),
    ('pipeline-lead', {
        'keywords': [
            'pipeline', 'orchestrate', 'coordinate agents', 'multi-phase',
            'пайплайн', 'оркестрируй', 'координируй',
        ],
        'anti': ['implement', 'fix'],
        'boost': ['phases', 'pipeline.md', 'agent teams'],
    }),

    # --- Analysis/debugging types ---
    ('analyzer', {
        'keywords': [
            'debug', 'diagnose', 'investigate', 'trace error', 'root cause',
            'analyze error', 'analyze failure', 'stack trace',
            'дебаг', 'диагностируй', 'исследуй ошибку', 'трассировка',
        ],
        'anti': ['implement', 'create', 'build'],
        'boost': ['error', 'failure', 'traceback', 'exception', 'crash'],
    }),
    ('reproducer', {
        'keywords': [
            'reproduce', 'minimal reproduction', 'repro case',
            'воспроизведи', 'минимальный пример',
        ],
        'anti': ['fix', 'implement'],
        'boost': ['bug', 'intermittent', 'flaky'],
    }),

    # --- QA types ---
    ('qa-reviewer', {
        'keywords': [
            'review', 'qa', 'audit', 'check quality', 'validate code',
            'code review', 'review code', 'review changes', 'inspect',
            'ревью', 'проверь код', 'валидация', 'аудит', 'проверь изменения',
        ],
        'anti': ['fix', 'implement', 'create', 'build'],
        'boost': ['quality', 'issues', 'criteria', 'acceptance', 'security'],
    }),
    ('qa-fixer', {
        'keywords': [
            'fix qa', 'fix review', 'address review', 'fix issues from',
            'исправь по ревью', 'исправь замечания',
        ],
        'anti': ['review', 'plan'],
        'boost': ['qa-issues', 'review comments', 'feedback'],
    }),

    # --- Fix types ---
    ('fixer', {
        'keywords': [
            'fix', 'repair', 'patch', 'resolve bug', 'correct error', 'hotfix',
            'исправь', 'почини', 'пофикси', 'устрани',
        ],
        'anti': ['review', 'plan', 'investigate'],
        'boost': ['bug', 'broken', 'failing', 'crash', 'error', 'баг'],
    }),

    # --- Planning types ---
    ('planner', {
        'keywords': [
            'plan', 'decompose', 'break down', 'design', 'strategy', 'roadmap',
            'спланируй', 'разбей', 'декомпозируй', 'проектируй', 'стратегия',
        ],
        'anti': ['implement', 'code', 'fix'],
        'boost': ['phases', 'tasks', 'architecture', 'subtasks'],
    }),
    ('complexity-assessor', {
        'keywords': [
            'assess complexity', 'estimate effort', 'complexity analysis',
            'оцени сложность', 'оценка трудозатрат',
        ],
        'anti': ['implement', 'fix'],
        'boost': ['risk', 'effort', 'difficulty'],
    }),

    # --- Research types ---
    ('spec-researcher', {
        'keywords': [
            'research', 'explore', 'study', 'discover', 'analyze codebase',
            'find information', 'gather context',
            'изучи', 'исследуй', 'найди информацию', 'собери контекст',
        ],
        'anti': ['implement', 'fix', 'create', 'build'],
        'boost': ['documentation', 'api', 'library', 'codebase'],
    }),

    # --- Verification ---
    ('verifier', {
        'keywords': [
            'verify', 'confirm', 'check passes', 'validate results',
            'run tests', 'check correctness',
            'проверь результат', 'верифицируй', 'запусти тесты',
        ],
        'anti': ['implement', 'fix', 'create', 'build'],
        'boost': ['test', 'pass', 'correct', 'assertion'],
    }),

    # --- Utility types ---
    ('template-syncer', {
        'keywords': [
            'sync', 'copy files', 'mirror', 'replicate template',
            'sync to bots', 'sync template',
            'синхронизируй', 'скопируй файлы',
        ],
        'anti': ['implement', 'review'],
        'boost': ['template', 'bot', 'project', 'copy'],
    }),
    ('commit-helper', {
        'keywords': [
            'commit', 'push', 'create pr', 'merge branch', 'git commit',
            'закоммить', 'запуш', 'создай pr',
        ],
        'anti': ['implement', 'review'],
        'boost': ['git', 'branch', 'changes', 'staged'],
    }),
    ('insight-extractor', {
        'keywords': [
            'extract insights', 'summarize results', 'extract learnings',
            'извлеки инсайты', 'подведи итоги',
        ],
        'anti': ['implement', 'fix'],
        'boost': ['learnings', 'summary', 'patterns'],
    }),

    # --- Default: coder (most common) ---
    # NOTE: "code" and "change" removed — too generic (match "code review", "review changes")
    ('coder', {
        'keywords': [
            'implement', 'build', 'create', 'add', 'write', 'develop',
            'update', 'modify', 'extend', 'integrate',
            'реализуй', 'создай', 'добавь', 'напиши', 'обнови', 'измени',
        ],
        'anti': ['review', 'debug', 'research', 'plan', 'sync', 'commit'],
        'boost': ['function', 'feature', 'endpoint', 'component', 'module'],
    }),
]


def detect_agent_type(task_description):
    """Auto-detect agent type from task description.

    Returns (agent_type, confidence, matched_keywords, explanation).
    Confidence: 0.0 - 1.0
    """
    task_lower = task_description.lower()

    best_type = 'coder'
    best_score = -1
    best_matches = []

    # Pre-compile word boundary check for accurate matching
    # Prevents "fix" matching "prefix", "add" matching "address", etc.
    def word_match(keyword, text):
        """Check if keyword appears as a whole word/phrase in text."""
        return bool(re.search(r'\b' + re.escape(keyword) + r'\b', text))

    for agent_type, rules in TYPE_RULES:
        score = 0
        matches = []

        for kw in rules['keywords']:
            if word_match(kw, task_lower):
                score += 2
                matches.append(f'+"{kw}"')

        for anti in rules['anti']:
            if word_match(anti, task_lower):
                score -= 1

        for boost in rules.get('boost', []):
            if word_match(boost, task_lower):
                score += 0.5
                matches.append(f'~"{boost}"')

        if score > best_score:
            best_score = score
            best_type = agent_type
            best_matches = matches

    # No positive matches → explicit fallback to coder
    if best_score <= 0:
        best_type = 'coder'
        best_matches = []

    # Confidence from score
    if best_score >= 5:
        confidence = 0.95
    elif best_score >= 3:
        confidence = 0.85
    elif best_score >= 2:
        confidence = 0.70
    elif best_score >= 1:
        confidence = 0.50
    else:
        confidence = 0.30

    explanation = (
        f"  Type:       {best_type}\n"
        f"  Confidence: {confidence:.0%}\n"
        f"  Matched:    {', '.join(best_matches[:6]) if best_matches else '(none — fallback to coder)'}"
    )

    return best_type, confidence, best_matches, explanation


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='One-command teammate spawning with auto-type detection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s --task "Implement login feature" --team feat --name dev-1
  %(prog)s --task "Review code changes" --team qa --name reviewer
  %(prog)s --task "Debug test failure" --team fix --name debugger
  %(prog)s --task "Sync template files" --detect-only
  %(prog)s --task "Build API" --type coder-complex  # override auto-detection
  %(prog)s --task "Fix qa issues" -o work/prompt.md
""")

    parser.add_argument('--task', '-T', required=True, help='Task description')
    parser.add_argument('--type', '-t', help='Override auto-detected agent type')
    parser.add_argument('--team', default='team', help='Team name (default: team)')
    parser.add_argument('--name', '-n', default='agent', help='Agent name')
    parser.add_argument('--criteria', '-c', help='Acceptance criteria')
    parser.add_argument('--constraints', help='Constraints')
    parser.add_argument('--output', '-o', help='Write prompt to file instead of stdout')
    parser.add_argument('--detect-only', action='store_true',
                        help='Only show detected type, do not generate prompt')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show detection + skill plan, no prompt output')

    args = parser.parse_args()

    # --- Type detection ---
    if args.type:
        agent_type = args.type
        confidence = 1.0
        explanation = f"  Type:       {agent_type}\n  Confidence: 100% (manual override)"
    else:
        agent_type, confidence, matched, explanation = detect_agent_type(args.task)

    # Detect-only mode
    if args.detect_only:
        print("Auto-detection result:")
        print(explanation)
        if confidence < 0.5:
            print(f"\n  Low confidence. Consider --type override.")
        return

    # --- Load generator ---
    gen = load_generator()
    root = gen.find_project_root()

    skills_dir = root / '.claude' / 'skills'
    registry_path = root / '.claude' / 'agents' / 'registry.md'
    memory_dir = root / '.claude' / 'memory'

    # Discover skills for detected type
    matched_skills, all_skills = gen.discover_skills(skills_dir, agent_type)

    # Get agent properties from registry
    props = gen.parse_registry(registry_path, agent_type)

    # Load memory context
    memory_level = props.get('memory', 'patterns')
    memory_context = gen.load_memory_context(memory_dir, memory_level)

    # Dry run
    if args.dry_run:
        print("Auto-detection:")
        print(explanation)
        skill_names = [s['name'] for s in matched_skills]
        total = sum(s['lines'] for s in matched_skills)
        print(f"\n  Registry:   tools={props['tools']}, thinking={props['thinking']}, "
              f"context={props['context']}, memory={props['memory']}")
        print(f"  Skills:     {', '.join(skill_names) or '(none)'}")
        print(f"  Lines:      {total}")
        print(f"  Team/Name:  {args.team}/{args.name}")
        if confidence < 0.5:
            print(f"\n  Low confidence. Consider --type override.")
        return

    # --- Build prompt ---
    prompt = gen.build_prompt(
        agent_type=agent_type,
        task=args.task,
        team=args.team,
        name=args.name,
        criteria=args.criteria or '',
        constraints=args.constraints or '',
        props=props,
        matched_skills=matched_skills,
        memory_context=memory_context,
    )

    # --- Output ---
    skill_names = [s['name'] for s in matched_skills]
    total_lines = sum(s['lines'] for s in matched_skills)
    info = (
        f"Auto-detection:\n{explanation}\n"
        f"  Skills:     {', '.join(skill_names) or '(none)'} ({total_lines} lines)\n"
        f"  Memory:     {memory_level}\n"
        f"  Team/Name:  {args.team}/{args.name}"
    )

    if confidence < 0.5:
        info += f"\n\n  WARNING: Low confidence ({confidence:.0%}). Consider --type override."

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(prompt, encoding='utf-8')
        print(info, file=sys.stderr)
        print(f"  Prompt:     {args.output} ({len(prompt)} chars)", file=sys.stderr)
    else:
        print(info, file=sys.stderr)
        print(prompt)


if __name__ == '__main__':
    main()
