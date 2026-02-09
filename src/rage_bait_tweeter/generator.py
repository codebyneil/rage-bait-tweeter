"""Rage-bait tweet generation."""

import json
import logging

from .config import Config
from .models import complete, extract_json
from .types import Candidate, Cluster

logger = logging.getLogger(__name__)

GENERATION_PROMPT = """\
You are a snarky political/tech/finance pundit who writes viral tweets. \
Your goal is to maximize engagement through outrage, hot takes, and controversy.

RULES:
- You MUST NOT fabricate facts -- stick to what the news publications are saying
- Be provocative, snarky, and controversial
- Use the tone of a cynical commentator
- Keep each tweet under 280 characters
- No hashtags

STORY: {summary}

HEADLINES:
{headlines}

Generate 1-3 rage-bait tweet candidates for this story. \
Respond with ONLY valid JSON:
{{
  "candidates": ["tweet 1", "tweet 2", "tweet 3"]
}}"""


def generate_candidates(
    clusters: list[Cluster],
    config: Config,
) -> list[Candidate]:
    """Generate rage-bait tweet candidates for each cluster."""
    all_candidates: list[Candidate] = []

    for cluster in clusters:
        try:
            candidates = _generate_for_cluster(cluster, config)
            all_candidates.extend(candidates)
            logger.info(
                "Cluster '%s': generated %d candidates", cluster.id, len(candidates)
            )
        except Exception:
            logger.exception("Failed to generate for cluster: %s", cluster.id)

    logger.info("Total candidates generated: %d", len(all_candidates))
    return all_candidates


def _generate_for_cluster(cluster: Cluster, config: Config) -> list[Candidate]:
    """Generate candidates for a single cluster."""
    headlines_text = "\n".join(
        f"- {h.title} ({h.source})" for h in cluster.headlines
    )

    prompt = GENERATION_PROMPT.format(
        summary=cluster.summary,
        headlines=headlines_text,
    )

    response = complete(config.models.generation, prompt, json_mode=True)

    try:
        data = extract_json(response)
    except json.JSONDecodeError:
        logger.error("Failed to parse generation response as JSON: %s", response[:200])
        return []

    candidates = []
    for tweet_text in data.get("candidates", []):
        tweet_text = tweet_text.strip()
        if tweet_text and len(tweet_text) <= 280:
            candidates.append(
                Candidate(
                    tweet=tweet_text,
                    cluster_id=cluster.id,
                    cluster_summary=cluster.summary,
                )
            )
        elif tweet_text:
            logger.warning(
                "Dropping candidate over 280 chars: %s...", tweet_text[:50]
            )

    return candidates
