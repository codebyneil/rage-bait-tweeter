"""Tests for the pipeline orchestration."""

from unittest.mock import MagicMock, patch

from rage_bait_tweeter.config import (
    Config,
    FeedConfig,
    LimitsConfig,
    ModelsConfig,
    PeakHoursConfig,
    PeakWindow,
    SlackConfig,
    TwitterConfig,
)
from rage_bait_tweeter.pipeline import run_pipeline
from rage_bait_tweeter.types import Candidate, Cluster, Headline, ScoredCandidate


def _make_config() -> Config:
    return Config(
        feeds=[FeedConfig(url="https://example.com/rss", category="tech")],
        twitter=TwitterConfig(handle="@test"),
        models=ModelsConfig(),
        slack=SlackConfig(),
        limits=LimitsConfig(),
        peak_hours=PeakHoursConfig(
            windows=[PeakWindow(start="00:00", end="23:59")]
        ),
    )


class TestPipeline:
    @patch("rage_bait_tweeter.pipeline.notify_skip")
    @patch("rage_bait_tweeter.pipeline.fetch_recent_tweets", return_value=[])
    @patch("rage_bait_tweeter.pipeline.fetch_headlines", return_value=[])
    def test_exits_on_no_headlines(self, mock_fetch, mock_tweets, mock_notify):
        run_pipeline(_make_config(), dry_run=True)
        mock_notify.assert_called_once()
        assert "No headlines" in mock_notify.call_args[0][0]

    @patch("rage_bait_tweeter.pipeline.notify_skip")
    @patch("rage_bait_tweeter.pipeline.notify_posted")
    @patch("rage_bait_tweeter.pipeline.pick_winner", return_value=None)
    @patch("rage_bait_tweeter.pipeline.score_candidates", return_value=[])
    @patch("rage_bait_tweeter.pipeline.generate_candidates")
    @patch("rage_bait_tweeter.pipeline.filter_covered")
    @patch("rage_bait_tweeter.pipeline.cluster_headlines")
    @patch("rage_bait_tweeter.pipeline.fetch_recent_tweets", return_value=[])
    @patch("rage_bait_tweeter.pipeline.fetch_headlines")
    def test_exits_on_no_winner(
        self, mock_fetch, mock_tweets, mock_cluster, mock_filter,
        mock_gen, mock_score, mock_pick, mock_posted, mock_skip,
    ):
        mock_fetch.return_value = [
            Headline(title="Test", url="https://example.com", source="tech"),
        ]
        mock_cluster.return_value = [
            Cluster(id="test", summary="Test", headlines=[]),
        ]
        mock_filter.return_value = mock_cluster.return_value
        mock_gen.return_value = [
            Candidate(tweet="Test tweet", cluster_id="test", cluster_summary="Test"),
        ]

        run_pipeline(_make_config(), dry_run=True)
        mock_skip.assert_called_once()
        assert "threshold" in mock_skip.call_args[0][0]
        mock_posted.assert_not_called()

    @patch("rage_bait_tweeter.pipeline.notify_posted")
    @patch("rage_bait_tweeter.pipeline.pick_winner")
    @patch("rage_bait_tweeter.pipeline.score_candidates")
    @patch("rage_bait_tweeter.pipeline.generate_candidates")
    @patch("rage_bait_tweeter.pipeline.filter_covered")
    @patch("rage_bait_tweeter.pipeline.cluster_headlines")
    @patch("rage_bait_tweeter.pipeline.fetch_recent_tweets", return_value=[])
    @patch("rage_bait_tweeter.pipeline.fetch_headlines")
    def test_dry_run_does_not_post(
        self, mock_fetch, mock_tweets, mock_cluster, mock_filter,
        mock_gen, mock_score, mock_pick, mock_posted,
    ):
        mock_fetch.return_value = [
            Headline(title="Test", url="https://example.com", source="tech"),
        ]
        mock_cluster.return_value = [
            Cluster(id="test", summary="Test", headlines=[]),
        ]
        mock_filter.return_value = mock_cluster.return_value
        mock_gen.return_value = [
            Candidate(tweet="Great tweet", cluster_id="test", cluster_summary="Test"),
        ]
        mock_score.return_value = []
        winner = ScoredCandidate(
            tweet="Great tweet", cluster_id="test",
            cluster_summary="Test", scores={"gpt-4o": 8.0}, avg_score=8.0,
        )
        mock_pick.return_value = winner

        run_pipeline(_make_config(), dry_run=True)
        mock_posted.assert_called_once()
