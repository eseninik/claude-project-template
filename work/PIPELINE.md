---
status: PHASE_3_TUNNEL_AUTH
mode: AUTONOMOUS_WITH_CONFIRM_GATES
created: 2026-04-27
goal: Deploy VS Code Remote Tunnels on Contabo to enable cross-device development (laptop/desktop/phone via vscode.dev) for the claude-project-template-update project, preserving the Always-Dual + Codex enforcer system end-to-end without breaking the production codex-image-bridge.
---

# PIPELINE — Remote Tunnels deployment + project transport + dual-implement live verification

## Context

User wants device-independent access to the same Claude Code sessions from any device. Server (admin@173.212.204.36, Contabo, Ubuntu 24.04) already runs production codex-image-bridge.service. Strategy: VS Code Remote Tunnels (outbound-only, no inbound port), tmux for session durability across devices, full Claude/Codex/dual-implement stack on server.

## Codex top-5 risks (gpt-5.5 second opinion 2026-04-27)

1. Tunnel service identity drift → install as `admin` user, NEVER sudo. Enable lingering for reboot persistence.
2. Accidental exposure of `127.0.0.1:18799` (image-bridge) via VS Code port-forwarding → set `remote.autoForwardPorts: false`, blacklist 18799, never mark public.
3. Single-client tunnel semantics → use tmux as durable session source; treat VS Code clients as disposable views.
4. `.claude/` portability gaps → git transports tracked files only; verify hooks, executable bits, dual-implement enforcer in dry-run after transport.
5. Performance/resource contention with image-bridge → monitor CPU/RAM; rollback if production bridge degrades.

## Server snapshot (2026-04-27 06:35)

| Resource | Status |
|---|---|
| OS / kernel | Ubuntu 24.04.4 LTS / 6.8.0-110 |
| CPU / RAM | AMD EPYC 8 cores / 23 GB (14 free, load 0.26) |
| Disk | 193 GB (87 free) |
| Node / Python / git / tmux | 22.22 / 3.12 / 2.43 / 3.4 — all present |
| codex-cli | 0.125.0 ✓ auth.json fresh (2026-04-26) |
| @anthropic-ai/claude-code | 2.1.114 ✓ (`/usr/bin/claude` works) |
| code (VS Code CLI) | 1.117.0 ✓ ~/.local/bin/code (Phase 2 done) |
| codex-image-bridge.service | active 15h, port 127.0.0.1:18799 — DO NOT DISTURB |
| openclaw-gateway / openclaw-node | active — DO NOT DISTURB |
| DNS / outbound HTTPS | healthy |

## Phases

### Phase 1: PRECHECK ✅
- [x] T1.1: SSH connectivity + resource snapshot
- [x] T1.2: Verify image-bridge health (active, no errors)
- [x] T1.3: Codex 5-risk review captured
- [x] T1.4: DNS sanity (false alarm — `global.code.visualstudio.com` does not exist; canonical endpoints all resolve)

### Phase 2: INSTALL_CODE_CLI ✅
- [x] T2.1: Download from `https://update.code.visualstudio.com/latest/cli-linux-x64/stable` (11.1 MB)
- [x] T2.2: Extract `code` binary to `~/.local/bin/code` — 30 MB single bin, owned by admin
- [x] T2.3: PATH already in `~/.profile`
- [x] T2.4: `code --version` → 1.117.0; `code tunnel --help` shows valid subcommands

### Phase 3: TUNNEL_AUTH_AND_SERVICE ← CURRENT
- [ ] T3.1: Run `code tunnel user login --provider github` inside tmux on server (capture device code + URL)
- [ ] T3.2: USER ACTION REQUIRED: open URL, enter device code, authorize
- [ ] T3.3: Poll login state until success
- [ ] T3.4: `code tunnel --name contabo-dev --accept-server-license-terms` foreground first → validate connectivity
- [ ] T3.5: Stop foreground, install user systemd service: `code tunnel service install --name contabo-dev --accept-server-license-terms`
- [ ] T3.6: One-time `sudo loginctl enable-linger admin` (additive systemd state, justifiable)
- [ ] T3.7: `systemctl --user status code-tunnel` shows active
- [ ] T3.8: Smoke test from local Windows browser at `https://vscode.dev/tunnel/contabo-dev`
- Gate: tunnel reachable from local browser; survives `systemctl --user restart`.

### Phase 4: PORT_FORWARD_HARDENING
- [ ] T4.1: Create `~/.config/Code/User/settings.json` on server with `remote.autoForwardPorts: false` + portsAttributes blacklist (18799, 18789, 18791)
- [ ] T4.2: After first connect, verify in VS Code "Ports" tab — 18799 not auto-forwarded
- [ ] T4.3: Pre/post `ss -ltnp | grep 18799` — only image-bridge should listen
- Gate: image-bridge port confirmed isolated.

### Phase 5: TRANSPORT_PROJECT
- [ ] T5.1: Determine transport (GitHub remote vs git bundle) — likely git bundle since this is a local template repo
- [ ] T5.2: `mkdir -p ~/projects && git clone <source> claude-project-template-update`
- [ ] T5.3: Checkout branch `fix/watchdog-dushnost`
- [ ] T5.4: Restore exec bits on `.claude/scripts/*.py` and `.claude/hooks/*.py`
- Gate: project tree on server matches local; exec bits preserved.

### Phase 6: VERIFY_HOOKS_LINUX
- [ ] T6.1: Audit hook commands — replace `py -3` with `python3` where needed
- [ ] T6.2: Add `~/.local/bin/py` shim if scripts hardcode `py`
- [ ] T6.3: Run no-op edit on a `.py` file → verify `codex-delegate-enforcer.py` fires correctly
- [ ] T6.4: `python3 .claude/scripts/dual-teams-selftest.py` — must pass 6/6
- [ ] T6.5: `python3 -m pytest .claude/tests/` — must remain 268/268 green
- Gate: 268 tests + selftest 6/6 + delegate-enforcer ledger writes.

### Phase 7: LIVE_DUAL_IMPLEMENT_TEST
- [ ] T7.1: Author tiny well-defined task `tasks/REMOTE-VERIFY-1.md`
- [ ] T7.2: Trigger `dual-teams-spawn` end-to-end
- [ ] T7.3: Verify both implementations complete; judge produces verdict
- Gate: end-to-end dual cycle completes without manual intervention.

### Phase 8: PARALLEL_VERIFICATION (Agent Teams Mode)
- [ ] T8.1: Spawn 3 parallel agents:
  - A: latency benchmark (keystroke RTT, throughput vs local baseline)
  - B: hook coverage scan (synthetic events through every handler)
  - C: production-impact check (image-bridge response times before/during/after tunnel load)
- [ ] T8.2: Aggregate findings into `work/remote-tunnels-verification.md`
- Gate: zero production-bridge regressions; terminal latency in acceptable band.

### Phase 9: DOCUMENT_AND_MEMORY
- [ ] T9.1: Write `work/remote-tunnels-setup-report.md`
- [ ] T9.2: Update `.claude/memory/activeContext.md`
- [ ] T9.3: Append to `.claude/memory/daily/2026-04-27.md`
- [ ] T9.4: Replace stale `feedback_no_remote_dev.md` with `feedback_remote_tunnels_adopted.md`
- [ ] T9.5: Add knowledge.md entries on tunnel + port-forward security
- Gate: memory consistent with current reality.

## Rollback policy

- Phase 2-3 fail → remove `~/.local/bin/code`, `systemctl --user disable code-tunnel`, no system damage.
- Phase 4 fail → kill tunnel, image-bridge intact (independent).
- Phase 5 fail → `rm -rf ~/projects/claude-project-template-update`, no impact.
- Phase 6-7 fail → STOP, deliver report, do NOT modify hooks blindly. User decides.
- Production bridge degradation → immediately stop tunnel, monitor recovery, do NOT proceed without root cause.

## Mode notes

- Agent Teams Mode activated only in Phase 8 — earlier phases sequential by dependency.
- Codex consulted at every gate (pre-flight, Phase 2 URL, will repeat at Phase 7 design + Phase 8 design).
- No PROD changes outside `~/.local/`, `~/.config/Code/User/`, `~/projects/`, plus one `loginctl enable-linger admin`.
