#!/bin/bash
# Setup server for CI/CD auto-deploy from GitHub
# Run this script on the server after cloning the repository

set -e

echo "=== CI/CD Server Setup ==="
echo ""

# Get repository info
REPO_PATH=$(pwd)
REPO_NAME=$(basename "$REPO_PATH")

if [ ! -d ".git" ]; then
    echo "ERROR: Not a git repository. Run this from your project directory."
    exit 1
fi

# Get current remote
CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null || echo "")
echo "Current directory: $REPO_PATH"
echo "Repository: $REPO_NAME"
echo "Current remote: $CURRENT_REMOTE"
echo ""

# Step 1: Check/Create SSH key
echo "=== Step 1: SSH Key ==="
SSH_KEY="$HOME/.ssh/id_ed25519"

if [ -f "$SSH_KEY" ]; then
    echo "SSH key already exists: $SSH_KEY"
else
    echo "Creating new SSH key..."
    ssh-keygen -t ed25519 -C "deploy-key-$REPO_NAME" -f "$SSH_KEY" -N ""
    echo "SSH key created."
fi

echo ""
echo "PUBLIC KEY (add to GitHub → Settings → Deploy keys):"
echo "----------------------------------------------------"
cat "${SSH_KEY}.pub"
echo "----------------------------------------------------"
echo ""

# Step 2: Add GitHub to known_hosts
echo "=== Step 2: Known Hosts ==="
if grep -q "github.com" ~/.ssh/known_hosts 2>/dev/null; then
    echo "GitHub already in known_hosts"
else
    echo "Adding GitHub to known_hosts..."
    ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null
    echo "Done."
fi
echo ""

# Step 3: Check if remote is HTTPS
echo "=== Step 3: Git Remote ==="
if echo "$CURRENT_REMOTE" | grep -q "https://"; then
    echo "Remote uses HTTPS. Extracting repo info..."

    # Extract owner/repo from HTTPS URL
    # https://github.com/owner/repo.git or https://github.com/owner/repo
    REPO_INFO=$(echo "$CURRENT_REMOTE" | sed -E 's|https://github.com/||' | sed 's|\.git$||')
    SSH_REMOTE="git@github.com:${REPO_INFO}.git"

    echo "Will switch to SSH: $SSH_REMOTE"
    echo ""
    read -p "Switch remote to SSH? (y/n): " SWITCH_REMOTE

    if [ "$SWITCH_REMOTE" = "y" ]; then
        git remote set-url origin "$SSH_REMOTE"
        echo "Remote updated to: $SSH_REMOTE"
    else
        echo "Skipped. You can do this later with:"
        echo "  git remote set-url origin $SSH_REMOTE"
    fi
else
    echo "Remote already uses SSH: $CURRENT_REMOTE"
fi
echo ""

# Step 4: Test SSH connection
echo "=== Step 4: Test SSH Connection ==="
echo "Testing connection to GitHub..."
echo ""

read -p "Have you added the public key to GitHub Deploy keys? (y/n): " KEY_ADDED

if [ "$KEY_ADDED" = "y" ]; then
    if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
        echo "SUCCESS: SSH authentication works!"

        # Test fetch
        echo ""
        echo "Testing git fetch..."
        if git fetch origin main 2>&1; then
            echo "SUCCESS: git fetch works!"
        else
            echo "WARNING: git fetch failed. Check remote URL."
        fi
    else
        echo "FAILED: SSH authentication not working."
        echo "Make sure you added the public key to GitHub Deploy keys."
    fi
else
    echo "Please add the public key to GitHub first, then run this script again."
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Add public key to GitHub (if not done)"
echo "2. Configure GitHub Secrets:"
echo "   - SERVER_HOST: $(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_SERVER_IP')"
echo "   - SERVER_USER: $USER"
echo "   - SERVER_SSH_KEY: (your local private key for SSH to this server)"
echo "   - PROJECT_PATH: $REPO_PATH"
echo ""
echo "3. Test with: git commit --allow-empty -m 'test: CI/CD' && git push origin main"
