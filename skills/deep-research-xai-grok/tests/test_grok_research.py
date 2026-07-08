"""Tests for deep-research-xai-grok skill."""
import sys
import os
import pytest
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path to import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import grok_research


@pytest.fixture
def mock_xai_client():
    """Mock xAI Client."""
    mock_client = MagicMock()
    return mock_client


@pytest.fixture
def mock_chat():
    """Mock chat object."""
    mock = MagicMock()

    # Mock streaming chunks
    class MockChunk:
        def __init__(self, content, is_thinking=False, tool_calls=None, citations=None):
            self.content = content
            self.is_thinking = is_thinking
            self.tool_calls = tool_calls or []
            self.citations = citations or []

    mock_chunks = [
        MockChunk("Final answer content", is_thinking=False, citations=[
            Mock(title="Source 1", url="https://example1.com"),
            Mock(title="Source 2", url="https://example2.com")
        ])
    ]

    def mock_stream():
        return iter(mock_chunks)

    mock.stream.return_value = mock_stream()
    mock.append = Mock()

    return mock


class TestGrokResearch:
    """Test the grok_research function."""

    def test_basic_research(self, mock_xai_client, mock_chat):
        """Test basic research query."""
        mock_xai_client.chat.create.return_value = mock_chat

        with patch.dict(os.environ, {'XAI_API_KEY': 'test_key'}):
            with patch('grok_research.Client', return_value=mock_xai_client):
                with patch('grok_research.user') as mock_user:
                    with patch('builtins.print') as mock_print:
                        grok_research.grok_research("test query")

        # Verify client was created
        mock_xai_client.chat.create.assert_called_once()

        # Verify user message was appended
        mock_chat.append.assert_called_once()

        # Check output was printed
        printed_values = [call[0][0] for call in mock_print.call_args_list if call[0]]
        assert any("Final answer" in str(val) for val in printed_values)

    def test_custom_model(self, mock_xai_client, mock_chat):
        """Test research with custom model."""
        mock_xai_client.chat.create.return_value = mock_chat

        with patch.dict(os.environ, {'XAI_API_KEY': 'test_key'}):
            with patch('grok_research.Client', return_value=mock_xai_client):
                with patch('grok_research.user'):
                    with patch('builtins.print'):
                        grok_research.grok_research(
                            "test query",
                            model="grok-4"
                        )

        # Verify correct model was used
        call_kwargs = mock_xai_client.chat.create.call_args[1]
        assert call_kwargs['model'] == "grok-4"

    def test_web_search_enabled(self, mock_xai_client, mock_chat):
        """Test research with web search enabled."""
        mock_xai_client.chat.create.return_value = mock_chat

        with patch.dict(os.environ, {'XAI_API_KEY': 'test_key'}):
            with patch('grok_research.Client', return_value=mock_xai_client):
                with patch('grok_research.user'):
                    with patch('grok_research.web_search') as mock_web_search:
                        with patch('builtins.print'):
                            grok_research.grok_research(
                                "test query",
                                enable_web_search=True
                            )

        # Verify web_search tool was called
        mock_web_search.assert_called_once()

        # Verify tools were passed to create
        call_kwargs = mock_xai_client.chat.create.call_args[1]
        assert 'tools' in call_kwargs
        assert len(call_kwargs['tools']) > 0

    def test_x_search_enabled(self, mock_xai_client, mock_chat):
        """Test research with X search enabled."""
        mock_xai_client.chat.create.return_value = mock_chat

        with patch.dict(os.environ, {'XAI_API_KEY': 'test_key'}):
            with patch('grok_research.Client', return_value=mock_xai_client):
                with patch('grok_research.user'):
                    with patch('grok_research.x_search') as mock_x_search:
                        with patch('builtins.print'):
                            grok_research.grok_research(
                                "test query",
                                enable_x_search=True
                            )

        # Verify x_search tool was called
        mock_x_search.assert_called_once()

    def test_both_searches_enabled(self, mock_xai_client, mock_chat):
        """Test research with both web and X search enabled."""
        mock_xai_client.chat.create.return_value = mock_chat

        with patch.dict(os.environ, {'XAI_API_KEY': 'test_key'}):
            with patch('grok_research.Client', return_value=mock_xai_client):
                with patch('grok_research.user'):
                    with patch('grok_research.web_search') as mock_web_search:
                        with patch('grok_research.x_search') as mock_x_search:
                            with patch('builtins.print'):
                                grok_research.grok_research(
                                    "test query",
                                    enable_web_search=True,
                                    enable_x_search=True
                                )

        # Verify both tools were called
        mock_web_search.assert_called_once()
        mock_x_search.assert_called_once()

        # Verify tools list has 2 items
        call_kwargs = mock_xai_client.chat.create.call_args[1]
        assert len(call_kwargs['tools']) == 2

    def test_no_tools_warning(self, mock_xai_client, mock_chat):
        """Test warning when no tools are enabled."""
        mock_xai_client.chat.create.return_value = mock_chat

        with patch.dict(os.environ, {'XAI_API_KEY': 'test_key'}):
            with patch('grok_research.Client', return_value=mock_xai_client):
                with patch('grok_research.user'):
                    with patch('builtins.print') as mock_print:
                        grok_research.grok_research("test query")

        # Check for warning in stderr
        stderr_calls = [
            call for call in mock_print.call_args_list
            if len(call[1]) > 0 and call[1].get('file') == sys.stderr
        ]
        warning_found = any(
            'No tools enabled' in str(call[0][0])
            for call in stderr_calls
        )
        assert warning_found

    def test_missing_api_key(self):
        """Test error when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                grok_research.grok_research("test query")

    def test_api_error_handling(self, mock_xai_client):
        """Test handling of API errors."""
        mock_xai_client.chat.create.side_effect = Exception("API error")

        with patch.dict(os.environ, {'XAI_API_KEY': 'test_key'}):
            with patch('grok_research.Client', return_value=mock_xai_client):
                with pytest.raises(SystemExit):
                    grok_research.grok_research("test query")


class TestStreamProcessing:
    """Test streaming response processing."""

    def test_thinking_chunks(self, mock_xai_client):
        """Test processing of thinking chunks."""
        mock_chat = MagicMock()

        class MockChunk:
            def __init__(self, content, is_thinking):
                self.content = content
                self.is_thinking = is_thinking
                self.tool_calls = []
                self.citations = []

        chunks = [
            MockChunk("Thinking step 1", is_thinking=True),
            MockChunk("Thinking step 2", is_thinking=True),
            MockChunk("Final answer", is_thinking=False)
        ]

        mock_chat.stream.return_value = iter(chunks)
        mock_chat.append = Mock()
        mock_xai_client.chat.create.return_value = mock_chat

        with patch.dict(os.environ, {'XAI_API_KEY': 'test_key'}):
            with patch('grok_research.Client', return_value=mock_xai_client):
                with patch('grok_research.user'):
                    with patch('builtins.print') as mock_print:
                        grok_research.grok_research("test query")

        # Check that thinking chunks were printed to stderr
        stderr_calls = [
            call for call in mock_print.call_args_list
            if len(call[1]) > 0 and call[1].get('file') == sys.stderr
        ]
        thinking_found = any(
            'Thinking' in str(call[0][0])
            for call in stderr_calls
        )
        assert thinking_found

    def test_tool_calls_in_stream(self, mock_xai_client):
        """Test processing of tool calls in stream."""
        mock_chat = MagicMock()

        class MockToolCall:
            def __init__(self, call_type, arguments):
                self.type = call_type
                self.arguments = arguments

        class MockChunk:
            def __init__(self, content, tool_calls=None):
                self.content = content
                self.is_thinking = False
                self.tool_calls = tool_calls or []
                self.citations = []

        chunks = [
            MockChunk("", tool_calls=[
                MockToolCall("web_search", {"query": "test"})
            ]),
            MockChunk("Final answer")
        ]

        mock_chat.stream.return_value = iter(chunks)
        mock_chat.append = Mock()
        mock_xai_client.chat.create.return_value = mock_chat

        with patch.dict(os.environ, {'XAI_API_KEY': 'test_key'}):
            with patch('grok_research.Client', return_value=mock_xai_client):
                with patch('grok_research.user'):
                    with patch('builtins.print') as mock_print:
                        grok_research.grok_research("test query")

        # Check that tool calls were printed to stderr
        stderr_calls = [
            call for call in mock_print.call_args_list
            if len(call[1]) > 0 and call[1].get('file') == sys.stderr
        ]
        tool_call_found = any(
            'Tool Call' in str(call[0][0])
            for call in stderr_calls
        )
        assert tool_call_found

    def test_citations_in_response(self, mock_xai_client):
        """Test processing of citations."""
        mock_chat = MagicMock()

        class MockChunk:
            def __init__(self):
                self.content = "Answer with citations"
                self.is_thinking = False
                self.tool_calls = []
                self.citations = [
                    Mock(title="Source 1", url="https://example1.com"),
                    Mock(title="Source 2", url="https://example2.com")
                ]

        mock_chat.stream.return_value = iter([MockChunk()])
        mock_chat.append = Mock()
        mock_xai_client.chat.create.return_value = mock_chat

        with patch.dict(os.environ, {'XAI_API_KEY': 'test_key'}):
            with patch('grok_research.Client', return_value=mock_xai_client):
                with patch('grok_research.user'):
                    with patch('builtins.print') as mock_print:
                        grok_research.grok_research("test query")

        # Check that citations were printed
        printed = ''.join([str(call) for call in mock_print.call_args_list])
        assert "Citations" in printed
        assert "Source 1" in printed
        assert "https://example1.com" in printed

    def test_empty_response(self, mock_xai_client):
        """Test handling of empty response."""
        mock_chat = MagicMock()

        class MockChunk:
            def __init__(self):
                self.content = None
                self.is_thinking = False
                self.tool_calls = []
                self.citations = []

        mock_chat.stream.return_value = iter([MockChunk()])
        mock_chat.append = Mock()
        mock_xai_client.chat.create.return_value = mock_chat

        with patch.dict(os.environ, {'XAI_API_KEY': 'test_key'}):
            with patch('grok_research.Client', return_value=mock_xai_client):
                with patch('grok_research.user'):
                    with patch('builtins.print') as mock_print:
                        grok_research.grok_research("test query")

        # Should handle gracefully
        printed = ''.join([str(call) for call in mock_print.call_args_list])
        assert "No final response" in printed


class TestClientConfiguration:
    """Test xAI client configuration."""

    def test_client_initialized_with_api_key(self, mock_xai_client, mock_chat):
        """Test that client is initialized with correct API key."""
        mock_xai_client.chat.create.return_value = mock_chat

        with patch.dict(os.environ, {'XAI_API_KEY': 'my_test_key'}):
            with patch('grok_research.Client') as mock_client_cls:
                mock_client_cls.return_value = mock_xai_client
                with patch('grok_research.user'):
                    with patch('builtins.print'):
                        grok_research.grok_research("test query")

        # Verify client was initialized with API key
        mock_client_cls.assert_called_once_with(api_key='my_test_key')


class TestModelOptions:
    """Test different model options."""

    @pytest.mark.parametrize("model", [
        "grok-4.1-fast-reasoning",
        "grok-4"
    ])
    def test_different_models(self, mock_xai_client, mock_chat, model):
        """Test different Grok models."""
        mock_xai_client.chat.create.return_value = mock_chat

        with patch.dict(os.environ, {'XAI_API_KEY': 'test_key'}):
            with patch('grok_research.Client', return_value=mock_xai_client):
                with patch('grok_research.user'):
                    with patch('builtins.print'):
                        grok_research.grok_research("test query", model=model)

        call_kwargs = mock_xai_client.chat.create.call_args[1]
        assert call_kwargs['model'] == model


class TestIntegration:
    """Integration tests."""

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv('XAI_API_KEY'),
        reason="XAI_API_KEY not set"
    )
    def test_real_grok_query(self):
        """Test with real xAI API (integration test)."""
        with patch('builtins.print'):
            grok_research.grok_research(
                "What is 2+2?",
                model="grok-4.1-fast-reasoning",
                enable_web_search=False
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
