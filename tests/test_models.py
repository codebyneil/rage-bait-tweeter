"""Tests for model utilities."""

import json

import pytest

from rage_bait_tweeter.models import _get_provider, extract_json


class TestGetProvider:
    def test_openai_gpt(self):
        assert _get_provider("gpt-4o") == "openai"
        assert _get_provider("gpt-4o-mini") == "openai"

    def test_openai_o_series(self):
        assert _get_provider("o1") == "openai"
        assert _get_provider("o3-mini") == "openai"

    def test_anthropic(self):
        assert _get_provider("claude-sonnet-4-5-20250929") == "anthropic"
        assert _get_provider("claude-haiku-3-5") == "anthropic"

    def test_google(self):
        assert _get_provider("gemini-2.0-flash") == "google"
        assert _get_provider("gemini-2.0-pro") == "google"

    def test_unknown(self):
        with pytest.raises(ValueError, match="Unknown model provider"):
            _get_provider("llama-3")


class TestExtractJson:
    def test_plain_json(self):
        data = {"key": "value"}
        result = extract_json(json.dumps(data))
        assert result == data

    def test_json_with_markdown_fences(self):
        text = '```json\n{"key": "value"}\n```'
        result = extract_json(text)
        assert result == {"key": "value"}

    def test_json_with_plain_fences(self):
        text = '```\n{"key": "value"}\n```'
        result = extract_json(text)
        assert result == {"key": "value"}

    def test_json_with_surrounding_text(self):
        text = 'Here is the JSON:\n```json\n{"clusters": [1, 2]}\n```\nDone!'
        result = extract_json(text)
        assert result == {"clusters": [1, 2]}

    def test_nested_json(self):
        data = {
            "clusters": [
                {"id": "test", "summary": "A test", "headline_indices": [0, 1]},
            ]
        }
        text = f"```json\n{json.dumps(data, indent=2)}\n```"
        result = extract_json(text)
        assert result == data

    def test_invalid_json(self):
        with pytest.raises(json.JSONDecodeError):
            extract_json("not json at all")

    def test_whitespace_padding(self):
        result = extract_json('  \n  {"key": "value"}  \n  ')
        assert result == {"key": "value"}
