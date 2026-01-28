#!/usr/bin/env python3
"""
X Monitor Bot - Main Entry Point

Monitor high-signal X/Twitter accounts and get instant alerts
for reply opportunities via Telegram.

Usage:
    python main.py              # Run continuous monitoring
    python main.py --single-run # Run once and exit (for testing)
"""

import argparse
import sys
import time

from loguru import logger
from x_monitor_bot.config import config
from x_monitor_bot.monitor import XMonitor


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="X Monitor Bot - Get instant alerts for reply opportunities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py              Run continuous monitoring
  python main.py --single-run Run once and exit (for testing)

Configuration:
  All settings are in .env file. Copy .env.example to .env and configure:
  - TELEGRAM_BOT_TOKEN: Your Telegram bot token
  - TELEGRAM_CHAT_ID: Your Telegram chat ID
  - MIN_OPPORTUNITY_SCORE: Minimum score for alerts (default: 30)
  - CHECK_INTERVAL_SECONDS: How often to check (default: 300)

For more info, see README.md
        """,
    )

    parser.add_argument(
        "--single-run",
        action="store_true",
        help="Run once and exit (useful for testing configuration)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="X Monitor Bot v0.1.0",
    )

    return parser.parse_args()


def run_single_cycle():
    """Run a single monitoring cycle and exit."""
    logger.info("Running in SINGLE-RUN mode (will exit after one cycle)")

    try:
        monitor = XMonitor()

        logger.info("=" * 60)
        logger.info("🧪 SINGLE-RUN MODE")
        logger.info("=" * 60)
        logger.info(f"📡 Checking {len(config.monitored_accounts)} accounts")
        logger.info(f"🎯 Alert threshold: {config.min_opportunity_score}/100")
        logger.info("=" * 60)

        alerts_sent = 0
        start_time = time.time()

        # Check each account once
        for username in config.monitored_accounts:
            tweet = monitor.check_account(username)

            if tweet:
                # Check if meets alert threshold
                if (
                    tweet["opportunity_score"] >= config.min_opportunity_score
                    and tweet["age_minutes"] <= config.max_tweet_age_minutes
                ):

                    logger.success(f"🚨 ALERT: @{username} - Score: {tweet['opportunity_score']}")

                    # Send alert
                    message = monitor.format_alert_message(tweet)
                    if monitor.send_telegram_alert(message):
                        alerts_sent += 1
                        logger.success("   ✅ Alert sent via Telegram")
                    else:
                        logger.error("   ❌ Failed to send alert")

            # Rate limiting
            time.sleep(config.delay_between_accounts)

        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"✅ Single run complete: {alerts_sent} alerts sent in {elapsed:.1f}s")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.exception(f"Error during single run: {e}")
        return 1


def run_continuous():
    """Run continuous monitoring loop."""
    logger.info("Running in CONTINUOUS mode (press Ctrl+C to stop)")

    try:
        monitor = XMonitor()
        monitor.run()
        return 0

    except KeyboardInterrupt:
        logger.info("\n\n👋 Shutting down gracefully...")
        return 0

    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        return 1


def main():
    """Main entry point."""
    args = parse_args()

    # Display banner
    print()
    print("=" * 60)
    print("🚀 X MONITOR BOT")
    print("=" * 60)
    print("Monitor high-signal accounts for reply opportunities")
    print("Based on X's open-source algorithm")
    print("=" * 60)
    print()

    # Validate configuration
    try:
        # This will raise ValueError if required env vars are missing
        _ = config.telegram_bot_token
        _ = config.telegram_chat_id
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please copy .env.example to .env and configure your settings")
        return 1

    # Run appropriate mode
    if args.single_run:
        return run_single_cycle()
    else:
        return run_continuous()


if __name__ == "__main__":
    sys.exit(main())
