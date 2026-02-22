<#
.SYNOPSIS
Unattended Windows installation script for Astra Userbot.
#>

Write-Host "🚀 Starting Astra Userbot Unattended Windows Setup..." -ForegroundColor Cyan

# 1. Dependency Checks & Winget Install
if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Host "📦 Installing FFmpeg via Winget..." -ForegroundColor Yellow
    winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements | Out-Null
    Write-Host "📦 Installing Node.js via Winget..." -ForegroundColor Yellow
    winget install -e --id OpenJS.NodeJS --accept-source-agreements --accept-package-agreements | Out-Null
} else {
    Write-Host "⚠️ Winget not found. Ensure FFmpeg and Node.js are physically installed." -ForegroundColor Yellow
}

# 2. Verify Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python is missing! Please install Python 3.10+ from python.org" -ForegroundColor Red
    exit 1
}

# 3. Create Virtual Environment
Write-Host "🐍 Creating Virtual Environment..." -ForegroundColor Yellow
python -m venv venv
if (-not (Test-Path "venv\Scripts\activate.ps1")) {
    Write-Host "❌ Failed to create Virtual Environment." -ForegroundColor Red
    exit 1
}

# 4. Install Dependencies
Write-Host "📦 Installing pip dependencies..." -ForegroundColor Yellow
& .\venv\Scripts\python.exe -m pip install --upgrade pip | Out-Null
& .\venv\Scripts\python.exe -m pip install -r requirements.txt | Out-Null

Write-Host "🎭 Installing Playwright browser engines..." -ForegroundColor Yellow
& .\venv\Scripts\playwright.exe install chromium

Write-Host "✅ Unattended Windows Setup Complete!" -ForegroundColor Green
Write-Host "👉 To configure and run the bot:" -ForegroundColor Cyan
Write-Host "   1. copy .env.example .env (Edit your credentials)"
Write-Host "   2. .\venv\Scripts\activate"
Write-Host "   3. python bot.py"
