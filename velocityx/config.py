"""
Configuration management for VelocityX Engine.

Loads settings from .env file and provides validation.
Sets up professional logging with loguru.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Fallback to constants if accounts.json not found
from .constants import DEFAULT_ACCOUNT_CATEGORIES

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class with validation and logging setup."""

    def __init__(self):
        """Initialize configuration and setup logging."""
        self._validate_required_vars()
        self._setup_logging()

    def _validate_required_vars(self) -> None:
        """Ensure all required environment variables are set."""
        required = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
        missing = [var for var in required if not os.getenv(var)]

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please copy .env.example to .env and fill in your details."
            )

    def _setup_logging(self) -> None:
        """Configure loguru logger with console and file output."""
        logger.remove()  # Remove default handler

        # Console logging with colors
        log_level = os.getenv("LOG_LEVEL", "INFO")
        logger.add(
            sys.stderr,
            colorize=True,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
            level=log_level,
        )

        # File logging (if enabled)
        if os.getenv("LOG_TO_FILE", "true").lower() == "true":
            log_file = os.getenv("LOG_FILE_PATH", "./logs/monitor.log")
            log_retention_days = int(os.getenv("LOG_RETENTION_DAYS", "3"))

            # Create logs directory if it doesn't exist
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)

            logger.add(
                log_file,
                rotation="1 day",  # New file every day
                retention=f"{log_retention_days} days",  # Keep logs for N days
                compression="zip",  # Compress old logs
                level=log_level,
            )

    # Telegram Configuration
    @property
    def telegram_bot_token(self) -> str:
        """Get Telegram bot token from environment."""
        return os.getenv("TELEGRAM_BOT_TOKEN", "")

    @property
    def telegram_chat_id(self) -> str:
        """Get Telegram chat ID from environment."""
        return os.getenv("TELEGRAM_CHAT_ID", "")

    # Monitoring Configuration
    @property
    def check_interval_seconds(self) -> int:
        """Get check interval in seconds (default: 300 = 5 minutes)."""
        return int(os.getenv("CHECK_INTERVAL_SECONDS", "300"))

    @property
    def min_opportunity_score(self) -> int:
        """Get minimum opportunity score for alerts (default: 30)."""
        return int(os.getenv("MIN_OPPORTUNITY_SCORE", "30"))

    @property
    def max_tweet_age_minutes(self) -> int:
        """Get maximum tweet age in minutes for alerts (default: 15)."""
        return int(os.getenv("MAX_TWEET_AGE_MINUTES", "15"))

    # AI Reply Configuration
    @property
    def groq_api_key(self) -> str:
        """Get Groq API key for AI reply generation."""
        return os.getenv("GROQ_API_KEY", "")

    @property
    def enable_ai_replies(self) -> bool:
        """
        Check if AI reply suggestions are enabled.
        Controlled by the ENABLE_AI_REPLIES environment variable, which
        defaults to "true" (enabled) if not explicitly set.
        """
        return os.getenv("ENABLE_AI_REPLIES", "true").lower() == "true"

    @property
    def groq_model_name(self) -> str:
        """Get Groq model name for AI reply generation."""
        return os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")

    @property
    def delay_between_accounts(self) -> float:
        """Get delay between account checks in seconds (default: 8.0)."""
        return float(os.getenv("DELAY_BETWEEN_ACCOUNTS", "8.0"))

    @property
    def request_jitter_seconds(self) -> float:
        """Get max random jitter added to each request delay (default: 3.0)."""
        return float(os.getenv("REQUEST_JITTER_SECONDS", "3.0"))

    @property
    def request_timeout_seconds(self) -> int:
        """Get request timeout in seconds (default: 15)."""
        return int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))

    @property
    def rss_max_retries(self) -> int:
        """Get max retries for RSS fetch (default: 3)."""
        return int(os.getenv("RSS_MAX_RETRIES", "3"))

    @property
    def rss_time_window(self) -> str:
        """Get time window for Google News search (default: 12h)."""
        return os.getenv("RSS_TIME_WINDOW", "12h")

    @property
    def http_proxy(self) -> str:
        """Get HTTP proxy URL (optional, for bypassing IP blocks)."""
        return os.getenv("HTTP_PROXY", "")

    @property
    def db_cleanup_days(self) -> int:
        """Get number of days to keep tweets in database (default: 7)."""
        return int(os.getenv("DB_CLEANUP_DAYS", "7"))

    @property
    def default_tweet_age_minutes(self) -> int:
        """Get default tweet age when RSS doesn't provide timestamp (default: 10)."""
        return int(os.getenv("DEFAULT_TWEET_AGE_MINUTES", "10"))

    @property
    def monitored_accounts(self) -> list[str]:
        """
        Get list of accounts to monitor.

        First tries to get from MONITORED_ACCOUNTS env variable.
        If not set, returns all accounts from curated lists.
        """
        # Try to get from env first
        env_accounts = os.getenv("MONITORED_ACCOUNTS", "")
        if env_accounts:
            return [acc.strip() for acc in env_accounts.split(",") if acc.strip()]

        # Otherwise use curated lists
        return self._get_default_accounts()

    def _get_default_accounts(self) -> list[str]:
        """Get all accounts from accounts.json (or fallback to constants.py)."""
        # Try to load from accounts.json first
        json_path = Path(__file__).parent / "accounts.json"

        if json_path.exists():
            try:
                with open(json_path) as f:
                    categories = json.load(f)
                all_accounts = []
                for category_accounts in categories.values():
                    all_accounts.extend(category_accounts)
                logger.debug(f"Loaded {len(all_accounts)} accounts from accounts.json")
                return all_accounts
            except Exception as e:
                logger.warning(f"Failed to load accounts.json: {e}, using fallback")

        # Fallback to hardcoded constants
        all_accounts = []
        for category_accounts in DEFAULT_ACCOUNT_CATEGORIES.values():
            all_accounts.extend(category_accounts)
        return all_accounts


# Create singleton config instance
config = Config()
