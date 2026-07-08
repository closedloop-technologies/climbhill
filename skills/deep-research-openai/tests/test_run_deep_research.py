"""Tests for deep-research-openai skill."""
import sys
import os
import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open

# Add parent directory to path to import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import run_deep_research


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    mock_client = MagicMock()

    # Mock streaming response
    class MockEvent:
        def __init__(self, event_type, content=None, error=None):
            self.type = event_type
            self.delta = content
            self.response = None
            self.error = error

    class MockStream:
        def __init__(self, events):
            self._events = events

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def __iter__(self):
            return iter(self._events)

    # Create mock events
    events = [
        MockEvent("response.output_text.delta", "Part 1 of report"),
        MockEvent("response.output_text.delta", " Part 2 of report"),
        MockEvent("response.completed"),
    ]
    events[-1].response = {"status": "completed"}

    mock_stream = MockStream(events)
    mock_client.responses.stream.return_value = mock_stream

    return mock_client


class TestValidateApiKey:
    """Test the validate_api_key function."""

    def test_validate_with_key(self):
        """Test validation passes with API key."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            # Should not raise
            run_deep_research.validate_api_key()

    def test_validate_without_key(self):
        """Test validation fails without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                run_deep_research.validate_api_key()


class TestRunDeepResearch:
    """Test the run_deep_research function."""

    def test_basic_research(self, mock_openai_client):
        """Test basic deep research execution."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            with patch('run_deep_research.OpenAI', return_value=mock_openai_client):
                with patch('builtins.print') as mock_print:
                    run_deep_research.run_deep_research("test prompt")

        # Verify the API was called
        mock_openai_client.responses.stream.assert_called_once()

        # Check output was printed
        printed_values = [call[0] for call in mock_print.call_args_list if call[0]]
        assert any("Part 1 of report" in str(val) for val in printed_values)

    def test_custom_model(self, mock_openai_client):
        """Test with custom model."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            with patch('run_deep_research.OpenAI', return_value=mock_openai_client):
                with patch('builtins.print'):
                    run_deep_research.run_deep_research(
                        "test prompt",
                        model="o3-deep-research"
                    )

        # Verify correct model was used
        call_kwargs = mock_openai_client.responses.stream.call_args[1]
        assert call_kwargs['model'] == "o3-deep-research"

    def test_effort_levels(self, mock_openai_client):
        """Test different effort levels."""
        for effort in ["low", "medium", "high"]:
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
                with patch('run_deep_research.OpenAI', return_value=mock_openai_client):
                    with patch('builtins.print'):
                        run_deep_research.run_deep_research(
                            "test prompt",
                            effort=effort
                        )

            # Verify effort was passed
            call_kwargs = mock_openai_client.responses.stream.call_args[1]
            assert call_kwargs['reasoning']['effort'] == effort

    def test_output_to_file(self, mock_openai_client, tmp_path):
        """Test saving report to file."""
        output_file = tmp_path / "report.txt"

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            with patch('run_deep_research.OpenAI', return_value=mock_openai_client):
                with patch('builtins.print'):
                    run_deep_research.run_deep_research(
                        "test prompt",
                        output_path=str(output_file)
                    )

        # Verify file was created
        assert output_file.exists()
        content = output_file.read_text()
        assert "Part 1 of report" in content
        assert "Part 2 of report" in content

    def test_json_output(self, mock_openai_client):
        """Test JSON output mode."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            with patch('run_deep_research.OpenAI', return_value=mock_openai_client):
                with patch('builtins.print') as mock_print:
                    run_deep_research.run_deep_research(
                        "test prompt",
                        emit_json=True
                    )

        # Should output JSON
        printed_values = [str(call[0]) for call in mock_print.call_args_list if call[0]]
        assert any('status' in val or '{' in val for val in printed_values)

    def test_json_output_to_file(self, mock_openai_client, tmp_path):
        """Test JSON output to file."""
        output_file = tmp_path / "report.json"

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            with patch('run_deep_research.OpenAI', return_value=mock_openai_client):
                with patch('builtins.print'):
                    run_deep_research.run_deep_research(
                        "test prompt",
                        emit_json=True,
                        output_path=str(output_file)
                    )

        # Verify JSON file was created
        assert output_file.exists()
        import json
        content = json.loads(output_file.read_text())
        assert 'status' in content


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_api_status_error(self, mock_openai_client):
        """Test handling of API status errors."""
        from openai._exceptions import APIStatusError

        mock_response = Mock()
        mock_response.status_code = 429
        error = APIStatusError(
            "Rate limit exceeded",
            response=mock_response,
            body={}
        )
        mock_openai_client.responses.stream.side_effect = error

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            with patch('run_deep_research.OpenAI', return_value=mock_openai_client):
                with pytest.raises(SystemExit):
                    run_deep_research.run_deep_research("test prompt")

    def test_general_exception(self, mock_openai_client):
        """Test handling of general exceptions."""
        mock_openai_client.responses.stream.side_effect = Exception("Unexpected error")

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            with patch('run_deep_research.OpenAI', return_value=mock_openai_client):
                with pytest.raises(SystemExit):
                    run_deep_research.run_deep_research("test prompt")

    def test_response_error_event(self, mock_openai_client):
        """Test handling of response error events."""
        class MockErrorEvent:
            def __init__(self):
                self.type = "response.error"
                self.error = "Processing failed"

        class MockErrorStream:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def __iter__(self):
                return iter([MockErrorEvent()])

        mock_openai_client.responses.stream.return_value = MockErrorStream()

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            with patch('run_deep_research.OpenAI', return_value=mock_openai_client):
                with pytest.raises(SystemExit):
                    run_deep_research.run_deep_research("test prompt")


class TestStreamProcessing:
    """Test streaming response processing."""

    def test_multiple_chunks(self, mock_openai_client):
        """Test processing multiple text chunks."""
        class MockEvent:
            def __init__(self, event_type, content=None):
                self.type = event_type
                self.delta = content
                self.response = None

        class MockStream:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def __iter__(self):
                events = [
                    MockEvent("response.output_text.delta", "Chunk 1 "),
                    MockEvent("response.output_text.delta", "Chunk 2 "),
                    MockEvent("response.output_text.delta", "Chunk 3"),
                    MockEvent("response.completed"),
                ]
                events[-1].response = {"status": "ok"}
                return iter(events)

        mock_openai_client.responses.stream.return_value = MockStream()

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            with patch('run_deep_research.OpenAI', return_value=mock_openai_client):
                with patch('builtins.print') as mock_print:
                    run_deep_research.run_deep_research("test prompt")

        # All chunks should be printed
        printed = ''.join([str(call[0][0]) for call in mock_print.call_args_list if call[0]])
        assert "Chunk 1" in printed
        assert "Chunk 2" in printed
        assert "Chunk 3" in printed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
