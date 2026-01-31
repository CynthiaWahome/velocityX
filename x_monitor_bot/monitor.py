"""
X/Twitter Monitor Bot - Main Monitoring Logic.

Monitors high-signal X/Twitter accounts via Google News RSS feeds.
Calculates opportunity scores based on X's open-source algorithm.
Sends Telegram alerts for high-value reply opportunities.

This script does NOT interact with X/Twitter directly - it only reads
public Google News RSS feeds. Your X account cannot be detected or banned.
"""

import hashlib
import time
from datetime import datetime
import urllib.parse
from io import BytesIO

import feedparser
import requests
from loguru import logger

from .config import config
from .constants import ALERT_EMOJIS
from .database import SeenTweetsDB
from .ai_replies import get_reply_suggestions


class XMonitor:
    """Main monitoring class for X/Twitter accounts."""

    def __init__(self):
        """Initialize the monitor with database and HTTP session."""
        self.db = SeenTweetsDB()
        
        # Create session with proper headers to avoid 503 errors
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
        })
        
        # Also configure feedparser's User-Agent as backup
        feedparser.USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

        logger.info("X Monitor Bot initialized")
        logger.info(f"Monitoring {len(config.monitored_accounts)} accounts")

    def send_telegram_alert(self, message: str) -> bool:
        """
        Send alert via Telegram.

        Args:
            message: Message to send (supports Markdown)

        Returns:
            True if sent successfully, False otherwise
        """
        url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"

        try:
            response = self.session.post(
                url,
                json={
                    "chat_id": config.telegram_chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": False,
                },
                timeout=10,
            )

            if response.status_code == 200:
                logger.debug("Telegram alert sent successfully")
                return True
            else:
                logger.error(f"Telegram API error: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False

    def get_google_rss_url(self, username: str) -> str:
        """
        Generate Google News RSS URL for X user.

        Args:
            username: X/Twitter username (without @)

        Returns:
            Google News RSS feed URL
        """
        import urllib.parse

        # Search both twitter.com and x.com domains
        # "when:1h" limits to last hour
        query = f"site:twitter.com/{username} OR site:x.com/{username} when:1h"
        encoded_query = urllib.parse.quote(query)
        return f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

    def fetch_rss_feed(self, url: str, retries: int = 3):
        """
        Fetch RSS feed with proper error handling and retries.

        Args:
            url: RSS feed URL
            retries: Number of retry attempts

        Returns:
            Parsed feed or None on error
        """
        from io import BytesIO

        for attempt in range(retries):
            try:
                # Use requests with proper headers
                response = self.session.get(url, timeout=10)

                if response.status_code == 200:
                    # Parse the RSS content
                    feed = feedparser.parse(BytesIO(response.content))
                    return feed

                elif response.status_code == 503:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"503 error on attempt {attempt + 1}/{retries}, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                else:
                    logger.error(f"HTTP {response.status_code} error fetching RSS")
                    return None

            except requests.exceptions.Timeout:
                wait_time = 2 ** attempt
                logger.warning(f"Timeout on attempt {attempt + 1}/{retries}, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue

            except Exception as e:
                logger.error(f"Error fetching RSS: {e}")
                return None

        logger.error(f"Failed to fetch RSS after {retries} attempts")
        return None

    def calculate_opportunity_score(self, age_minutes: int) -> int:
        """
        Calculate opportunity score based on tweet age.

        Uses X algorithm's recency preference:
        - Fresh tweets (<10 min) get highest score
        - Older tweets score lower

        Args:
            age_minutes: Estimated age of tweet in minutes

        Returns:
            Score from 0-100
        """
        if age_minutes < 10:
            base_score = 100
        elif age_minutes < 15:
            base_score = 85
        elif age_minutes < 30:
            base_score = 60
        elif age_minutes < 60:
            base_score = 40
        else:
            base_score = 20

        return base_score

    def generate_tweet_id(self, entry: dict) -> str:
        """
        Generate unique ID for tweet.

        Args:
            entry: RSS feed entry

        Returns:
            MD5 hash of link and title
        """
        # Support both dict and feedparser entry objects
        link = entry.get("link") if isinstance(entry, dict) else entry.link
        title = entry.get("title") if isinstance(entry, dict) else entry.title
        content = f"{link}{title}"
        return hashlib.md5(content.encode()).hexdigest()

    def check_account(self, username: str) -> dict | None:
        """
        Check single account for new tweets.

        Args:
            username: X/Twitter username (without @)

        Returns:
            Tweet data dict if new tweet found, None otherwise
        """
        rss_url = self.get_google_rss_url(username)

        try:
            # Fetch RSS feed with proper headers and retry logic
            logger.debug(f"Fetching RSS for @{username}...")
            feed = self.fetch_rss_feed(rss_url)

            if feed is None:
                logger.debug(f"Failed to fetch RSS feed for @{username}")
                return None

            if not feed.entries:
                logger.debug(f"No recent tweets from @{username}")
                return None

            # Get latest tweet
            latest = feed.entries[0]
            
            # Support both dict and feedparser entry objects
            link = latest.get("link") if isinstance(latest, dict) else getattr(latest, "link", None)
            title = latest.get("title") if isinstance(latest, dict) else getattr(latest, "title", None)
            
            if not link or not title:
                logger.debug(f"@{username}: Missing link or title in RSS entry")
                return None
            
            tweet_id = self.generate_tweet_id(latest)

            # Skip if already seen
            if self.db.is_seen(tweet_id):
                logger.debug(f"@{username}: Already alerted on this tweet")
                return None

            # Mark as seen
            self.db.mark_seen(tweet_id)

            # Estimate age (Google News has 5-15 min indexing delay)
            # We estimate 10 minutes as middle ground
            estimated_age = 10

            # Calculate opportunity score
            opportunity_score = self.calculate_opportunity_score(estimated_age)

            logger.info(f"@{username}: New tweet detected (score: {opportunity_score})")

            published = latest.get("published") if isinstance(latest, dict) else getattr(latest, "published", "Unknown")

            return {
                "username": username,
                "title": title,
                "link": link,
                "age_minutes": estimated_age,
                "opportunity_score": opportunity_score,
                "published": published,
            }

        except Exception as e:
            logger.warning(f"Error checking @{username}: {e}")
            return None

    def format_alert_message(self, tweet: dict) -> str:
        """
        Format pretty Telegram alert with AI reply suggestions.

        Args:
            tweet: Tweet data dictionary

        Returns:
            Formatted Markdown message
        """
        score = tweet["opportunity_score"]

        # Choose emoji based on score
        if score >= 80:
            emoji = ALERT_EMOJIS["critical"]  # 🔥🔥🔥
        elif score >= 50:
            emoji = ALERT_EMOJIS["high"]  # 🚨
        else:
            emoji = ALERT_EMOJIS["medium"]  # 📢

        # Truncate title if too long
        title = tweet["title"]
        if len(title) > 200:
            title = title[:200] + "..."

        # Construct profile URL (more reliable than Google News redirect)
        profile_url = f"https://twitter.com/{tweet['username']}"

        message = f"""{emoji} *NEW OPPORTUNITY*

*Account:* @{tweet['username']}
*Score:* {score}/100
*Age:* ~{tweet['age_minutes']} minutes

📝 *Tweet:*
{title}

🔗 *Profile:* {profile_url}
_(Check recent tweets)_

⏰ *Reply NOW for maximum visibility!*
"""
        
        # Add AI reply suggestions if enabled
        if config.enable_ai_replies and config.groq_api_key:
            try:
                replies = get_reply_suggestions(title, tweet['username'], 5)
                if replies:
                    message += "\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    message += "💡 *REPLY SUGGESTIONS:*\n\n"
                    for i, reply in enumerate(replies, 1):
                        message += f"*{i}.* {reply}\n\n"
                    message += "_Pick one, customize, post!_ 🚀"
            except Exception as e:
                logger.warning(f"Failed to generate AI replies: {e}")
                # Fall back to static tips
                message += "\n_AI suggestions unavailable_"
        else:
            # Static tips if AI not enabled
            message += """
_Why reply now:_
• Replies are 13.5x more valuable than likes
• Author reply back = 75x multiplier
• First 15 min are critical for distribution
"""

        return message

    def run(self) -> None:
        """Main monitoring loop."""

        logger.info("=" * 60)
        logger.info("🚀 X MONITOR BOT STARTED")
        logger.info("=" * 60)
        logger.info(f"📡 Monitoring {len(config.monitored_accounts)} accounts")
        logger.info(f"⏱️  Checking every {config.check_interval_seconds} seconds")
        logger.info(f"🎯 Alert threshold: {config.min_opportunity_score}/100")
        logger.info(f"⏰ Max tweet age: {config.max_tweet_age_minutes} minutes")
        logger.info(f"🔄 Delay between accounts: {config.delay_between_accounts}s")
        logger.info("=" * 60)

        # Send startup notification
        startup_msg = f"""✅ *X Monitor Bot Started*

Monitoring {len(config.monitored_accounts)} accounts
Checking every {config.check_interval_seconds // 60} minutes

Ready to catch opportunities! 🎯"""

        self.send_telegram_alert(startup_msg)

        cycle_count = 0

        while True:
            try:
                cycle_count += 1
                start_time = time.time()

                logger.info(f"\n📊 CYCLE #{cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
                logger.info("-" * 60)

                alerts_sent = 0

                # Check each account
                for username in config.monitored_accounts:
                    tweet = self.check_account(username)

                    if tweet:
                        # Check if meets alert threshold
                        if (
                            tweet["opportunity_score"] >= config.min_opportunity_score
                            and tweet["age_minutes"] <= config.max_tweet_age_minutes
                        ):

                            logger.success(
                                f"🚨 ALERT: @{username} - Score: {tweet['opportunity_score']}"
                            )

                            # Send alert
                            message = self.format_alert_message(tweet)
                            if self.send_telegram_alert(message):
                                alerts_sent += 1
                                logger.success("   ✅ Alert sent via Telegram")
                            else:
                                logger.error("   ❌ Failed to send alert")
                        else:
                            logger.debug(f"   Below threshold: @{username}")

                    # Rate limiting - ensure a minimum 2-second delay
                    time.sleep(max(2, config.delay_between_accounts))

                # Cycle summary
                elapsed = time.time() - start_time
                logger.info("-" * 60)
                logger.info(f"✅ Cycle complete: {alerts_sent} alerts sent in {elapsed:.1f}s")
                logger.info(f"💤 Sleeping for {config.check_interval_seconds} seconds...")

                # Cleanup old tweets from database (every cycle)
                cleaned = self.db.cleanup_old(days=7)
                if cleaned > 0:
                    logger.debug(f"🗑️  Cleaned up {cleaned} old tweets from database")

                # Wait before next cycle
                time.sleep(config.check_interval_seconds)

            except KeyboardInterrupt:
                logger.info("\n\n👋 Shutting down gracefully...")
                shutdown_msg = "❌ *X Monitor Bot Stopped*\n\nMonitoring paused."
                self.send_telegram_alert(shutdown_msg)
                break

            except Exception as e:
                logger.exception(f"Unexpected error: {e}")
                error_msg = f"⚠️ *Bot Error*\n\n{str(e)}\n\nRetrying in 60 seconds..."
                self.send_telegram_alert(error_msg)
                time.sleep(60)
