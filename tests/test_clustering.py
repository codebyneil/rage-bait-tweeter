"""Tests for headline clustering."""

import json
from datetime import datetime, timezone
from unittest.mock import patch

from rage_bait_tweeter.clustering import _parse_clusters, filter_covered
from rage_bait_tweeter.types import Cluster, Headline


def _make_headlines(n: int) -> list[Headline]:
    return [
        Headline(
            title=f"Headline {i}",
            url=f"https://example.com/{i}",
            source="tech",
            published=datetime.now(timezone.utc),
        )
        for i in range(n)
    ]


class TestParseClusters:
    def test_basic_parsing(self):
        headlines = _make_headlines(5)
        response = json.dumps({
            "clusters": [
                {
                    "id": "test-story",
                    "summary": "A test story about stuff",
                    "headline_indices": [0, 2, 4],
                    "already_covered": False,
                },
                {
                    "id": "other-story",
                    "summary": "Another story",
                    "headline_indices": [1, 3],
                    "already_covered": True,
                },
            ]
        })

        clusters = _parse_clusters(response, headlines)
        assert len(clusters) == 2
        assert clusters[0].id == "test-story"
        assert len(clusters[0].headlines) == 3
        assert clusters[0].already_covered is False
        assert clusters[1].id == "other-story"
        assert len(clusters[1].headlines) == 2
        assert clusters[1].already_covered is True

    def test_out_of_range_indices(self):
        headlines = _make_headlines(3)
        response = json.dumps({
            "clusters": [
                {
                    "id": "test",
                    "summary": "Test",
                    "headline_indices": [0, 1, 99],
                    "already_covered": False,
                },
            ]
        })

        clusters = _parse_clusters(response, headlines)
        assert len(clusters[0].headlines) == 2  # 99 is skipped

    def test_invalid_json(self):
        clusters = _parse_clusters("not json", [])
        assert clusters == []

    def test_empty_clusters(self):
        clusters = _parse_clusters('{"clusters": []}', [])
        assert clusters == []


class TestFilterCovered:
    def test_filters_covered(self):
        clusters = [
            Cluster(id="a", summary="A", headlines=[], already_covered=False),
            Cluster(id="b", summary="B", headlines=[], already_covered=True),
            Cluster(id="c", summary="C", headlines=[], already_covered=False),
        ]
        result = filter_covered(clusters)
        assert len(result) == 2
        assert [c.id for c in result] == ["a", "c"]

    def test_all_covered(self):
        clusters = [
            Cluster(id="a", summary="A", headlines=[], already_covered=True),
        ]
        assert filter_covered(clusters) == []

    def test_none_covered(self):
        clusters = [
            Cluster(id="a", summary="A", headlines=[], already_covered=False),
        ]
        result = filter_covered(clusters)
        assert len(result) == 1
