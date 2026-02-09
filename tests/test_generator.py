"""Tests for rage-bait generation."""

import json
from unittest.mock import patch

from rage_bait_tweeter.config import Config, FeedConfig, LimitsConfig, ModelsConfig, PeakHoursConfig, SlackConfig, TwitterConfig
from rage_bait_tweeter.generator import _generate_for_cluster
from rage_bait_tweeter.types import Cluster, Headline


def _make_config() -> Config:
    return Config(
        feeds=[],
        twitter=TwitterConfig(handle="@test"),
        models=ModelsConfig(generation="claude-sonnet-4-5-20250929"),
        slack=SlackConfig(),
        limits=LimitsConfig(),
        peak_hours=PeakHoursConfig(),
    )


def _make_cluster() -> Cluster:
    return Cluster(
        id="test-story",
        summary="Tech companies announce layoffs",
        headlines=[
            Headline(title="Big Tech Layoffs Continue", url="https://example.com/1", source="tech"),
            Headline(title="More Jobs Cut at startups", url="https://example.com/2", source="tech"),
        ],
    )


class TestGenerateForCluster:
    @patch("rage_bait_tweeter.generator.complete")
    def test_parses_valid_response(self, mock_complete):
        mock_complete.return_value = json.dumps({
            "candidates": [
                "Breaking: Tech companies discover employees are people, immediately regret it",
                "Another round of layoffs, another CEO discovering AI can't run a company yet",
            ]
        })

        config = _make_config()
        cluster = _make_cluster()
        candidates = _generate_for_cluster(cluster, config)

        assert len(candidates) == 2
        assert candidates[0].cluster_id == "test-story"
        assert candidates[0].cluster_summary == "Tech companies announce layoffs"
        assert "Tech companies" in candidates[0].tweet

    @patch("rage_bait_tweeter.generator.complete")
    def test_drops_long_tweets(self, mock_complete):
        long_tweet = "x" * 281
        mock_complete.return_value = json.dumps({
            "candidates": [long_tweet, "Short tweet that's fine"]
        })

        candidates = _generate_for_cluster(_make_cluster(), _make_config())
        assert len(candidates) == 1
        assert candidates[0].tweet == "Short tweet that's fine"

    @patch("rage_bait_tweeter.generator.complete")
    def test_handles_invalid_json(self, mock_complete):
        mock_complete.return_value = "I can't generate that content"

        candidates = _generate_for_cluster(_make_cluster(), _make_config())
        assert candidates == []

    @patch("rage_bait_tweeter.generator.complete")
    def test_handles_markdown_wrapped_json(self, mock_complete):
        mock_complete.return_value = '```json\n{"candidates": ["Test tweet"]}\n```'

        candidates = _generate_for_cluster(_make_cluster(), _make_config())
        assert len(candidates) == 1
        assert candidates[0].tweet == "Test tweet"
