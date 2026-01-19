# Integration Test Scenarios

> Test cases for validating the new orchestration and automation features.

---

## Test 1: Orchestrator Intent Classification

### 1.1 Trivial Intent

**Input:** "Что такое async/await?"

**Expected:**
- Intent type: `trivial`
- Confidence: ~0.95
- Action: Direct response, no skills needed
- No orchestration pipeline started

**Verification:** Agent answers directly without invoking skills or subagents.

---

### 1.2 Explicit Intent (Feature)

**Input:** "autowork: добавь кнопку logout в header"

**Expected:**
- Intent type: `autowork` (explicit)
- Confidence: 1.0
- Pipeline: Full autowork (spec → implement → UAT → verify)
- Skills selected: user-spec-planning, tech-spec-planning, subagent-driven-development

**Verification:**
- [ ] Intent classified correctly
- [ ] Asks for user-spec details
- [ ] Creates tech-spec with tasks
- [ ] Executes via subagent-driven-development
- [ ] Runs UAT before completion

---

### 1.3 Exploratory Intent

**Input:** "улучши производительность бота"

**Expected:**
- Intent type: `exploratory`
- Confidence: ~0.6
- Action: Use context-capture skill first
- Ask clarifying questions

**Verification:**
- [ ] Recognized as exploratory (vague)
- [ ] Asks clarifying questions before proceeding
- [ ] Does NOT immediately start implementing

---

### 1.4 Ambiguous Intent

**Input:** "сделай что-нибудь с авторизацией"

**Expected:**
- Intent type: `ambiguous`
- Confidence: ~0.4
- Action: Ask user for clarification
- Present options (A/B/C)

**Verification:**
- [ ] Recognized as ambiguous
- [ ] Presents interpretation options
- [ ] Waits for user choice

---

## Test 2: Session Auto-Resume

### Setup

Create `work/STATE.md` with incomplete task:

```markdown
## Текущая работа

- **Task:** Implement user authentication
- **Phase:** implementation
- **Status:** in_progress
- **Feature:** user-auth

## Следующие шаги

- Complete JWT token generation
- Add password validation
- Write tests

## Session Notes

**2026-01-18:**
- Started auth implementation
- Created user model
```

### Test

**Action:** Start new session

**Expected:**
```
📋 Незавершённая работа:
- Task: Implement user authentication
- Status: in_progress
- Last session: 2026-01-18

Продолжить? (да/нет/показать детали)
```

**Verification:**
- [ ] STATE.md detected and parsed
- [ ] Summary displayed correctly (Russian)
- [ ] User prompted for choice
- [ ] If "да": context loaded, work continues
- [ ] If "нет": STATE.md cleared, fresh start

---

## Test 3: Context Monitor

### 3.1 Warning at 50%

**Setup:** Load multiple large files to reach ~50% context

**Action:**
```
Read: large-file-1.py (500 lines)
Read: large-file-2.py (500 lines)
Read: large-file-3.py (500 lines)
... continue until ~50%
```

**Expected:**
```
⚠️ Контекст: ~50%
Начинается деградация качества.
Рекомендую завершить текущую задачу или использовать субагента.
```

**Verification:**
- [ ] Warning displayed at ~50%
- [ ] Work continues (not blocked)
- [ ] Subagent suggested for new tasks

---

### 3.2 Block at 70%

**Setup:** Continue loading until ~70%

**Expected:**
```
🛑 Контекст: ~70% - КРИТИЧЕСКИЙ УРОВЕНЬ
Качество существенно снижено.

Варианты:
1. Завершить сессию
2. Использовать субагента
3. Override (на свой риск)
```

**Verification:**
- [ ] Block message displayed
- [ ] New complex tasks blocked
- [ ] Override mechanism works if user requests

---

## Test 4: Background Task Tracking

### Setup

Start subagent-driven-development with 3+ independent tasks.

### Test

**Action:** Monitor `work/background-tasks.json`

**Expected JSON updates:**

1. Task dispatched:
```json
{
  "tasks": [{
    "id": "task-001-wave1",
    "status": "running",
    "startedAt": "2026-01-19T10:00:00Z"
  }]
}
```

2. Task completed:
```json
{
  "tasks": [{
    "id": "task-001-wave1",
    "status": "completed",
    "completedAt": "2026-01-19T10:05:30Z",
    "result": "User model created"
  }]
}
```

**Verification:**
- [ ] JSON created at start
- [ ] Tasks added when dispatched
- [ ] Status updated on completion
- [ ] Wave tracking works
- [ ] Duration calculated correctly

---

## Test 5: Autowork Pipeline (Full)

### Input

```
autowork: добавь простую форму контакта
```

### Expected Flow

1. **Intent Classification**
   - [ ] Type: autowork (explicit)
   - [ ] Confidence: 1.0

2. **Spec Generation**
   - [ ] Mini user-spec interview started
   - [ ] User-spec.md created
   - [ ] User approval requested
   - [ ] Tech-spec.md created with tasks
   - [ ] User approval requested

3. **Execution**
   - [ ] subagent-driven-development invoked
   - [ ] Tasks executed (parallel if independent)
   - [ ] Code review after each task/wave
   - [ ] Progress tracked in background-tasks.json

4. **Quality Gates**
   - [ ] UAT scenarios generated from user-spec
   - [ ] UAT checklist presented to user
   - [ ] User confirmation received
   - [ ] Verification skill invoked

5. **Completion**
   - [ ] Commit offered
   - [ ] STATE.md updated

### Verification Checklist

- [ ] Full pipeline executed without errors
- [ ] Each phase completed before next started
- [ ] User approvals obtained at checkpoints
- [ ] UAT NOT skipped
- [ ] Verification NOT skipped
- [ ] Files created: user-spec.md, tech-spec.md, tasks/*.md, implementation

---

## Test 6: Error Recovery

### 6.1 Edit Error Recovery

**Setup:** Trigger Edit failure (old_string not found)

**Expected:**
1. Error detected
2. error-recovery skill pattern applied
3. File re-read
4. Edit retried with correct content
5. Success or escalation after 3 attempts

**Verification:**
- [ ] Error caught
- [ ] Recovery attempted
- [ ] Escalated if unrecoverable

---

### 6.2 Test Failure Recovery

**Setup:** Run failing test

**Expected:**
1. Test failure detected
2. error-recovery invokes systematic-debugging
3. Root cause analysis performed
4. Fix NOT proposed until root cause identified

**Verification:**
- [ ] systematic-debugging triggered
- [ ] No premature fix proposals
- [ ] Root cause reported

---

### 6.3 Timeout Recovery

**Setup:** Run slow command that times out

**Expected:**
1. Timeout detected
2. Retry with longer timeout
3. Or run in background

**Verification:**
- [ ] Timeout handled gracefully
- [ ] Recovery attempted
- [ ] User notified if persistent

---

## Test 7: Self-Completion

### Setup

Create TodoWrite with 6 pending items:
1. Task A
2. Task B
3. Task C
4. Task D
5. Task E
6. Task F

### Test

**Action:** Start self-completion

**Expected:**
- Tasks 1-5 completed automatically
- At task 6: `<max_iterations>` marker output
- Message: "Completed 5 tasks. 1 remaining."
- User asked whether to continue

**Verification:**
- [ ] Auto-continues without prompting (tasks 1-5)
- [ ] Stops at max_iterations (5)
- [ ] Marker output correctly
- [ ] Progress visible in todo list

---

## Summary Checklist

| Test | Component | Status |
|------|-----------|--------|
| 1.1 | Orchestrator - Trivial | ⬜ |
| 1.2 | Orchestrator - Explicit | ⬜ |
| 1.3 | Orchestrator - Exploratory | ⬜ |
| 1.4 | Orchestrator - Ambiguous | ⬜ |
| 2 | Session Auto-Resume | ⬜ |
| 3.1 | Context Monitor - Warning | ⬜ |
| 3.2 | Context Monitor - Block | ⬜ |
| 4 | Background Task Tracking | ⬜ |
| 5 | Autowork Pipeline | ⬜ |
| 6.1 | Error Recovery - Edit | ⬜ |
| 6.2 | Error Recovery - Test | ⬜ |
| 6.3 | Error Recovery - Timeout | ⬜ |
| 7 | Self-Completion | ⬜ |

---

## Notes

- Tests are manual (no automated test framework for agent behavior)
- Execute in fresh session for accurate context measurement
- Document any issues found in test-results.md
