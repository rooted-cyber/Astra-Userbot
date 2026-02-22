#!/bin/bash

# Astra Userbot Setup Script
# Works on macOS and Linux (Ubuntu/Debian)

echo "🚀 Starting Astra Userbot Setup..."

# Detect OS
OS_TYPE="$(uname)"

if [ "$OS_TYPE" == "Darwin" ]; then
    echo "🍎 Detected macOS..."
    # Check for Homebrew
    if ! command -v brew &> /dev/null; then
        echo "🍺 Homebrew not found. Installing unattended..."
        NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    echo "📦 Installing system dependencies via Homebrew..."
    brew install node ffmpeg yt-dlp python3
elif [ "$OS_TYPE" == "Linux" ]; then
    echo "🐧 Detected Linux..."
    # Check for apt
    if command -v apt &> /dev/null; then
        echo "📦 Installing system dependencies via apt..."
        sudo apt update
        sudo apt install -y nodejs npm ffmpeg python3-venv python3-pip
        # Install yt-dlp via pip for latest version
        pip3 install yt-dlp --break-system-packages
    else
        echo "⚠️  Unsupported Linux distribution. Please install node, ffmpeg, and yt-dlp manually."
    fi
else
    echo "❗ Unsupported OS: $OS_TYPE"
    exit 1
fi

echo "🐍 Setting up Python Virtual Environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created."
fi

# Activate venv
source venv/bin/activate

echo "📦 Installing Python dependencies into venv..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🎭 Installing Playwright browser engines..."
playwright install chromium

echo "✅ Setup complete!"
echo "👉 To run the bot:"
echo "   source venv/bin/activate"
echo "   python bot.py"
