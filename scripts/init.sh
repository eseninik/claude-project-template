#!/bin/bash
# Claude Project Template - Unix Setup Script
# Run: ./scripts/init.sh

echo "Claude Project Template Setup"
echo "============================="
echo ""

# Get project info
read -p "Project name: " PROJECT_NAME
read -p "Short description: " PROJECT_DESC
read -p "Primary language (e.g., Russian, English): " PRIMARY_LANG

echo ""
echo "Updating CLAUDE.md..."

# Update CLAUDE.md
sed -i "s/<!-- TODO: Describe your project here -->/$PROJECT_DESC/g" CLAUDE.md
sed -i "s/<!-- TODO: e.g., Russian, English -->/$PRIMARY_LANG/g" CLAUDE.md

echo "Updating openspec/project.md..."

# Update project.md
sed -i "s/<!-- TODO: Describe your project purpose here -->/$PROJECT_DESC/g" openspec/project.md

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit CLAUDE.md - add commands, architecture, env vars"
echo "2. Edit openspec/project.md - add tech stack, conventions"
echo "3. Edit .github/workflows/deploy.yml - configure deployment"
echo "4. Add GitHub Secrets: SERVER_HOST, SERVER_USER, SERVER_SSH_KEY, PROJECT_PATH"
echo ""
echo "Start working with Claude Code!"
