import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import you_research


class Response:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "output": {
                "content": "Answer with citation [[1]].",
                "sources": [{"title": "Example", "url": "https://example.com"}],
            }
        }


def test_run_research_posts_input_and_lite_effort(monkeypatch):
    captured = {}
    monkeypatch.setenv("YOU_API_KEY", "test-key")

    def fake_post(url, headers, json, timeout):
        captured.update({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return Response()

    monkeypatch.setattr(you_research.requests, "post", fake_post)

    payload = you_research.run_research("Prompt", research_effort="lite", timeout=10)

    assert payload["output"]["content"].startswith("Answer")
    assert captured["url"] == you_research.API_URL
    assert captured["headers"]["X-API-Key"] == "test-key"
    assert captured["json"] == {"input": "Prompt", "research_effort": "lite"}
    assert captured["timeout"] == 10


def test_run_finance_research_uses_finance_endpoint(monkeypatch):
    captured = {}
    monkeypatch.setenv("YOU_API_KEY", "test-key")

    def fake_post(url, headers, json, timeout):
        captured.update({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return Response()

    monkeypatch.setattr(you_research.requests, "post", fake_post)

    you_research.run_research("Compare margins", research_effort="deep", timeout=10, api="finance")

    assert captured["url"] == you_research.FINANCE_API_URL
    assert captured["json"] == {"input": "Compare margins", "research_effort": "deep"}


def test_render_markdown_includes_sources():
    markdown = you_research.render_markdown(Response().json())

    assert "# You.com Research Result" in markdown
    assert "[Example](https://example.com)" in markdown
