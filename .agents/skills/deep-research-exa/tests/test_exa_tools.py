"""Tests for deep-research-exa skill."""
import sys
import os
import pytest
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path to import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import exa_tools


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for research."""
    mock = MagicMock()
    yield mock


class TestSearch:
    """Test the search function."""

    def test_search_with_text(self):
        """Test basic search with text content."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "url": "https://example.com",
                    "title": "Test Result",
                    "text": "Sample text content",
                }
            ]
        }

        with patch.dict(os.environ, {'EXA_API_KEY': 'test_key'}):
            with patch('exa_tools.requests.post', return_value=mock_response) as mock_post:
                results = exa_tools.search("test query", num_results=1, highlights=False)

        assert len(results) == 1
        assert results[0]['url'] == "https://example.com"
        assert results[0]['title'] == "Test Result"
        assert results[0]['content'] == "Sample text content"

        mock_post.assert_called_once()

    def test_search_with_highlights(self):
        """Test search with highlights enabled."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "url": "https://example.com",
                    "title": "Test Result",
                    "text": "Full text",
                    "highlights": ["highlight1", "highlight2"],
                }
            ]
        }

        with patch.dict(os.environ, {'EXA_API_KEY': 'test_key'}):
            with patch('exa_tools.requests.post', return_value=mock_response):
                results = exa_tools.search("test query", num_results=1, highlights=True)

        assert results[0]['content'] == ["highlight1", "highlight2"]

    def test_search_multiple_results(self):
        """Test search with multiple results."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "url": f"https://example{i}.com",
                    "title": f"Result {i}",
                    "text": f"Content {i}",
                }
                for i in range(3)
            ]
        }

        with patch.dict(os.environ, {'EXA_API_KEY': 'test_key'}):
            with patch('exa_tools.requests.post', return_value=mock_response):
                results = exa_tools.search("test query", num_results=3, highlights=False)

        assert len(results) == 3
        for i in range(3):
            assert results[i]['url'] == f"https://example{i}.com"


class TestResearch:
    """Test the research function."""

    def test_research_basic(self, mock_openai_client):
        """Test basic research query."""
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "Research result content"

        mock_openai_client.chat.completions.create.return_value = mock_completion

        with patch.dict(os.environ, {'EXA_API_KEY': 'test_key'}):
            with patch('exa_tools.OpenAI', return_value=mock_openai_client):
                result = exa_tools.research("test research query")

        assert result['output'] == "Research result content"
        mock_openai_client.chat.completions.create.assert_called_once()

    def test_research_with_pro_model(self, mock_openai_client):
        """Test research with pro model."""
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "Pro research result"

        mock_openai_client.chat.completions.create.return_value = mock_completion

        with patch.dict(os.environ, {'EXA_API_KEY': 'test_key'}):
            with patch('exa_tools.OpenAI', return_value=mock_openai_client):
                result = exa_tools.research("test query", model="exa-research-pro")

        assert result['output'] == "Pro research result"


class TestFindSimilar:
    """Test the find_similar function."""

    def test_find_similar_exits_without_sdk(self):
        """find_similar is intentionally outside the benchmark path."""
        with pytest.raises(SystemExit):
            exa_tools.find_similar("https://example.com", num_results=2)


class TestGetExaClient:
    """Test the get_exa_client function."""

    def test_get_exa_client_with_key(self):
        """Test client creation with valid API key."""
        with patch.dict(os.environ, {'EXA_API_KEY': 'test_key'}):
            exa_tools.get_exa_client()

    def test_get_exa_client_without_key(self):
        """Test client creation fails without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                exa_tools.get_exa_client()


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_search_api_error(self):
        """Test search handles API errors."""
        with patch.dict(os.environ, {'EXA_API_KEY': 'test_key'}):
            with patch('exa_tools.requests.post', side_effect=exa_tools.requests.RequestException("API Error")):
                with pytest.raises(SystemExit):
                    exa_tools.search("test query")

    def test_research_api_error(self, mock_openai_client):
        """Test research handles API errors."""
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")

        with patch.dict(os.environ, {'EXA_API_KEY': 'test_key'}):
            with patch('exa_tools.OpenAI', return_value=mock_openai_client):
                with pytest.raises(SystemExit):
                    exa_tools.research("test query")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
