"""Tests for config loading."""

import tempfile
from pathlib import Path

import pytest
import yaml

from rage_bait_tweeter.config import load_config


def _write_config(data: dict) -> Path:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    yaml.dump(data, f)
    f.close()
    return Path(f.name)


MINIMAL_CONFIG = {
    "feeds": [
        {"url": "https://example.com/rss", "category": "tech"},
    ],
    "twitter": {"handle": "@test"},
    "models": {
        "clustering": "gpt-4o-mini",
        "generation": "claude-sonnet-4-5-20250929",
        "scoring": ["gpt-4o", "gemini-2.0-flash"],
    },
    "slack": {"webhook_secret": "https://hooks.slack.com/test"},
    "limits": {
        "max_tweets_per_day": 2,
        "headline_window_hours": 6,
        "min_score_threshold": 7.0,
    },
    "peak_hours": {
        "timezone": "America/New_York",
        "windows": [{"start": "07:00", "end": "09:00"}],
    },
}


def test_load_minimal_config():
    path = _write_config(MINIMAL_CONFIG)
    config = load_config(path)

    assert len(config.feeds) == 1
    assert config.feeds[0].url == "https://example.com/rss"
    assert config.feeds[0].category == "tech"
    assert config.twitter.handle == "@test"
    assert config.models.clustering == "gpt-4o-mini"
    assert config.models.generation == "claude-sonnet-4-5-20250929"
    assert config.models.scoring == ["gpt-4o", "gemini-2.0-flash"]
    assert config.limits.max_tweets_per_day == 2
    assert config.limits.headline_window_hours == 6
    assert config.limits.min_score_threshold == 7.0
    assert config.peak_hours.timezone == "America/New_York"
    assert len(config.peak_hours.windows) == 1
    assert config.peak_hours.windows[0].start == "07:00"
    assert config.peak_hours.windows[0].end == "09:00"


def test_load_config_defaults():
    """Missing sections should use defaults."""
    path = _write_config({"feeds": [], "twitter": {"handle": "@x"}})
    config = load_config(path)

    assert config.models.clustering == "gpt-4o-mini"
    assert config.limits.max_tweets_per_day == 3
    assert config.limits.min_score_threshold == 6.5
    assert config.peak_hours.timezone == "America/New_York"


def test_load_config_multiple_feeds():
    data = {
        **MINIMAL_CONFIG,
        "feeds": [
            {"url": "https://a.com/rss", "category": "tech"},
            {"url": "https://b.com/rss", "category": "finance"},
            {"url": "https://c.com/rss", "category": "politics"},
        ],
    }
    path = _write_config(data)
    config = load_config(path)
    assert len(config.feeds) == 3
    assert [f.category for f in config.feeds] == ["tech", "finance", "politics"]


def test_load_config_multiple_peak_windows():
    data = {
        **MINIMAL_CONFIG,
        "peak_hours": {
            "timezone": "US/Pacific",
            "windows": [
                {"start": "07:00", "end": "09:00"},
                {"start": "12:00", "end": "13:00"},
                {"start": "17:00", "end": "20:00"},
            ],
        },
    }
    path = _write_config(data)
    config = load_config(path)
    assert config.peak_hours.timezone == "US/Pacific"
    assert len(config.peak_hours.windows) == 3
