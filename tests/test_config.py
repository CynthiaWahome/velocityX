"""
Tests for configuration management.
"""

import os
from unittest.mock import patch

import pytest

from x_monitor_bot.config import Config
from x_monitor_bot.constants import DEFAULT_ACCOUNT_CATEGORIES


class TestConfig:
    """Test configuration loading and validation."""

    def test_missing_telegram_token_raises_error(self):
        """Test that missing TELEGRAM_BOT_TOKEN raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Missing required environment variables"):
                Config()

    def test_missing_telegram_chat_id_raises_error(self):
        """Test that missing TELEGRAM_CHAT_ID raises ValueError."""
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test_token"}, clear=True):
            with pytest.raises(ValueError, match="Missing required environment variables"):
                Config()

    def test_valid_config_initialization(self):
        """Test that config initializes with required env vars."""
        with patch.dict(
            os.environ,
            {"TELEGRAM_BOT_TOKEN": "test_token", "TELEGRAM_CHAT_ID": "123456"},
            clear=True,
        ):
            config = Config()
            assert config.telegram_bot_token == "test_token"
            assert config.telegram_chat_id == "123456"

    def test_default_check_interval(self):
        """Test default check interval is 300 seconds."""
        with patch.dict(
            os.environ,
            {"TELEGRAM_BOT_TOKEN": "test_token", "TELEGRAM_CHAT_ID": "123456"},
            clear=True,
        ):
            config = Config()
            assert config.check_interval_seconds == 300

    def test_custom_check_interval(self):
        """Test custom check interval from env."""
        with patch.dict(
            os.environ,
            {
                "TELEGRAM_BOT_TOKEN": "test_token",
                "TELEGRAM_CHAT_ID": "123456",
                "CHECK_INTERVAL_SECONDS": "600",
            },
            clear=True,
        ):
            config = Config()
            assert config.check_interval_seconds == 600

    def test_default_min_opportunity_score(self):
        """Test default minimum opportunity score is 30."""
        with patch.dict(
            os.environ,
            {"TELEGRAM_BOT_TOKEN": "test_token", "TELEGRAM_CHAT_ID": "123456"},
            clear=True,
        ):
            config = Config()
            assert config.min_opportunity_score == 30

    def test_custom_min_opportunity_score(self):
        """Test custom minimum opportunity score from env."""
        with patch.dict(
            os.environ,
            {
                "TELEGRAM_BOT_TOKEN": "test_token",
                "TELEGRAM_CHAT_ID": "123456",
                "MIN_OPPORTUNITY_SCORE": "50",
            },
            clear=True,
        ):
            config = Config()
            assert config.min_opportunity_score == 50

    def test_default_max_tweet_age(self):
        """Test default max tweet age is 15 minutes."""
        with patch.dict(
            os.environ,
            {"TELEGRAM_BOT_TOKEN": "test_token", "TELEGRAM_CHAT_ID": "123456"},
            clear=True,
        ):
            config = Config()
            assert config.max_tweet_age_minutes == 15

    def test_default_delay_between_accounts(self):
        """Test default delay between accounts is 1.0 seconds."""
        with patch.dict(
            os.environ,
            {"TELEGRAM_BOT_TOKEN": "test_token", "TELEGRAM_CHAT_ID": "123456"},
            clear=True,
        ):
            config = Config()
            assert config.delay_between_accounts == 8.0

    def test_custom_delay_between_accounts(self):
        """Test custom delay between accounts from env."""
        with patch.dict(
            os.environ,
            {
                "TELEGRAM_BOT_TOKEN": "test_token",
                "TELEGRAM_CHAT_ID": "123456",
                "DELAY_BETWEEN_ACCOUNTS": "2.5",
            },
            clear=True,
        ):
            config = Config()
            assert config.delay_between_accounts == 2.5

    def test_custom_monitored_accounts_from_env(self):
        """Test loading custom monitored accounts from env."""
        with patch.dict(
            os.environ,
            {
                "TELEGRAM_BOT_TOKEN": "test_token",
                "TELEGRAM_CHAT_ID": "123456",
                "MONITORED_ACCOUNTS": "sama,karpathy,ylecun",
            },
            clear=True,
        ):
            config = Config()
            assert config.monitored_accounts == ["sama", "karpathy", "ylecun"]

    def test_custom_monitored_accounts_with_spaces(self):
        """Test loading custom monitored accounts with spaces."""
        with patch.dict(
            os.environ,
            {
                "TELEGRAM_BOT_TOKEN": "test_token",
                "TELEGRAM_CHAT_ID": "123456",
                "MONITORED_ACCOUNTS": "sama, karpathy, ylecun",
            },
            clear=True,
        ):
            config = Config()
            assert config.monitored_accounts == ["sama", "karpathy", "ylecun"]

    def test_default_monitored_accounts(self):
        """Test default monitored accounts from curated lists."""
        with patch.dict(
            os.environ,
            {"TELEGRAM_BOT_TOKEN": "test_token", "TELEGRAM_CHAT_ID": "123456"},
            clear=True,
        ):
            config = Config()
            accounts = config.monitored_accounts

            # Should have accounts from all categories
            assert len(accounts) > 0

            # Should include accounts from each category
            for category_accounts in DEFAULT_ACCOUNT_CATEGORIES.values():
                for account in category_accounts:
                    assert account in accounts

    def test_empty_monitored_accounts_uses_defaults(self):
        """Test that empty MONITORED_ACCOUNTS env var uses defaults."""
        with patch.dict(
            os.environ,
            {
                "TELEGRAM_BOT_TOKEN": "test_token",
                "TELEGRAM_CHAT_ID": "123456",
                "MONITORED_ACCOUNTS": "",
            },
            clear=True,
        ):
            config = Config()
            accounts = config.monitored_accounts

            # Should use default accounts
            assert len(accounts) > 0

    def test_default_groq_api_key(self):
        """Test that groq_api_key defaults to an empty string."""
        with patch.dict(
            os.environ,
            {"TELEGRAM_BOT_TOKEN": "test_token", "TELEGRAM_CHAT_ID": "123456"},
            clear=True,
        ):
            config = Config()
            assert config.groq_api_key == ""

    def test_custom_groq_api_key(self):
        """Test custom Groq API key from env."""
        with patch.dict(
            os.environ,
            {
                "TELEGRAM_BOT_TOKEN": "test_token",
                "TELEGRAM_CHAT_ID": "123456",
                "GROQ_API_KEY": "my-secret-key",
            },
            clear=True,
        ):
            config = Config()
            assert config.groq_api_key == "my-secret-key"

    def test_default_enable_ai_replies(self):
        """Test that enable_ai_replies defaults to True."""
        with patch.dict(
            os.environ,
            {"TELEGRAM_BOT_TOKEN": "test_token", "TELEGRAM_CHAT_ID": "123456"},
            clear=True,
        ):
            config = Config()
            assert config.enable_ai_replies is True

    def test_disable_ai_replies(self):
        """Test disabling AI replies from env."""
        with patch.dict(
            os.environ,
            {
                "TELEGRAM_BOT_TOKEN": "test_token",
                "TELEGRAM_CHAT_ID": "123456",
                "ENABLE_AI_REPLIES": "false",
            },
            clear=True,
        ):
            config = Config()
            assert config.enable_ai_replies is False
