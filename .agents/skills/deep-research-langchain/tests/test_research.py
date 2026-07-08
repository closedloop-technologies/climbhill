"""Tests for deep-research-langchain skill."""
import sys
import os
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch

# Add parent directory to path to import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import research


@pytest.fixture
def mock_langgraph_client():
    """Mock LangGraph client."""
    mock_client = MagicMock()

    # Mock threads.create
    mock_client.threads.create = AsyncMock(return_value={"thread_id": "test_thread_123"})

    # Mock runs.stream
    async def mock_stream(*args, **kwargs):
        # Simulate streaming chunks
        mock_msg = Mock()
        mock_msg.content = "# Research Report\n\nThis is the final research result."

        chunk1 = Mock()
        chunk1.data = {
            "agent": {
                "messages": [mock_msg]
            }
        }

        yield chunk1

    mock_client.runs.stream = mock_stream

    return mock_client


class TestRunResearch:
    """Test the run_research function."""

    @pytest.mark.asyncio
    async def test_basic_research(self, mock_langgraph_client):
        """Test basic research execution."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test_key',
            'TAVILY_API_KEY': 'test_key'
        }):
            with patch('research.get_client', return_value=mock_langgraph_client):
                with patch('builtins.print') as mock_print:
                    await research.run_research("test query")

        # Verify client methods were called
        mock_langgraph_client.threads.create.assert_called_once()

        # Check that the report was printed
        printed_values = [call[0][0] for call in mock_print.call_args_list]
        assert any("Research Report" in str(val) for val in printed_values)

    @pytest.mark.asyncio
    async def test_custom_max_iterations(self, mock_langgraph_client):
        """Test research with custom max iterations."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test_key',
            'TAVILY_API_KEY': 'test_key'
        }):
            with patch('research.get_client', return_value=mock_langgraph_client):
                with patch('builtins.print'):
                    await research.run_research("test query", max_iterations=5)

        mock_langgraph_client.threads.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_output_to_file(self, mock_langgraph_client, tmp_path):
        """Test saving report to file."""
        output_file = tmp_path / "report.md"

        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test_key',
            'TAVILY_API_KEY': 'test_key'
        }):
            with patch('research.get_client', return_value=mock_langgraph_client):
                with patch('builtins.print'):
                    await research.run_research(
                        "test query",
                        output_file=str(output_file)
                    )

        # Verify file was created
        assert output_file.exists()
        content = output_file.read_text()
        assert "Research Report" in content

    @pytest.mark.asyncio
    async def test_missing_openai_key(self):
        """Test error when OPENAI_API_KEY is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                await research.run_research("test query")

    @pytest.mark.asyncio
    async def test_missing_tavily_key_warning(self, mock_langgraph_client):
        """Test warning when TAVILY_API_KEY is missing."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            with patch('research.get_client', return_value=mock_langgraph_client):
                with patch('builtins.print') as mock_print:
                    await research.run_research("test query")

        # Check that warning was printed
        stderr_calls = [
            call for call in mock_print.call_args_list
            if len(call[1]) > 0 and call[1].get('file') == sys.stderr
        ]
        warning_found = any(
            'TAVILY_API_KEY' in str(call[0][0])
            for call in stderr_calls
        )
        assert warning_found

    @pytest.mark.asyncio
    async def test_connection_error(self):
        """Test handling of connection error to LangGraph server."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            with patch('research.get_client', side_effect=ConnectionError("Cannot connect")):
                with pytest.raises(SystemExit):
                    await research.run_research("test query")

    @pytest.mark.asyncio
    async def test_no_messages_in_final_state(self, mock_langgraph_client):
        """Test error handling when no messages received."""
        # Mock client with empty response
        async def mock_empty_stream(*args, **kwargs):
            chunk = Mock()
            chunk.data = {"agent": {"messages": []}}
            yield chunk

        mock_langgraph_client.runs.stream = mock_empty_stream

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            with patch('research.get_client', return_value=mock_langgraph_client):
                with pytest.raises(SystemExit):
                    await research.run_research("test query")

    @pytest.mark.asyncio
    async def test_general_exception_handling(self, mock_langgraph_client):
        """Test general exception handling."""
        mock_langgraph_client.threads.create.side_effect = Exception("Unexpected error")

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            with patch('research.get_client', return_value=mock_langgraph_client):
                with pytest.raises(SystemExit):
                    await research.run_research("test query")


class TestStreamProcessing:
    """Test streaming response processing."""

    @pytest.mark.asyncio
    async def test_stream_with_multiple_messages(self, mock_langgraph_client):
        """Test processing stream with multiple message chunks."""
        async def mock_multi_stream(*args, **kwargs):
            # First chunk
            msg1 = Mock()
            msg1.content = "Intermediate result"
            chunk1 = Mock()
            chunk1.data = {"step1": {"messages": [msg1]}}
            yield chunk1

            # Second chunk with final result
            msg2 = Mock()
            msg2.content = "Final research report"
            chunk2 = Mock()
            chunk2.data = {"final": {"messages": [msg2]}}
            yield chunk2

        mock_langgraph_client.runs.stream = mock_multi_stream

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            with patch('research.get_client', return_value=mock_langgraph_client):
                with patch('builtins.print') as mock_print:
                    await research.run_research("test query")

        # Should print final message
        printed_values = [call[0][0] for call in mock_print.call_args_list]
        assert any("Final research report" in str(val) for val in printed_values)


class TestEnvironmentVariables:
    """Test environment variable handling."""

    @pytest.mark.asyncio
    async def test_anthropic_key_alternative(self, mock_langgraph_client):
        """Test that ANTHROPIC_API_KEY works as alternative to OPENAI_API_KEY."""
        with patch.dict(os.environ, {
            'ANTHROPIC_API_KEY': 'test_key',
            'TAVILY_API_KEY': 'test_key'
        }):
            with patch('research.get_client', return_value=mock_langgraph_client):
                with patch('builtins.print'):
                    # Should not raise SystemExit
                    await research.run_research("test query")

        mock_langgraph_client.threads.create.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
