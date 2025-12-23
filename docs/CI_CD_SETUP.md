# CI/CD Setup Guide

Complete guide for setting up auto-deploy from GitHub to your server.

## Overview

```
Ветки:
  dev  — рабочая ветка (все коммиты сюда)
  main — продакшн ветка (автодеплой на сервер)

Workflow:
  Работа → commit → push dev → тест локально → merge в main → push main → auto-deploy
```

## Prerequisites

- Server with SSH access (AWS EC2, DigitalOcean, etc.)
- GitHub repository
- `systemd` service for your app (optional but recommended)

---

## Step 1: Server Preparation

### 1.1 Clone Repository (First Time Only)

```bash
ssh your-user@your-server

# Clone via HTTPS initially
cd /home/your-user
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

### 1.2 Create SSH Key for GitHub

```bash
# Generate key (no passphrase for automation)
ssh-keygen -t ed25519 -C "deploy-key-YOUR_REPO" -f ~/.ssh/id_ed25519 -N ""

# Show public key
cat ~/.ssh/id_ed25519.pub
```

### 1.3 Add Deploy Key to GitHub

1. Go to: Repository → Settings → Deploy keys → Add deploy key
2. Title: `Server Deploy Key`
3. Key: paste output from `cat ~/.ssh/id_ed25519.pub`
4. Check "Allow write access" (optional)
5. Click "Add key"

### 1.4 Switch Repository to SSH

```bash
# Check current remote (will show https://...)
git remote -v

# Switch to SSH
git remote set-url origin git@github.com:YOUR_USERNAME/YOUR_REPO.git

# Verify SSH works
ssh -T git@github.com
# Expected: "Hi YOUR_USERNAME/YOUR_REPO! You've successfully authenticated..."

# Test fetch
git fetch origin main
```

### 1.5 Create Systemd Service (Optional)

```bash
sudo nano /etc/systemd/system/your-app.service
```

```ini
[Unit]
Description=Your App Name
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/home/your-user/YOUR_REPO
Environment=PATH=/home/your-user/YOUR_REPO/.venv/bin:/usr/bin:/bin
ExecStart=/home/your-user/YOUR_REPO/.venv/bin/python -m src.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable your-app.service
sudo systemctl start your-app.service
```

---

## Step 2: GitHub Secrets

Go to: Repository → Settings → Secrets and variables → Actions

Add these secrets:

| Secret | Value | Example |
|--------|-------|---------|
| `SERVER_HOST` | Server IP or hostname | `123.45.67.89` |
| `SERVER_USER` | SSH username | `ubuntu` |
| `SERVER_SSH_KEY` | Private SSH key (see below) | Full key content |
| `PROJECT_PATH` | Full path to project on server | `/home/ubuntu/YOUR_REPO` |

### Getting SERVER_SSH_KEY

**Option A: Use existing key (if you have one locally)**
```bash
cat ~/.ssh/id_ed25519
```

**Option B: Create new key for GitHub Actions**
```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f github_deploy_key -N ""
cat github_deploy_key  # This goes in SERVER_SSH_KEY secret
cat github_deploy_key.pub  # Add this to server's ~/.ssh/authorized_keys
```

Add public key to server:
```bash
ssh your-user@your-server
echo "PUBLIC_KEY_CONTENT" >> ~/.ssh/authorized_keys
```

---

## Step 3: Configure Workflow

Edit `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Server

on:
  push:
    branches: [main]

jobs:
  deploy:
    name: Deploy to Server
    runs-on: ubuntu-latest

    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            cd ${{ secrets.PROJECT_PATH }}

            # Pull latest changes
            git fetch origin main
            git reset --hard origin/main

            # Install dependencies (uncomment for your stack)
            # Python:
            # source .venv/bin/activate
            # pip install -e . --quiet

            # Node.js:
            # npm ci --production

            # Restart service (uncomment and customize)
            # sudo systemctl restart your-app.service

            echo "Deploy completed at $(date)"
```

---

## Step 4: Test Deployment

### 4.1 Make Test Commit

```bash
git commit --allow-empty -m "test: verify CI/CD pipeline"
git push origin main
```

### 4.2 Check GitHub Actions

1. Go to: Repository → Actions
2. Click on the running workflow
3. Check logs for errors

### 4.3 Verify on Server

```bash
ssh your-user@your-server
cd /path/to/project
git log -1 --oneline
# Should show your test commit
```

---

## Troubleshooting

### Error: "fatal: could not read Username for 'https://github.com'"

**Cause:** Repository on server uses HTTPS remote, but no credentials stored.

**Fix:**
```bash
# Switch to SSH
git remote set-url origin git@github.com:YOUR_USERNAME/YOUR_REPO.git

# Ensure SSH key is set up (see Step 1.2-1.4)
ssh -T git@github.com
```

### Error: "Permission denied (publickey)"

**Cause:** SSH key not set up or not added to GitHub.

**Fix:**
```bash
# Check if key exists
ls ~/.ssh/id_ed25519*

# If not, create one (Step 1.2)
ssh-keygen -t ed25519 -C "deploy-key" -f ~/.ssh/id_ed25519 -N ""

# Add public key to GitHub Deploy Keys (Step 1.3)
cat ~/.ssh/id_ed25519.pub
```

### Error: "Host key verification failed"

**Cause:** GitHub's host key not in known_hosts.

**Fix:**
```bash
ssh-keyscan github.com >> ~/.ssh/known_hosts
```

### Workflow Shows Green But Code Not Updated

**Cause:** `PROJECT_PATH` secret is wrong.

**Fix:**
1. SSH to server and find correct path:
   ```bash
   find /home -name ".git" -type d 2>/dev/null
   ```
2. Update `PROJECT_PATH` secret in GitHub

### Service Not Restarting

**Cause:** User doesn't have sudo privileges without password.

**Fix:**
```bash
sudo visudo
# Add line:
your-user ALL=(ALL) NOPASSWD: /bin/systemctl restart your-app.service
```

---

## Quick Reference

### Server Commands
```bash
# Check service status
sudo systemctl status your-app.service

# View logs
sudo journalctl -u your-app.service -f

# Manual restart
sudo systemctl restart your-app.service

# Check current commit
git log -1 --oneline
```

### Local Commands
```bash
# Обычная работа (коммит в dev)
git add . && git commit -m "feat: description" && git push origin dev

# Deploy (merge dev to main and push)
git checkout main && git merge dev && git push origin main && git checkout dev

# Check workflow status
gh run list --limit 5
```

---

## Checklist

- [ ] Server: Repository cloned
- [ ] Server: SSH key created (`~/.ssh/id_ed25519`)
- [ ] GitHub: Deploy key added (Settings → Deploy keys)
- [ ] Server: Git remote switched to SSH
- [ ] Server: `ssh -T git@github.com` works
- [ ] GitHub: All 4 secrets configured
- [ ] GitHub: Workflow file customized for your stack
- [ ] Test: Empty commit deployed successfully
