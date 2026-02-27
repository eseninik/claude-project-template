# Expert Analysis: Agent Orchestrator vs Our Autonomous Pipeline

> Date: 2026-02-27
> Source: github.com/ComposioHQ/agent-orchestrator (157 TS files, 3288 tests)
> Target: Our `.claude/` template system (guides + skills + prompts + memory)

---

## Executive Summary

**Agent Orchestrator (AO)** и **наша система** решают РАЗНЫЕ задачи на РАЗНЫХ уровнях:

| Dimension | Agent Orchestrator | Наша система |
|-----------|-------------------|--------------|
| **Уровень** | Внешний оркестратор (TypeScript процесс) | Внутренняя самоорганизация (markdown instructions) |
| **Фокус** | Управление ФЛОТОМ агентов по РАЗНЫМ задачам | Управление ОДНОЙ сложной задачей через ФАЗЫ |
| **Жизненный цикл** | Issue → Branch → PR → CI → Review → Merge | Spec → Plan → Implement → QA → Test → Deploy |
| **Параллелизм** | Много агентов × много issues | Много агентов × одна задача (Agent Teams) |
| **Runtime** | tmux/Docker/Process (внешний) | Claude Code TeamCreate/Task (нативный) |
| **Агенты** | Claude Code / Codex / Aider (агностик) | Только Claude Code |
| **Состояние** | Flat-file key=value metadata | PIPELINE.md с `<- CURRENT` маркерами |
| **UI** | Web dashboard + CLI (`ao status`) | Markdown files + terminal |

**Вывод: системы КОМПЛЕМЕНТАРНЫ, не конкурируют.** AO управляет "внешним циклом" (какие задачи → каким агентам), наша система — "внутренним циклом" (как агент выполняет задачу).

---

## Part 1: Architecture Comparison

### 1.1 AO Architecture (Simplified)

```
┌─────────────────────────────────────────────────────────────┐
│                    ao CLI / Web Dashboard                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Core Services                             │
│  SessionManager │ LifecycleManager │ PluginRegistry          │
│  PromptBuilder  │ ReactionEngine   │ MetadataStore           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌────────────┬──────────┬───────────┬──────────┬──────────────┐
│  Runtime   │  Agent   │ Workspace │ Tracker  │  Notifier    │
│  (tmux)    │ (claude) │(worktree) │ (github) │  (slack)     │
└────────────┴──────────┴───────────┴──────────┴──────────────┘
```

**8 Plugin Slots** — каждый можно заменить:
- Runtime: tmux, docker, k8s, process
- Agent: claude-code, codex, aider, opencode
- Workspace: worktree, clone
- Tracker: github, linear
- SCM: github
- Notifier: desktop, slack, webhook, composio
- Terminal: iterm2, web
- Lifecycle: core

### 1.2 Our Architecture (Simplified)

```
┌─────────────────────────────────────────────────────────────┐
│                    CLAUDE.md (Instruction Layer)              │
│  Summary rules + blocking rules + hard constraints           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                        │
│  PIPELINE.md (state machine) │ Agent Teams │ Agent Chains    │
│  Expert Panel │ Quality Gates │ Phase Transitions            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Memory Layer                               │
│  knowledge.md (typed, decay) │ Graphiti │ daily logs         │
│  activeContext.md │ observations/ │ memory-engine.py          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌────────────┬──────────────┬──────────────┬──────────────────┐
│  Skills    │  Guides      │  Prompts     │  Agent Registry  │
│  (47 шт)  │ (10+ guides) │ (5 roles)    │ (24 agent types) │
└────────────┴──────────────┴──────────────┴──────────────────┘
```

### 1.3 Key Architectural Differences

| Aspect | AO | Our System |
|--------|-----|-----------|
| **State encoding** | Flat file `key=value` (bash-compatible) | Markdown with `<- CURRENT` marker |
| **Plugin model** | TypeScript interfaces + registry | Skills (markdown protocols) + guides |
| **Agent spawning** | External: tmux session + CLI command | Native: TeamCreate + Task tool |
| **State machine** | Implicit (status field transitions) | Explicit (PIPELINE.md phases) |
| **Error recovery** | Reaction engine (event → auto-fix) | Recovery manager + attempt tracking |
| **Monitoring** | Web dashboard + activity detection via JSONL | Terminal output + manual checks |
| **Prompt composition** | 3-layer: base + config + user rules | CLAUDE.md + skills + focused prompts |
| **Memory** | No cross-session memory | Ebbinghaus decay + Graphiti + typed memory |
| **Quality gates** | CI checks + PR reviews | 4-verdict model (PASS/CONCERNS/REWORK/FAIL) |

---

## Part 2: What AO Does That We Don't

### 2.1 Event-Driven Reaction Engine ⭐⭐⭐

**AO's killer feature.** Automatic handling of external events:

```yaml
reactions:
  ci-failed:
    auto: true
    action: send-to-agent
    retries: 2
  changes-requested:
    auto: true
    action: send-to-agent
    escalateAfter: 30m
  approved-and-green:
    auto: false
    action: notify
```

Когда CI падает → AO собирает логи → отправляет агенту → агент чинит → пушит.
Когда ревьювер оставляет комментарий → AO собирает → форвардит агенту.

**У нас:** Нет автоматических реакций на внешние события. Если CI падает, мы узнаём об этом только при следующем ручном запуске.

**Оценка:** ВЫСОКАЯ ЦЕННОСТЬ. Но для наших миграционных ботов не критично (нет CI/CD пайплайнов). Полезно для будущих проектов с CI.

### 2.2 Activity Detection (Session Introspection) ⭐⭐

AO читает JSONL файлы Claude Code из `~/.claude/projects/` для определения состояния агента:

```
active   → agent working (thinking, reading, writing)
ready    → agent finished turn, waiting for input
idle     → inactive >5 min
waiting_input → permission prompt
blocked  → error state
exited   → process dead
```

**У нас:** Когда мы спавним Agent Teams, мы НЕ мониторим их состояние. Просто ждём, пока они отправят сообщение обратно.

**Оценка:** СРЕДНЯЯ ЦЕННОСТЬ. Было бы полезно для длинных операций, но TeamCreate уже обрабатывает жизненный цикл за нас.

### 2.3 Web Dashboard ⭐⭐

Next.js dashboard с:
- Список сессий в реальном времени
- PR/CI статус бейджи
- Activity dots (active/ready/idle)
- Terminal embed
- SSE для real-time обновлений

**У нас:** Всё в терминале. Нет визуального мониторинга.

**Оценка:** ЖЕЛАТЕЛЬНО, но большой scope. Не приоритет для текущих задач.

### 2.4 Multi-Agent Fleet Management ⭐⭐⭐

AO может запустить 30 агентов на 30 разных issues одновременно, каждый в своём worktree:

```bash
ao spawn my-project 101
ao spawn my-project 102
ao spawn my-project 103
# 3 agents, 3 worktrees, 3 branches, 3 PRs
```

**У нас:** Agent Teams работают ВНУТРИ одной задачи. У нас нет "запусти 10 задач и мониторь их все".

**Оценка:** ВЫСОКАЯ ЦЕННОСТЬ для бот-флота. Сейчас мы синхронизируем ботов через TeamCreate из основной сессии, но AO мог бы это автоматизировать.

### 2.5 Convention-over-Configuration ⭐

AO автоматически выводит пути из минимального конфига (3 обязательных поля):

```yaml
projects:
  my-app:
    repo: owner/my-app
    path: ~/my-app
    defaultBranch: main
# Всё остальное — auto-derived
```

**У нас:** Много конфигурации разбросано по файлам (config.yaml, CLAUDE.md, agent registry, etc.).

**Оценка:** ПРИЯТНО, но не критично. Наша конфигурация уже работает.

### 2.6 Hash-Based Namespacing ⭐

```typescript
instanceId = sha256(dirname(configPath)).slice(0, 12) + "-" + projectId
// Prevents collisions between multiple orchestrator checkouts
```

**У нас:** Не нужно — мы не запускаем несколько экземпляров шаблона одновременно.

**Оценка:** НИЗКАЯ ЦЕННОСТЬ для нас.

---

## Part 3: What We Have That AO Doesn't

### 3.1 Memory System ⭐⭐⭐

Наша 3-слойная память не имеет аналога в AO:
- **Typed memory** (knowledge.md): Паттерны + готчи с decay по Ebbinghaus
- **Graphiti**: Семантическая память через MCP
- **Daily logs + activeContext.md**: Сессионный контекст

AO: Нет кросс-сессионной памяти вообще. Каждый spawned агент начинает с нуля (кроме issue context).

### 3.2 Pipeline State Machine ⭐⭐⭐

Наш PIPELINE.md с фазами, гейтами, вердиктами и `<- CURRENT` маркерами — это формальная state machine для сложных задач.

AO: Простая линейная модель (spawn → work → PR → merge). Нет фаз, нет гейтов, нет рабочих процессов.

### 3.3 Expert Panel ⭐⭐

3-5 экспертных агентов анализируют задачу с разных перспектив ДО реализации.

AO: Нет аналога. Агенты получают issue и сразу пишут код.

### 3.4 Quality Gates & QA Validation Loop ⭐⭐⭐

4-verdict model (PASS/CONCERNS/REWORK/FAIL) + автоматический QA цикл (reviewer → fixer → re-reviewer).

AO: Качество = CI checks + PR reviews. Нет внутреннего QA до PR.

### 3.5 Compaction Survival ⭐⭐

`<- CURRENT` маркеры + Phase Transition Protocol + typed memory спасают контекст при compaction.

AO: Не нужно — внешний процесс не теряет контекст (он в Node.js памяти, не в LLM context window).

### 3.6 Skills/Guides Ecosystem ⭐⭐

47 skills, 10+ guides, загружаемые по триггерам.

AO: Нет skills. Конфигурация через YAML + user rules.

---

## Part 4: Overlap Analysis

### Что делают ОБЕ системы (и кто делает лучше):

| Capability | AO | Our System | Winner |
|------------|-----|-----------|--------|
| **Agent spawning** | External (tmux + CLI) | Native (TeamCreate) | **Tie** — different approach |
| **Prompt building** | 3-layer composition | CLAUDE.md + skills + prompts | **Our system** — more sophisticated |
| **Error recovery** | Reaction engine + retries | Recovery manager + attempt history | **AO** — more automated |
| **State tracking** | Flat-file metadata | PIPELINE.md + STATE.md | **Our system** — more structured |
| **Git workflow** | Auto worktree + auto branch | Manual or via pipeline | **AO** — more automated |
| **PR lifecycle** | Full (CI + review + merge) | Not handled | **AO** — we don't have this |
| **Monitoring** | Web dashboard | Terminal only | **AO** — visual |
| **Quality assurance** | CI checks + PR reviews | 4-verdict gates + QA loop | **Our system** — pre-PR quality |

---

## Part 5: Integration Scenarios

### Scenario A: Use AO as External Fleet Manager (RECOMMENDED)

```
AO (outer loop):
  ao spawn bot-1 "sync template"
  ao spawn bot-2 "fix migration bug #42"
  ao spawn bot-3 "add new feature"
  ao monitor & react to CI/reviews

Each spawned agent (inner loop):
  Uses our CLAUDE.md + skills + pipeline system
  Executes: SPEC → PLAN → IMPLEMENT → QA → TEST
  Memory preserved via typed memory + Graphiti
```

**Pros:**
- Best of both worlds
- AO handles what we're bad at (fleet management, CI reactions, PR lifecycle)
- Our system handles what AO is bad at (complex task decomposition, quality gates, memory)

**Cons:**
- Two systems to maintain
- TypeScript dependency (AO) alongside our Python ecosystem
- Need to sync AO config with our `.claude/` structure

### Scenario B: Adopt AO Patterns Into Our System (ALTERNATIVE)

Не использовать AO как софт, а перенять ключевые паттерны:

1. **Reaction Engine** → Реализовать как hook или skill
2. **Activity Detection** → Читать JSONL для мониторинга Agent Teams
3. **Session State Machine** → Расширить PIPELINE.md формальными статусами
4. **Convention-over-Config** → Упростить нашу конфигурацию
5. **Fleet Spawn** → Skill для batch-spawning агентов по issues

**Pros:**
- Одна система (наша), обогащённая лучшими идеями
- Нет TypeScript зависимости
- Полный контроль

**Cons:**
- Больше работы по реализации
- Можем не достичь того же уровня автоматизации
- Придётся поддерживать reaction engine самим

### Scenario C: Replace Our System With AO (NOT RECOMMENDED)

**Почему нет:**
- Теряем memory system (нет аналога в AO)
- Теряем quality gates (AO полагается на CI, которого у наших ботов нет)
- Теряем pipeline state machine (AO — простая линейная модель)
- Теряем 47 skills и guides
- Теряем compaction survival
- AO не поддерживает Windows нативно (tmux не работает)

---

## Part 6: Конкретные Паттерны Для Заимствования

### 6.1 ОБЯЗАТЕЛЬНО ВЗЯТЬ (High Value, Low Effort)

#### P1: Layered Prompt Composition
AO строит промпты из 3 слоёв: base + config-derived + user rules.
У нас уже похоже (CLAUDE.md + skills + prompts), но можно формализовать.

**Action:** Создать `.claude/prompts/prompt-composer.md` — гайд по слоям промптов.

#### P2: Flat-File Session Metadata
AO хранит состояние сессий как `key=value` файлы. Простой, bash-совместимый формат.

**Action:** Для наших Agent Teams записывать metadata в `work/sessions/{team-name}/{agent-name}.meta`.

#### P3: Activity Detection via JSONL
AO читает `~/.claude/projects/` для определения состояния агента.

**Action:** Создать скрипт `.claude/scripts/agent-activity.py` для мониторинга текущих Team agents.

### 6.2 ЖЕЛАТЕЛЬНО ВЗЯТЬ (High Value, Medium Effort)

#### P4: Reaction Engine Concept
Автоматические реакции на события (CI fail → fix, review comment → address).

**Action:** Создать `.claude/skills/reaction-engine/SKILL.md` — протокол автоматических реакций.
Для начала: простые реакции через hooks (PostToolUseFailure → log + suggest fix).

#### P5: Fleet Spawn Command
`ao spawn` одной командой создаёт worktree + branch + agent.

**Action:** Создать skill `/fleet-spawn` для batch-операций с ботами (sync, update, migrate).

### 6.3 РАССМОТРЕТЬ (Medium Value, High Effort)

#### P6: Web Dashboard
Визуальный мониторинг — приятно, но большой scope.

**Action:** НЕ сейчас. Возможно в будущем если бот-флот вырастет до 20+.

#### P7: CI/PR Lifecycle Management
Автоматическое создание PR, мониторинг CI, forwarding review comments.

**Action:** НЕ сейчас. Наши боты не имеют CI пайплайнов. Если появятся — рассмотреть.

### 6.4 НЕ БРАТЬ (Low Value for Us)

- Hash-based namespacing (нет мультиинстанс проблемы)
- Plugin slot architecture (мы не агностичны по агентам)
- tmux/Docker/K8s runtimes (используем TeamCreate)
- Linear tracker integration (не используем Linear)

---

## Part 7: Risk Assessment

### If We Adopt AO (Scenario A)

| Risk | Level | Mitigation |
|------|-------|------------|
| Windows compatibility | HIGH | AO depends on tmux which doesn't work on Windows |
| Maintenance burden | MEDIUM | Two codebases to maintain |
| Version drift | MEDIUM | AO updates may break our integration |
| TypeScript dependency | LOW | We can install Node.js alongside Python |

### If We Adopt Patterns Only (Scenario B)

| Risk | Level | Mitigation |
|------|-------|------------|
| Implementation time | MEDIUM | Focus on P1-P3 first, iterate |
| Incomplete adoption | LOW | We already have most of the foundation |
| Over-engineering | MEDIUM | Strict "only what we need" policy |

---

## Part 8: Recommendation

### Рекомендация: **Scenario B — Adopt Patterns, Not Software**

**Причины:**

1. **Windows limitation** — AO зависит от tmux, который не работает на Windows. Это блокер для Scenario A.

2. **Мы уже впереди по памяти и quality gates** — наша memory system + pipeline state machine + QA validation loop более зрелые, чем у AO.

3. **AO решает проблему, которой у нас пока нет** — fleet management для 30 агентов по 30 issues. У нас 8-10 ботов, и мы управляем ими через TeamCreate.

4. **Лучшие идеи AO можно реализовать как skills** — reaction engine, activity detection, fleet spawn — это не rocket science.

### Конкретный План Действий

| Priority | Pattern | Effort | Skill/Guide |
|----------|---------|--------|-------------|
| **P1** | Layered prompt composition | Small | Update teammate-prompt-template.md |
| **P2** | Flat-file session metadata | Small | work/sessions/ convention |
| **P3** | Activity detection | Medium | .claude/scripts/agent-activity.py |
| **P4** | Reaction engine concept | Medium | .claude/skills/reaction-engine/ |
| **P5** | Fleet spawn command | Medium | .claude/skills/fleet-spawn/ |

**Timeline:** P1-P2 можно сделать за одну сессию. P3-P5 — по сессии каждый.

---

## Appendix: File-by-File AO Structure

```
agent-orchestrator/
├── agent-orchestrator.yaml          # Config (single source of truth)
├── CLAUDE.md                        # Dev conventions
├── ARCHITECTURE.md                  # Architecture overview
├── packages/
│   ├── core/src/
│   │   ├── types.ts                 # All interfaces (1000+ lines)
│   │   ├── config.ts                # Zod-validated config loading
│   │   ├── paths.ts                 # Hash-based namespacing
│   │   ├── metadata.ts              # Flat-file key=value store
│   │   ├── session-manager.ts       # Session CRUD
│   │   ├── lifecycle-manager.ts     # State machine + reactions
│   │   ├── prompt-builder.ts        # 3-layer prompt composition
│   │   ├── plugin-registry.ts       # Plugin discovery
│   │   ├── tmux.ts                  # Tmux wrappers
│   │   └── orchestrator-prompt.ts   # Base agent prompt
│   ├── cli/src/
│   │   ├── commands/                # ao init/spawn/status/send/session
│   │   └── lib/                     # Helpers
│   ├── plugins/                     # 16 built-in plugins
│   │   ├── agent-claude-code/       # Claude Code integration (800+ lines)
│   │   ├── agent-codex/             # Codex integration
│   │   ├── agent-aider/             # Aider integration
│   │   ├── runtime-tmux/            # tmux runtime
│   │   ├── workspace-worktree/      # Git worktree workspace
│   │   ├── tracker-github/          # GitHub issues
│   │   ├── scm-github/              # GitHub PR/CI/review (600+ lines)
│   │   ├── notifier-slack/          # Slack notifications
│   │   └── ...                      # 8 more plugins
│   └── web/src/                     # Next.js dashboard
│       ├── app/page.tsx             # Session list
│       ├── app/sessions/[id]/       # Session detail + terminal
│       └── app/api/                 # REST API routes
├── examples/                        # Config examples
└── docs/                            # Design docs
```
