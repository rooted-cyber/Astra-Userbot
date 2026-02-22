#!/bin/bash

echo "🚀 Welcome to the Astra-Userbot Auto-Installer"
echo "-----------------------------------------------"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Attempting to install git..."
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y git
    elif command -v brew &> /dev/null; then
        brew install git
    else
        echo "⚠️ Could not install git automatically. Please install git and run again."
        exit 1
    fi
fi

# Clone the repository
if [ -d "Astra-Userbot" ]; then
    echo "⚠️ Directory 'Astra-Userbot' already exists. Updating..."
    cd Astra-Userbot
    git pull origin main
else
    echo "📥 Cloning Astra-Userbot repository..."
    git clone https://github.com/paman7647/Astra-Userbot.git
    cd Astra-Userbot
fi

# Make the setup script executable and run it
echo "⚙️ Executing platform setup..."
chmod +x setup.sh
./setup.sh
