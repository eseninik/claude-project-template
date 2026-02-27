#!/usr/bin/env python3
"""generate-prompt.py — Teammate prompt generator with skill auto-discovery.

Generates complete teammate prompts with embedded skills, memory context,
and handoff template. Skills are auto-discovered via `roles:` field in
YAML front matter of each SKILL.md.

Adding a new skill: create .claude/skills/{name}/SKILL.md with `roles: [agent-types]`
in YAML front matter. The generator auto-discovers it — no other files to edit.

Usage:
  python .claude/scripts/generate-prompt.py --type coder --task "Implement X" --team my-team --name dev-1
  python .claude/scripts/generate-prompt.py --type qa-reviewer --task "Review changes" --criteria "No critical issues"
  python .claude/scripts/generate-prompt.py --list-types
  python .claude/scripts/generate-prompt.py --list-skills --type coder
"""

import argparse
import os
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Project root discovery
# ---------------------------------------------------------------------------

def find_project_root():
    """Find project root by locating .claude/ directory."""
    # Script lives in .claude/scripts/ — root is 2 levels up
    script_dir = Path(__file__).resolve().parent
    root = script_dir.parent.parent
    if (root / ".claude").is_dir():
        return root
    # Fallback: walk up from cwd
    current = Path.cwd()
    while current != current.parent:
        if (current / ".claude").is_dir():
            return current
        current = current.parent
    print("ERROR: Could not find project root (.claude/ directory)", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# YAML front matter parser (stdlib only, no PyYAML dependency)
# ---------------------------------------------------------------------------

def parse_yaml_front_matter(content):
    """Parse simple YAML front matter between --- markers.

    Handles:
      - key: value (string)
      - key: | (multiline block scalar)
      - key: [a, b, c] (inline list)
      - key:\\n  - a\\n  - b (block list)
    """
    result = {}
    # Strip BOM (Windows UTF-8 files may start with \ufeff)
    content = content.lstrip('\ufeff')
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return result

    lines = match.group(1).split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue

        m = re.match(r'^(\w[\w-]*)\s*:\s*(.*)', line)
        if not m:
            i += 1
            continue

        key = m.group(1)
        value = m.group(2).strip()

        # Inline list: [a, b, c]
        if value.startswith('[') and value.endswith(']'):
            items = [x.strip().strip('"\'') for x in value[1:-1].split(',')]
            result[key] = [x for x in items if x]
            i += 1

        # Multiline block scalar: |
        elif value == '|':
            block_lines = []
            i += 1
            while i < len(lines):
                if lines[i] and not lines[i][0].isspace():
                    break
                block_lines.append(lines[i])
                i += 1
            result[key] = '\n'.join(block_lines).strip()

        # Empty value — check for block list on next lines
        elif value == '':
            items = []
            i += 1
            while i < len(lines) and lines[i].strip().startswith('- '):
                items.append(lines[i].strip()[2:].strip())
                i += 1
            result[key] = items if items else ''

        # Simple scalar
        else:
            result[key] = value
            i += 1

    return result


def strip_front_matter(content):
    """Remove YAML front matter from skill content, return body only."""
    m = re.match(r'^---\s*\n.*?\n---\s*\n?', content, re.DOTALL)
    return content[m.end():] if m else content


# ---------------------------------------------------------------------------
# Skill discovery
# ---------------------------------------------------------------------------

def discover_skills(skills_dir, agent_type=None):
    """Scan .claude/skills/*/SKILL.md, return (matched, all) skill lists.

    Each skill dict: {name, path, roles, content, description, lines}
    A skill matches if agent_type is in its roles list, or roles contains '*'.
    """
    matched = []
    all_skills = []

    if not skills_dir.is_dir():
        return matched, all_skills

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            continue

        content = skill_file.read_text(encoding='utf-8', errors='replace')
        meta = parse_yaml_front_matter(content)
        roles = meta.get('roles', [])
        if isinstance(roles, str):
            roles = [roles] if roles else []

        info = {
            'name': meta.get('name', skill_dir.name),
            'dir_name': skill_dir.name,
            'path': str(skill_file),
            'roles': roles,
            'content': content,
            'body': strip_front_matter(content),
            'description': meta.get('description', ''),
            'lines': len(content.split('\n')),
        }
        all_skills.append(info)

        if agent_type and (agent_type in roles or '*' in roles):
            matched.append(info)

    return matched, all_skills


# ---------------------------------------------------------------------------
# Registry parser
# ---------------------------------------------------------------------------

def parse_registry(registry_path, agent_type):
    """Extract agent properties from registry.md table row."""
    props = {
        'tools': 'full',
        'thinking': 'standard',
        'context': 'standard',
        'memory': 'patterns',
    }

    if not registry_path.is_file():
        return props

    content = registry_path.read_text(encoding='utf-8', errors='replace')

    for line in content.split('\n'):
        if f'`{agent_type}`' in line:
            cells = [c.strip() for c in line.split('|')]
            # Remove empty first/last from split
            cells = [c for c in cells if c]
            if len(cells) >= 6:
                props['tools'] = cells[1]
                props['thinking'] = cells[3]
                props['context'] = cells[4]
                props['memory'] = cells[5]
            break

    return props


# ---------------------------------------------------------------------------
# Memory context loader
# ---------------------------------------------------------------------------

def load_memory_context(memory_dir, level='patterns'):
    """Load memory context from knowledge.md based on level."""
    if level == 'none':
        return 'No memory context needed for this task type.'

    knowledge_path = memory_dir / 'knowledge.md'
    if not knowledge_path.is_file():
        return 'No knowledge.md found.'

    content = knowledge_path.read_text(encoding='utf-8', errors='replace')

    if level == 'full':
        return content

    # patterns level: extract Patterns + Gotchas sections
    sections = []

    patterns = re.search(r'## Patterns\s*\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
    if patterns:
        sections.append("### Project Patterns\n" + patterns.group(1).strip())

    gotchas = re.search(r'## Gotchas\s*\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
    if gotchas:
        sections.append("### Known Gotchas\n" + gotchas.group(1).strip())

    return '\n\n'.join(sections) if sections else 'No patterns or gotchas found.'


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def build_tools_line(tools_raw):
    """Convert registry tools value to human-readable description."""
    t = tools_raw.lower().strip()
    if 'read-only' in t:
        return "read-only (Read, Glob, Grep only — NO file modifications)"
    elif 'web' in t:
        return "full + web (Read, Glob, Grep, Write, Edit, Bash, WebSearch, WebFetch)"
    else:
        return "full (Read, Glob, Grep, Write, Edit, Bash)"


def build_prompt(agent_type, task, team, name, criteria, constraints,
                 props, matched_skills, memory_context, max_skill_lines=2000):
    """Assemble the complete teammate prompt."""

    tools_line = build_tools_line(props.get('tools', 'full'))
    thinking = props.get('thinking', 'standard')

    # --- Skills section ---
    total_lines = sum(s['lines'] for s in matched_skills)
    trimmed = False

    skills_block = ""
    if matched_skills:
        for skill in matched_skills:
            body = skill['body'].strip()
            # If over budget, trim examples
            if total_lines > max_skill_lines:
                trimmed = True
                # Remove example sections to save space
                body = re.sub(
                    r'(?m)^#{2,3}\s*(Example|Примеры?).*?(?=^#{2,3}\s|\Z)',
                    '', body, flags=re.DOTALL
                ).strip()
            skills_block += f"\n### {skill['name']}\n{body}\n"

        size_note = ""
        if trimmed:
            size_note = (
                f"\n> NOTE: Total skill content ({total_lines} lines) exceeds "
                f"{max_skill_lines}-line budget. Examples trimmed to save context.\n"
            )
        skills_block = size_note + skills_block
    else:
        skills_block = "\nNo specific skills required for this task.\n"

    # --- Criteria / Constraints ---
    criteria_block = criteria if criteria else (
        "- Task completed successfully\n- No errors or regressions introduced"
    )
    constraints_block = constraints if constraints else (
        "- Follow existing code patterns\n- Do not modify files outside task scope"
    )

    # --- Assemble ---
    prompt = f"""You are a teammate on team "{team}". Your name is "{name}".

## Agent Type
{agent_type}
- Tools: {tools_line}
- Thinking: {thinking}

## Required Skills
{skills_block}

## Memory Context

{memory_context}

## Verification Rules (MANDATORY)
- Run tests before claiming done
- Verify each acceptance criterion with evidence (VERIFY/RESULT format)
- If any check fails -> fix first, do NOT claim done
- Update work/attempt-history.json if retry

## Handoff Output (MANDATORY when your task is done)

When completing your task, output this structured block:

=== PHASE HANDOFF: {name} ===
Status: PASS | REWORK | BLOCKED
Files Modified:
- [path/to/file1.ext]
Tests: [passed/failed/skipped counts or N/A]
Skills Invoked:
- [skill-name via embedded in prompt / none]
Decisions Made:
- [key decision with brief rationale]
Learnings:
- Friction: [what was hard or slow] | NONE
- Surprise: [what was unexpected] | NONE
- Pattern: [reusable insight for knowledge.md] | NONE
Next Phase Input: [what the next agent/phase needs to know]
=== END HANDOFF ===

## Your Task
{task}

## Acceptance Criteria
{criteria_block}

## Constraints
{constraints_block}"""

    return prompt


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

def cmd_list_types(registry_path):
    """Print all known agent types from registry."""
    if not registry_path.is_file():
        print("Registry not found:", registry_path, file=sys.stderr)
        return

    content = registry_path.read_text(encoding='utf-8', errors='replace')
    # Match `type-name` in table rows
    types = re.findall(r'\|\s*`([\w-]+)`\s*\|', content)
    # Deduplicate preserving order
    seen = set()
    skip = {'read-only', 'full', 'quick', 'standard', 'deep', 'minimal',
            'none', 'patterns', 'context7'}
    for t in types:
        if t not in seen and t not in skip:
            print(t)
            seen.add(t)


def cmd_list_skills(skills_dir, agent_type=None):
    """Print all skills, optionally filtered by agent type."""
    matched, all_skills = discover_skills(skills_dir, agent_type)

    if agent_type:
        print(f"Skills for agent type '{agent_type}':")
        if matched:
            for s in matched:
                print(f"  + {s['name']} ({s['lines']} lines)")
        else:
            print("  (none — no skills have this type in their roles)")
        print(f"\nAll skills ({len(all_skills)}):")
        matched_names = {s['name'] for s in matched}
        for s in all_skills:
            marker = " <-- MATCH" if s['name'] in matched_names else ""
            roles = ', '.join(s['roles']) if s['roles'] else '(no roles)'
            print(f"  {s['name']} ({s['lines']} lines) roles: [{roles}]{marker}")
    else:
        print(f"All skills ({len(all_skills)}):")
        for s in all_skills:
            roles = ', '.join(s['roles']) if s['roles'] else '(no roles)'
            print(f"  {s['name']} ({s['lines']} lines) roles: [{roles}]")


def cmd_generate(args, root):
    """Generate a teammate prompt."""
    skills_dir = root / '.claude' / 'skills'
    registry_path = root / '.claude' / 'agents' / 'registry.md'
    memory_dir = root / '.claude' / 'memory'

    # Discover skills for this agent type
    matched_skills, all_skills = discover_skills(skills_dir, args.type)

    # Get agent properties from registry
    props = parse_registry(registry_path, args.type)

    # Load memory context
    memory_level = props.get('memory', 'patterns')
    memory_context = load_memory_context(memory_dir, memory_level)

    # Dry run
    if args.dry_run:
        skill_names = [s['name'] for s in matched_skills]
        total_lines = sum(s['lines'] for s in matched_skills)
        print(f"Agent type:  {args.type}")
        print(f"Properties:  tools={props['tools']}, thinking={props['thinking']}, "
              f"context={props['context']}, memory={props['memory']}")
        print(f"Skills:      {', '.join(skill_names) or '(none)'}")
        print(f"Skill lines: {total_lines}")
        print(f"Memory:      {memory_level}")
        print(f"Team/Name:   {args.team}/{args.name}")
        return

    # Build prompt
    prompt = build_prompt(
        agent_type=args.type,
        task=args.task,
        team=args.team,
        name=args.name,
        criteria=args.criteria or '',
        constraints=args.constraints or '',
        props=props,
        matched_skills=matched_skills,
        memory_context=memory_context,
    )

    # Output
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(prompt, encoding='utf-8')
        # Summary to stderr
        skill_names = [s['name'] for s in matched_skills]
        total_lines = sum(s['lines'] for s in matched_skills)
        print(f"Prompt written to {args.output}", file=sys.stderr)
        print(f"Agent: {args.type} | Skills: {', '.join(skill_names) or 'none'} "
              f"| Skill lines: {total_lines} | Memory: {memory_level}",
              file=sys.stderr)
    else:
        print(prompt)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Generate teammate prompts with auto-discovered skills',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s --type coder --task "Implement login" --team feat --name dev-1
  %(prog)s --type qa-reviewer --task "Review auth" -o work/prompt.md
  %(prog)s --list-types
  %(prog)s --list-skills --type coder
  %(prog)s --dry-run --type planner --task "Plan refactoring"
""")

    parser.add_argument('--type', '-t', help='Agent type from registry.md')
    parser.add_argument('--task', '-T', help='Task description')
    parser.add_argument('--team', default='team', help='Team name (default: team)')
    parser.add_argument('--name', '-n', default='agent', help='Agent name')
    parser.add_argument('--criteria', '-c', help='Acceptance criteria')
    parser.add_argument('--constraints', help='Constraints')
    parser.add_argument('--output', '-o', help='Write to file instead of stdout')
    parser.add_argument('--list-types', action='store_true', help='List agent types')
    parser.add_argument('--list-skills', action='store_true', help='List skills')
    parser.add_argument('--dry-run', action='store_true', help='Show plan, no output')

    args = parser.parse_args()
    root = find_project_root()

    if args.list_types:
        cmd_list_types(root / '.claude' / 'agents' / 'registry.md')
        return

    if args.list_skills:
        cmd_list_skills(root / '.claude' / 'skills', args.type)
        return

    if not args.type:
        parser.error("--type is required (use --list-types to see options)")
    if not args.task and not args.dry_run:
        parser.error("--task is required")

    cmd_generate(args, root)


if __name__ == '__main__':
    main()
