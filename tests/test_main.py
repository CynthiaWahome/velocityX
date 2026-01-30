"""
Tests for CLI interface.
"""

import sys
from unittest.mock import Mock, patch

import pytest
import os

import main


class TestCLI:
    """Test command-line interface."""

    def test_parse_args_default(self):
        """Test default argument parsing."""
        with patch.object(sys, "argv", ["main.py"]):
            args = main.parse_args()
            assert args.single_run is False

    def test_parse_args_single_run(self):
        """Test --single-run flag."""
        with patch.object(sys, "argv", ["main.py", "--single-run"]):
            args = main.parse_args()
            assert args.single_run is True

    def test_parse_args_version(self):
        """Test --version flag."""
        with patch.object(sys, "argv", ["main.py", "--version"]):
            with pytest.raises(SystemExit) as exc_info:
                main.parse_args()
            assert exc_info.value.code == 0

    def test_parse_args_help(self):
        """Test --help flag."""
        with patch.object(sys, "argv", ["main.py", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main.parse_args()
            assert exc_info.value.code == 0

    @patch("main.XMonitor")
    @patch("main.config")
    def test_run_single_cycle_success(self, mock_config, mock_monitor_class):
        """Test successful single cycle run."""
        # Setup mocks
        mock_config.monitored_accounts = ["sama", "karpathy"]
        mock_config.min_opportunity_score = 30
        mock_config.max_tweet_age_minutes = 15
        mock_config.delay_between_accounts = 0.1

        mock_monitor = Mock()
        mock_monitor.check_account.return_value = None
        mock_monitor_class.return_value = mock_monitor

        # Run single cycle
        result = main.run_single_cycle()

        assert result == 0
        assert mock_monitor.check_account.call_count == 2

    @patch("main.XMonitor")
    @patch("main.config")
    def test_run_single_cycle_with_alert(self, mock_config, mock_monitor_class):
        """Test single cycle with alert sent."""
        # Setup mocks
        mock_config.monitored_accounts = ["sama"]
        mock_config.min_opportunity_score = 30
        mock_config.max_tweet_age_minutes = 15
        mock_config.delay_between_accounts = 0.1

        mock_monitor = Mock()
        mock_monitor.check_account.return_value = {
            "username": "sama",
            "title": "Test tweet",
            "link": "https://twitter.com/sama/status/123",
            "age_minutes": 10,
            "opportunity_score": 85,
        }
        mock_monitor.format_alert_message.return_value = "Test alert"
        mock_monitor.send_telegram_alert.return_value = True
        mock_monitor_class.return_value = mock_monitor

        # Run single cycle
        result = main.run_single_cycle()

        assert result == 0
        mock_monitor.send_telegram_alert.assert_called_once()

    @patch("main.XMonitor")
    @patch("main.config")
    def test_run_single_cycle_below_threshold(self, mock_config, mock_monitor_class):
        """Test single cycle with tweet below threshold."""
        # Setup mocks
        mock_config.monitored_accounts = ["sama"]
        mock_config.min_opportunity_score = 50
        mock_config.max_tweet_age_minutes = 15
        mock_config.delay_between_accounts = 0.1

        mock_monitor = Mock()
        mock_monitor.check_account.return_value = {
            "username": "sama",
            "title": "Test tweet",
            "link": "https://twitter.com/sama/status/123",
            "age_minutes": 10,
            "opportunity_score": 30,  # Below threshold
        }
        mock_monitor_class.return_value = mock_monitor

        # Run single cycle
        result = main.run_single_cycle()

        assert result == 0
        # Should not send alert
        mock_monitor.send_telegram_alert.assert_not_called()

    @patch("main.XMonitor")
    def test_run_single_cycle_error(self, mock_monitor_class):
        """Test single cycle with error."""
        mock_monitor_class.side_effect = Exception("Test error")

        result = main.run_single_cycle()

        assert result == 1

    @patch("main.XMonitor")
    def test_run_continuous_keyboard_interrupt(self, mock_monitor_class):
        """Test continuous mode with keyboard interrupt."""
        mock_monitor = Mock()
        mock_monitor.run.side_effect = KeyboardInterrupt()
        mock_monitor_class.return_value = mock_monitor

        result = main.run_continuous()

        assert result == 0

    @patch("main.XMonitor")
    def test_run_continuous_error(self, mock_monitor_class):
        """Test continuous mode with error."""
        mock_monitor = Mock()
        mock_monitor.run.side_effect = Exception("Test error")
        mock_monitor_class.return_value = mock_monitor

        result = main.run_continuous()

        assert result == 1

    @patch("main.config")
    @patch("main.run_single_cycle")
    def test_main_single_run_mode(self, mock_run_single, mock_config):
        """Test main function in single-run mode."""
        mock_config.telegram_bot_token = "test_token"
        mock_config.telegram_chat_id = "123456"
        mock_run_single.return_value = 0

        with patch.object(sys, "argv", ["main.py", "--single-run"]):
            result = main.main()

        assert result == 0
        mock_run_single.assert_called_once()

    @patch("main.config")
    @patch("main.run_continuous")
    def test_main_continuous_mode(self, mock_run_continuous, mock_config):
        """Test main function in continuous mode."""
        mock_config.telegram_bot_token = "test_token"
        mock_config.telegram_chat_id = "123456"
        mock_run_continuous.return_value = 0

        with patch.object(sys, "argv", ["main.py"]):
            result = main.main()

        assert result == 0
        mock_run_continuous.assert_called_once()

    @patch("main.config")
    def test_main_missing_config(self, mock_main_config):
        """Test main function with missing configuration."""
        type(mock_main_config).telegram_bot_token = property(
            lambda self: (_ for _ in ()).throw(ValueError("Missing Telegram Bot Token"))
        )
        type(mock_main_config).telegram_chat_id = property(
            lambda self: (_ for _ in ()).throw(ValueError("Missing Telegram Chat ID"))
        )

        with patch.object(sys, "argv", ["main.py"]):
            result = main.main()

        assert result == 1
