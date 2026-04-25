"""dual-teams-spawn.py -- DUAL_TEAMS orchestration helper.

For each T{i}.md: creates paired claude+codex worktrees, writes Claude
teammate prompt via spawn-agent.py, launches codex-wave.py in background,
writes work/<feature>/dual-teams-plan.md. Prep + report only -- does NOT
spawn the Agent tool.
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


logger = logging.getLogger("dual_teams_spawn")

DEFAULT_WORKTREE_BASE = Path("worktrees/dual-teams")
DEFAULT_CODEX_WAVE_SCRIPT = Path(".claude/scripts/codex-wave.py")
DEFAULT_SPAWN_AGENT_SCRIPT = Path(".claude/scripts/spawn-agent.py")
DEFAULT_LOG_DIR = Path(".claude/logs")
_TASK_ID_RE = re.compile(r"T(\d+)", re.IGNORECASE)


@dataclass
class TaskPair:
    """Dual-worktree record for one task spec."""
    task_id: str
    task_file: str
    claude_worktree: str
    claude_branch: str
    codex_worktree: str
    codex_branch: str
    claude_prompt_file: str
    claude_prompt_status: str = "pending"
    claude_prompt_error: Optional[str] = None


@dataclass
class WavePlan:
    """Captured background-process reference for the Codex side."""
    pid: Optional[int]
    cmd: list[str]
    log_file: str
    started: bool
    error: Optional[str] = None
    result_dir: Optional[str] = None


@dataclass
class PlanResult:
    """Complete orchestration outcome consumed by _write_report."""
    feature: str
    timestamp: str
    worktree_base: str
    parallel: int
    pairs: list[TaskPair] = field(default_factory=list)
    wave: Optional[WavePlan] = None
    report_path: Optional[str] = None
    dry_run: bool = False


def _configure_logging(verbose: bool = False) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")


def derive_task_id(task_file: Path) -> str:
    """T{N} id from filename; fall back to stem."""
    m = _TASK_ID_RE.search(task_file.stem)
    return f"T{m.group(1)}" if m else task_file.stem


def expand_tasks(tasks_arg: str) -> list[Path]:
    """Expand comma-separated task file paths (dedup by absolute path)."""
    logger.info("expand_tasks_started tasks_arg=%r", tasks_arg)
    seen: set[str] = set()
    result: list[Path] = []
    for entry in (p.strip() for p in tasks_arg.split(",") if p.strip()):
        abs_e = str(Path(entry).resolve())
        if abs_e not in seen:
            seen.add(abs_e)
            result.append(Path(entry))
    logger.info("expand_tasks_completed count=%d", len(result))
    return result


def _run(cmd: list[str], cwd: Optional[Path] = None,
         timeout: Optional[int] = None) -> tuple[int, str, str]:
    """Blocking subprocess; (rc, stdout, stderr)."""
    logger.debug("run_cmd cmd=%r cwd=%s timeout=%s", cmd, cwd, timeout)
    proc = subprocess.run(cmd, cwd=str(cwd) if cwd else None,
                          capture_output=True, text=True,
                          check=False, timeout=timeout)
    logger.debug("run_cmd_done rc=%d", proc.returncode)
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def _write_base_ref_sidecar(project_root: Path, worktree_path: Path,
                            base: str) -> None:
    """Best-effort `<worktree>/.dual-base-ref` sidecar (SHA + LF). Swallow errors."""
    logger.info("write_base_ref_sidecar_started worktree=%s base=%s", worktree_path, base)
    try:
        rc, out, err = _run(["git", "rev-parse", base], cwd=project_root)
    except Exception as exc:
        logger.warning("write_base_ref_sidecar_revparse_crashed err=%s", exc)
        return
    sha = (out or "").strip()
    if rc != 0 or not sha:
        logger.warning("write_base_ref_sidecar_revparse_failed rc=%d err=%s", rc, (err or "").strip())
        return
    sidecar = worktree_path / ".dual-base-ref"
    try:
        sidecar.write_bytes((sha + "\n").encode("utf-8"))
    except OSError as exc:
        logger.warning("write_base_ref_sidecar_write_failed path=%s err=%s", sidecar, exc)
        return
    logger.info("write_base_ref_sidecar_completed path=%s sha=%s", sidecar, sha)


def create_worktree(project_root: Path, worktree_path: Path, branch: str,
                    base: str = "HEAD") -> None:
    """Create git worktree; RuntimeError on failure. Removes stale entries."""
    logger.info("create_worktree_started path=%s branch=%s base=%s",
                worktree_path, branch, base)
    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    if worktree_path.exists():
        logger.warning("create_worktree_stale path=%s", worktree_path)
        _run(["git", "worktree", "remove", "--force", str(worktree_path)],
             cwd=project_root)
    rc, out, err = _run(
        ["git", "worktree", "add", "-b", branch, str(worktree_path), base],
        cwd=project_root)
    if rc != 0:
        logger.error("create_worktree_failed rc=%d stderr=%s", rc, err.strip())
        raise RuntimeError(
            f"git worktree add failed (rc={rc}): {err.strip() or out.strip()}")
    logger.info("create_worktree_completed path=%s", worktree_path)
    _write_base_ref_sidecar(project_root, worktree_path, base)


def remove_worktree(project_root: Path, worktree_path: Path) -> None:
    """Best-effort rollback of a worktree we created in this run."""
    logger.info("remove_worktree_started path=%s", worktree_path)
    rc, _, err = _run(
        ["git", "worktree", "remove", "--force", str(worktree_path)],
        cwd=project_root)
    if rc != 0:
        logger.warning("remove_worktree_failed rc=%d stderr=%s", rc, err.strip())
    else:
        logger.info("remove_worktree_completed path=%s", worktree_path)


def generate_claude_prompt(spawn_agent_script: Path, task_file: Path,
                           prompt_output: Path, team_name: str,
                           agent_name: str, project_root: Path,
                           ) -> tuple[bool, Optional[str]]:
    """Invoke spawn-agent.py; (ok, err). Soft failure."""
    logger.info("generate_claude_prompt_started task=%s output=%s",
                task_file, prompt_output)
    prompt_output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(spawn_agent_script),
           "--task", f"Implement task spec: {task_file}",
           "--team", team_name, "--name", agent_name,
           "--output", str(prompt_output)]
    try:
        rc, out, err = _run(cmd, cwd=project_root, timeout=120)
    except subprocess.TimeoutExpired:
        logger.error("generate_claude_prompt_timeout task=%s", task_file)
        return False, "spawn-agent.py timed out after 120s"
    except FileNotFoundError as exc:
        logger.exception("generate_claude_prompt_script_missing")
        return False, f"spawn-agent.py not found: {exc}"
    except Exception as exc:
        logger.exception("generate_claude_prompt_crashed")
        return False, f"spawn-agent.py crashed: {exc}"
    if rc != 0:
        logger.error("generate_claude_prompt_failed rc=%d", rc)
        return False, f"spawn-agent.py rc={rc}: {err.strip() or out.strip()}"
    if not prompt_output.is_file():
        logger.error("generate_claude_prompt_missing_output %s", prompt_output)
        return False, f"spawn-agent.py rc=0 but {prompt_output} missing"
    logger.info("generate_claude_prompt_completed path=%s", prompt_output)
    return True, None


def launch_codex_wave(codex_wave_script: Path, task_files: list[Path],
                      parallel: int, worktree_base: Path, log_file: Path,
                      project_root: Path, base_branch: str,
                      result_dir: Optional[Path] = None) -> WavePlan:
    """Launch codex-wave.py in background; capture PID + log."""
    cmd = [sys.executable, str(codex_wave_script),
           "--tasks", ",".join(str(t) for t in task_files),
           "--parallel", str(parallel),
           "--worktree-base", str(worktree_base),
           "--base-branch", base_branch]
    resolved_result_dir = result_dir.resolve() if result_dir is not None else None
    if resolved_result_dir is not None:
        cmd += ["--result-dir", str(resolved_result_dir)]
    logger.info("launch_codex_wave_started cmd=%r log=%s parallel=%d",
                cmd, log_file, parallel)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        fh = open(log_file, "ab", buffering=0)
    except OSError as exc:
        logger.exception("launch_codex_wave_log_open_failed")
        return WavePlan(None, cmd, str(log_file), False,
                        error=f"cannot open log file: {exc}",
                        result_dir=(str(resolved_result_dir)
                                    if resolved_result_dir is not None else None))
    kw: dict = dict(stdout=fh, stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL, cwd=str(project_root))
    if os.name == "nt":
        kw["creationflags"] = getattr(subprocess,
                                      "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        kw["start_new_session"] = True
    try:
        proc = subprocess.Popen(cmd, **kw)  # noqa: S603
    except FileNotFoundError as exc:
        fh.close()
        logger.exception("launch_codex_wave_script_missing")
        return WavePlan(None, cmd, str(log_file), False,
                        error=f"codex-wave.py not found: {exc}",
                        result_dir=(str(resolved_result_dir)
                                    if resolved_result_dir is not None else None))
    except Exception as exc:
        fh.close()
        logger.exception("launch_codex_wave_crashed")
        return WavePlan(None, cmd, str(log_file), False,
                        error=f"Popen failed: {exc}",
                        result_dir=(str(resolved_result_dir)
                                    if resolved_result_dir is not None else None))
    logger.info("launch_codex_wave_started_ok pid=%d", proc.pid)
    try:
        fh.close()
    except Exception:
        logger.warning("launch_codex_wave_fh_close_warn")
    return WavePlan(proc.pid, cmd, str(log_file), True,
                    result_dir=(str(resolved_result_dir)
                                if resolved_result_dir is not None else None))


def build_plan(task_files: list[Path], project_root: Path,
               worktree_base: Path, feature: str) -> list[TaskPair]:
    """Materialize TaskPair records; no side effects."""
    logger.info("build_plan_started tasks=%d worktree_base=%s feature=%s",
                len(task_files), worktree_base, feature)
    prompts_dir = project_root / "work" / feature / "prompts"
    pairs: list[TaskPair] = []
    for tf in task_files:
        tid = derive_task_id(tf)
        pairs.append(TaskPair(
            task_id=tid, task_file=str(tf),
            claude_worktree=str((project_root / worktree_base / "claude" / tid).resolve()),
            claude_branch=f"claude/dual-teams/{tid}",
            codex_worktree=str((project_root / worktree_base / "codex" / tid).resolve()),
            codex_branch=f"codex/dual-teams/{tid}",
            claude_prompt_file=str(prompts_dir / f"{tid}-claude.md"),
        ))
    logger.info("build_plan_completed pairs=%d", len(pairs))
    return pairs


def _write_report(report_path: Path, plan: PlanResult) -> None:
    """Write the Opus-facing orchestration report."""
    logger.info("write_report_started path=%s pairs=%d",
                report_path, len(plan.pairs))
    report_path.parent.mkdir(parents=True, exist_ok=True)
    L: list[str] = [f"# dual-teams plan -- feature: {plan.feature}", "",
                    f"- timestamp: {plan.timestamp}",
                    f"- worktree_base: `{plan.worktree_base}`",
                    f"- parallel: {plan.parallel}",
                    f"- pairs: {len(plan.pairs)}"]
    if plan.dry_run:
        L.append("- mode: **DRY RUN (nothing created)**")
    L += ["", "## Task pairs"]
    for p in plan.pairs:
        L += [f"### {p.task_id}",
              f"- task_file: `{p.task_file}`",
              f"- claude_worktree: `{p.claude_worktree}` (branch `{p.claude_branch}`)",
              f"- codex_worktree:  `{p.codex_worktree}` (branch `{p.codex_branch}`)",
              f"- claude_prompt:   `{p.claude_prompt_file}` [{p.claude_prompt_status}]"]
        if p.claude_prompt_error:
            L.append(f"  - prompt_error: `{p.claude_prompt_error}`")
        L.append("")
    L.append("## Codex wave (background)")
    if plan.wave is None:
        L.append("- (not launched -- dry run or no tasks)")
    elif plan.wave.started:
        L += [f"- pid: `{plan.wave.pid}`",
              f"- log: `{plan.wave.log_file}`"]
        if plan.wave.result_dir:
            L.append(f"- result_dir: {plan.wave.result_dir}")
        L.append(f"- cmd: `{' '.join(plan.wave.cmd)}`")
    else:
        L += [f"- **failed to start**: {plan.wave.error}",
              f"- attempted cmd: `{' '.join(plan.wave.cmd)}`"]
        if plan.wave.result_dir:
            L.append(f"- result_dir: {plan.wave.result_dir}")
    L += ["", "## Instructions for Opus", "",
          "1. Spawn N Claude teammates (one per task) via TeamCreate. Use each",
          "   prompt file above; each teammate's cwd is its claude_worktree.", "",
          "2. Wait on the Codex wave (background PID above). Monitor with:"]
    if plan.wave and plan.wave.started:
        L.append(f'       tasklist /FI "PID eq {plan.wave.pid}"'
                 if os.name == "nt" else f"       ps -p {plan.wave.pid}")
        L.append(f"       tail -f {plan.wave.log_file}")
    else:
        L.append("       (codex wave did not start -- see error above)")
    L += ["", "3. Paired results:",
          "   - Claude diffs: each claude_worktree (branch claude/dual-teams/T{i})",
          "   - Codex diffs:  each codex_worktree (branch codex/dual-teams/T{i})",
          "   - Codex result.md: work/codex-implementations/task-T{i}-result.md", "",
          "4. Use cross-model-review skill to judge each pair; pick winner or hybrid.",
          ""]
    report_path.write_text("\n".join(L) + "\n", encoding="utf-8")
    logger.info("write_report_completed bytes=%d", report_path.stat().st_size)


def orchestrate(task_files: list[Path], feature: str, project_root: Path,
                worktree_base: Path, parallel: int,
                codex_wave_script: Path, spawn_agent_script: Path,
                log_dir: Path, base_branch: str, dry_run: bool,
                result_dir: Optional[Path] = None) -> PlanResult:
    """Main orchestration: plan -> worktrees -> prompts -> Codex wave."""
    logger.info("orchestrate_started tasks=%d feature=%s parallel=%d dry_run=%s",
                len(task_files), feature, parallel, dry_run)
    plan = PlanResult(
        feature=feature,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        worktree_base=str(worktree_base), parallel=parallel,
        pairs=build_plan(task_files, project_root, worktree_base, feature),
        dry_run=dry_run)
    if dry_run:
        logger.info("orchestrate_dry_run pairs=%d", len(plan.pairs))
        return plan
    created: list[Path] = []
    for pair in plan.pairs:
        try:
            create_worktree(project_root, Path(pair.claude_worktree),
                            pair.claude_branch, base_branch)
            created.append(Path(pair.claude_worktree))
            create_worktree(project_root, Path(pair.codex_worktree),
                            pair.codex_branch, base_branch)
            created.append(Path(pair.codex_worktree))
        except Exception as exc:
            logger.exception("orchestrate_worktree_failed id=%s", pair.task_id)
            for wt in reversed(created):
                remove_worktree(project_root, wt)
            raise RuntimeError(
                f"worktree creation failed for {pair.task_id}: {exc}") from exc
    for pair in plan.pairs:
        ok, err = generate_claude_prompt(
            spawn_agent_script=spawn_agent_script,
            task_file=Path(pair.task_file),
            prompt_output=Path(pair.claude_prompt_file),
            team_name=f"dual-{feature}",
            agent_name=f"{pair.task_id}-claude",
            project_root=project_root)
        pair.claude_prompt_status = "ok" if ok else "error"
        pair.claude_prompt_error = err
    log_file = log_dir / f"codex-wave-{feature}-{int(time.time())}.log"
    plan.wave = launch_codex_wave(
        codex_wave_script=codex_wave_script,
        task_files=[Path(p.task_file) for p in plan.pairs],
        parallel=parallel, worktree_base=worktree_base / "codex",
        log_file=log_file, project_root=project_root, base_branch=base_branch,
        result_dir=result_dir)
    logger.info("orchestrate_completed pairs=%d wave_started=%s",
                len(plan.pairs), plan.wave.started if plan.wave else False)
    return plan


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dual-teams-spawn.py",
        description="Orchestrate DUAL_TEAMS: paired Claude+Codex worktrees "
                    "per T{i}.md, generate prompts, launch codex-wave.py, "
                    "write plan report. Opus spawns the Agent tool.")
    p.add_argument("--tasks", required=True)
    p.add_argument("--feature", required=True)
    p.add_argument("--parallel", type=int, default=0)
    p.add_argument("--worktree-base", default=str(DEFAULT_WORKTREE_BASE))
    p.add_argument("--base-branch", default="HEAD")
    p.add_argument("--codex-wave-script", default=str(DEFAULT_CODEX_WAVE_SCRIPT))
    p.add_argument("--spawn-agent-script", default=str(DEFAULT_SPAWN_AGENT_SCRIPT))
    p.add_argument("--log-dir", default=str(DEFAULT_LOG_DIR))
    p.add_argument("--result-dir", type=Path, default=None,
                   help="If set, passed through as `--result-dir` to the "
                        "spawned codex-wave.py so result.md files land at "
                        "this absolute path. Recommended: "
                        "`<project_root>/work/codex-implementations` so "
                        "the orchestrator's codex-delegate-enforcer can "
                        "find them.")
    p.add_argument("--project-root", default=".")
    p.add_argument("--report", default=None)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--verbose", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _configure_logging(args.verbose)
    project_root = Path(args.project_root).resolve()
    worktree_base = Path(args.worktree_base)
    codex_wave_script = Path(args.codex_wave_script)
    spawn_agent_script = Path(args.spawn_agent_script)
    log_dir = Path(args.log_dir)
    logger.info("main_started tasks=%s feature=%s parallel=%d dry_run=%s",
                args.tasks, args.feature, args.parallel, args.dry_run)
    task_files = expand_tasks(args.tasks)
    if not task_files:
        logger.error("main_no_tasks tasks_arg=%r", args.tasks)
        print("ERROR: no task files supplied", file=sys.stderr)
        return 2
    missing = [t for t in task_files if not Path(t).is_file()]
    if missing:
        logger.error("main_missing_task_files count=%d", len(missing))
        for m in missing:
            print(f"ERROR: task file not found: {m}", file=sys.stderr)
        return 2
    if not args.dry_run:
        for script, label in ((codex_wave_script, "codex-wave"),
                              (spawn_agent_script, "spawn-agent")):
            if not script.is_file():
                logger.error("main_script_missing label=%s path=%s",
                             label, script)
                print(f"ERROR: {label} script not found: {script}",
                      file=sys.stderr)
                return 2
    parallel = args.parallel if args.parallel > 0 else len(task_files)
    try:
        plan = orchestrate(
            task_files=task_files, feature=args.feature,
            project_root=project_root, worktree_base=worktree_base,
            parallel=parallel, codex_wave_script=codex_wave_script,
            spawn_agent_script=spawn_agent_script, log_dir=log_dir,
            base_branch=args.base_branch, dry_run=args.dry_run,
            result_dir=args.result_dir)
    except RuntimeError as exc:
        logger.error("main_orchestrate_failed err=%s", exc)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    report_path = Path(args.report) if args.report else (
        project_root / "work" / args.feature / "dual-teams-plan.md")
    _write_report(report_path, plan)
    plan.report_path = str(report_path)
    print(f"dual-teams plan -- feature={args.feature} pairs={len(plan.pairs)} "
          f"dry_run={plan.dry_run}")
    for p in plan.pairs:
        print(f"  {p.task_id:6s} claude={p.claude_worktree}  "
              f"codex={p.codex_worktree}  prompt={p.claude_prompt_status}")
    if plan.wave and plan.wave.started:
        print(f"codex-wave PID={plan.wave.pid} log={plan.wave.log_file}")
    elif plan.wave and plan.wave.error:
        print(f"codex-wave FAILED TO LAUNCH: {plan.wave.error}")
    print(f"Report: {report_path}")
    logger.info("main_completed report=%s pairs=%d",
                report_path, len(plan.pairs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
