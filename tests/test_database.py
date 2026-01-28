"""
Tests for database persistence layer.
"""

import os
import tempfile
from pathlib import Path

import pytest

from src.database import SeenTweetsDB


class TestSeenTweetsDB:
    """Test database operations for seen tweets."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_tweets.db")
            db = SeenTweetsDB(db_path)
            yield db

    def test_database_initialization(self, temp_db):
        """Test that database file is created."""
        assert Path(temp_db.db_path).exists()

    def test_is_seen_returns_false_for_new_tweet(self, temp_db):
        """Test that new tweets are not marked as seen."""
        assert temp_db.is_seen("tweet123") is False

    def test_mark_seen_adds_tweet(self, temp_db):
        """Test that marking a tweet as seen works."""
        temp_db.mark_seen("tweet123")
        assert temp_db.is_seen("tweet123") is True

    def test_mark_seen_is_idempotent(self, temp_db):
        """Test that marking the same tweet multiple times doesn't cause errors."""
        temp_db.mark_seen("tweet123")
        temp_db.mark_seen("tweet123")  # Should not raise error
        assert temp_db.is_seen("tweet123") is True

    def test_multiple_tweets(self, temp_db):
        """Test tracking multiple different tweets."""
        tweets = ["tweet1", "tweet2", "tweet3"]

        for tweet_id in tweets:
            temp_db.mark_seen(tweet_id)

        for tweet_id in tweets:
            assert temp_db.is_seen(tweet_id) is True

        # New tweet should not be seen
        assert temp_db.is_seen("tweet4") is False

    def test_get_count(self, temp_db):
        """Test getting count of seen tweets."""
        assert temp_db.get_count() == 0

        temp_db.mark_seen("tweet1")
        assert temp_db.get_count() == 1

        temp_db.mark_seen("tweet2")
        assert temp_db.get_count() == 2

        # Marking same tweet again shouldn't increase count
        temp_db.mark_seen("tweet1")
        assert temp_db.get_count() == 2

    def test_clear_all(self, temp_db):
        """Test clearing all seen tweets."""
        # Add some tweets
        temp_db.mark_seen("tweet1")
        temp_db.mark_seen("tweet2")
        assert temp_db.get_count() == 2

        # Clear all
        temp_db.clear_all()
        assert temp_db.get_count() == 0

        # Tweets should no longer be seen
        assert temp_db.is_seen("tweet1") is False
        assert temp_db.is_seen("tweet2") is False

    def test_cleanup_old_tweets(self, temp_db):
        """Test cleanup of old tweets."""
        # Add a tweet
        temp_db.mark_seen("tweet1")
        assert temp_db.get_count() == 1

        # Cleanup tweets older than 7 days (should not remove recent tweet)
        removed = temp_db.cleanup_old(days=7)
        assert removed == 0
        assert temp_db.get_count() == 1

        # Cleanup tweets older than 0 days (should remove all)
        removed = temp_db.cleanup_old(days=0)
        assert removed == 1
        assert temp_db.get_count() == 0

    def test_database_persistence(self):
        """Test that database persists across instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_tweets.db")

            # Create first instance and add tweet
            db1 = SeenTweetsDB(db_path)
            db1.mark_seen("tweet123")
            assert db1.is_seen("tweet123") is True

            # Create second instance (simulating restart)
            db2 = SeenTweetsDB(db_path)
            # Tweet should still be marked as seen
            assert db2.is_seen("tweet123") is True

    def test_concurrent_access(self, temp_db):
        """Test that multiple operations work correctly."""
        # Simulate concurrent-like access
        tweets = [f"tweet{i}" for i in range(100)]

        for tweet_id in tweets:
            temp_db.mark_seen(tweet_id)

        # All should be seen
        for tweet_id in tweets:
            assert temp_db.is_seen(tweet_id) is True

        assert temp_db.get_count() == 100
