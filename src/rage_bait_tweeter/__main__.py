"""Entry point for rage-bait-tweeter."""

import argparse
import logging
import sys
from pathlib import Path

from .config import load_config
from .pipeline import run_pipeline

logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Autonomous rage-bait tweet generator",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to config file (default: config.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run pipeline without posting to Twitter",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config = load_config(args.config)
    logger.info(
        "Loaded config: %d feeds, models: clustering=%s generation=%s scoring=%s",
        len(config.feeds),
        config.models.clustering,
        config.models.generation,
        config.models.scoring,
    )

    run_pipeline(config, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
