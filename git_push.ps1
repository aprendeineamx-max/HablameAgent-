# Git Helper Script for HablameAgent
# This script makes it easy to commit and push changes to GitHub
# Run this script after making changes to your project

param(
    [string]$CommitMessage = "Update HablameAgent project"
)

# Refresh PATH to ensure git is available
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

Write-Host "=== HablameAgent Git Helper ===" -ForegroundColor Cyan

# Check git status
Write-Host "`nChecking repository status..." -ForegroundColor Yellow
git status

# Add all changes
Write-Host "`nAdding all changes..." -ForegroundColor Yellow
git add .

# Show what will be committed
Write-Host "`nFiles to be committed:" -ForegroundColor Yellow
git status --short

# Commit changes
Write-Host "`nCommitting changes..." -ForegroundColor Yellow
git commit -m $CommitMessage

# Push to GitHub
Write-Host "`nPushing to GitHub..." -ForegroundColor Yellow
git push

Write-Host "`n=== Complete ===" -ForegroundColor Green
Write-Host "Your changes have been pushed to GitHub!" -ForegroundColor Green
