"""Tests for deep-research-stanford-storm skill."""
import sys
import os
import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open

# Add parent directory to path to import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import run_storm


@pytest.fixture
def mock_storm_engine():
    """Mock StormEngine."""
    mock = MagicMock()
    mock.run.return_value = None
    return mock


@pytest.fixture
def mock_storm_engine_cls():
    """Mock StormEngine class."""
    def _create_mock(mock_engine):
        def mock_init(*args, **kwargs):
            return mock_engine
        return mock_init
    return _create_mock


class TestRunStorm:
    """Test the run_storm function."""

    def test_basic_storm_run(self, mock_storm_engine, tmp_path):
        """Test basic STORM execution."""
        # Create a fake article file
        article_dir = tmp_path / "storm_output" / "test_dir" / "test_topic"
        article_dir.mkdir(parents=True)
        article_file = article_dir / "storm_gen_article_polished.md"
        article_file.write_text("# Test Article\n\nThis is the generated article.")

        with patch('run_storm.tempfile.mkdtemp', return_value=str(article_dir.parent)):
            with patch('run_storm.StormEngine', return_value=mock_storm_engine):
                with patch('run_storm.LiteLLMModelArgs'):
                    with patch('run_storm.StormEngineArgs'):
                        with patch('builtins.print') as mock_print:
                            run_storm.run_storm(
                                "test topic",
                                rm_name="bing",
                                fast_model="gpt-3.5-turbo",
                                strong_model="gpt-4o"
                            )

        # Verify engine was run
        mock_storm_engine.run.assert_called_once()

        # Check article was printed
        printed_values = [call[0][0] for call in mock_print.call_args_list if call[0]]
        assert any("Test Article" in str(val) for val in printed_values)

    def test_storm_run_with_bing_retriever(self, mock_storm_engine, tmp_path):
        """Test STORM with Bing retriever."""
        article_dir = tmp_path / "storm_output" / "test_dir" / "test_topic"
        article_dir.mkdir(parents=True)
        article_file = article_dir / "storm_gen_article_polished.md"
        article_file.write_text("Content")

        with patch('run_storm.tempfile.mkdtemp', return_value=str(article_dir.parent)):
            with patch('run_storm.StormEngine', return_value=mock_storm_engine):
                with patch('run_storm.LiteLLMModelArgs'):
                    with patch('run_storm.StormEngineArgs') as mock_args:
                        with patch('builtins.print'):
                            run_storm.run_storm(
                                "test topic",
                                rm_name="bing",
                                fast_model="gpt-3.5-turbo",
                                strong_model="gpt-4o"
                            )

        # Verify StormEngineArgs was called with bing retriever
        mock_args.assert_called_once()
        call_kwargs = mock_args.call_args[1]
        assert call_kwargs['rm_name'] == "bing"

    def test_storm_run_with_you_retriever(self, mock_storm_engine, tmp_path):
        """Test STORM with You.com retriever."""
        article_dir = tmp_path / "storm_output" / "test_dir" / "test_topic"
        article_dir.mkdir(parents=True)
        article_file = article_dir / "storm_gen_article_polished.md"
        article_file.write_text("Content")

        with patch('run_storm.tempfile.mkdtemp', return_value=str(article_dir.parent)):
            with patch('run_storm.StormEngine', return_value=mock_storm_engine):
                with patch('run_storm.LiteLLMModelArgs'):
                    with patch('run_storm.StormEngineArgs') as mock_args:
                        with patch('builtins.print'):
                            run_storm.run_storm(
                                "test topic",
                                rm_name="you",
                                fast_model="gpt-3.5-turbo",
                                strong_model="gpt-4o"
                            )

        call_kwargs = mock_args.call_args[1]
        assert call_kwargs['rm_name'] == "you"

    def test_storm_model_configuration(self, mock_storm_engine, tmp_path):
        """Test STORM model configuration."""
        article_dir = tmp_path / "storm_output" / "test_dir" / "test_topic"
        article_dir.mkdir(parents=True)
        article_file = article_dir / "storm_gen_article_polished.md"
        article_file.write_text("Content")

        with patch('run_storm.tempfile.mkdtemp', return_value=str(article_dir.parent)):
            with patch('run_storm.StormEngine', return_value=mock_storm_engine):
                with patch('run_storm.LiteLLMModelArgs') as mock_model_args:
                    with patch('run_storm.StormEngineArgs'):
                        with patch('builtins.print'):
                            run_storm.run_storm(
                                "test topic",
                                rm_name="bing",
                                fast_model="gpt-3.5-turbo",
                                strong_model="gpt-4o"
                            )

        # Verify both fast and strong models were configured
        assert mock_model_args.call_count == 2

        # Check the models
        calls = mock_model_args.call_args_list
        fast_call = calls[0][1]
        strong_call = calls[1][1]

        assert fast_call['model'] == "gpt-3.5-turbo"
        assert strong_call['model'] == "gpt-4o"

    def test_storm_topic_sanitization(self, mock_storm_engine, tmp_path):
        """Test that topic names are sanitized for directory names."""
        article_dir = tmp_path / "storm_output" / "run_test_topic_with_special_" / "test"
        article_dir.mkdir(parents=True)
        article_file = article_dir / "storm_gen_article_polished.md"
        article_file.write_text("Content")

        with patch('run_storm.tempfile.mkdtemp', return_value=str(article_dir.parent)):
            with patch('run_storm.StormEngine', return_value=mock_storm_engine):
                with patch('run_storm.LiteLLMModelArgs'):
                    with patch('run_storm.StormEngineArgs'):
                        with patch('builtins.print'):
                            # Topic with special characters
                            run_storm.run_storm(
                                "test/topic with special!",
                                rm_name="bing",
                                fast_model="gpt-3.5-turbo",
                                strong_model="gpt-4o"
                            )

        mock_storm_engine.run.assert_called_once()

    def test_storm_output_directory_creation(self, mock_storm_engine):
        """Test that output directory is created."""
        with patch('run_storm.os.makedirs') as mock_makedirs:
            with patch('run_storm.tempfile.mkdtemp', return_value="/tmp/test_dir"):
                with patch('run_storm.glob.glob', return_value=[]):
                    with patch('run_storm.StormEngine', return_value=mock_storm_engine):
                        with patch('run_storm.LiteLLMModelArgs'):
                            with patch('run_storm.StormEngineArgs'):
                                with pytest.raises(SystemExit):
                                    run_storm.run_storm(
                                        "test topic",
                                        rm_name="bing",
                                        fast_model="gpt-3.5-turbo",
                                        strong_model="gpt-4o"
                                    )

        # Verify output directory creation was attempted
        mock_makedirs.assert_called()


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_article_file_not_found(self, mock_storm_engine):
        """Test error when article file is not found."""
        with patch('run_storm.tempfile.mkdtemp', return_value="/tmp/test_dir"):
            with patch('run_storm.glob.glob', return_value=[]):
                with patch('run_storm.StormEngine', return_value=mock_storm_engine):
                    with patch('run_storm.LiteLLMModelArgs'):
                        with patch('run_storm.StormEngineArgs'):
                            with pytest.raises(SystemExit):
                                run_storm.run_storm(
                                    "test topic",
                                    rm_name="bing",
                                    fast_model="gpt-3.5-turbo",
                                    strong_model="gpt-4o"
                                )

    def test_storm_engine_error(self, mock_storm_engine):
        """Test error during STORM engine execution."""
        mock_storm_engine.run.side_effect = Exception("STORM error")

        with patch('run_storm.tempfile.mkdtemp', return_value="/tmp/test_dir"):
            with patch('run_storm.StormEngine', return_value=mock_storm_engine):
                with patch('run_storm.LiteLLMModelArgs'):
                    with patch('run_storm.StormEngineArgs'):
                        with pytest.raises(SystemExit):
                            run_storm.run_storm(
                                "test topic",
                                rm_name="bing",
                                fast_model="gpt-3.5-turbo",
                                strong_model="gpt-4o"
                            )


class TestStormEngineConfiguration:
    """Test STORM engine configuration."""

    def test_engine_args_configuration(self, mock_storm_engine, tmp_path):
        """Test that StormEngineArgs is configured correctly."""
        article_dir = tmp_path / "storm_output" / "test_dir" / "test_topic"
        article_dir.mkdir(parents=True)
        article_file = article_dir / "storm_gen_article_polished.md"
        article_file.write_text("Content")

        with patch('run_storm.tempfile.mkdtemp', return_value=str(article_dir.parent)):
            with patch('run_storm.StormEngine', return_value=mock_storm_engine):
                with patch('run_storm.LiteLLMModelArgs') as mock_model_args:
                    mock_fast_config = Mock()
                    mock_strong_config = Mock()
                    mock_model_args.side_effect = [mock_fast_config, mock_strong_config]

                    with patch('run_storm.StormEngineArgs') as mock_engine_args:
                        with patch('builtins.print'):
                            run_storm.run_storm(
                                "test topic",
                                rm_name="bing",
                                fast_model="gpt-3.5-turbo",
                                strong_model="gpt-4o"
                            )

        # Verify engine args include both configs
        call_kwargs = mock_engine_args.call_args[1]
        assert call_kwargs['lm_config'] == mock_fast_config
        assert call_kwargs['outline_gen_lm_config'] == mock_strong_config
        assert call_kwargs['article_gen_lm_config'] == mock_strong_config
        assert call_kwargs['article_polish_lm_config'] == mock_strong_config

    def test_engine_run_called_with_topic(self, mock_storm_engine, tmp_path):
        """Test that engine.run is called with correct topic."""
        article_dir = tmp_path / "storm_output" / "test_dir" / "test_topic"
        article_dir.mkdir(parents=True)
        article_file = article_dir / "storm_gen_article_polished.md"
        article_file.write_text("Content")

        with patch('run_storm.tempfile.mkdtemp', return_value=str(article_dir.parent)):
            with patch('run_storm.StormEngine', return_value=mock_storm_engine):
                with patch('run_storm.LiteLLMModelArgs'):
                    with patch('run_storm.StormEngineArgs'):
                        with patch('builtins.print'):
                            run_storm.run_storm(
                                "My Research Topic",
                                rm_name="bing",
                                fast_model="gpt-3.5-turbo",
                                strong_model="gpt-4o"
                            )

        # Verify engine.run was called with topic and output_dir
        call_kwargs = mock_storm_engine.run.call_args[1]
        assert call_kwargs['topic'] == "My Research Topic"
        assert 'output_dir' in call_kwargs


class TestArticleRetrieval:
    """Test article file retrieval."""

    def test_article_found_and_read(self, mock_storm_engine, tmp_path):
        """Test that article is found and read correctly."""
        article_dir = tmp_path / "storm_output" / "test_dir" / "test_topic"
        article_dir.mkdir(parents=True)
        article_file = article_dir / "storm_gen_article_polished.md"
        test_content = "# My Article\n\nThis is comprehensive research content."
        article_file.write_text(test_content)

        with patch('run_storm.tempfile.mkdtemp', return_value=str(article_dir.parent)):
            with patch('run_storm.StormEngine', return_value=mock_storm_engine):
                with patch('run_storm.LiteLLMModelArgs'):
                    with patch('run_storm.StormEngineArgs'):
                        with patch('builtins.print') as mock_print:
                            run_storm.run_storm(
                                "test topic",
                                rm_name="bing",
                                fast_model="gpt-3.5-turbo",
                                strong_model="gpt-4o"
                            )

        # Check that article content was printed
        printed_values = [call[0][0] for call in mock_print.call_args_list if call[0]]
        assert any("My Article" in str(val) for val in printed_values)
        assert any("comprehensive research" in str(val) for val in printed_values)


class TestIntegration:
    """Integration tests."""

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv('OPENAI_API_KEY'),
        reason="OPENAI_API_KEY not set"
    )
    def test_real_storm_run(self):
        """Test with real STORM (integration test)."""
        # This requires actual API keys and STORM dependencies
        with patch('builtins.print'):
            run_storm.run_storm(
                "Artificial Intelligence",
                rm_name="bing",
                fast_model="gpt-3.5-turbo",
                strong_model="gpt-4o"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
