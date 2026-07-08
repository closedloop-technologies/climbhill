"""Tests for deep-research-perplexity skill."""
import sys
import os
import pytest
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path to import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import ask


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for Perplexity API."""
    mock_client = MagicMock()

    # Mock chat completion response
    mock_response = Mock()
    mock_message = Mock()
    mock_message.content = "This is the research answer with citations."
    mock_choice = Mock()
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]

    mock_client.chat.completions.create.return_value = mock_response

    return mock_client


class TestAskPerplexity:
    """Test the ask_perplexity function."""

    def test_basic_query(self, mock_openai_client):
        """Test basic query to Perplexity."""
        with patch.dict(os.environ, {'PERPLEXITY_API_KEY': 'test_key'}):
            with patch('ask.OpenAI', return_value=mock_openai_client):
                with patch('builtins.print') as mock_print:
                    ask.ask_perplexity("test question")

        # Verify API was called
        mock_openai_client.chat.completions.create.assert_called_once()

        # Check answer was printed
        printed_values = [call[0][0] for call in mock_print.call_args_list]
        assert any("research answer" in str(val) for val in printed_values)

    def test_custom_model(self, mock_openai_client):
        """Test with custom model."""
        with patch.dict(os.environ, {'PERPLEXITY_API_KEY': 'test_key'}):
            with patch('ask.OpenAI', return_value=mock_openai_client):
                with patch('builtins.print'):
                    ask.ask_perplexity("test question", model="sonar-large-online")

        # Verify correct model was used
        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        assert call_kwargs['model'] == "sonar-large-online"

    def test_all_models(self, mock_openai_client):
        """Test all supported models."""
        models = ["sonar-small-online", "sonar-medium-online", "sonar-large-online"]

        for model in models:
            with patch.dict(os.environ, {'PERPLEXITY_API_KEY': 'test_key'}):
                with patch('ask.OpenAI', return_value=mock_openai_client):
                    with patch('builtins.print'):
                        ask.ask_perplexity("test question", model=model)

            call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
            assert call_kwargs['model'] == model

    def test_missing_api_key(self):
        """Test error when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                ask.ask_perplexity("test question")

    def test_system_prompt_included(self, mock_openai_client):
        """Test that system prompt is included in messages."""
        with patch.dict(os.environ, {'PERPLEXITY_API_KEY': 'test_key'}):
            with patch('ask.OpenAI', return_value=mock_openai_client):
                with patch('builtins.print'):
                    ask.ask_perplexity("test question")

        # Check messages structure
        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        messages = call_kwargs['messages']

        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert 'expert researcher' in messages[0]['content'].lower()
        assert messages[1]['role'] == 'user'
        assert messages[1]['content'] == 'test question'

    def test_api_error_handling(self, mock_openai_client):
        """Test handling of API errors."""
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")

        with patch.dict(os.environ, {'PERPLEXITY_API_KEY': 'test_key'}):
            with patch('ask.OpenAI', return_value=mock_openai_client):
                with pytest.raises(SystemExit):
                    ask.ask_perplexity("test question")


class TestClientConfiguration:
    """Test OpenAI client configuration for Perplexity."""

    def test_base_url_configuration(self, mock_openai_client):
        """Test that Perplexity base URL is configured correctly."""
        with patch.dict(os.environ, {'PERPLEXITY_API_KEY': 'test_key'}):
            with patch('ask.OpenAI') as mock_openai_cls:
                mock_openai_cls.return_value = mock_openai_client
                with patch('builtins.print'):
                    ask.ask_perplexity("test question")

        # Verify OpenAI client was initialized with Perplexity settings
        mock_openai_cls.assert_called_once()
        call_kwargs = mock_openai_cls.call_args[1]
        assert call_kwargs['api_key'] == 'test_key'
        assert call_kwargs['base_url'] == 'https://api.perplexity.ai'


class TestResponseHandling:
    """Test response handling."""

    def test_empty_response(self, mock_openai_client):
        """Test handling of empty response."""
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = ""
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        mock_openai_client.chat.completions.create.return_value = mock_response

        with patch.dict(os.environ, {'PERPLEXITY_API_KEY': 'test_key'}):
            with patch('ask.OpenAI', return_value=mock_openai_client):
                with patch('builtins.print') as mock_print:
                    ask.ask_perplexity("test question")

        # Should still print (even if empty)
        assert mock_print.called

    def test_long_response(self, mock_openai_client):
        """Test handling of long research responses."""
        long_answer = "This is a very long answer. " * 100

        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = long_answer
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        mock_openai_client.chat.completions.create.return_value = mock_response

        with patch.dict(os.environ, {'PERPLEXITY_API_KEY': 'test_key'}):
            with patch('ask.OpenAI', return_value=mock_openai_client):
                with patch('builtins.print') as mock_print:
                    ask.ask_perplexity("test question")

        # Check full answer was printed
        printed = str(mock_print.call_args_list[0][0][0])
        assert len(printed) > 1000


class TestIntegration:
    """Integration tests (require real API key)."""

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv('PERPLEXITY_API_KEY'),
        reason="PERPLEXITY_API_KEY not set"
    )
    def test_real_query(self):
        """Test with real API (integration test)."""
        with patch('builtins.print'):
            ask.ask_perplexity("What is 2+2?", model="sonar-small-online")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
