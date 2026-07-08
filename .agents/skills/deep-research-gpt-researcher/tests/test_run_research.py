"""Tests for deep-research-gpt-researcher skill."""
import sys
import os
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch

# Add parent directory to path to import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import run_research


@pytest.fixture
def mock_gpt_researcher():
    """Mock GPTResearcher class."""
    mock = MagicMock()
    mock.conduct_research = AsyncMock()
    mock.write_report = AsyncMock(return_value="# Research Report\n\nThis is a test report.")
    return mock


class TestGenerateResearchReport:
    """Test the generate_research_report function."""

    @pytest.mark.asyncio
    async def test_basic_research_report(self, mock_gpt_researcher):
        """Test generating a basic research report."""
        with patch.dict(os.environ, {'TAVILY_API_KEY': 'test_key'}):
            with patch('run_research.GPTResearcher', return_value=mock_gpt_researcher):
                with patch('builtins.print') as mock_print:
                    await run_research.generate_research_report("test query")

        mock_gpt_researcher.conduct_research.assert_called_once()
        mock_gpt_researcher.write_report.assert_called_once()

        # Check that report was printed
        printed_values = [call[0][0] for call in mock_print.call_args_list]
        assert "# Research Report" in printed_values

    @pytest.mark.asyncio
    async def test_custom_report_type(self, mock_gpt_researcher):
        """Test generating a custom report type."""
        with patch.dict(os.environ, {'TAVILY_API_KEY': 'test_key'}):
            with patch('run_research.GPTResearcher', return_value=mock_gpt_researcher) as mock_cls:
                with patch('builtins.print'):
                    await run_research.generate_research_report(
                        "test query",
                        report_type="deep_research_report"
                    )

        # Verify the correct report type was passed
        mock_cls.assert_called_once_with(
            query="test query",
            report_type="deep_research_report"
        )

    @pytest.mark.asyncio
    async def test_missing_tavily_key_warning(self, mock_gpt_researcher):
        """Test that a warning is issued when TAVILY_API_KEY is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('run_research.GPTResearcher', return_value=mock_gpt_researcher):
                with patch('builtins.print') as mock_print:
                    await run_research.generate_research_report("test query")

        # Check that warning was printed to stderr
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
    async def test_research_error_handling(self, mock_gpt_researcher):
        """Test error handling during research."""
        mock_gpt_researcher.conduct_research.side_effect = Exception("Research failed")

        with patch.dict(os.environ, {'TAVILY_API_KEY': 'test_key'}):
            with patch('run_research.GPTResearcher', return_value=mock_gpt_researcher):
                with pytest.raises(SystemExit):
                    await run_research.generate_research_report("test query")

    @pytest.mark.asyncio
    async def test_write_report_error_handling(self, mock_gpt_researcher):
        """Test error handling during report writing."""
        mock_gpt_researcher.write_report.side_effect = Exception("Write failed")

        with patch.dict(os.environ, {'TAVILY_API_KEY': 'test_key'}):
            with patch('run_research.GPTResearcher', return_value=mock_gpt_researcher):
                with pytest.raises(SystemExit):
                    await run_research.generate_research_report("test query")


class TestReportTypes:
    """Test different report types."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("report_type", [
        "research_report",
        "resource_report",
        "outline_report",
        "custom_report",
        "deep_research_report"
    ])
    async def test_all_report_types(self, mock_gpt_researcher, report_type):
        """Test all supported report types."""
        with patch.dict(os.environ, {'TAVILY_API_KEY': 'test_key'}):
            with patch('run_research.GPTResearcher', return_value=mock_gpt_researcher) as mock_cls:
                with patch('builtins.print'):
                    await run_research.generate_research_report(
                        "test query",
                        report_type=report_type
                    )

        mock_cls.assert_called_once_with(
            query="test query",
            report_type=report_type
        )


class TestIntegration:
    """Integration tests (can be skipped if dependencies not available)."""

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv('TAVILY_API_KEY') or not os.getenv('OPENAI_API_KEY'),
        reason="API keys not set"
    )
    @pytest.mark.asyncio
    async def test_real_research_flow(self):
        """Test with real API (integration test)."""
        # This test requires actual API keys and will be skipped by default
        with patch('builtins.print'):
            await run_research.generate_research_report(
                "What is the capital of France?",
                report_type="research_report"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
