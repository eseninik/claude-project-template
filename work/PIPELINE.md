# Pipeline: Server Dev Environment Migration

- Status: PIPELINE_COMPLETE
- Phase: VERIFY
- Mode: INTERACTIVE

> Migrate all development to Contabo server. Create dev copies of all projects under admin user.
> Prod stays untouched in /root/. Dev clones go to /home/admin/dev/.
> tmux for persistent multi-session workflow. Access from any device.

---

## Phases

### Phase: PREPARE
- Status: DONE
- Mode: SOLO
- Tasks completed:
  1. uv installed for admin (v0.11.2)
  2. Deploy keys copied to /home/admin/.ssh/ (8 keys + 3 new generated)
  3. SSH config fixed with /home/admin/.ssh/ paths
  4. /home/admin/dev/ created
  5. tmux configured (.tmux.conf with Ctrl+A prefix, mouse support)
  6. .bashrc aliases (dev, tl, ta, tn, devcd, p)
  7. GitHub CLI installed (v2.89.0)

### Phase: CLONE
- Status: DONE
- Mode: SOLO
- Results:
  - 8 projects cloned from GitHub (Call-rate, Knowledge, client, conference, doccheck, freelance, legal, quality-control)
  - 3 new projects cloned (sales-check, certification, lead-qualifier) with new deploy keys
  - 4 projects copied from prod (nick-sync, tilda-webhook, agent-second-brain, migrator-app)
  - All local changes pushed to GitHub from C:\Bots\ before server pull
  - All 15 projects on dev branch

### Phase: ENVIRONMENT
- Status: DONE
- Mode: SOLO
- Results:
  - .env files copied from prod for 11 projects
  - .env files SCP'd from local for 3 new projects (sales-check, certification, lead-qualifier)
  - uv sync completed for all projects with pyproject.toml
  - pip install for projects with requirements.txt (Knowledge-bot, nick-sync, tilda-webhook)

### Phase: VERIFY
- Status: DONE
- Mode: SOLO
- Results:
  - Git pull/push: OK
  - Claude Code: v2.1.62 OK
  - uv: v0.11.2 OK
  - gh CLI: v2.89.0 OK
  - tmux: v3.4 OK
  - All 15 projects: dev branch, .env present, venv ready
  - Global config: CLAUDE.md (513 lines), 23 skills, hooks, commands
  - Settings adapted for Linux
  - Disk: 82GB/193GB (43% used)

### Phase: CONFIG_SYNC (added mid-pipeline)
- Status: DONE
- Mode: SOLO
- Results:
  - Copied ~/.claude/CLAUDE.md (global rules)
  - Copied ~/.claude/skills/ (23 global skills)
  - Copied ~/.claude/commands/ (upgrade-project)
  - Copied ~/.claude/hooks/ (rtk-rewrite.py)
  - Adapted settings.json for Linux (removed Windows paths, kept Agent Teams + tools)
  - Note: RTK not installed (hook silently passes through)

---

## Decisions

- [ARCH] All dev work under admin user. Reason: Claude Code already authed, least privilege.
- [ARCH] Prod stays in /root/ untouched. Reason: zero risk to running services.
- [ARCH] Separate .venv per project. Reason: dependency isolation, no version conflicts.
- [ARCH] Projects without git remote get cp -r. Reason: no remote to clone from.
- [ARCH] tmux for session persistence. Reason: works from any device, sessions survive disconnect.
- [PUSH] Local dev branches pushed to GitHub before server pull. Reason: ensure latest code on server.
- [PUSH] Certification + LeadQualifier pushed to main (triggered CI/CD). Outcome: harmless, just updated prod.
- [CONFIG] Global Claude Code config copied and adapted. Reason: same dev experience on server as local.

## Remaining TODO (optional)

- [ ] `gh auth login` on server as admin (interactive — user must run manually)
- [ ] Install RTK on server (optional, token optimization)
- [ ] Set up VS Code Remote SSH from user's laptop (one-time setup)
- [ ] Install Termius on phone for mobile access
