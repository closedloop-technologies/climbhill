"""Tests for deep-research-tavily skill."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import tavily_search


class Response:
    def __init__(self, payload=None):
        self.payload = payload or {
            "answer": "This is the synthesized answer.",
            "results": [
                {"title": "Result 1", "url": "https://example1.com", "content": "Content 1"},
                {"title": "Result 2", "url": "https://example2.com", "content": "Content 2"},
            ],
        }

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_basic_search_posts_bounded_payload(monkeypatch):
    captured = {}
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    def fake_post(url, headers, json, timeout):
        captured.update({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return Response()

    monkeypatch.setattr(tavily_search.requests, "post", fake_post)

    with patch("builtins.print") as mock_print:
        tavily_search.perform_search("test query")

    assert captured["url"] == tavily_search.API_URL
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["json"] == {
        "query": "test query",
        "search_depth": "basic",
        "max_results": 5,
        "include_answer": True,
        "include_raw_content": False,
    }
    printed = json.loads(mock_print.call_args[0][0])
    assert printed["answer"] == "This is the synthesized answer."
    assert len(printed["results"]) == 2


def test_search_with_custom_parameters(monkeypatch):
    captured = {}
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    def fake_post(url, headers, json, timeout):
        captured.update({"json": json})
        return Response()

    monkeypatch.setattr(tavily_search.requests, "post", fake_post)

    with patch("builtins.print"):
        tavily_search.perform_search("query", search_depth="advanced", max_results=2)

    assert captured["json"]["search_depth"] == "advanced"
    assert captured["json"]["max_results"] == 2


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    with pytest.raises(SystemExit):
        tavily_search.perform_search("test query")


def test_search_error_handling(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    def fake_post(*args, **kwargs):
        raise tavily_search.requests.RequestException("Search failed")

    monkeypatch.setattr(tavily_search.requests, "post", fake_post)

    with pytest.raises(SystemExit):
        tavily_search.perform_search("test query")


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("TAVILY_API_KEY"), reason="TAVILY_API_KEY not set")
def test_real_search():
    with patch("builtins.print"):
        tavily_search.perform_search("What is Python?", search_depth="basic", max_results=3)
