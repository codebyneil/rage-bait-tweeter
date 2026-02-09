"""Configuration loading and validation."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class FeedConfig:
    url: str
    category: str


@dataclass
class TwitterConfig:
    handle: str
    cookies_secret: str = ""


@dataclass
class ModelsConfig:
    clustering: str = "gpt-4o-mini"
    generation: str = "claude-sonnet-4-5-20250929"
    scoring: list[str] = field(
        default_factory=lambda: [
            "gpt-4o",
            "claude-sonnet-4-5-20250929",
            "gemini-2.0-flash",
        ]
    )


@dataclass
class SlackConfig:
    webhook_secret: str = ""


@dataclass
class LimitsConfig:
    max_tweets_per_day: int = 3
    headline_window_hours: int = 12
    min_score_threshold: float = 6.5


@dataclass
class PeakWindow:
    start: str
    end: str


@dataclass
class PeakHoursConfig:
    timezone: str = "America/New_York"
    windows: list[PeakWindow] = field(default_factory=list)


@dataclass
class Config:
    feeds: list[FeedConfig]
    twitter: TwitterConfig
    models: ModelsConfig
    slack: SlackConfig
    limits: LimitsConfig
    peak_hours: PeakHoursConfig


def load_config(path: Path) -> Config:
    """Load configuration from a YAML file."""
    with open(path) as f:
        raw = yaml.safe_load(f)

    feeds = [FeedConfig(**feed) for feed in raw.get("feeds", [])]

    twitter_raw = raw.get("twitter", {})
    twitter = TwitterConfig(
        handle=twitter_raw.get("handle", ""),
        cookies_secret=twitter_raw.get("cookies_secret", ""),
    )

    models_raw = raw.get("models", {})
    models = ModelsConfig(
        clustering=models_raw.get("clustering", ModelsConfig.clustering),
        generation=models_raw.get("generation", ModelsConfig.generation),
        scoring=models_raw.get("scoring", ModelsConfig().scoring),
    )

    slack_raw = raw.get("slack", {})
    slack = SlackConfig(webhook_secret=slack_raw.get("webhook_secret", ""))

    limits_raw = raw.get("limits", {})
    limits = LimitsConfig(
        max_tweets_per_day=limits_raw.get("max_tweets_per_day", 3),
        headline_window_hours=limits_raw.get("headline_window_hours", 12),
        min_score_threshold=limits_raw.get("min_score_threshold", 6.5),
    )

    peak_raw = raw.get("peak_hours", {})
    windows = [
        PeakWindow(start=w["start"], end=w["end"])
        for w in peak_raw.get("windows", [])
    ]
    peak_hours = PeakHoursConfig(
        timezone=peak_raw.get("timezone", "America/New_York"),
        windows=windows,
    )

    return Config(
        feeds=feeds,
        twitter=twitter,
        models=models,
        slack=slack,
        limits=limits,
        peak_hours=peak_hours,
    )
