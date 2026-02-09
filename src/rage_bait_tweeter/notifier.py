"""Slack webhook notifications."""

import logging

import httpx

from .config import Config
from .types import ScoredCandidate

logger = logging.getLogger(__name__)


def notify_posted(
    candidate: ScoredCandidate,
    tweet_url: str | None,
    config: Config,
) -> None:
    """Notify Slack about a posted tweet."""
    webhook_url = config.slack.webhook_secret
    if not webhook_url:
        logger.debug("No Slack webhook configured, skipping notification")
        return

    score_detail = ", ".join(
        f"{m}: {s:.1f}" for m, s in candidate.scores.items()
    )
    lines = [
        f":bird: *New Tweet Posted*",
        f"",
        f"> {candidate.tweet}",
        f"",
        f":newspaper: *Story:* {candidate.cluster_summary}",
        f":star: *Score:* {candidate.avg_score:.1f}/10 ({score_detail})",
    ]
    if tweet_url:
        lines.append(f":bird: *Tweet:* {tweet_url}")

    _send_webhook(webhook_url, {"text": "\n".join(lines)})


def notify_skip(reason: str, config: Config) -> None:
    """Notify Slack about a skipped run."""
    webhook_url = config.slack.webhook_secret
    if not webhook_url:
        return

    _send_webhook(webhook_url, {"text": f":fast_forward: Skipped: {reason}"})


def notify_error(error: str, config: Config) -> None:
    """Notify Slack about an error."""
    webhook_url = config.slack.webhook_secret
    if not webhook_url:
        return

    _send_webhook(webhook_url, {"text": f":x: Error: {error}"})


def _send_webhook(url: str, payload: dict) -> None:
    """Send a payload to a Slack webhook URL."""
    try:
        response = httpx.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            logger.warning(
                "Slack webhook returned %d: %s",
                response.status_code,
                response.text,
            )
    except Exception:
        logger.exception("Failed to send Slack notification")
