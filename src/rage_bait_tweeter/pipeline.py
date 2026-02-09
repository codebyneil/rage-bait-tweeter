"""Main pipeline orchestration."""

import logging

from .aggregator import fetch_headlines, fetch_recent_tweets
from .clustering import cluster_headlines, filter_covered
from .config import Config
from .gate import check_daily_limit, is_peak_hours
from .generator import generate_candidates
from .notifier import notify_error, notify_posted, notify_skip
from .scorer import pick_winner, score_candidates
from .twitter import post_tweet

logger = logging.getLogger(__name__)


def run_pipeline(config: Config, *, dry_run: bool = False) -> None:
    """Execute the rage-bait pipeline.

    Stages:
    1. Peak hours gate — exit early if outside posting windows
    2. Aggregate — poll RSS feeds + fetch recent tweets
    3. Daily limit check — exit if we've hit max tweets today
    4. Cluster — group headlines by story/event
    5. Filter — drop clusters matching recent tweets
    6. Generate — create rage-bait candidates per cluster
    7. Score — multi-model panel rates candidates
    8. Post — tweet the winner
    9. Notify — mirror to Slack
    """
    logger.info("Starting rage-bait pipeline (dry_run=%s)", dry_run)

    try:
        _run(config, dry_run=dry_run)
    except Exception as e:
        logger.exception("Pipeline failed")
        notify_error(str(e), config)


def _run(config: Config, *, dry_run: bool) -> None:
    # Stage 1: Peak hours gate
    if not dry_run and not is_peak_hours(config):
        notify_skip("Outside peak hours", config)
        return

    # Stage 2: Aggregate
    headlines = fetch_headlines(config)
    recent_tweets = fetch_recent_tweets(config)

    if not headlines:
        logger.info("No headlines found, exiting pipeline")
        notify_skip("No headlines in feed window", config)
        return

    # Stage 3: Daily limit check
    if not dry_run and not check_daily_limit(recent_tweets, config):
        logger.info("Daily tweet limit reached, exiting pipeline")
        notify_skip("Daily tweet limit reached", config)
        return

    # Stage 4: Cluster
    clusters = cluster_headlines(headlines, recent_tweets, config)
    logger.info("Found %d clusters", len(clusters))

    if not clusters:
        logger.info("No clusters found, exiting pipeline")
        return

    # Stage 5: Filter
    clusters = filter_covered(clusters)

    if not clusters:
        logger.info("All clusters already covered, exiting pipeline")
        notify_skip("All stories already covered", config)
        return

    logger.info("%d clusters after filtering", len(clusters))

    # Stage 6: Generate
    candidates = generate_candidates(clusters, config)

    if not candidates:
        logger.info("No candidates generated, exiting pipeline")
        return

    # Stage 7: Score
    scored = score_candidates(candidates, config)
    winner = pick_winner(scored, config)

    if not winner:
        notify_skip("No candidates met score threshold", config)
        return

    # Stage 8: Post
    tweet_url = None
    if dry_run:
        logger.info("DRY RUN — would post: %s", winner.tweet)
    else:
        tweet_url = post_tweet(winner.tweet, config)
        if not tweet_url:
            logger.error("Failed to post tweet")
            notify_error("Failed to post winning tweet", config)
            return

    # Stage 9: Notify
    notify_posted(winner, tweet_url, config)

    logger.info("Pipeline complete")
