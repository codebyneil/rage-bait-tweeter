"""Multi-model scoring panel."""

import logging
import re

from .config import Config
from .models import complete
from .types import Candidate, ScoredCandidate

logger = logging.getLogger(__name__)

SCORING_PROMPT = """\
Rate this tweet 1-10 on "rage-bait-iness" — how likely is it to drive \
engagement through outrage, hot takes, or controversy?

Consider: provocativeness, shareability, emotional punch, clarity.
Do NOT penalize for being controversial — that's the point.

Tweet: {tweet}

Reply with just a number 1-10."""


def score_candidates(
    candidates: list[Candidate],
    config: Config,
) -> list[ScoredCandidate]:
    """Score all candidates using the multi-model panel."""
    scored: list[ScoredCandidate] = []

    for candidate in candidates:
        scores: dict[str, float] = {}

        for model_id in config.models.scoring:
            try:
                score = _score_single(candidate.tweet, model_id)
                if score is not None:
                    scores[model_id] = score
            except Exception:
                logger.exception(
                    "Scoring failed for model %s on tweet: %s...",
                    model_id,
                    candidate.tweet[:50],
                )

        if not scores:
            logger.warning("No scores for candidate: %s...", candidate.tweet[:50])
            continue

        avg = sum(scores.values()) / len(scores)
        scored.append(
            ScoredCandidate(
                tweet=candidate.tweet,
                cluster_id=candidate.cluster_id,
                cluster_summary=candidate.cluster_summary,
                scores=scores,
                avg_score=avg,
            )
        )
        logger.debug("Scored %.1f: %s", avg, candidate.tweet[:60])

    scored.sort(key=lambda s: s.avg_score, reverse=True)
    return scored


def _score_single(tweet: str, model_id: str) -> float | None:
    """Get a single score from one model."""
    prompt = SCORING_PROMPT.format(tweet=tweet)
    response = complete(model_id, prompt)

    match = re.search(r"(\d+(?:\.\d+)?)", response.strip())
    if match:
        score = float(match.group(1))
        if 1 <= score <= 10:
            return score
        logger.warning("Score out of range from %s: %s", model_id, score)
    else:
        logger.warning("Could not parse score from %s: %s", model_id, response)
    return None


def pick_winner(
    scored: list[ScoredCandidate],
    config: Config,
) -> ScoredCandidate | None:
    """Pick the best candidate that meets the minimum threshold."""
    threshold = config.limits.min_score_threshold

    for candidate in scored:
        if candidate.avg_score >= threshold:
            logger.info("Winner (%.1f): %s", candidate.avg_score, candidate.tweet)
            return candidate

    if scored:
        logger.info(
            "No candidates met threshold %.1f (best: %.1f)",
            threshold,
            scored[0].avg_score,
        )
    else:
        logger.info("No scored candidates")
    return None
