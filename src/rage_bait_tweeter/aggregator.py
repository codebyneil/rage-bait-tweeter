"""RSS feed aggregation and recent tweet fetching."""

import calendar
import logging
import subprocess
from datetime import datetime, timedelta, timezone

import feedparser

from .config import Config
from .types import Headline

logger = logging.getLogger(__name__)


def fetch_headlines(config: Config) -> list[Headline]:
    """Poll all configured RSS feeds and return headlines within the time window."""
    window_hours = config.limits.headline_window_hours
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)

    all_headlines: list[Headline] = []

    for feed_cfg in config.feeds:
        try:
            headlines = _parse_feed(feed_cfg.url, feed_cfg.category, cutoff)
            logger.info("Feed %s: %d headlines", feed_cfg.url, len(headlines))
            all_headlines.extend(headlines)
        except Exception:
            logger.exception("Failed to fetch feed: %s", feed_cfg.url)

    logger.info(
        "Total headlines: %d (from %d feeds)", len(all_headlines), len(config.feeds)
    )
    return all_headlines


def _parse_feed(url: str, category: str, cutoff: datetime) -> list[Headline]:
    """Parse a single RSS feed and return headlines after cutoff."""
    feed = feedparser.parse(url)
    headlines = []

    for entry in feed.entries:
        published = _parse_date(entry)

        # If we can't determine the date, include it (better to over-include)
        if published and published < cutoff:
            continue

        title = entry.get("title", "").strip()
        if not title:
            continue

        headlines.append(
            Headline(
                title=title,
                url=entry.get("link", ""),
                source=category,
                published=published,
                summary=entry.get("summary", "").strip(),
            )
        )

    return headlines


def _parse_date(entry) -> datetime | None:
    """Extract a timezone-aware datetime from a feed entry."""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        ts = calendar.timegm(entry.published_parsed)
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        ts = calendar.timegm(entry.updated_parsed)
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    return None


def fetch_recent_tweets(config: Config) -> list[str]:
    """Fetch recent tweets from our account via bird CLI."""
    handle = config.twitter.handle
    try:
        result = subprocess.run(
            ["bird", "user-tweets", handle, "-n", "10"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            logger.warning("bird user-tweets failed: %s", result.stderr)
            return []

        tweets = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        logger.info("Fetched %d recent tweets for %s", len(tweets), handle)
        return tweets
    except FileNotFoundError:
        logger.warning("bird CLI not found — skipping recent tweet fetch")
        return []
    except subprocess.TimeoutExpired:
        logger.warning("bird user-tweets timed out")
        return []
