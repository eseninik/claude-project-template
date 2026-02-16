# Deploy Integration Design

**Date:** 2026-02-16
**Scope:** Complete deployment pipeline for Python/Telegram bot projects
**Flow:** `feature/{name} -> dev -> main -> deploy to server`

---

## 1. Git Workflow

### Branch Strategy

```
feature/{name}   Created by pipeline from dev, one per task/feature
dev              Main development branch, all features merge here
main             Production-stable, deploys from here
```

### Automated Git Steps (Pipeline Phase: GIT_RELEASE)

```bash
# 1. Create feature branch (at IMPLEMENT phase start)
git checkout dev
git pull origin dev
git checkout -b feature/{task-name}

# 2. Develop + test on feature branch (IMPLEMENT + TEST phases)
# ... normal development ...

# 3. Create PR (after TEST passes)
gh pr create \
  --base dev \
  --title "feat: {task-name}" \
  --body "$(cat work/test-results.md)"

# 4. Merge to dev (after review gate)
gh pr merge --squash --delete-branch

# 5. Tag release (at GIT_RELEASE phase)
git checkout dev && git pull
NEXT_TAG=$(git tag -l 'v*' | sort -V | tail -1 | awk -F. '{$NF+=1; print $0}' OFS=.)
git tag -a "$NEXT_TAG" -m "Release $NEXT_TAG"
git push origin dev --tags

# 6. Fast-forward main to dev
git checkout main && git merge --ff-only dev && git push origin main
```

### Release Tagging Convention

```
v{major}.{minor}.{patch}

major: breaking changes, new architecture
minor: new features, new bot commands
patch: bug fixes, config changes, dependency updates
```

### PR Body Template

```markdown
## Changes
{auto-generated from git log --oneline feature..dev}

## Test Results
{contents of work/test-results.md}

## Checklist
- [ ] Tests pass
- [ ] No secrets in diff
- [ ] Requirements.txt updated (if dependencies changed)
```

---

## 2. SSH Deployment Protocol (Windows Git Bash -> Linux VPS)

### Connection Setup

```bash
# Environment variables (from .env or pipeline config)
SSH_KEY="$HOME/.ssh/deploy_key"
SSH_USER="deploy"
SSH_HOST="server.example.com"
APP_DIR="/opt/mybot"
SERVICE_NAME="mybot.service"

SSH_CMD="ssh -i $SSH_KEY -o StrictHostKeyChecking=accept-new $SSH_USER@$SSH_HOST"
```

### Code Upload

```bash
# rsync from Windows (Git Bash) to Linux VPS
rsync -avz \
  --exclude='.venv' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='.claude' \
  --exclude='work' \
  --exclude='*.pyc' \
  --exclude='.env' \
  -e "ssh -i $SSH_KEY" \
  ./ "$SSH_USER@$SSH_HOST:$APP_DIR/"
```

**Excludes rationale:**
- `.venv` -- server has its own venv
- `__pycache__`, `*.pyc` -- recompiled on server
- `.git`, `.claude`, `work` -- dev-only, not needed on server
- `.env` -- server has its own env file (never overwrite)

### Dependency Installation

```bash
$SSH_CMD "cd $APP_DIR && source .venv/bin/activate && pip install -r requirements.txt"
```

### Service Management

```bash
# Restart
$SSH_CMD "sudo systemctl restart $SERVICE_NAME"

# Check status
$SSH_CMD "sudo systemctl status $SERVICE_NAME --no-pager"
```

### Full Deploy Script

```bash
#!/bin/bash
# deploy.sh — Deploy Python bot to VPS
set -euo pipefail

SSH_KEY="${SSH_KEY:-$HOME/.ssh/deploy_key}"
SSH_USER="${SSH_USER:-deploy}"
SSH_HOST="${SSH_HOST:-server.example.com}"
APP_DIR="${APP_DIR:-/opt/mybot}"
SERVICE_NAME="${SERVICE_NAME:-mybot.service}"
SSH_CMD="ssh -i $SSH_KEY -o StrictHostKeyChecking=accept-new $SSH_USER@$SSH_HOST"

echo "=== Uploading code ==="
rsync -avz \
  --exclude='.venv' --exclude='__pycache__' --exclude='.git' \
  --exclude='.claude' --exclude='work' --exclude='*.pyc' --exclude='.env' \
  -e "ssh -i $SSH_KEY" \
  ./ "$SSH_USER@$SSH_HOST:$APP_DIR/"

echo "=== Installing dependencies ==="
$SSH_CMD "cd $APP_DIR && source .venv/bin/activate && pip install -r requirements.txt"

echo "=== Restarting service ==="
$SSH_CMD "sudo systemctl restart $SERVICE_NAME"

echo "=== Deploy complete ==="
```

---

## 3. Post-Deploy Verification

### Health Check Polling

```bash
HEALTH_URL="http://localhost:8080/health"
MAX_RETRIES=3
RETRY_DELAY=5

for i in $(seq 1 $MAX_RETRIES); do
  echo "Health check attempt $i/$MAX_RETRIES..."
  RESPONSE=$($SSH_CMD "curl -s -o /dev/null -w '%{http_code}' $HEALTH_URL" 2>/dev/null)
  if [ "$RESPONSE" = "200" ]; then
    echo "Health check PASSED"
    exit 0
  fi
  echo "Got HTTP $RESPONSE, retrying in ${RETRY_DELAY}s..."
  sleep $RETRY_DELAY
done

echo "Health check FAILED after $MAX_RETRIES attempts"
exit 1
```

### Log Monitoring

```bash
# Check for errors in last 2 minutes of logs
$SSH_CMD "journalctl -u $SERVICE_NAME --since '2 min ago' --no-pager"

# Check for Python tracebacks
ERROR_COUNT=$($SSH_CMD "journalctl -u $SERVICE_NAME --since '2 min ago' | grep -c 'Traceback\|Error\|Exception' || true")
if [ "$ERROR_COUNT" -gt 0 ]; then
  echo "WARNING: $ERROR_COUNT errors found in logs"
fi
```

### Rollback Protocol

```bash
# Rollback to previous git tag
PREV_TAG=$(git tag -l 'v*' | sort -V | tail -2 | head -1)

echo "Rolling back to $PREV_TAG..."

# 1. Checkout previous version locally
git checkout "$PREV_TAG"

# 2. Re-deploy previous version
rsync -avz \
  --exclude='.venv' --exclude='__pycache__' --exclude='.git' \
  --exclude='.claude' --exclude='work' --exclude='*.pyc' --exclude='.env' \
  -e "ssh -i $SSH_KEY" \
  ./ "$SSH_USER@$SSH_HOST:$APP_DIR/"

# 3. Reinstall deps + restart
$SSH_CMD "cd $APP_DIR && source .venv/bin/activate && pip install -r requirements.txt"
$SSH_CMD "sudo systemctl restart $SERVICE_NAME"

# 4. Verify rollback
sleep 5
RESPONSE=$($SSH_CMD "curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/health")
if [ "$RESPONSE" = "200" ]; then
  echo "Rollback successful"
else
  echo "CRITICAL: Rollback failed! Manual intervention required."
  exit 2
fi

# 5. Return to dev branch
git checkout dev
```

---

## 4. Stress Testing with Locust

### locustfile.py Template

```python
"""Stress test template for Telegram bot projects.

Usage:
  locust -f locustfile.py --headless -u 100 -r 10 --run-time 60s --host http://server:8080
"""
from locust import HttpUser, task, between


class TelegramBotUser(HttpUser):
    """Simulates Telegram webhook traffic to the bot."""

    wait_time = between(0.5, 2)

    @task(1)
    def health_check(self):
        """Lightweight health endpoint."""
        self.client.get("/health")

    @task(5)
    def send_text_message(self):
        """Simulate a /start or text message webhook."""
        self.client.post("/webhook", json={
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {"id": 100, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 100, "type": "private"},
                "date": 1700000000,
                "text": "/start"
            }
        })

    @task(2)
    def send_callback_query(self):
        """Simulate inline button press."""
        self.client.post("/webhook", json={
            "update_id": 123456790,
            "callback_query": {
                "id": "cb_1",
                "from": {"id": 100, "is_bot": False, "first_name": "Test"},
                "message": {
                    "message_id": 2,
                    "chat": {"id": 100, "type": "private"},
                    "date": 1700000000
                },
                "data": "action:test"
            }
        })
```

### Running Stress Tests

```bash
# From local machine, targeting deployed server
locust -f locustfile.py \
  --headless \
  -u 100 \         # 100 concurrent users
  -r 10 \          # ramp up 10 users/second
  --run-time 60s \ # run for 60 seconds
  --host "http://$SSH_HOST:8080" \
  --csv=work/stress-results

# Or run on the server itself for lower latency measurement
$SSH_CMD "cd $APP_DIR && locust -f locustfile.py --headless -u 100 -r 10 --run-time 60s --host http://localhost:8080 --csv=/tmp/stress-results"
scp -i "$SSH_KEY" "$SSH_USER@$SSH_HOST:/tmp/stress-results_stats.csv" work/stress-results_stats.csv
```

### Success Criteria (Quality Gate)

| Metric | Threshold | Action on Fail |
|--------|-----------|----------------|
| Response time p50 | < 200ms | CONCERNS |
| Response time p95 | < 500ms | REWORK |
| Response time p99 | < 2000ms | FAIL |
| Error rate | < 1% | FAIL |
| Requests/sec | > 50 | CONCERNS |

### Results Collection

```bash
# Parse CSV results into performance-report.md
cat > work/performance-report.md << 'REPORT'
# Performance Report

**Date:** $(date +%Y-%m-%d)
**Target:** $SSH_HOST:8080
**Config:** 100 users, 10 ramp-up/s, 60s duration

## Results

$(column -t -s',' work/stress-results_stats.csv | head -20)

## Verdict

{PASS | CONCERNS | REWORK | FAIL based on thresholds above}
REPORT
```

---

## 5. Pipeline Phase Definitions

### Phase: GIT_RELEASE

```markdown
### Phase: GIT_RELEASE
- Status: NOT_STARTED
- Mode: SOLO
- On PASS: -> DEPLOY
- On FAIL: -> BLOCKED (alert user)
- Gate: PR merged, tag created, main updated

Process:
1. Create PR from feature branch to dev
2. Include test-results.md in PR body
3. Merge PR (squash)
4. Create version tag
5. Fast-forward main to dev
```

### Phase: DEPLOY

```markdown
### Phase: DEPLOY
- Status: NOT_STARTED
- Mode: SOLO
- Attempts: 0 of 2
- On PASS: -> SMOKE_TEST
- On FAIL: -> ROLLBACK
- On ROLLBACK_PASS: -> BLOCKED (manual fix needed)
- Gate: rsync success, systemctl restart success

Process:
1. rsync code to server (excluding dev files)
2. Install dependencies on server
3. Restart systemd service
4. Verify service is running (systemctl status)
```

### Phase: SMOKE_TEST

```markdown
### Phase: SMOKE_TEST
- Status: NOT_STARTED
- Mode: SOLO
- On PASS: -> STRESS_TEST
- On FAIL: -> DEPLOY (rollback + retry)
- Gate: health check returns 200, no errors in logs

Process:
1. Poll health endpoint (3x, 5s delay)
2. Check journalctl for errors
3. If health OK and no errors -> PASS
4. If health fails -> trigger rollback -> FAIL
```

### Phase: STRESS_TEST

```markdown
### Phase: STRESS_TEST
- Status: NOT_STARTED
- Mode: SOLO
- On PASS: -> PIPELINE_COMPLETE
- On CONCERNS: -> PIPELINE_COMPLETE (with notes)
- On FAIL: -> BLOCKED (performance issue)
- Gate: p95 < 500ms, error_rate < 1%

Process:
1. Run locust with standard config
2. Collect CSV results
3. Generate performance-report.md
4. Evaluate against thresholds
```

---

## 6. Environment Configuration

### .env Variables for Deploy

```bash
# Deploy configuration (in .env, never committed)
DEPLOY_SSH_KEY=~/.ssh/deploy_key
DEPLOY_SSH_USER=deploy
DEPLOY_SSH_HOST=server.example.com
DEPLOY_APP_DIR=/opt/mybot
DEPLOY_SERVICE_NAME=mybot.service
DEPLOY_HEALTH_URL=http://localhost:8080/health
```

### Server Prerequisites

```bash
# One-time server setup (manual or via init script)
sudo useradd -m -s /bin/bash deploy
sudo mkdir -p /opt/mybot
sudo chown deploy:deploy /opt/mybot

# Python environment
cd /opt/mybot
python3 -m venv .venv

# Systemd service
sudo tee /etc/systemd/system/mybot.service << 'EOF'
[Unit]
Description=Telegram Bot
After=network.target

[Service]
Type=simple
User=deploy
WorkingDirectory=/opt/mybot
ExecStart=/opt/mybot/.venv/bin/python -m bot
Restart=always
RestartSec=5
EnvironmentFile=/opt/mybot/.env

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable mybot.service
```

---

## 7. GitHub Actions CI/CD (Optional)

```yaml
# .github/workflows/deploy.yml
name: Deploy to VPS

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pytest --tb=short

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.SSH_HOST }}
          username: ${{ secrets.SSH_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/mybot
            git pull origin main
            source .venv/bin/activate
            pip install -r requirements.txt
            sudo systemctl restart mybot.service

      - name: Health Check
        run: |
          for i in 1 2 3; do
            sleep 5
            STATUS=$(curl -s -o /dev/null -w '%{http_code}' "http://${{ secrets.SSH_HOST }}:8080/health")
            if [ "$STATUS" = "200" ]; then exit 0; fi
          done
          exit 1
```
