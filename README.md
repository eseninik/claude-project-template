# Claude Project Template

Template repository with pre-configured Claude Code workflow including Skills, OpenSpec, and Git CI/CD.

## What's Included

```
.claude/
├── skills/              # 20+ development skills (TDD, debugging, etc.)
│   ├── SKILLS_INDEX.md  # Skill selection guide
│   ├── test-driven-development/
│   ├── systematic-debugging/
│   ├── verification-before-completion/
│   └── ...
└── commands/
    └── openspec/        # OpenSpec slash commands

.github/
└── workflows/
    └── deploy.yml       # Auto-deploy on push to main

openspec/
├── AGENTS.md            # OpenSpec agent instructions
├── project.md           # Project context (fill this!)
├── changes/             # Active change proposals
└── specs/               # Specification documents

CLAUDE.md                # Main Claude Code instructions
```

## Quick Start

### Option 1: Use as GitHub Template

1. Click "Use this template" on GitHub
2. Clone your new repository
3. Run setup: `./scripts/init.sh` (or `init.ps1` on Windows)

### Option 2: Copy to Existing Project

```bash
# Clone template
git clone https://github.com/YOUR_USERNAME/claude-project-template.git temp-template

# Copy to your project
cp -r temp-template/.claude your-project/
cp -r temp-template/openspec your-project/
cp -r temp-template/.github your-project/
cp temp-template/CLAUDE.md your-project/

# Clean up
rm -rf temp-template

# Customize
cd your-project
./scripts/init.sh  # or edit files manually
```

## Setup Checklist

After copying/cloning, customize these files:

### 1. CLAUDE.md

Edit the `## Project Overview` section:
- [ ] Project description
- [ ] Primary language
- [ ] Commands (install, test, lint)
- [ ] Architecture overview
- [ ] Environment variables

### 2. openspec/project.md

Fill in:
- [ ] Project purpose and workflow
- [ ] Tech stack
- [ ] Code style conventions
- [ ] Testing strategy
- [ ] Domain context
- [ ] Constraints

### 3. .github/workflows/deploy.yml

Configure:
- [ ] Deployment commands for your stack
- [ ] Service restart command
- [ ] Add GitHub Secrets:
  - `SERVER_HOST`
  - `SERVER_USER`
  - `SERVER_SSH_KEY`
  - `PROJECT_PATH`

## Workflow Overview

### OpenSpec (WHAT to do)

```bash
# Create proposal for new features
openspec proposal

# Implement approved changes
openspec apply

# Archive after deployment
openspec archive <id> -y
```

### Skills (HOW to do it)

Skills are loaded on-demand based on the task:

| Task | Skill |
|------|-------|
| Bug fix | `systematic-debugging` |
| New code | `test-driven-development` |
| Completion | `verification-before-completion` |

### Git Workflow

```
dev branch  ──[push]──>  main branch  ──[GitHub Action]──>  Server
     │                        │
     │    git merge dev       │
     └────────────────────────┘
```

1. All work happens on `dev`
2. When ready: merge `dev` into `main`
3. Push to `main` triggers auto-deploy

## Skills Reference

| Skill | When to Use |
|-------|-------------|
| `brainstorming` | Before implementing features |
| `test-driven-development` | Writing any new code |
| `systematic-debugging` | Any bug or error |
| `verification-before-completion` | Before claiming "done" |
| `condition-based-waiting` | Flaky tests / race conditions |
| `root-cause-tracing` | Deep error investigation |
| `executing-plans` | Following implementation plans |
| `writing-plans` | Creating detailed task breakdowns |

See `.claude/skills/SKILLS_INDEX.md` for full list.

## License

MIT
