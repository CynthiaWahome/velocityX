"""
Tests for core monitoring logic.
"""

from unittest.mock import Mock, patch

import pytest

from velocityx.monitor import VelocityXEngine


class TestVelocityXEngine:
    """Test monitoring functionality."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        with patch("velocityx.monitor.config") as mock_cfg:
            mock_cfg.telegram_bot_token = "test_token"
            mock_cfg.telegram_chat_id = "123456"
            mock_cfg.monitored_accounts = ["sama", "karpathy"]
            mock_cfg.check_interval_seconds = 300
            mock_cfg.min_opportunity_score = 30
            mock_cfg.max_tweet_age_minutes = 15
            mock_cfg.delay_between_accounts = 1.0
            mock_cfg.request_jitter_seconds = 0  # No jitter in tests
            mock_cfg.request_timeout_seconds = 10
            mock_cfg.rss_max_retries = 3
            mock_cfg.rss_time_window = "12h"
            mock_cfg.http_proxy = ""
            mock_cfg.db_cleanup_days = 7
            mock_cfg.default_tweet_age_minutes = 10
            yield mock_cfg

    @pytest.fixture
    def mock_db(self):
        """Mock database."""
        with patch("velocityx.monitor.SeenTweetsDB") as mock_db_class:
            mock_db = Mock()
            mock_db.is_seen.return_value = False
            mock_db.mark_seen.return_value = None
            mock_db.cleanup_old.return_value = 0
            mock_db_class.return_value = mock_db
            yield mock_db

    @pytest.fixture
    def monitor(self, mock_config, mock_db):
        """Create monitor instance with mocked dependencies."""
        with patch("velocityx.monitor.VelocityXEngine.send_telegram_alert"):
            return VelocityXEngine()

    def test_monitor_initialization(self, monitor):
        """Test that monitor initializes correctly."""
        assert monitor.db is not None
        assert monitor.session is not None

    def test_get_google_rss_url(self, monitor):
        """Test RSS URL generation."""
        url = monitor.get_google_rss_url("sama")
        assert "news.google.com/rss/search" in url
        assert "sama" in url
        # Query should contain 'when:' with the configured time window (URL-encoded or not)
        # Default is 12h but can be configured
        assert "when%3A" in url or "when:" in url

    def test_calculate_opportunity_score_fresh(self, monitor):
        """Test scoring for very fresh tweets."""
        score = monitor.calculate_opportunity_score(5)
        assert score == 100

    def test_calculate_opportunity_score_medium(self, monitor):
        """Test scoring for medium age tweets."""
        score = monitor.calculate_opportunity_score(12)
        assert score == 85

    def test_calculate_opportunity_score_old(self, monitor):
        """Test scoring for older tweets."""
        score = monitor.calculate_opportunity_score(70)
        assert score == 20

    def test_generate_tweet_id(self, monitor):
        """Test tweet ID generation."""
        entry = {
            "link": "https://twitter.com/sama/status/123",
            "title": "Test tweet",
        }
        tweet_id = monitor.generate_tweet_id(entry)
        assert isinstance(tweet_id, str)
        assert len(tweet_id) == 32  # MD5 hash length

        # Same entry should generate same ID
        tweet_id2 = monitor.generate_tweet_id(entry)
        assert tweet_id == tweet_id2

    def test_format_alert_message_high_score(self, monitor):
        """Test alert message formatting for high score."""
        tweet = {
            "username": "sama",
            "title": "This is a test tweet",
            "link": "https://twitter.com/sama/status/123",
            "age_minutes": 10,
            "opportunity_score": 85,
            "published": "2024-01-01",
        }

        message = monitor.format_alert_message(tweet)
        assert "@sama" in message
        # V2: Score and age no longer shown (always 85, misleading)
        assert "This is a test tweet" in message
        assert "https://twitter.com/sama" in message  # Profile link
        assert "🔥🔥🔥" in message  # Critical score emoji (>=80)

    def test_format_alert_message_critical_score(self, monitor):
        """Test alert message formatting for critical score."""
        tweet = {
            "username": "karpathy",
            "title": "Critical tweet",
            "link": "https://twitter.com/karpathy/status/456",
            "age_minutes": 5,
            "opportunity_score": 95,
            "published": "2024-01-01",
        }

        message = monitor.format_alert_message(tweet)
        assert "🔥🔥🔥" in message  # Critical emoji

    @patch("velocityx.monitor.get_reply_suggestions", return_value=[])
    def test_format_alert_message_truncates_long_title(self, mock_get_reply_suggestions, monitor):
        """Test that long titles are truncated."""
        long_title = "A" * 250
        tweet = {
            "username": "sama",
            "title": long_title,
            "link": "https://twitter.com/sama/status/123",
            "age_minutes": 10,
            "opportunity_score": 50,
            "published": "2024-01-01",
        }

        message = monitor.format_alert_message(tweet)
        assert "..." in message
        assert len(message) < len(long_title) + 500

    @patch("requests.Session.get")
    @patch("velocityx.monitor.feedparser")
    def test_check_account_no_tweets(self, mock_get, mock_feedparser, monitor, mock_db):
        """Test checking account with no recent tweets."""
        mock_get.return_value = Mock(status_code=200, content=b"")
        mock_feedparser.parse.return_value = Mock(entries=[])

        result = monitor.check_account("sama")
        assert result is None

    @patch("velocityx.monitor.feedparser")
    def test_check_account_already_seen(self, mock_feedparser, monitor, mock_db):
        """Test checking account with already seen tweet."""
        mock_entry = {
            "title": "Test tweet",
            "link": "https://twitter.com/sama/status/123",
            "published": "2024-01-01",
        }
        mock_feedparser.parse.return_value = Mock(entries=[mock_entry])
        mock_db.is_seen.return_value = True  # Explicitly set for this test

        result = monitor.check_account("sama")
        assert result is None

    @patch("velocityx.monitor.feedparser")
    @patch("requests.Session.get")  # Patch requests.Session.get
    def test_check_account_new_tweet(self, mock_get, mock_feedparser, monitor, mock_db):
        """Test checking account with new tweet."""
        # Configure mock_get for successful response
        mock_get.return_value = Mock(status_code=200, content=b"mock_rss_content")

        mock_entry = {
            "title": "New test tweet",
            "link": "https://twitter.com/sama/status/789",
            "published": "2024-01-01",
        }
        mock_feedparser.parse.return_value = Mock(entries=[mock_entry])
        mock_db.is_seen.return_value = False

        result = monitor.check_account("sama")

        assert result is not None
        assert result["username"] == "sama"
        assert result["title"] == "New test tweet"
        assert result["link"] == "https://twitter.com/sama/status/789"
        assert result["opportunity_score"] > 0
        mock_db.mark_seen.assert_called_once()

    @patch("velocityx.monitor.requests.Session.post")
    def test_send_telegram_alert_success(self, mock_post, monitor):
        """Test successful Telegram alert."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = monitor.send_telegram_alert("Test message")
        assert result is True
        mock_post.assert_called_once()

    @patch("velocityx.monitor.requests.Session.post")
    def test_send_telegram_alert_failure(self, mock_post, monitor):
        """Test failed Telegram alert."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        result = monitor.send_telegram_alert("Test message")
        assert result is False

    @patch("velocityx.monitor.requests.Session.post")
    def test_send_telegram_alert_exception(self, mock_post, monitor):
        """Test Telegram alert with exception."""
        mock_post.side_effect = Exception("Network error")

        result = monitor.send_telegram_alert("Test message")
        assert result is False
