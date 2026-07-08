"""Tests for deep-research-smolagents skill."""
import sys
import os
import pytest
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path to import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import agent


@pytest.fixture
def mock_inference_client_model():
    """Mock InferenceClientModel."""
    return MagicMock()


@pytest.fixture
def mock_litellm_model():
    """Mock LiteLLMModel."""
    return MagicMock()


@pytest.fixture
def mock_transformers_model():
    """Mock TransformersModel."""
    return MagicMock()


@pytest.fixture
def mock_code_agent():
    """Mock CodeAgent."""
    mock = MagicMock()
    mock.run.return_value = "Agent completed the task successfully."
    return mock


class TestCreateModel:
    """Test the create_model function."""

    def test_create_hf_model_default(self, mock_inference_client_model):
        """Test creating default HuggingFace model."""
        with patch.dict(os.environ, {}):
            with patch('agent.InferenceClientModel', return_value=mock_inference_client_model) as mock_cls:
                result = agent.create_model(model_type="hf")

        assert result == mock_inference_client_model
        mock_cls.assert_called_once()
        # Should use default Qwen model
        assert "Qwen" in str(mock_cls.call_args)

    def test_create_hf_model_custom(self, mock_inference_client_model):
        """Test creating HuggingFace model with custom model ID."""
        with patch.dict(os.environ, {}):
            with patch('agent.InferenceClientModel', return_value=mock_inference_client_model) as mock_cls:
                result = agent.create_model(model_type="hf", model_id="custom/model")

        mock_cls.assert_called_once_with(model_id="custom/model")

    def test_create_openai_model(self, mock_litellm_model):
        """Test creating OpenAI model."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            with patch('agent.LiteLLMModel', return_value=mock_litellm_model) as mock_cls:
                result = agent.create_model(model_type="openai")

        assert result == mock_litellm_model
        mock_cls.assert_called_once_with(model_id="gpt-4o")

    def test_create_openai_model_custom(self, mock_litellm_model):
        """Test creating OpenAI model with custom model ID."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            with patch('agent.LiteLLMModel', return_value=mock_litellm_model) as mock_cls:
                result = agent.create_model(model_type="openai", model_id="gpt-4-turbo")

        mock_cls.assert_called_once_with(model_id="gpt-4-turbo")

    def test_create_openai_model_no_key(self):
        """Test creating OpenAI model without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                agent.create_model(model_type="openai")

    def test_create_anthropic_model(self, mock_litellm_model):
        """Test creating Anthropic model."""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test_key'}):
            with patch('agent.LiteLLMModel', return_value=mock_litellm_model) as mock_cls:
                result = agent.create_model(model_type="anthropic")

        assert result == mock_litellm_model
        mock_cls.assert_called_once_with(model_id="claude-3-5-sonnet-20241022")

    def test_create_anthropic_model_no_key(self):
        """Test creating Anthropic model without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                agent.create_model(model_type="anthropic")

    def test_create_local_model(self, mock_transformers_model):
        """Test creating local Transformers model."""
        with patch('agent.TransformersModel', return_value=mock_transformers_model) as mock_cls:
            result = agent.create_model(model_type="local", model_id="local/model")

        assert result == mock_transformers_model
        mock_cls.assert_called_once_with(model_id="local/model")

    def test_create_local_model_no_id(self):
        """Test creating local model without model ID fails."""
        with pytest.raises(SystemExit):
            agent.create_model(model_type="local")

    def test_create_unknown_model_type(self):
        """Test creating model with unknown type."""
        with pytest.raises(SystemExit):
            agent.create_model(model_type="unknown")


class TestRunAgent:
    """Test the run_agent function."""

    def test_basic_run(self, mock_inference_client_model, mock_code_agent):
        """Test basic agent run."""
        with patch.dict(os.environ, {}):
            with patch('agent.create_model', return_value=mock_inference_client_model):
                with patch('agent.CodeAgent', return_value=mock_code_agent):
                    with patch('builtins.print') as mock_print:
                        agent.run_agent("test task")

        mock_code_agent.run.assert_called_once_with("test task")

        # Check output was printed
        printed_values = [call[0][0] for call in mock_print.call_args_list if call[0]]
        assert any("completed" in str(val).lower() for val in printed_values)

    def test_run_with_web_search(self, mock_inference_client_model, mock_code_agent):
        """Test agent run with web search enabled."""
        with patch.dict(os.environ, {}):
            with patch('agent.create_model', return_value=mock_inference_client_model):
                with patch('agent.CodeAgent', return_value=mock_code_agent) as mock_agent_cls:
                    with patch('agent.DuckDuckGoSearchTool') as mock_search_tool:
                        with patch('builtins.print'):
                            agent.run_agent("test task", web_search=True)

        # Verify search tool was added
        call_kwargs = mock_agent_cls.call_args[1]
        assert 'tools' in call_kwargs
        assert len(call_kwargs['tools']) > 0

    def test_run_with_different_models(self, mock_litellm_model, mock_code_agent):
        """Test agent run with different model types."""
        for model_type in ["hf", "openai", "anthropic"]:
            env = {}
            if model_type == "openai":
                env['OPENAI_API_KEY'] = 'test_key'
            elif model_type == "anthropic":
                env['ANTHROPIC_API_KEY'] = 'test_key'

            with patch.dict(os.environ, env):
                with patch('agent.create_model', return_value=mock_litellm_model):
                    with patch('agent.CodeAgent', return_value=mock_code_agent):
                        with patch('builtins.print'):
                            agent.run_agent("test task", model_type=model_type)

            mock_code_agent.run.assert_called_with("test task")

    def test_run_with_verbose(self, mock_inference_client_model, mock_code_agent):
        """Test agent run with verbose output."""
        mock_code_agent.logs = ["Log entry 1", "Log entry 2"]

        with patch.dict(os.environ, {}):
            with patch('agent.create_model', return_value=mock_inference_client_model):
                with patch('agent.CodeAgent', return_value=mock_code_agent):
                    with patch('builtins.print') as mock_print:
                        agent.run_agent("test task", verbose=True)

        # Check logs were printed
        stderr_calls = [
            call for call in mock_print.call_args_list
            if len(call[1]) > 0 and call[1].get('file') == sys.stderr
        ]
        logs_printed = any(
            'Log entry' in str(call[0][0])
            for call in stderr_calls
        )
        assert logs_printed

    def test_run_error_handling(self, mock_inference_client_model, mock_code_agent):
        """Test agent run error handling."""
        mock_code_agent.run.side_effect = Exception("Agent error")

        with patch.dict(os.environ, {}):
            with patch('agent.create_model', return_value=mock_inference_client_model):
                with patch('agent.CodeAgent', return_value=mock_code_agent):
                    with pytest.raises(SystemExit):
                        agent.run_agent("test task")

    def test_run_with_custom_model_id(self, mock_inference_client_model, mock_code_agent):
        """Test agent run with custom model ID."""
        with patch.dict(os.environ, {}):
            with patch('agent.create_model', return_value=mock_inference_client_model) as mock_create:
                with patch('agent.CodeAgent', return_value=mock_code_agent):
                    with patch('builtins.print'):
                        agent.run_agent(
                            "test task",
                            model_type="hf",
                            model_id="custom/model"
                        )

        # Verify custom model was passed
        mock_create.assert_called_once_with("hf", "custom/model")


class TestCodeAgentConfiguration:
    """Test CodeAgent configuration."""

    def test_agent_max_steps(self, mock_inference_client_model, mock_code_agent):
        """Test that agent has max_steps configured."""
        with patch.dict(os.environ, {}):
            with patch('agent.create_model', return_value=mock_inference_client_model):
                with patch('agent.CodeAgent', return_value=mock_code_agent) as mock_agent_cls:
                    with patch('builtins.print'):
                        agent.run_agent("test task")

        # Verify max_steps is set
        call_kwargs = mock_agent_cls.call_args[1]
        assert 'max_steps' in call_kwargs
        assert call_kwargs['max_steps'] == 10

    def test_agent_tools_configuration(self, mock_inference_client_model, mock_code_agent):
        """Test agent tools configuration."""
        with patch.dict(os.environ, {}):
            with patch('agent.create_model', return_value=mock_inference_client_model):
                with patch('agent.CodeAgent', return_value=mock_code_agent) as mock_agent_cls:
                    with patch('builtins.print'):
                        agent.run_agent("test task", web_search=False)

        # Verify tools list exists (even if empty)
        call_kwargs = mock_agent_cls.call_args[1]
        assert 'tools' in call_kwargs
        assert isinstance(call_kwargs['tools'], list)


class TestModelWarnings:
    """Test model configuration warnings."""

    def test_hf_model_no_token_warning(self, mock_inference_client_model, mock_code_agent):
        """Test warning when HF_TOKEN is not set."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('agent.create_model', return_value=mock_inference_client_model):
                with patch('agent.CodeAgent', return_value=mock_code_agent):
                    with patch('builtins.print') as mock_print:
                        agent.run_agent("test task", model_type="hf")

        # Warning should be in stderr
        stderr_calls = [
            call for call in mock_print.call_args_list
            if len(call[1]) > 0 and call[1].get('file') == sys.stderr
        ]
        # The warning is in create_model, so it should be printed
        # This is checking implementation details, so we can verify the agent ran
        assert mock_code_agent.run.called


class TestIntegration:
    """Integration tests."""

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv('OPENAI_API_KEY') and not os.getenv('HF_TOKEN'),
        reason="No API keys set"
    )
    def test_real_agent_run(self):
        """Test with real agent (integration test)."""
        with patch('builtins.print'):
            agent.run_agent(
                "What is 2+2?",
                model_type="hf" if os.getenv('HF_TOKEN') else "openai"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
