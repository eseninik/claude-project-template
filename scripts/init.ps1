# Claude Project Template - Windows Setup Script
# Run: .\scripts\init.ps1

Write-Host "Claude Project Template Setup" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan
Write-Host ""

# Get project name
$projectName = Read-Host "Project name"
$projectDesc = Read-Host "Short description"
$primaryLang = Read-Host "Primary language (e.g., Russian, English)"

Write-Host ""
Write-Host "Updating CLAUDE.md..." -ForegroundColor Yellow

# Read and update CLAUDE.md
$claudeMd = Get-Content "CLAUDE.md" -Raw
$claudeMd = $claudeMd -replace '<!-- TODO: Describe your project here -->', $projectDesc
$claudeMd = $claudeMd -replace '<!-- TODO: e.g., Russian, English -->', $primaryLang
Set-Content "CLAUDE.md" $claudeMd

Write-Host "Updating openspec/project.md..." -ForegroundColor Yellow

# Read and update project.md
$projectMd = Get-Content "openspec/project.md" -Raw
$projectMd = $projectMd -replace '<!-- TODO: Describe your project purpose here -->', $projectDesc
Set-Content "openspec/project.md" $projectMd

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Edit CLAUDE.md - add commands, architecture, env vars"
Write-Host "2. Edit openspec/project.md - add tech stack, conventions"
Write-Host "3. Edit .github/workflows/deploy.yml - configure deployment"
Write-Host "4. Add GitHub Secrets: SERVER_HOST, SERVER_USER, SERVER_SSH_KEY, PROJECT_PATH"
Write-Host ""
Write-Host "Start working with Claude Code!" -ForegroundColor Green
