"""Tests for peak hours gate."""

from unittest.mock import patch
from datetime import datetime
from zoneinfo import ZoneInfo

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
from rage_bait_tweeter.gate import is_peak_hours, check_daily_limit


def _make_config(windows: list[PeakWindow], tz: str = "America/New_York") -> Config:
    return Config(
        feeds=[],
        twitter=TwitterConfig(handle="@test"),
        models=ModelsConfig(),
        slack=SlackConfig(),
        limits=LimitsConfig(),
        peak_hours=PeakHoursConfig(timezone=tz, windows=windows),
    )


class TestIsPeakHours:
    def test_inside_window(self):
        config = _make_config([PeakWindow(start="07:00", end="09:00")])
        fake_time = datetime(2026, 2, 8, 8, 0, tzinfo=ZoneInfo("America/New_York"))
        with patch("rage_bait_tweeter.gate.datetime") as mock_dt:
            mock_dt.now.return_value = fake_time
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert is_peak_hours(config) is True

    def test_outside_window(self):
        config = _make_config([PeakWindow(start="07:00", end="09:00")])
        fake_time = datetime(2026, 2, 8, 10, 0, tzinfo=ZoneInfo("America/New_York"))
        with patch("rage_bait_tweeter.gate.datetime") as mock_dt:
            mock_dt.now.return_value = fake_time
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert is_peak_hours(config) is False

    def test_at_window_start(self):
        config = _make_config([PeakWindow(start="07:00", end="09:00")])
        fake_time = datetime(2026, 2, 8, 7, 0, tzinfo=ZoneInfo("America/New_York"))
        with patch("rage_bait_tweeter.gate.datetime") as mock_dt:
            mock_dt.now.return_value = fake_time
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert is_peak_hours(config) is True

    def test_at_window_end(self):
        config = _make_config([PeakWindow(start="07:00", end="09:00")])
        fake_time = datetime(2026, 2, 8, 9, 0, tzinfo=ZoneInfo("America/New_York"))
        with patch("rage_bait_tweeter.gate.datetime") as mock_dt:
            mock_dt.now.return_value = fake_time
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert is_peak_hours(config) is False

    def test_multiple_windows(self):
        config = _make_config([
            PeakWindow(start="07:00", end="09:00"),
            PeakWindow(start="17:00", end="20:00"),
        ])
        # 18:00 should be in second window
        fake_time = datetime(2026, 2, 8, 18, 0, tzinfo=ZoneInfo("America/New_York"))
        with patch("rage_bait_tweeter.gate.datetime") as mock_dt:
            mock_dt.now.return_value = fake_time
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert is_peak_hours(config) is True

    def test_no_windows(self):
        config = _make_config([])
        assert is_peak_hours(config) is False


class TestCheckDailyLimit:
    def test_no_tweets_allows_posting(self):
        config = _make_config([])
        assert check_daily_limit([], config) is True

    def test_with_tweets_allows_posting(self):
        config = _make_config([])
        assert check_daily_limit(["tweet1", "tweet2"], config) is True
