#!/usr/bin/env python3
"""Unit tests for task-spec-validator.py."""
from __future__ import annotations

import importlib.util
import json
import logging
import tempfile
import unittest
from pathlib import Path

logger = logging.getLogger("test_task_spec_validator")

SCRIPT_PATH = Path(__file__).resolve().with_name("task-spec-validator.py")


def load_validator():
    logger.debug("entry: load_validator", extra={"extra_fields": {"path": str(SCRIPT_PATH)}})
    spec = importlib.util.spec_from_file_location("task_spec_validator", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load task-spec-validator.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    logger.debug("exit: load_validator", extra={"extra_fields": {"loaded": True}})
    return module


VALID_SPEC = """---
executor: dual
risk_class: routine
reasoning: high
---

# Task X: valid

## Your Task

Build the validator and keep it read-only.

## Scope Fence

**Allowed:**
- `.claude/scripts/task-spec-validator.py`

**Forbidden:**
- Any other path

## Test Commands

```bash
py -3 .claude/scripts/test_task_spec_validator.py
py -3 .claude/scripts/task-spec-validator.py --help
```

## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: CLI accepts one or more specs.
- [ ] AC2: Frontmatter is validated.
- [ ] AC3: Required sections are validated.
- [ ] AC4: JSON output is valid.
- [ ] AC5: Strict mode escalates warnings.
- [ ] AC6: Missing files continue processing.
- [ ] AC7: Logging is structured.
- [ ] AC8: Stdlib only.
- [ ] AC9: Windows paths work.
- [ ] AC10: All Test Commands above exit 0.

## Handoff Output

Standard handoff.
"""


def write_spec(root: Path, name: str, text: str) -> Path:
    logger.debug("entry: write_spec", extra={"extra_fields": {"name": name}})
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    logger.debug("exit: write_spec", extra={"extra_fields": {"path": str(path)}})
    return path


class TaskSpecValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        logger.debug("entry: setUpClass", extra={"extra_fields": {}})
        cls.validator = load_validator()
        logger.debug("exit: setUpClass", extra={"extra_fields": {}})

    def validate_text(self, text: str):
        logger.debug("entry: validate_text", extra={"extra_fields": {"chars": len(text)}})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = write_spec(root, "work/demo/tasks/task-X.md", text)
            report = self.validator.validate_file(path, root)
        logger.debug("exit: validate_text", extra={"extra_fields": {"overall": report.overall}})
        return report

    def status_for(self, report, name: str) -> str:
        logger.debug("entry: status_for", extra={"extra_fields": {"name": name}})
        for check in report.checks:
            if check.name == name:
                logger.debug("exit: status_for", extra={"extra_fields": {"status": check.status}})
                return check.status
        raise AssertionError(f"missing check {name}")

    def test_happy_path_passes_all_checks(self) -> None:
        report = self.validate_text(VALID_SPEC)
        self.assertEqual(report.overall, "ok")
        self.assertTrue(all(check.status == "ok" for check in report.checks))

    def test_missing_frontmatter_fails(self) -> None:
        report = self.validate_text(VALID_SPEC.split("---\n", 2)[-1])
        self.assertEqual(self.status_for(report, "frontmatter.present"), "fail")
        self.assertEqual(report.overall, "fail")

    def test_invalid_executor_value_fails(self) -> None:
        report = self.validate_text(VALID_SPEC.replace("executor: dual", "executor: robot"))
        self.assertEqual(self.status_for(report, "frontmatter.executor"), "fail")

    def test_missing_scope_fence_fails(self) -> None:
        text = VALID_SPEC.replace("## Scope Fence", "## Scope Notes")
        report = self.validate_text(text)
        self.assertEqual(self.status_for(report, "section.scope_fence"), "fail")

    def test_three_acceptance_criteria_warns(self) -> None:
        weak = """## Acceptance Criteria (IMMUTABLE)

- [ ] AC1: One.
- [ ] AC2: Two.
- [ ] All Test Commands above exit 0.

## Handoff Output"""
        text = VALID_SPEC.split("## Acceptance Criteria (IMMUTABLE)")[0] + weak + "\nDone.\n"
        report = self.validate_text(text)
        self.assertEqual(self.status_for(report, "section.acceptance_criteria"), "warn")
        self.assertEqual(report.overall, "warn")

    def test_no_test_commands_block_fails(self) -> None:
        text = VALID_SPEC.replace("```bash\npy -3 .claude/scripts/test_task_spec_validator.py\npy -3 .claude/scripts/task-spec-validator.py --help\n```", "No commands here.")
        report = self.validate_text(text)
        self.assertEqual(self.status_for(report, "section.test_commands"), "fail")

    def test_strict_escalates_warn_to_fail(self) -> None:
        report = self.validate_text(VALID_SPEC.replace("- [ ] AC7: Logging is structured.\n- [ ] AC8: Stdlib only.\n- [ ] AC9: Windows paths work.\n", ""))
        strict = self.validator.apply_strict(report)
        self.assertEqual(report.overall, "warn")
        self.assertEqual(strict.overall, "fail")
        self.assertTrue(any("strict" in check.detail for check in strict.checks))

    def test_missing_file_fails_and_exit_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code = self.validator.run(["--project-root", tmp, str(Path(tmp) / "missing.md")])
        self.assertEqual(code, 1)

    def test_multiple_files_mixed_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            good = write_spec(root, "task-good.md", VALID_SPEC)
            bad = write_spec(root, "task-bad.md", VALID_SPEC.replace("executor: dual", "executor: bad"))
            reports = [self.validator.validate_file(good, root), self.validator.validate_file(bad, root)]
        self.assertEqual([report.overall for report in reports], ["ok", "fail"])

    def test_json_roundtrip(self) -> None:
        report = self.validate_text(VALID_SPEC)
        payload = self.validator.to_json_payload([report])
        dumped = json.dumps(payload)
        self.assertEqual(json.loads(dumped)["files"][0]["overall"], "ok")

    def test_json_schema_complete(self) -> None:
        report = self.validate_text(VALID_SPEC)
        payload = self.validator.to_json_payload([report])
        self.assertEqual(set(payload), {"files", "summary"})
        self.assertEqual(set(payload["files"][0]), {"path", "checks", "overall"})
        self.assertEqual(set(payload["files"][0]["checks"][0]), {"name", "status", "detail"})
        self.assertEqual(set(payload["summary"]), {"fail", "warn", "ok", "files"})

    def test_exception_during_check_becomes_fail(self) -> None:
        result = self.validator.safe_check("boom", lambda: (_ for _ in ()).throw(ValueError("bad check")))
        self.assertEqual(result.status, "fail")
        self.assertEqual(result.name, "boom")
        self.assertIn("bad check", result.detail)


if __name__ == "__main__":
    unittest.main(verbosity=2)
