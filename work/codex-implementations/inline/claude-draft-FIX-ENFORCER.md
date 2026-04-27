# Claude-side draft for FIX-ENFORCER (paired with codex run on `worktrees/fix-enforcer/codex`)

> Living draft. Will be applied once codex result.md lands at `work/codex-implementations/task-FIX-ENFORCER-result.md` and clears the enforcer.

## Patch — `.claude/hooks/codex-delegate-enforcer.py`

Insert immediately above `def decide(payload, project_dir):` (currently line 385):

```python
def is_dual_teams_worktree(project_dir: Path) -> bool:
    """True iff project_dir (or any ancestor up to the filesystem root) holds
    a regular file named ``.dual-base-ref``.

    The sentinel is written by ``codex-wave.py`` / ``dual-teams-spawn.py``
    into every freshly-created teammate worktree to record the diff
    baseline. Its presence means:
      * the agent IS the writer-half of an ongoing dual-implement run, and
      * a parallel Codex sibling is already executing the same task spec.
    In that case the enforcer would only deadlock the writer half — Codex
    coverage already exists by construction. Allow all edits in this tree.
    """
    logger = logging.getLogger(HOOK_NAME)
    logger.debug("is_dual_teams_worktree.enter project_dir=%s", project_dir)
    try:
        cur = project_dir.resolve()
    except (OSError, ValueError) as exc:
        logger.debug("is_dual_teams_worktree.resolve_fail exc=%s", exc)
        return False
    seen: set = set()
    while True:
        if cur in seen:
            break
        seen.add(cur)
        try:
            if (cur / ".dual-base-ref").is_file():
                logger.debug("is_dual_teams_worktree.match path=%s", cur)
                return True
        except OSError as exc:
            logger.debug("is_dual_teams_worktree.probe_err path=%s exc=%s", cur, exc)
        if cur.parent == cur:
            break
        cur = cur.parent
    logger.debug("is_dual_teams_worktree.no_match")
    return False
```

Insert into `decide()` immediately after the `tool_name not in {"Edit","Write","MultiEdit"}` check (currently line 396):

```python
    if is_dual_teams_worktree(project_dir):
        logger.info(
            "decide.passthrough reason=dual-teams-worktree project=%s", project_dir
        )
        return True
```

## Tests — `.claude/hooks/test_codex_delegate_enforcer.py`

Append a new test class (the existing fixture in `BaseEnforcerTest` covers everything we need):

```python
class TestDualTeamsSentinel(BaseEnforcerTest):
    """Sentinel-based exemption for dual-teams writer-half worktrees."""

    def test_sentinel_in_project_dir_returns_true(self):
        m = _load_module()
        (self.root / ".dual-base-ref").write_text("c0ffee\n", encoding="utf-8")
        self.assertTrue(m.is_dual_teams_worktree(self.root))

    def test_sentinel_in_ancestor_returns_true(self):
        m = _load_module()
        deep = self.root / "a" / "b" / "c" / "d"
        deep.mkdir(parents=True)
        (self.root / ".dual-base-ref").write_text("c0ffee\n", encoding="utf-8")
        self.assertTrue(m.is_dual_teams_worktree(deep))

    def test_no_sentinel_returns_false(self):
        m = _load_module()
        self.assertFalse(m.is_dual_teams_worktree(self.root))

    def test_sentinel_as_directory_returns_false(self):
        m = _load_module()
        (self.root / ".dual-base-ref").mkdir()
        self.assertFalse(m.is_dual_teams_worktree(self.root))

    def test_decide_allows_edit_when_sentinel_present(self):
        m = _load_module()
        (self.root / ".dual-base-ref").write_text("c0ffee\n", encoding="utf-8")
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": ".claude/scripts/foo.py"},
        }
        self.assertTrue(m.decide(payload, self.root))

    def test_decide_denies_edit_when_sentinel_absent(self):
        # Existing behavior: no sentinel + no fresh result.md -> deny
        m = _load_module()
        rc, stdout, _stderr = self._run_enforcer({
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": ".claude/scripts/foo.py"},
        })
        self.assertEqual(rc, 0)
        body = json.loads(stdout)
        self.assertEqual(
            body["hookSpecificOutput"]["permissionDecision"], "deny"
        )
```

## Mental model

The sentinel is the *single source of truth* for "this is a dual-teams worktree":
- `.gitignore` ignores it → preflight is happy (Y7 fix)
- `codex-delegate-enforcer.py` walks ancestors looking for it → enforcer is happy (Y6 fix)
- Future code (judge.py already, anything else that must distinguish "dual" from "main") can ask the same question

One sentinel file → two regressions resolved → one new well-named helper that future code can lean on.
