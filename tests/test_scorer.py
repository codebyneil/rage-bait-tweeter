"""Tests for multi-model scoring."""

from unittest.mock import patch

from rage_bait_tweeter.config import Config, FeedConfig, LimitsConfig, ModelsConfig, PeakHoursConfig, SlackConfig, TwitterConfig
from rage_bait_tweeter.scorer import _score_single, pick_winner, score_candidates
from rage_bait_tweeter.types import Candidate, ScoredCandidate


def _make_config(threshold: float = 6.5) -> Config:
    return Config(
        feeds=[],
        twitter=TwitterConfig(handle="@test"),
        models=ModelsConfig(scoring=["gpt-4o", "gemini-2.0-flash"]),
        slack=SlackConfig(),
        limits=LimitsConfig(min_score_threshold=threshold),
        peak_hours=PeakHoursConfig(),
    )


class TestScoreSingle:
    @patch("rage_bait_tweeter.scorer.complete")
    def test_parses_integer_score(self, mock_complete):
        mock_complete.return_value = "8"
        assert _score_single("test tweet", "gpt-4o") == 8.0

    @patch("rage_bait_tweeter.scorer.complete")
    def test_parses_decimal_score(self, mock_complete):
        mock_complete.return_value = "7.5"
        assert _score_single("test tweet", "gpt-4o") == 7.5

    @patch("rage_bait_tweeter.scorer.complete")
    def test_parses_score_with_text(self, mock_complete):
        mock_complete.return_value = "I'd rate this a 9 out of 10"
        assert _score_single("test tweet", "gpt-4o") == 9.0

    @patch("rage_bait_tweeter.scorer.complete")
    def test_rejects_out_of_range(self, mock_complete):
        mock_complete.return_value = "15"
        assert _score_single("test tweet", "gpt-4o") is None

    @patch("rage_bait_tweeter.scorer.complete")
    def test_rejects_no_number(self, mock_complete):
        mock_complete.return_value = "This tweet is great!"
        assert _score_single("test tweet", "gpt-4o") is None


class TestPickWinner:
    def test_picks_highest_above_threshold(self):
        scored = [
            ScoredCandidate(tweet="best", cluster_id="a", cluster_summary="s", scores={"m": 9.0}, avg_score=9.0),
            ScoredCandidate(tweet="ok", cluster_id="a", cluster_summary="s", scores={"m": 7.0}, avg_score=7.0),
        ]
        config = _make_config(threshold=6.5)
        winner = pick_winner(scored, config)
        assert winner is not None
        assert winner.tweet == "best"

    def test_none_above_threshold(self):
        scored = [
            ScoredCandidate(tweet="meh", cluster_id="a", cluster_summary="s", scores={"m": 5.0}, avg_score=5.0),
        ]
        config = _make_config(threshold=6.5)
        assert pick_winner(scored, config) is None

    def test_empty_list(self):
        assert pick_winner([], _make_config()) is None


class TestScoreCandidates:
    @patch("rage_bait_tweeter.scorer.complete")
    def test_scores_with_multiple_models(self, mock_complete):
        mock_complete.side_effect = ["8", "7"]
        config = _make_config()
        candidates = [
            Candidate(tweet="Test tweet", cluster_id="a", cluster_summary="s"),
        ]

        scored = score_candidates(candidates, config)
        assert len(scored) == 1
        assert scored[0].avg_score == 7.5
        assert "gpt-4o" in scored[0].scores
        assert "gemini-2.0-flash" in scored[0].scores
