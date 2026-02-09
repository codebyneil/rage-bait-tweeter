"""Shared data types for the pipeline."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Headline:
    title: str
    url: str
    source: str
    published: datetime | None = None
    summary: str = ""


@dataclass
class Cluster:
    id: str
    summary: str
    headlines: list[Headline]
    already_covered: bool = False


@dataclass
class Candidate:
    tweet: str
    cluster_id: str
    cluster_summary: str


@dataclass
class ScoredCandidate:
    tweet: str
    cluster_id: str
    cluster_summary: str
    scores: dict[str, float]
    avg_score: float
