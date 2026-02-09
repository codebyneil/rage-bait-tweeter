"""Headline clustering and filtering using LLM."""

import json
import logging

from .config import Config
from .models import complete, extract_json
from .types import Cluster, Headline

logger = logging.getLogger(__name__)

CLUSTERING_PROMPT = """\
You are a news headline clustering assistant. Group the following headlines \
by the underlying story or event they cover.

Headlines:
{headlines}

{recent_tweets_section}

Instructions:
- Group headlines that cover the same underlying news story or event
- Each headline should belong to exactly one cluster
- Give each cluster a short slug ID and a one-sentence summary
- If recent tweets are provided, mark clusters as "already_covered": true \
if they match a recent tweet's topic

Respond with ONLY valid JSON in this format:
{{
  "clusters": [
    {{
      "id": "short-slug",
      "summary": "One sentence summary of the story",
      "headline_indices": [0, 3, 5],
      "already_covered": false
    }}
  ]
}}"""


def cluster_headlines(
    headlines: list[Headline],
    recent_tweets: list[str],
    config: Config,
) -> list[Cluster]:
    """Cluster headlines by story and mark already-covered ones."""
    if not headlines:
        return []

    headlines_text = "\n".join(
        f"[{i}] {h.title} ({h.source})" for i, h in enumerate(headlines)
    )

    if recent_tweets:
        tweets_text = (
            "Recent tweets from our account "
            "(mark matching clusters as already_covered):\n"
        )
        tweets_text += "\n".join(f"- {t}" for t in recent_tweets)
    else:
        tweets_text = "No recent tweets available."

    prompt = CLUSTERING_PROMPT.format(
        headlines=headlines_text,
        recent_tweets_section=tweets_text,
    )

    response = complete(config.models.clustering, prompt, json_mode=True)
    return _parse_clusters(response, headlines)


def _parse_clusters(response: str, headlines: list[Headline]) -> list[Cluster]:
    """Parse LLM JSON response into Cluster objects."""
    try:
        data = extract_json(response)
    except json.JSONDecodeError:
        logger.error("Failed to parse clustering response as JSON: %s", response[:200])
        return []

    clusters = []
    for c in data.get("clusters", []):
        indices = c.get("headline_indices", [])
        cluster_headlines = [headlines[i] for i in indices if i < len(headlines)]
        clusters.append(
            Cluster(
                id=c.get("id", "unknown"),
                summary=c.get("summary", ""),
                headlines=cluster_headlines,
                already_covered=c.get("already_covered", False),
            )
        )

    return clusters


def filter_covered(clusters: list[Cluster]) -> list[Cluster]:
    """Remove clusters that have already been covered by recent tweets."""
    surviving = [c for c in clusters if not c.already_covered]
    dropped = len(clusters) - len(surviving)
    if dropped:
        logger.info("Filtered out %d already-covered clusters", dropped)
    return surviving
