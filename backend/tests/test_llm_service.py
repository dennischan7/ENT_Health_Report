"""
Tests for LLM Client Service.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from pydantic import BaseModel, Field

from app.services.llm_service import (
    LLMClient,
    LLMError,
    LLMConfigNotFoundError,
    LLMGenerationError,
    get_llm_client,
)
from app.models.ai_config import AIProvider


class TestPydanticSchemas:
    """Test Pydantic schemas for structured output."""

    class Joke(BaseModel):
        """A joke with setup and punchline."""

        setup: str = Field(description="The setup of the joke")
        punchline: str = Field(description="The punchline to the joke")

    class AnalysisResult(BaseModel):
        """Analysis result with sentiment."""

        sentiment: str = Field(description="Positive, negative, or neutral")
        confidence: float = Field(description="Confidence score 0-1")
        summary: str = Field(description="Brief summary")


class TestLLMClientInit:
    """Test LLMClient initialization."""

    def test_default_init(self):
        """Test default initialization."""
        client = LLMClient()
        assert client.max_retries == 3
        assert client.base_delay == 1.0
        assert client.max_delay == 30.0

    def test_custom_init(self):
        """Test custom initialization."""
        client = LLMClient(max_retries=5, base_delay=2.0, max_delay=60.0)
        assert client.max_retries == 5
        assert client.base_delay == 2.0
        assert client.max_delay == 60.0

    def test_get_llm_client_function(self):
        """Test convenience function."""
        client = get_llm_client()
        assert isinstance(client, LLMClient)
        assert client.max_retries == 3

        client = get_llm_client(max_retries=5, base_delay=2.0, max_delay=60.0)
        assert client.max_retries == 5


class TestProviderMapping:
    """Test provider to model_provider mapping."""

    def test_provider_mapping_exists(self):
        """Test all providers have mappings."""
        client = LLMClient()
        expected_providers = [
            AIProvider.OPENAI,
            AIProvider.DEEPSEEK,
            AIProvider.QWEN,
            AIProvider.KIMI,
            AIProvider.MINIMAX,
            AIProvider.GEMINI,
            AIProvider.GLM,
            AIProvider.OPENAI_COMPATIBLE,
        ]
        for provider in expected_providers:
            assert provider in client.PROVIDER_MAPPING

    def test_openai_uses_openai_provider(self):
        """Test OpenAI uses openai model_provider."""
        client = LLMClient()
        assert client.PROVIDER_MAPPING[AIProvider.OPENAI] == "openai"

    def test_gemini_uses_google_genai(self):
        """Test Gemini uses google_genai model_provider."""
        client = LLMClient()
        assert client.PROVIDER_MAPPING[AIProvider.GEMINI] == "google_genai"

    def test_chinese_providers_use_openai_compatible(self):
        """Test Chinese providers use OpenAI-compatible API."""
        client = LLMClient()
        openai_compatible = [
            AIProvider.DEEPSEEK,
            AIProvider.QWEN,
            AIProvider.KIMI,
            AIProvider.MINIMAX,
            AIProvider.GLM,
        ]
        for provider in openai_compatible:
            assert client.PROVIDER_MAPPING[provider] == "openai"


class TestDefaultBaseUrls:
    """Test default base URLs for providers."""

    def test_default_base_urls_exist(self):
        """Test Chinese providers have default base URLs."""
        client = LLMClient()
        assert AIProvider.DEEPSEEK in client.DEFAULT_BASE_URLS
        assert AIProvider.QWEN in client.DEFAULT_BASE_URLS
        assert AIProvider.KIMI in client.DEFAULT_BASE_URLS
        assert AIProvider.MINIMAX in client.DEFAULT_BASE_URLS
        assert AIProvider.GLM in client.DEFAULT_BASE_URLS

    def test_deepseek_base_url(self):
        """Test DeepSeek base URL."""
        client = LLMClient()
        assert "deepseek" in client.DEFAULT_BASE_URLS[AIProvider.DEEPSEEK]

    def test_qwen_base_url(self):
        """Test Qwen base URL."""
        client = LLMClient()
        assert "dashscope" in client.DEFAULT_BASE_URLS[AIProvider.QWEN]

    def test_kimi_base_url(self):
        """Test Kimi base URL."""
        client = LLMClient()
        assert "moonshot" in client.DEFAULT_BASE_URLS[AIProvider.KIMI]


class TestConvertMessages:
    """Test message conversion."""

    def test_convert_dict_user_message(self):
        """Test converting dict user message."""
        client = LLMClient()
        messages = [{"role": "user", "content": "Hello!"}]
        converted = client._convert_messages(messages)
        assert len(converted) == 1
        assert converted[0].content == "Hello!"

    def test_convert_dict_system_message(self):
        """Test converting dict system message."""
        client = LLMClient()
        messages = [{"role": "system", "content": "You are helpful."}]
        converted = client._convert_messages(messages)
        assert len(converted) == 1

    def test_convert_dict_assistant_message(self):
        """Test converting dict assistant message."""
        client = LLMClient()
        messages = [{"role": "assistant", "content": "Hi there!"}]
        converted = client._convert_messages(messages)
        assert len(converted) == 1

    def test_convert_multiple_messages(self):
        """Test converting multiple messages."""
        client = LLMClient()
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi!"},
            {"role": "user", "content": "How are you?"},
        ]
        converted = client._convert_messages(messages)
        assert len(converted) == 4

    def test_convert_invalid_role_raises_error(self):
        """Test invalid role raises error."""
        client = LLMClient()
        messages = [{"role": "invalid", "content": "test"}]
        with pytest.raises(LLMError, match="Invalid message role"):
            client._convert_messages(messages)


class TestCreateChatModel:
    """Test chat model creation."""

    @patch("app.services.llm_service.init_chat_model")
    def test_create_openai_model(self, mock_init):
        """Test creating OpenAI model."""
        mock_model = MagicMock()
        mock_init.return_value = mock_model

        client = LLMClient()
        result = client._create_chat_model(
            provider=AIProvider.OPENAI,
            model="gpt-4",
            api_key="test-key",
            temperature=0.5,
            max_tokens=1000,
        )

        mock_init.assert_called_once()
        call_kwargs = mock_init.call_args[1]
        assert call_kwargs["model"] == "gpt-4"
        assert call_kwargs["model_provider"] == "openai"
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["max_tokens"] == 1000
        assert call_kwargs["api_key"] == "test-key"

    @patch("app.services.llm_service.init_chat_model")
    def test_create_deepseek_model_with_base_url(self, mock_init):
        """Test creating DeepSeek model with automatic base URL."""
        mock_model = MagicMock()
        mock_init.return_value = mock_model

        client = LLMClient()
        result = client._create_chat_model(
            provider=AIProvider.DEEPSEEK,
            model="deepseek-chat",
            api_key="test-key",
        )

        call_kwargs = mock_init.call_args[1]
        assert "base_url" in call_kwargs
        assert "deepseek" in call_kwargs["base_url"]

    @patch("app.services.llm_service.init_chat_model")
    def test_create_model_with_custom_base_url(self, mock_init):
        """Test creating model with custom base URL."""
        mock_model = MagicMock()
        mock_init.return_value = mock_model

        client = LLMClient()
        result = client._create_chat_model(
            provider=AIProvider.OPENAI_COMPATIBLE,
            model="custom-model",
            api_key="test-key",
            base_url="https://custom.api.com/v1",
        )

        call_kwargs = mock_init.call_args[1]
        assert call_kwargs["base_url"] == "https://custom.api.com/v1"

    @patch("app.services.llm_service.init_chat_model")
    def test_create_model_with_string_provider(self, mock_init):
        """Test creating model with string provider name."""
        mock_model = MagicMock()
        mock_init.return_value = mock_model

        client = LLMClient()
        result = client._create_chat_model(
            provider="deepseek",
            model="deepseek-chat",
            api_key="test-key",
        )

        mock_init.assert_called_once()


class TestGenerate:
    """Test generate method."""

    @patch("app.services.llm_service.init_chat_model")
    def test_generate_simple(self, mock_init):
        """Test simple generation."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Hello! How can I help you?"
        mock_model.invoke.return_value = mock_response
        mock_init.return_value = mock_model

        client = LLMClient()
        result = client.generate(
            messages=[{"role": "user", "content": "Hello"}],
            provider=AIProvider.DEEPSEEK,
            model="deepseek-chat",
            api_key="test-key",
        )

        assert result == "Hello! How can I help you?"
        mock_model.invoke.assert_called_once()

    @patch("app.services.llm_service.init_chat_model")
    def test_generate_with_retry_success(self, mock_init):
        """Test generation with retry that eventually succeeds."""
        mock_model = MagicMock()
        # First call fails, second succeeds
        mock_model.invoke.side_effect = [
            Exception("Rate limit"),
            MagicMock(content="Success!"),
        ]
        mock_init.return_value = mock_model

        client = LLMClient(max_retries=3, base_delay=0.01)
        result = client.generate(
            messages=[{"role": "user", "content": "Hello"}],
            provider=AIProvider.OPENAI,
            model="gpt-4",
            api_key="test-key",
        )

        assert result == "Success!"
        assert mock_model.invoke.call_count == 2

    @patch("app.services.llm_service.init_chat_model")
    def test_generate_all_retries_fail(self, mock_init):
        """Test generation fails after all retries."""
        mock_model = MagicMock()
        mock_model.invoke.side_effect = Exception("API Error")
        mock_init.return_value = mock_model

        client = LLMClient(max_retries=2, base_delay=0.01)
        with pytest.raises(LLMGenerationError, match="Failed after 2 retries"):
            client.generate(
                messages=[{"role": "user", "content": "Hello"}],
                provider=AIProvider.OPENAI,
                model="gpt-4",
                api_key="test-key",
            )


class TestGenerateStructured:
    """Test generate_structured method."""

    @patch("app.services.llm_service.init_chat_model")
    def test_generate_structured_simple(self, mock_init):
        """Test structured output generation."""
        mock_model = MagicMock()
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = TestPydanticSchemas.Joke(
            setup="Why did the chicken cross the road?",
            punchline="To get to the other side!",
        )
        mock_model.with_structured_output.return_value = mock_structured
        mock_init.return_value = mock_model

        client = LLMClient()
        result = client.generate_structured(
            messages=[{"role": "user", "content": "Tell me a joke"}],
            schema=TestPydanticSchemas.Joke,
            provider=AIProvider.OPENAI,
            model="gpt-4",
            api_key="test-key",
        )

        assert isinstance(result, TestPydanticSchemas.Joke)
        assert result.setup == "Why did the chicken cross the road?"
        assert result.punchline == "To get to the other side!"
        mock_model.with_structured_output.assert_called_once_with(TestPydanticSchemas.Joke)

    @patch("app.services.llm_service.init_chat_model")
    def test_generate_structured_with_retry(self, mock_init):
        """Test structured output with retry."""
        mock_model = MagicMock()
        mock_structured = MagicMock()
        # First call fails, second succeeds
        mock_structured.invoke.side_effect = [
            Exception("Temporary error"),
            TestPydanticSchemas.AnalysisResult(
                sentiment="positive",
                confidence=0.95,
                summary="Great product!",
            ),
        ]
        mock_model.with_structured_output.return_value = mock_structured
        mock_init.return_value = mock_model

        client = LLMClient(max_retries=3, base_delay=0.01)
        result = client.generate_structured(
            messages=[{"role": "user", "content": "Analyze this"}],
            schema=TestPydanticSchemas.AnalysisResult,
            provider=AIProvider.DEEPSEEK,
            model="deepseek-chat",
            api_key="test-key",
        )

        assert isinstance(result, TestPydanticSchemas.AnalysisResult)
        assert result.sentiment == "positive"
        assert result.confidence == 0.95


class TestGetActiveClient:
    """Test get_active_client method."""

    def test_no_config_found(self):
        """Test error when no config found."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        client = LLMClient()
        with pytest.raises(LLMConfigNotFoundError, match="No active LLM configuration"):
            client.get_active_client(mock_db)

    @patch("app.services.llm_service.init_chat_model")
    @patch("app.services.llm_service.decrypt")
    def test_get_default_config(self, mock_decrypt, mock_init):
        """Test getting default configuration."""
        mock_decrypt.return_value = "decrypted-key"
        mock_model = MagicMock()
        mock_init.return_value = mock_model

        # Create mock config
        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.config_name = "default-openai"
        mock_config.provider = AIProvider.OPENAI
        mock_config.model_name = "gpt-4"
        mock_config.encrypted_api_key = "encrypted-key"
        mock_config.api_base_url = None
        mock_config.temperature = 0.7
        mock_config.max_tokens = 2000
        mock_config.is_default = True
        mock_config.is_active = True

        # Setup mock DB
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()

        # First query for default
        mock_filter.first.return_value = mock_config
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        client = LLMClient()
        chat_model, config = client.get_active_client(mock_db)

        assert config.config_name == "default-openai"
        mock_decrypt.assert_called_once_with("encrypted-key")
        mock_init.assert_called_once()

    @patch("app.services.llm_service.init_chat_model")
    @patch("app.services.llm_service.decrypt")
    def test_get_config_by_name(self, mock_decrypt, mock_init):
        """Test getting configuration by name."""
        mock_decrypt.return_value = "decrypted-key"
        mock_model = MagicMock()
        mock_init.return_value = mock_model

        # Create mock config
        mock_config = MagicMock()
        mock_config.config_name = "deepseek-config"
        mock_config.provider = AIProvider.DEEPSEEK
        mock_config.model_name = "deepseek-chat"
        mock_config.encrypted_api_key = "encrypted-key"
        mock_config.api_base_url = "https://api.deepseek.com/v1"
        mock_config.temperature = 0.5
        mock_config.max_tokens = 1000

        # Setup mock DB
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = mock_config
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        client = LLMClient()
        chat_model, config = client.get_active_client(mock_db, config_name="deepseek-config")

        assert config.config_name == "deepseek-config"

    @patch("app.services.llm_service.decrypt")
    def test_decrypt_failure(self, mock_decrypt):
        """Test error when decryption fails."""
        mock_decrypt.side_effect = Exception("Invalid key")

        # Create mock config
        mock_config = MagicMock()
        mock_config.encrypted_api_key = "bad-encrypted-key"
        mock_config.is_active = True
        mock_config.is_default = True

        # Setup mock DB
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = mock_config
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        client = LLMClient()
        with pytest.raises(LLMError, match="Failed to decrypt API key"):
            client.get_active_client(mock_db)


class TestGenerateFromConfig:
    """Test generate_from_config method."""

    @patch("app.services.llm_service.init_chat_model")
    @patch("app.services.llm_service.decrypt")
    def test_generate_from_config(self, mock_decrypt, mock_init):
        """Test generation from database config."""
        mock_decrypt.return_value = "decrypted-key"
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Generated response"
        mock_model.invoke.return_value = mock_response
        mock_init.return_value = mock_model

        # Create mock config
        mock_config = MagicMock()
        mock_config.config_name = "test-config"
        mock_config.provider = AIProvider.OPENAI
        mock_config.model_name = "gpt-4"
        mock_config.encrypted_api_key = "encrypted-key"
        mock_config.api_base_url = None
        mock_config.temperature = 0.7
        mock_config.max_tokens = 2000
        mock_config.is_default = True
        mock_config.is_active = True

        # Setup mock DB
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = mock_config
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        client = LLMClient()
        result = client.generate_from_config(
            messages=[{"role": "user", "content": "Hello"}],
            db=mock_db,
        )

        assert result == "Generated response"

    @patch("app.services.llm_service.init_chat_model")
    @patch("app.services.llm_service.decrypt")
    def test_generate_from_config_with_overrides(self, mock_decrypt, mock_init):
        """Test generation from config with temperature override."""
        mock_decrypt.return_value = "decrypted-key"
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Generated response"
        mock_model.invoke.return_value = mock_response
        mock_init.return_value = mock_model

        # Create mock config
        mock_config = MagicMock()
        mock_config.config_name = "test-config"
        mock_config.provider = AIProvider.OPENAI
        mock_config.model_name = "gpt-4"
        mock_config.encrypted_api_key = "encrypted-key"
        mock_config.api_base_url = None
        mock_config.temperature = 0.7
        mock_config.max_tokens = 2000
        mock_config.is_default = True
        mock_config.is_active = True

        # Setup mock DB
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = mock_config
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        client = LLMClient()
        result = client.generate_from_config(
            messages=[{"role": "user", "content": "Hello"}],
            db=mock_db,
            temperature=0.1,
            max_tokens=500,
        )

        assert result == "Generated response"
        # Check that init_chat_model was called with overridden values
        last_call = mock_init.call_args
        assert last_call[1]["temperature"] == 0.1
        assert last_call[1]["max_tokens"] == 500


class TestGenerateStructuredFromConfig:
    """Test generate_structured_from_config method."""

    @patch("app.services.llm_service.init_chat_model")
    @patch("app.services.llm_service.decrypt")
    def test_generate_structured_from_config(self, mock_decrypt, mock_init):
        """Test structured generation from database config."""
        mock_decrypt.return_value = "decrypted-key"
        mock_model = MagicMock()
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = TestPydanticSchemas.Joke(
            setup="Setup text",
            punchline="Punchline text",
        )
        mock_model.with_structured_output.return_value = mock_structured
        mock_init.return_value = mock_model

        # Create mock config
        mock_config = MagicMock()
        mock_config.config_name = "test-config"
        mock_config.provider = AIProvider.OPENAI
        mock_config.model_name = "gpt-4"
        mock_config.encrypted_api_key = "encrypted-key"
        mock_config.api_base_url = None
        mock_config.temperature = 0.7
        mock_config.max_tokens = 2000
        mock_config.is_default = True
        mock_config.is_active = True

        # Setup mock DB
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = mock_config
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        client = LLMClient()
        result = client.generate_structured_from_config(
            messages=[{"role": "user", "content": "Tell me a joke"}],
            schema=TestPydanticSchemas.Joke,
            db=mock_db,
        )

        assert isinstance(result, TestPydanticSchemas.Joke)
        assert result.setup == "Setup text"


class TestExceptions:
    """Test custom exceptions."""

    def test_llm_error_is_exception(self):
        """Test LLMError is an Exception."""
        assert issubclass(LLMError, Exception)

    def test_llm_config_not_found_error_is_llm_error(self):
        """Test LLMConfigNotFoundError is an LLMError."""
        assert issubclass(LLMConfigNotFoundError, LLMError)

    def test_llm_generation_error_is_llm_error(self):
        """Test LLMGenerationError is an LLMError."""
        assert issubclass(LLMGenerationError, LLMError)

    def test_exception_messages(self):
        """Test exception messages."""
        with pytest.raises(LLMError) as exc_info:
            raise LLMError("Test error")
        assert "Test error" in str(exc_info.value)

        with pytest.raises(LLMConfigNotFoundError) as exc_info:
            raise LLMConfigNotFoundError("Config not found")
        assert "Config not found" in str(exc_info.value)

        with pytest.raises(LLMGenerationError) as exc_info:
            raise LLMGenerationError("Generation failed")
        assert "Generation failed" in str(exc_info.value)


class TestRetryLogic:
    """Test retry logic with exponential backoff."""

    @patch("app.services.llm_service.time.sleep")
    @patch("app.services.llm_service.init_chat_model")
    def test_exponential_backoff_delay(self, mock_init, mock_sleep):
        """Test that exponential backoff is applied correctly."""
        mock_model = MagicMock()
        # Fail twice, then succeed
        mock_model.invoke.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            MagicMock(content="Success"),
        ]
        mock_init.return_value = mock_model

        client = LLMClient(max_retries=3, base_delay=1.0)
        result = client.generate(
            messages=[{"role": "user", "content": "Test"}],
            provider=AIProvider.OPENAI,
            model="gpt-4",
            api_key="test-key",
        )

        assert result == "Success"
        # Check sleep was called with exponential backoff
        assert mock_sleep.call_count == 2
        # First retry: 1.0 * 2^0 = 1.0
        # Second retry: 1.0 * 2^1 = 2.0
        mock_sleep.assert_any_call(1.0)
        mock_sleep.assert_any_call(2.0)

    @patch("app.services.llm_service.time.sleep")
    @patch("app.services.llm_service.init_chat_model")
    def test_max_delay_cap(self, mock_init, mock_sleep):
        """Test that delay is capped at max_delay."""
        mock_model = MagicMock()
        mock_model.invoke.side_effect = Exception("Always fails")
        mock_init.return_value = mock_model

        client = LLMClient(max_retries=5, base_delay=10.0, max_delay=15.0)

        with pytest.raises(LLMGenerationError):
            client.generate(
                messages=[{"role": "user", "content": "Test"}],
                provider=AIProvider.OPENAI,
                model="gpt-4",
                api_key="test-key",
            )

        # Check that delays are capped at max_delay
        for call in mock_sleep.call_args_list:
            assert call[0][0] <= 15.0
