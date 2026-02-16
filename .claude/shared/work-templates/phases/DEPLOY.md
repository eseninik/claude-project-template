# Phase Template: DEPLOY

> Merge code, deploy to server via SSH, restart service, verify health.

## Metadata
- Default Mode: SOLO
- Gate Type: AUTO
- Loop Target: FIX (on deploy failure)
- Max Attempts: 2
- Checkpoint: pipeline-checkpoint-DEPLOY

## Inputs
- Passing test suite (from TEST phase)
- Server connection config (SSH_SERVER_CONNECTION.md or .env)
- Service name (systemd unit)

## Process
1. Merge feature branch to dev:
   ```bash
   git checkout dev && git merge feature/{name} --no-ff
   ```
2. Push to remote: `git push origin dev`
3. Upload code to server:
   ```bash
   rsync -avz --exclude='.venv' --exclude='__pycache__' --exclude='.git' \
     ./ user@server:/app/
   ```
4. Install dependencies on server:
   ```bash
   ssh user@server "cd /app && pip install -r requirements.txt"
   ```
5. Restart service:
   ```bash
   ssh user@server "sudo systemctl restart mybot.service"
   ```
6. Wait 5 seconds, then verify health:
   ```bash
   ssh user@server "sudo systemctl is-active mybot.service"
   ssh user@server "curl -sf http://localhost:8080/health"
   ```
7. Write deployment log to `work/{feature}/deployment-log.md`

## Outputs
- `work/{feature}/deployment-log.md` (timestamps, commands, results)
- Deployed and running service on server

## Quality Gate
```bash
ssh user@server "sudo systemctl is-active mybot.service"
ssh user@server "curl -sf http://localhost:8080/health"
```

### Verdicts
- PASS: Service active, health check returns 200
- CONCERNS: Service active but health check slow (>2s response)
- REWORK: Service failed to start -> check logs, fix, retry (loop to FIX)
- FAIL: Max deploy attempts reached or server unreachable

## Context Recovery
After compaction, re-read:
- `work/PIPELINE.md` (find current phase + attempt count)
- `work/{feature}/deployment-log.md` (if exists — see what was tried)
- `SSH_SERVER_CONNECTION.md` (server connection details)
