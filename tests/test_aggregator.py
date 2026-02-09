"""Tests for the RSS aggregator."""

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from rage_bait_tweeter.aggregator import _parse_date, _parse_feed, fetch_recent_tweets
from rage_bait_tweeter.config import Config, FeedConfig, LimitsConfig, ModelsConfig, PeakHoursConfig, SlackConfig, TwitterConfig


def _make_config() -> Config:
    return Config(
        feeds=[FeedConfig(url="https://example.com/rss", category="tech")],
        twitter=TwitterConfig(handle="@test"),
        models=ModelsConfig(),
        slack=SlackConfig(),
        limits=LimitsConfig(headline_window_hours=12),
        peak_hours=PeakHoursConfig(),
    )


class TestParseDate:
    def test_published_parsed(self):
        entry = MagicMock()
        entry.published_parsed = time.gmtime()
        entry.updated_parsed = None
        result = _parse_date(entry)
        assert result is not None
        assert result.tzinfo == timezone.utc

    def test_updated_parsed_fallback(self):
        entry = MagicMock()
        entry.published_parsed = None
        entry.updated_parsed = time.gmtime()
        result = _parse_date(entry)
        assert result is not None

    def test_no_date(self):
        entry = MagicMock()
        entry.published_parsed = None
        entry.updated_parsed = None
        result = _parse_date(entry)
        assert result is None


class TestFetchRecentTweets:
    @patch("rage_bait_tweeter.aggregator.subprocess")
    def test_bird_not_found(self, mock_subprocess):
        mock_subprocess.run.side_effect = FileNotFoundError()
        config = _make_config()
        result = fetch_recent_tweets(config)
        assert result == []

    @patch("rage_bait_tweeter.aggregator.subprocess")
    def test_bird_success(self, mock_subprocess):
        mock_subprocess.run.return_value = MagicMock(
            returncode=0,
            stdout="tweet 1\ntweet 2\ntweet 3\n",
        )
        config = _make_config()
        result = fetch_recent_tweets(config)
        assert result == ["tweet 1", "tweet 2", "tweet 3"]

    @patch("rage_bait_tweeter.aggregator.subprocess")
    def test_bird_failure(self, mock_subprocess):
        mock_subprocess.run.return_value = MagicMock(
            returncode=1,
            stderr="auth error",
        )
        config = _make_config()
        result = fetch_recent_tweets(config)
        assert result == []
