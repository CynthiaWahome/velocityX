"""
SQLite database for persisting seen tweets.

This prevents duplicate alerts when the bot restarts.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


class SeenTweetsDB:
    """Database for tracking which tweets have been alerted on."""

    def __init__(self, db_path: str = "data/seen_tweets.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

        # Create data directory if it doesn't exist
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self) -> None:
        """Create the seen_tweets table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS seen_tweets (
                    tweet_id TEXT PRIMARY KEY,
                    seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def is_seen(self, tweet_id: str) -> bool:
        """
        Check if a tweet has been seen before.

        Args:
            tweet_id: Unique identifier for the tweet

        Returns:
            True if tweet has been seen, False otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM seen_tweets WHERE tweet_id = ?",
                (tweet_id,),
            )
            return cursor.fetchone() is not None

    def mark_seen(self, tweet_id: str) -> None:
        """
        Mark a tweet as seen.

        Args:
            tweet_id: Unique identifier for the tweet
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO seen_tweets (tweet_id) VALUES (?)",
                (tweet_id,),
            )
            conn.commit()

    def cleanup_old(self, days: int = 7) -> int:
        """
        Remove tweets older than specified days.

        This prevents the database from growing indefinitely.

        Args:
            days: Remove tweets older than this many days

        Returns:
            Number of tweets removed
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM seen_tweets WHERE seen_at < ?",
                (cutoff_date,),
            )
            conn.commit()
            return cursor.rowcount

    def get_count(self) -> int:
        """
        Get total number of seen tweets in database.

        Returns:
            Count of seen tweets
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM seen_tweets")
            result = cursor.fetchone()
            return result[0] if result else 0

    def clear_all(self) -> None:
        """
        Clear all seen tweets from database.

        Use with caution - this will cause all tweets to be treated as new.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM seen_tweets")
            conn.commit()
