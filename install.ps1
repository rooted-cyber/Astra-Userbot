<#
.SYNOPSIS
Astra-Userbot Auto-Installer for Windows users.
#>

Write-Host "🚀 Welcome to the Astra-Userbot Auto-Installer" -ForegroundColor Cyan
Write-Host "-----------------------------------------------" -ForegroundColor Cyan

# Check if git is installed
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git is not installed. Attempting to install git via winget..." -ForegroundColor Yellow
    winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements | Out-Null
    # Note: Winget updates path, but current terminal may need reload
}

# Clone the repository
if (Test-Path "Astra-Userbot") {
    Write-Host "⚠️ Directory 'Astra-Userbot' already exists. Updating..." -ForegroundColor Yellow
    Set-Location Astra-Userbot
    git pull origin main
}
else {
    Write-Host "📥 Cloning Astra-Userbot repository..." -ForegroundColor Cyan
    git clone https://github.com/paman7647/Astra-Userbot.git
    Set-Location Astra-Userbot
}

# Run the setup script
Write-Host "⚙️ Executing platform setup..." -ForegroundColor Cyan
Set-ExecutionPolicy Bypass -Scope Process -Force
.\setup.ps1
