import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import gemini_research


class Response:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "output_text": "Grounded answer.",
            "steps": [
                {
                    "type": "model_output",
                    "content": [
                        {
                            "type": "text",
                            "text": "Grounded answer.",
                            "annotations": [
                                {
                                    "type": "url_citation",
                                    "title": "Example",
                                    "url": "https://example.com",
                                }
                            ],
                        }
                    ],
                }
            ],
        }


def test_grounded_research_posts_interactions_payload(monkeypatch):
    captured = {}
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    def fake_post(url, headers, json, timeout):
        captured.update({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return Response()

    monkeypatch.setattr(gemini_research.requests, "post", fake_post)

    payload = gemini_research.grounded_research("Prompt", model="gemini-3.5-flash", timeout=10)

    assert payload["output_text"] == "Grounded answer."
    assert captured["url"] == gemini_research.INTERACTIONS_URL
    assert captured["headers"]["x-goog-api-key"] == "test-key"
    assert captured["json"]["tools"] == [{"type": "google_search"}]
    assert captured["timeout"] == 10


def test_start_deep_research_uses_deep_research_agent_config(monkeypatch):
    captured = {}
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    def fake_post(url, headers, json, timeout):
        captured.update({"json": json})
        return Response()

    monkeypatch.setattr(gemini_research.requests, "post", fake_post)

    gemini_research.start_deep_research("Prompt", agent="deep-research-preview-04-2026")

    assert captured["json"]["background"] is True
    assert captured["json"]["agent_config"]["type"] == "deep-research"


def test_render_markdown_includes_citations():
    markdown = gemini_research.render_markdown(Response().json(), "grounded")

    assert "# Gemini grounded Result" in markdown
    assert "[Example](https://example.com)" in markdown
