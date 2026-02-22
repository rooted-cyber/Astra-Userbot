# 🚢 Astra Userbot Deployment Guide

This guide provides step-by-step instructions for deploying the **Astra Userbot** across different environments.

---

## 🛠️ Environment Prerequisites

Regardless of your chosen platform, you will need:
- **WhatsApp Account**: A secondary account is recommended for userbot usage.
- **Gemini API Key**: Obtain one from the [Google AI Studio](https://aistudio.google.com/).
- **Node.js 18+ & Python 3.10+**: Core runtimes for the engine and plugins.

---

## 🏠 1. Local Hosting (Windows/macOS/Linux)

Ideal for development or personal use on a machine you keep running.

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/astra-userbot.git
   cd astra-userbot
   ```
2. **Run the Setup Script**:
   This installs Node.js, FFmpeg, and Python requirements.
   ```bash
   chmod +x setup.sh && ./setup.sh
   ```
3. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```
4. **Authenticate & Start**:
   ```bash
   export ASTRA_HEADLESS="false" # Show browser for first QR scan
   python3 bot.py
   ```

---

## ☁️ 2. VPS Deployment (Ubuntu/Debian)

Recommended for 24/7 reliability. We use **PM2** to keep the bot alive.

1. **Update System & Install PM2**:
   ```bash
   sudo apt update && sudo apt install -y nodejs npm
   sudo npm install -g pm2
   ```
2. **Setup Bot**: Follow the **Local Hosting** steps up to Step 3.
3. **Start with PM2**:
   ```bash
   pm2 start bot.py --name "astra-bot" --interpreter python3
   pm2 save
   pm2 startup
   ```

---

## 🐳 3. Docker Deployment (Recommended)

The most professional and isolated way to run the bot.

1. **Ensure Docker is installed**: [Install Docker](https://docs.docker.com/get-docker/)
2. **Configure your `.env`**: Ensure `ASTRA_HEADLESS` is set to `true`.
3. **Build & Launch**:
   ```bash
   docker-compose up -d --build
   ```
4. **Authenticating**:
   Check logs for the pairing code or QR instructions:
   ```bash
   docker logs astra-bot -f
   ```

---

## 🚀 4. Cloud Platforms (Railway / Render)

### Railway.app (Easiest)
1. Fork this repository.
2. Link your GitHub to Railway.
3. Add all variables from `.env.example` to the Railway Dashboard.
4. Railway will automatically detect the `Dockerfile` and deploy.

---

## ⚠️ Important Security Notes
- **Keep `.env` Private**: Never share your `.env` file or commit it to a public repo.
- **Session Safety**: Your session is stored in the `.astra_sessions` directory. Protect this folder as it contains your WhatsApp account access.
- **Graceful Shutdown**: Always use `pm2 stop` or `ctrl+c` to allow the bot to save its state.

---
*For support, join our [Telegram Community](https://t.me/astra_userbot_chat).*
