# X Monitor Bot 
![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)
![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Telegram](https://img.shields.io/badge/telegram-2.0+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

Monitor high-signal X/Twitter accounts and get instant alerts for reply opportunities.



## Features

- Monitors 50+ curated tech/Python/DevOps/security accounts
- Calculates "opportunity scores" based on X's open-source algorithm
- Sends Telegram alerts when high-value tweets are detected
- You manually reply to capitalize on early engagement (13.5x-75x multiplier)

## ⚡ Quick Start

### 1. Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Telegram account

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/CynthiaWahome/x-monitor-bot.git
cd x-monitor-bot

# Install dependencies with uv
uv sync

# Copy environment template
cp .env.example .env

# Edit .env with your Telegram bot credentials
# (See Configuration section below)
```

### 3. Configuration

1. **Create Telegram Bot:**
   - Open Telegram and message [@BotFather](https://t.me/botfather)
   - Send `/newbot` and follow instructions
   - Copy your bot token

2. **Get Chat ID:**
   - Message your bot (say "hello")
   - Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - Copy the chat ID from the response

3. **Update .env file:**
   ```env
   TELEGRAM_BOT_TOKEN=your_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```

### 4. Run

```bash
# Run the monitor
uv run python main.py

# Or run once and exit (for testing)
uv run python main.py --single-run
```

## 📊 How It Works

Based on [X's open-source algorithm](https://github.com/twitter/the-algorithm):

| Action | Weight | Strategy |
|--------|--------|----------|
| Like | 0.5x | Weak signal |
| Reply | 13.5x | **Our main target** |
| Reply + Author Engagement | 75.0x | **The jackpot** |

**Key insight:** One reply that gets a response from the original author = 150 likes worth of algorithmic value.

## 🔒 Safety & Privacy

**Does X/Twitter know I'm running this?**
- **NO.** We only read Google News RSS feeds (public data)
- We never call X's API
- We never use your X credentials
- X cannot detect, rate-limit, or ban you for this

**The only time X sees you is when YOU manually reply to tweets.**

## ⚙️ Configuration

All settings are in `.env` file:

```env
CHECK_INTERVAL_SECONDS=300    # How often to check (5 minutes minimum)
MIN_OPPORTUNITY_SCORE=30      # Only alert if score >= this (adjust 30-70)
MAX_TWEET_AGE_MINUTES=15      # Only alert for fresh tweets
DELAY_BETWEEN_ACCOUNTS=1.0    # Rate limiting (seconds between checks)
LOG_RETENTION_DAYS=3          # How long to keep logs
```

## 📝 Monitored Accounts

By default, monitors 50+ curated accounts across:
- Tech Visionaries
- Python/Django developers
- Backend/DevOps experts
- Tech memes
- Security/Ethical Hacking

You can customize via `MONITORED_ACCOUNTS` in `.env`.

## 🚀 Deployment

### Local Development
```bash
uv run python main.py
```

### EC2 (24/7 Deployment)
```bash
# SSH into EC2
ssh -i your-key.pem ubuntu@your-ec2-ip

# Setup and run in screen
screen -S xmonitor
uv run python main.py

# Detach: Ctrl+A, then D
# Reattach: screen -r xmonitor
```

## 🧪 Testing

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing

# Run linting
uv run ruff check .

# Format code
uv run ruff format .
```

## 📄 License

MIT License - See [LICENSE](x-monitor-bot/LICENSE.md) file for details

## ⚠️ Disclaimer

This tool is for educational purposes. Use responsibly. Don't spam. Write quality replies that add value.

---

**Built with modern Python tooling:**
- [uv](https://github.com/astral-sh/uv) - Fast package manager
- [ruff](https://github.com/astral-sh/ruff) - Fast linter & formatter
- [loguru](https://github.com/Delgan/loguru) - Beautiful logging
- [pytest](https://pytest.org/) - Testing framework
