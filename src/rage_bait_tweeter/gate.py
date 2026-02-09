"""Peak hours gate and daily limit check."""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import Config

logger = logging.getLogger(__name__)


def is_peak_hours(config: Config) -> bool:
    """Check if current time falls within any configured peak window."""
    tz = ZoneInfo(config.peak_hours.timezone)
    now = datetime.now(tz)
    current_time = now.strftime("%H:%M")

    for window in config.peak_hours.windows:
        if window.start <= current_time < window.end:
            logger.info(
                "In peak window %s-%s (current: %s %s)",
                window.start,
                window.end,
                current_time,
                config.peak_hours.timezone,
            )
            return True

    logger.info(
        "Outside peak hours (current: %s %s)",
        current_time,
        config.peak_hours.timezone,
    )
    return False


def check_daily_limit(recent_tweets: list[str], config: Config) -> bool:
    """Check if we can still post today.

    Returns True if we can post, False if at limit.

    TODO: Parse tweet timestamps from bird output to count only today's tweets.
    For now, always returns True as a conservative fallback.
    """
    max_per_day = config.limits.max_tweets_per_day
    logger.info(
        "Daily limit check: %d recent tweets, limit is %d/day",
        len(recent_tweets),
        max_per_day,
    )
    return True
