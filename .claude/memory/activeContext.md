# Active Context

> Мост между сессиями. Агент читает в начале, обновляет в конце.

**Last updated:** 2026-02-16

---

## Current Focus

Autonomous Pipeline System — implemented and ready for testing. CLAUDE.md restructured for compaction resilience, PIPELINE.md state machine, Ralph Loop script, autonomous-pipeline guide. Next: test pipeline with real task (skills audit).

---

## Recent Decisions

| Date | Decision | Rationale | Files Affected |
|------|----------|-----------|----------------|
| 2026-01-29 | Добавить memory/ и adr/ в шаблон | Deep research показал что это решает "project amnesia" | .claude/memory/, .claude/adr/ |
| 2026-01-29 | AUTO-BEHAVIORS вместо команд | Пользователь хочет автоматику без ручных действий | CLAUDE.md |
| 2026-01-29 | Git hooks для автообновления | Память должна обновляться без участия человека | .claude/hooks/post-commit.sh |
| 2026-01-29 | Трёхуровневая система памяти | Гарантировать что память всегда обновляется | pre-commit.sh, post-commit.sh |
| 2026-01-30 | Plan execution enforcer | 100% enforcement с минимальным CLAUDE.md footprint | CLAUDE.md, plan-execution-enforcer.md |
| 2026-02-06 | Context Recovery Hook System | Auto-backup/restore при compaction, zero friction | hooks/, settings.json, CLAUDE.md, ADR-005 |
| 2026-02-07 | mcp-cli интеграция | On-demand MCP вместо загрузки tool descriptions в контекст | mcp-integration/SKILL.md, SKILLS_INDEX.md, CLAUDE.md, mcp_servers.json |
| 2026-02-09 | Синхронизация DocCheck Bot → шаблон | Перенос debug logging, Windows .cmd wrappers, /clear support, AGENT TEAM PROPOSAL, guides, knowledge, scripts | hooks/, settings.json, CLAUDE.md, guides/, knowledge/, scripts/ |
| 2026-02-11 | Skills Quality Upgrade (45 скиллов) | Применение SKILLS_QUALITY_STANDARD.md: frontmatter, imperative form, examples, edge cases, size reduction | .claude/skills/*/SKILL.md |
| 2026-02-11 | Expert Panel Mode (ADR-006) | Two-phase Agent Teams: adaptive 3-5 expert panel + implementation pipeline | SKILL, guides, CLAUDE.md, SKILLS_INDEX, ADR-006 |
| 2026-02-11 | Hook system upgrade from TalkCheckBot | COMPACTINSTRUCTIONS stdout, JSON hookSpecificOutput, .cmd wrappers, CLI args, timeouts | hooks/, settings.json, template CLAUDE.md |
| 2026-02-11 | Auto-clear system instead of auto-compact | DISABLE_AUTO_COMPACT + UserPromptSubmit context guard (90% warn, 95% block) + statusLine temp file | hooks/, settings.json, CLAUDE.md |
| 2026-02-12 | Pyramid Backup System (ADR-007, supersedes ADR-005) | Hook auto-recovery не работает, agent-driven backups качественнее | hooks/, settings.json, CLAUDE.md, guides/, ADR-007 |

---

## Active Questions

- [x] Нужно ли добавить pre-commit hook для проверки заполненности памяти? → Да, добавлен
- [ ] Как обрабатывать большие Session Log (архивация)? → archive/ директория создана

---

## Learned Patterns

### What Works
- Триггерные правила в CLAUDE.md заставляют агента следовать протоколу
- Разделение STATE.md (задачи) и activeContext.md (контекст) — разные цели
- Трёхуровневая защита: BLOCKING RULE → pre-commit warning → post-commit fallback
- Structured checkpoint format делает нарушения видимыми
- Agent Teams для параллельного исследования и реализации — работают эффективно

### What Doesn't Work
- Команды требуют ручного вызова — пользователи забывают

### Gotchas
- При upgrade-project не трогать memory/ и adr/ — это проектные данные
- Windows: mcp-cli daemon не работает (Unix sockets) — direct mode с latency 2-10 сек
- mcp-cli не на npm — устанавливается через git clone + bun link

---

## Next Steps

1. **[IN PROGRESS] Test autonomous pipeline** — создать реальный pipeline для аудита скиллов (44 скилла не используются Agent Teams)
2. **[WAITING] User decision on telegram-safe-mcp** — ответы на Open Questions в work/expert-analysis.md
3. Рассмотреть перенос agents/ в new-project template
4. Обновить upgrade-project чтобы не трогал memory/ и adr/

---

## Auto-Generated Summaries

> Записи добавляются post-commit когда агент не обновил память.
> При следующей сессии: интегрировать в Session Log и очистить.

---

## Session Log

### 2026-02-16 (сессия 2)
**Did:** Autonomous Pipeline System — full implementation (Tier 1-4 from expert-analysis.md):
- Expert Panel (5 agents): deep research of 12+ repos/sources on autonomous pipelines
- CLAUDE.md restructured: Summary Instructions at TOP, AUTONOMOUS PIPELINE PROTOCOL section, positive constraints, 281→213 lines
- New-project template CLAUDE.md: same restructure, 295→221 lines
- scripts/ralph.sh (132 lines): fresh-context loop with colored output, git checkpoints, error handling
- .claude/shared/work-templates/PIPELINE.md: state machine template with `<- CURRENT` markers
- .claude/shared/work-templates/PROMPT.md: Ralph Loop prompt template (5-step protocol)
- .claude/guides/autonomous-pipeline.md (213 lines): full guide for pipeline creation, execution, recovery, anti-drift
- init-project.md: added Step 8 (Pipeline Setup) for new projects
- SKILLS_INDEX.md: added AUTONOMOUS PIPELINE section with all 4 resources
- All files synced to new-project template
- Agent team: 6 agents total (5 research + 2 implementation)
**Decided:** Summary Instructions at TOP of CLAUDE.md (highest attention zone); PIPELINE.md state machine as external memory; Ralph Loop for compaction-immune execution; positive constraints ("Instead Do" column); no model routing (all Opus per user preference)
**Learned:** Agent Teams Mode lost after compaction because behavioral rules are first to be dropped; "Lost in the Middle" = mid-file rules have lowest recall; file-based state machines survive compaction; fresh-context per phase eliminates compaction entirely
**Next:** Test pipeline with real task — skills audit (44 skills unused by Agent Teams); iterate based on results

### 2026-02-16 (сессия 1)
**Did:** Expert Panel Analysis — Telegram MCP & MCP-CLI Integration:
- Phase 1 (4 research agents): deep-dive mcp-cli, telegram-mcp, QC Bot Telethon, template MCP
- mcp-cli fixes: synced template skill (195→147 lines), migrated API keys to env vars in ~/.bashrc
- Phase 2 (4 design agents): System Architect, Security Analyst, API Designer, Risk Assessor
- Phase 3 (1 architect agent): refined tool catalog from 25 → 10 tools, detailed file structure
- Synthesized all 9 agents into work/expert-analysis.md (420 lines)
**Decided:** telegram-mcp unsafe (4/10), build custom "telegram-safe-mcp" (10 tools, FastMCP 2.0 + Telethon, ~400-600 LOC)
**Learned:** Security by absence > security by restriction; Encrypted file > session string in env var; 10 tools sufficient for testing pipeline
**Next:** User decision on Open Questions, then implement if approved

### 2026-02-12 (сессия 1)
**Did:** Pyramid Backup System (ADR-007, supersedes ADR-005):
- Deleted session-start-compact.sh/.cmd (4 files, main + template) — SessionStart hooks removed entirely
- Rewrote pre-compact.sh (227→75 lines) — safety-net only, no COMPACTINSTRUCTIONS stdout
- Modified user-prompt-context-guard.sh — removed pre-compact.sh call, updated messages to reference pyramid backup
- Modified context-status-line.sh — backup status: Pyramid > SafetyNet > None
- Modified settings.json — removed SessionStart hooks (main + template)
- Created .claude/guides/session-backup-format.md (~170 lines) — pyramid format spec
- Updated CLAUDE.md (7 sections) — SESSION START, CONTEXT EXHAUSTION, triggers, constraints, knowledge, forbidden, blocking rules
- Updated template CLAUDE.md — same logical changes
- Updated .gitignore (main + template) — new patterns for session-*/, latest-session/, safety-net-*
- Created ADR-007, updated decisions.md, marked ADR-005 superseded
- Cleaned up old backup files (latest.md, latest-slim.md, session-*.md, session-*-slim.md)
- All changes synced main ↔ template
**Decided:** Agent-driven pyramid backups > hook auto-recovery (hooks produce lower quality backups from shell script parsing)
**Learned:** SessionStart hook context injection was unreliable; agent has full context and creates better structured backups; pre-compact hook still useful as safety net
**Next:** Test pyramid backup flow in real session (create backup, /clear, recover)

### 2026-02-11 (сессия 3, часть 2)
**Did:** Auto-clear system — замена auto-compact на backup+clear для предотвращения галлюцинаций:
- Deep research: 3 команды исследователей (hook analysis, compact threshold, creative solutions)
- Ключевое открытие: auto-compact порог 83% хардкоднут (Math.min в cli.js), CLAUDE_AUTOCOMPACT_PCT_OVERRIDE не поднимает выше
- Ключевое открытие: UserPromptSubmit hook поддерживает exit code 2 (блокировка промпта)
- Новый хук: user-prompt-context-guard.sh/.cmd — при 90% инжектит WARNING, при 95% блокирует промпт (exit 2)
- StatusLine: пишет % в temp file для UserPromptSubmit хука
- Global settings: DISABLE_AUTO_COMPACT=1, удалён CLAUDE_AUTOCOMPACT_PCT_OVERRIDE
- settings.json: зарегистрирован UserPromptSubmit хук
- CLAUDE.md: CONTEXT EXHAUSTION протокол заменил AFTER COMPACTION
- Всё синхронизировано в shared/templates/new-project/
**Decided:** /clear вместо compact — compact после нескольких итераций вызывает галлюцинации; backup+clear даёт чистый контекст
**Learned:** Math.min в cli.js блокирует повышение порога; UserPromptSubmit поддерживает exit 2 blocking; statusLine → temp file → UserPromptSubmit = межхуковая коммуникация
**Next:** Протестировать auto-clear flow в реальной сессии; проверить что UserPromptSubmit корректно блокирует при 95%

### 2026-02-11 (сессия 3)
**Did:** Hook system upgrade — портирование auto-compact из TalkCheckBot в шаблон:
- Expert Panel (4 эксперта): System Architect, 2 Researchers, Risk Assessor — полный анализ обоих проектов
- Implementation Team (4 dev агента Wave 1 + 1 syncer Wave 2 + 1 verifier Wave 3)
- pre-compact.sh: +COMPACTINSTRUCTIONS stdout (строки 185-226) — компактор теперь знает что сохранять
- pre-compact.sh: +RECENT_DECISIONS extraction, GIT_BRANCH moved earlier
- session-start-compact.sh: заменён на JSON hookSpecificOutput через Python + sed fallback
- session-start-compact.sh: CLI-first ($1), stdin fallback (read -t 2)
- settings.json: .cmd wrappers, %CLAUDE_PROJECT_DIR%, "compact" CLI arg, timeout: 15
- context-status-line.cmd: новый .cmd wrapper
- Template CLAUDE.md: +AFTER COMPACTION section, +backups in KNOWLEDGE, +compaction HARD CONSTRAINT
- Всё синхронизировано main ↔ shared/templates/new-project/
- Верификация: 25/25 checks pass (syntax, JSON, content parity, features, reference comparison, CLAUDE.md)
**Decided:** JSON hookSpecificOutput — правильный протокол Claude Code hooks API; COMPACTINSTRUCTIONS stdout — самое ценное улучшение (направляет компактор)
**Learned:** Expert Panel → Implementation pipeline через Agent Teams работает эффективно; 3-wave execution (impl → sync → verify); pre-compact stdout = единственный способ направить компактор
**Next:** Протестировать COMPACTINSTRUCTIONS в реальной compaction; протестировать JSON context injection

### 2026-02-11 (сессия 2)
**Did:** Enhanced Agent Teams Mode with Expert Panel:
- 5 new files: expert-panel/SKILL.md (10-role adaptive pool), expert-panel-workflow.md (4-phase orchestration), priority-ladder.md (7-level conflict resolution), expert-panel.md command, ADR-006
- 4 modified files: CLAUDE.md (+EXPERT PANEL MODE section, +ROLE SKILLS MAPPING, +CONTEXT TRIGGER, +HARD CONSTRAINT, +BLOCKING RULE), SKILLS_INDEX.md (44 skills), teammate-prompt-template.md (+Expert Panel Roles), decisions.md (+ADR-006)
- Template sync: all new+modified files mirrored to shared/templates/new-project/
- Verification: all 7 checks passed (structure, CLAUDE.md consistency, skill refs, backward compat, template sync, ADR index, SKILLS_INDEX count)
**Decided:** Two separate teams (panel shutdown → impl team); adaptive 3-5 from pool of 10; Priority Ladder for conflict resolution; expert-analysis.md as bridge file
**Learned:** 4-wave execution with subagents efficient for doc-heavy tasks; ADR-006 is project-specific (not synced to template); template CLAUDE.md has different structure but same sections can be applied
**Next:** Test Expert Panel with a real task; consider syncing updated skills to new-project template (from session 1 TODO)

### 2026-02-11 (сессия 1)
**Did:** Skills Quality Upgrade — обновление всех 45 скиллов по SKILLS_QUALITY_STANDARD.md:
- Agent Team (5 параллельных updater агентов, по 9 скиллов каждому)
- Frontmatter: все 45 теперь имеют WHAT + WHEN + anti-definitions в description
- Body: imperative form, удалён AI slop, добавлены примеры и edge cases
- Размер: ~15,766 → ~7,207 строк (54% сокращение)
- Критические фиксы: 6 скиллов превышали 500 строк (subagent-driven-dev 1425→179+refs), 5+ скиллов с русскими descriptions без триггеров
- Удалено нестандартное поле version из всех frontmatter
- subagent-driven-development: split в SKILL.md + references/ (worktree-mode.md, background-task-tracking.md)
**Decided:** SKILLS_QUALITY_STANDARD.md как стандарт качества для всех скиллов
**Learned:** 5 parallel agents handle 45 skills efficiently; biggest issue was oversized skills (>500 lines); Russian-only descriptions invisible to skill routing; version field not standard
**Next:** Синхронизировать обновлённые скиллы в new-project template

### 2026-02-09
**Did:** Синхронизация улучшений из DocCheck Bot в шаблон через Agent Team (10 агентов):
- Hooks: debug logging (HOOK_LOG, log_debug, trap ERR) во всех 3 хуках + ротация лога (>200→100)
- Hooks: session-start-compact.sh — $1 CLI override для Windows stdin + поддержка /clear
- Hooks: Windows .cmd wrappers (pre-compact.cmd, session-start-compact.cmd)
- settings.json: второй SessionStart matcher для "clear" (оба файла)
- CLAUDE.md: AGENT TEAM PROPOSAL auto-behavior + TeamCreate hard constraint (оба файла)
- Guides: plan-format-conversion.md, principles.md, reference.md, skills-reference.md
- Knowledge: parallelization-patterns.md (576 строк паттернов параллелизации)
- Scripts: setup-hooks.sh (симлинки git hooks)
- Methodology: autowork-guide.md, skill-composition.md
- .gitignore: hook-debug.log
- Всё синхронизировано в main + shared/templates/new-project/
**Decided:** Портировать improvements, не project-specific данные (.env, pyproject.toml, project-specific .gitignore entries)
**Learned:** Agent Teams масштабируются хорошо (10 параллельных агентов); DocCheck Bot settings.json использует .cmd вместо bash — workaround для Windows; /clear source нужен отдельный matcher в settings.json
**Next:** Протестировать hook debug logging в реальной работе, рассмотреть перенос agents/ (orchestrator, security-auditor) в new-project template

### 2026-02-07
**Did:** Интеграция mcp-cli для on-demand MCP вызовов:
- Исследование: Agent Team (researcher + analyzer) — параллельный анализ mcp-cli и структуры проекта
- Skill: .claude/skills/mcp-integration/SKILL.md — workflow grep → info → call, 5 серверов
- Config: ~/.config/mcp/mcp_servers.json — perplexity, context7, firecrawl, ref, exa
- .env.example: секция MCP API ключей (проект + шаблон)
- SKILLS_INDEX.md: новая категория EXTERNAL SERVICES + entry point + combination
- CLAUDE.md: новый trigger "Нужен внешний сервис" → mcp-integration
- Template sync: SKILL.md + .env.example в shared/templates/new-project/
- Install: Bun 1.3.8 + mcp-cli v0.3.0 (через git clone + bun link из-за отсутствия npm пакета)
**Decided:** mcp-cli как параллельная система для Claude Code (Claude Desktop конфиг остаётся)
**Learned:** mcp-cli daemon не работает на Windows (Unix sockets) — direct mode fallback; пакет не на npm — установка через git clone; Agent Teams эффективны для research + parallel implementation
**Next:** Настроить API ключи, протестировать с реальными данными, перенести на серверы

### 2026-02-06
**Did:** Реализовал Context Recovery Hook System:
- StatusLine: context-status-line.sh — мониторинг контекста в реальном времени
- PreCompact: pre-compact.sh — автоматический бэкап перед compaction
- SessionStart: session-start-compact.sh — восстановление после compaction
- settings.json: регистрация хуков
- CLAUDE.md: AFTER COMPACTION auto-behavior + constraint + trigger + knowledge
- ADR-005: документация решения
- decisions.md: обновлён индекс
- Синхронизировано с template new-project
**Decided:** Hook-based system (PreCompact + SessionStart + StatusLine) для zero-friction recovery
**Learned:** Windows Git Bash: no jq/bc/grep -oP, set -euo pipefail опасен для скриптов которые не должны падать
**Next:** Протестировать с реальной compaction, рассмотреть transcript parsing

### 2026-01-30
**Did:** Создал plan-execution-enforcer.md с structured checkpoint format
- CLAUDE.md: -9 строк (секция Plan Detected: 12 → 3 строки)
- Новый guide: plan-execution-enforcer.md (302 строки, on-demand)
- Синхронизировал с template new-project
- Создал ADR-004
**Decided:** Enforcement через mandatory bordered YAML box с self-verification checklist
**Learned:** Structured output format > текстовые инструкции для enforcement
**Next:** Протестировать с реальными планами, убедиться в 100% checkpoint output

### 2026-01-29 (сессия 2)
**Did:** Реализовал трёхуровневую систему памяти:
- pre-commit.sh: warning если память не обновлена
- post-commit.sh: fallback auto-entry если агент забыл
- BLOCKING RULE в CLAUDE.md
- Auto-Generated Summaries секция в activeContext.md
- Синхронизировал шаблоны new-project
**Decided:** WARNING mode для pre-commit (не блокирует CI/CD)
**Learned:** Wave analysis показал 100% parallelization → все задачи Wave 1 независимы
**Next:** Установить hooks и протестировать

### 2026-01-29 (сессия 1)
**Did:** Создал структуру memory/ и adr/, обновил CLAUDE.md шаблона
**Decided:** AUTO-BEHAVIORS подход вместо команд
**Learned:** Система должна быть полностью автоматической
**Next:** Обновить upgrade-project, протестировать
