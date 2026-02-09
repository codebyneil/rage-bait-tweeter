"""Twitter posting via bird CLI."""

import logging
import subprocess

from .config import Config

logger = logging.getLogger(__name__)


def post_tweet(text: str, config: Config) -> str | None:
    """Post a tweet using bird CLI. Returns tweet URL on success."""
    try:
        result = subprocess.run(
            ["bird", "tweet", text],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            logger.error("bird tweet failed: %s", result.stderr)
            return None

        url = result.stdout.strip()
        if url:
            logger.info("Tweet posted: %s", url)
            return url

        logger.warning("bird tweet succeeded but returned no URL")
        return "posted"
    except FileNotFoundError:
        logger.error("bird CLI not found — cannot post tweet")
        return None
    except subprocess.TimeoutExpired:
        logger.error("bird tweet timed out")
        return None
