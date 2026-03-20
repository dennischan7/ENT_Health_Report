"""
LLM Client Service for multi-provider LLM support.

This module provides a unified interface for interacting with multiple LLM providers
through LangChain's init_chat_model. Supports structured output with Pydantic models
and includes retry logic with exponential backoff.

Supported Providers:
    - openai: OpenAI GPT models
    - deepseek: DeepSeek models
    - qwen: Alibaba Qwen models
    - kimi: Moonshot Kimi models
    - minimax: MiniMax models
    - gemini: Google Gemini models
    - glm: ZhipuAI GLM models
    - openai-compatible: Any OpenAI-compatible API
"""

import logging
import time
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.encryption import decrypt
from app.models.ai_config import AIConfig, AIProvider

logger = logging.getLogger(__name__)

# Type variable for Pydantic models
T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Base exception for LLM-related errors."""

    pass


class LLMConfigNotFoundError(LLMError):
    """Raised when no active LLM configuration is found."""

    pass


class LLMGenerationError(LLMError):
    """Raised when LLM generation fails after all retries."""

    pass


class LLMClient:
    """
    Unified LLM client supporting multiple providers via LangChain.

    This client provides a unified interface for interacting with various LLM
    providers through LangChain's init_chat_model. It supports structured output
    using Pydantic models and includes automatic retry with exponential backoff.

    Attributes:
        max_retries: Maximum number of retry attempts (default: 3).
        base_delay: Base delay in seconds for exponential backoff (default: 1.0).
        max_delay: Maximum delay in seconds between retries (default: 30.0).

    Example:
        >>> client = LLMClient()
        >>> # Simple generation
        >>> response = client.generate(
        ...     messages=[{"role": "user", "content": "Hello!"}],
        ...     provider="deepseek",
        ...     api_key="your-api-key",
        ...     model="deepseek-chat"
        ... )
        >>> print(response)

        >>> # Structured output
        >>> class Joke(BaseModel):
        ...     setup: str
        ...     punchline: str
        >>> joke = client.generate_structured(
        ...     messages=[{"role": "user", "content": "Tell me a joke"}],
        ...     schema=Joke,
        ...     provider="openai"
        ... )
        >>> print(joke.setup)
    """

    # Provider to model_provider mapping for init_chat_model
    PROVIDER_MAPPING: Dict[AIProvider, str] = {
        AIProvider.OPENAI: "openai",
        AIProvider.DEEPSEEK: "openai",  # DeepSeek uses OpenAI-compatible API
        AIProvider.QWEN: "openai",  # Qwen uses OpenAI-compatible API
        AIProvider.KIMI: "openai",  # Kimi uses OpenAI-compatible API
        AIProvider.MINIMAX: "openai",  # MiniMax uses OpenAI-compatible API
        AIProvider.GEMINI: "google_genai",
        AIProvider.GLM: "openai",  # GLM uses OpenAI-compatible API
        AIProvider.OPENAI_COMPATIBLE: "openai",
    }

    # Default base URLs for providers that require them
    DEFAULT_BASE_URLS: Dict[AIProvider, str] = {
        AIProvider.DEEPSEEK: "https://api.deepseek.com/v1",
        AIProvider.QWEN: "https://dashscope.aliyuncs.com/compatible-mode/v1",
        AIProvider.KIMI: "https://api.moonshot.cn/v1",
        AIProvider.MINIMAX: "https://api.minimax.chat/v1",
        AIProvider.GLM: "https://open.bigmodel.cn/api/paas/v4",
    }

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
    ):
        """
        Initialize the LLM client.

        Args:
            max_retries: Maximum number of retry attempts for failed requests.
            base_delay: Base delay in seconds for exponential backoff.
            max_delay: Maximum delay in seconds between retries.
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    def _create_chat_model(
        self,
        provider: Union[AIProvider, str],
        model: str,
        api_key: str,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> BaseChatModel:
        """
        Create a LangChain chat model instance for the specified provider.

        Args:
            provider: The LLM provider (enum or string).
            model: The model name/identifier.
            api_key: The API key for authentication.
            base_url: Optional custom base URL for the API.
            temperature: Temperature for generation (0.0 to 2.0).
            max_tokens: Maximum tokens in the response.

        Returns:
            BaseChatModel: A LangChain chat model instance.

        Raises:
            LLMError: If the provider is not supported.
        """
        # Convert string to enum if needed
        if isinstance(provider, str):
            # Normalize the string: lowercase and handle various formats
            normalized = provider.lower().replace(" ", "-")

            # Try to find matching enum by value
            for p in AIProvider:
                if p.value == normalized:
                    provider = p
                    break
            else:
                # Fallback: try converting underscores to hyphens
                for p in AIProvider:
                    if p.value == normalized.replace("_", "-"):
                        provider = p
                        break
                else:
                    raise LLMError(f"Unsupported provider: {provider}")

        # Get the model_provider for init_chat_model
        model_provider = self.PROVIDER_MAPPING.get(provider)
        if not model_provider:
            raise LLMError(f"Unsupported provider: {provider}")

        # Get default base URL if not provided
        if not base_url:
            base_url = self.DEFAULT_BASE_URLS.get(provider)

        # Build kwargs for init_chat_model
        kwargs: Dict[str, Any] = {
            "model": model,
            "model_provider": model_provider,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "api_key": api_key,
        }

        # Add base_url for OpenAI-compatible providers
        if base_url and model_provider == "openai":
            kwargs["base_url"] = base_url

        logger.info(f"Creating chat model for provider={provider}, model={model}")

        return init_chat_model(**kwargs)

    def _convert_messages(
        self, messages: List[Union[Dict[str, str], BaseMessage]]
    ) -> List[BaseMessage]:
        """
        Convert message dictionaries to LangChain message objects.

        Args:
            messages: List of message dictionaries or BaseMessage objects.

        Returns:
            List[BaseMessage]: List of LangChain message objects.

        Raises:
            LLMError: If a message has an invalid role.
        """
        converted = []
        for msg in messages:
            if isinstance(msg, BaseMessage):
                converted.append(msg)
            elif isinstance(msg, dict):
                role = msg.get("role", "user").lower()
                content = msg.get("content", "")

                if role == "user":
                    converted.append(HumanMessage(content=content))
                elif role == "assistant" or role == "ai":
                    converted.append(AIMessage(content=content))
                elif role == "system":
                    converted.append(SystemMessage(content=content))
                else:
                    raise LLMError(f"Invalid message role: {role}")
            else:
                raise LLMError(f"Invalid message type: {type(msg)}")

        return converted

    def _retry_with_backoff(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """
        Execute a function with exponential backoff retry logic.

        Args:
            func: The function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            The result of the function call.

        Raises:
            LLMGenerationError: If all retries fail.
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    # Calculate delay with exponential backoff
                    delay = min(self.base_delay * (2**attempt), self.max_delay)
                    logger.warning(
                        f"LLM request failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"LLM request failed after {self.max_retries} attempts: {e}")

        raise LLMGenerationError(f"Failed after {self.max_retries} retries: {last_exception}")

    def generate(
        self,
        messages: List[Union[Dict[str, str], BaseMessage]],
        provider: Union[AIProvider, str],
        model: str,
        api_key: str,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Generate a text response from the LLM.

        This method sends messages to the LLM and returns the generated text.
        It includes automatic retry with exponential backoff for transient failures.

        Args:
            messages: List of message dictionaries or LangChain message objects.
                Each dict should have 'role' and 'content' keys.
            provider: The LLM provider to use.
            model: The model name/identifier.
            api_key: The API key for authentication.
            base_url: Optional custom base URL for the API.
            temperature: Temperature for generation (0.0 to 2.0, default: 0.7).
            max_tokens: Maximum tokens in the response (default: 2000).

        Returns:
            str: The generated text response.

        Raises:
            LLMError: If the provider is not supported.
            LLMGenerationError: If generation fails after all retries.

        Example:
            >>> client = LLMClient()
            >>> response = client.generate(
            ...     messages=[
            ...         {"role": "system", "content": "You are a helpful assistant."},
            ...         {"role": "user", "content": "What is Python?"}
            ...     ],
            ...     provider="deepseek",
            ...     model="deepseek-chat",
            ...     api_key="your-api-key"
            ... )
        """
        chat_model = self._create_chat_model(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        converted_messages = self._convert_messages(messages)

        def _invoke() -> str:
            response = chat_model.invoke(converted_messages)
            return response.content

        return self._retry_with_backoff(_invoke)

    def generate_structured(
        self,
        messages: List[Union[Dict[str, str], BaseMessage]],
        schema: Type[T],
        provider: Union[AIProvider, str],
        model: str,
        api_key: str,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> T:
        """
        Generate a structured response from the LLM using a Pydantic schema.

        This method uses LangChain's structured output feature to ensure
        the response conforms to the provided Pydantic schema.

        Note: Some providers (like DeepSeek, Moonshot, etc.) don't support
        native structured output. For these providers, we use JSON mode
        and manual parsing.

        Args:
            messages: List of message dictionaries or LangChain message objects.
            schema: Pydantic model class defining the expected response structure.
            provider: The LLM provider to use.
            model: The model name/identifier.
            api_key: The API key for authentication.
            base_url: Optional custom base URL for the API.
            temperature: Temperature for generation (0.0 to 2.0, default: 0.7).
            max_tokens: Maximum tokens in the response (default: 2000).

        Returns:
            An instance of the provided Pydantic schema.

        Raises:
            LLMGenerationError: If generation fails after retries.
            LLMError: If the response cannot be parsed into the schema.
        """
        import json
        from pydantic import ValidationError

        chat_model = self._create_chat_model(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        converted_messages = self._convert_messages(messages)

        # Check if provider supports structured output
        # Providers known to support native structured output
        STRUCTURED_OUTPUT_PROVIDERS = {
            AIProvider.OPENAI,
            "openai",
        }

        provider_str = provider.value if hasattr(provider, "value") else str(provider)

        if provider_str.lower() in [
            p.value if hasattr(p, "value") else str(p).lower() for p in STRUCTURED_OUTPUT_PROVIDERS
        ]:
            # Use native structured output
            structured_model = chat_model.with_structured_output(schema)

            def _invoke() -> T:
                return structured_model.invoke(converted_messages)

            return self._retry_with_backoff(_invoke)
        else:
            # Use JSON mode for providers that don't support structured output
            # Add instruction for JSON output
            schema_json = schema.model_json_schema()
            json_instruction = f"\n\nIMPORTANT: You must respond with a valid JSON object that matches this schema:\n{json.dumps(schema_json, indent=2)}\n\nRespond ONLY with the JSON object, no other text."

            # Add instruction to the last user message
            enhanced_messages = []
            for msg in converted_messages:
                enhanced_messages.append(msg)

            # Add JSON instruction as a system message
            enhanced_messages.append(SystemMessage(content=json_instruction))

            def _invoke_json() -> T:
                response = chat_model.invoke(enhanced_messages)
                content = response.content

                # Try to extract JSON from the response
                # Handle potential markdown code blocks
                if "```json" in content:
                    start = content.find("```json") + 7
                    end = content.find("```", start)
                    content = content[start:end].strip()
                elif "```" in content:
                    start = content.find("```") + 3
                    end = content.find("```", start)
                    content = content[start:end].strip()

                # Parse JSON and validate against schema
                data = json.loads(content)
                return schema.model_validate(data)

            return self._retry_with_backoff(_invoke_json)

    def get_active_client(
        self,
        db: Session,
        config_name: Optional[str] = None,
    ) -> tuple[BaseChatModel, AIConfig]:
        """
        Get an active LLM client from the database configuration.

        This method retrieves an active LLM configuration from the database,
        decrypts the API key, and returns a configured chat model.

        Args:
            db: SQLAlchemy database session.
            config_name: Optional specific configuration name to use.
                        If None, uses the default active configuration.

        Returns:
            tuple[BaseChatModel, AIConfig]: A tuple containing the configured
                chat model and the database configuration record.

        Raises:
            LLMConfigNotFoundError: If no active configuration is found.

        Example:
            >>> from app.db.session import SessionLocal
            >>>
            >>> db = SessionLocal()
            >>> client = LLMClient()
            >>> chat_model, config = client.get_active_client(db)
            >>> response = chat_model.invoke([HumanMessage(content="Hello!")])
        """
        query = db.query(AIConfig)

        if config_name:
            config = query.filter(
                AIConfig.config_name == config_name,
                AIConfig.is_active == True,
            ).first()
        else:
            # Try to get default config first, then any active config
            config = query.filter(
                AIConfig.is_default == True,
                AIConfig.is_active == True,
            ).first()

            if not config:
                config = query.filter(AIConfig.is_active == True).first()

        if not config:
            raise LLMConfigNotFoundError(
                "No active LLM configuration found. "
                "Please configure an LLM provider in the admin settings."
            )

        # Decrypt the API key
        try:
            api_key = decrypt(config.encrypted_api_key)
        except Exception as e:
            raise LLMError(f"Failed to decrypt API key: {e}")

        # Create the chat model
        chat_model = self._create_chat_model(
            provider=config.provider,
            model=config.model_name,
            api_key=api_key,
            base_url=config.api_base_url,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )

        return chat_model, config

    def generate_from_config(
        self,
        messages: List[Union[Dict[str, str], BaseMessage]],
        db: Session,
        config_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text using a database-stored configuration.

        Convenience method that combines get_active_client and generate.

        Args:
            messages: List of message dictionaries or LangChain message objects.
            db: SQLAlchemy database session.
            config_name: Optional specific configuration name to use.
            temperature: Override temperature from config (optional).
            max_tokens: Override max_tokens from config (optional).

        Returns:
            str: The generated text response.

        Raises:
            LLMConfigNotFoundError: If no active configuration is found.
            LLMGenerationError: If generation fails after all retries.
        """
        chat_model, config = self.get_active_client(db, config_name)

        # Override settings if provided
        if temperature is not None or max_tokens is not None:
            chat_model = self._create_chat_model(
                provider=config.provider,
                model=config.model_name,
                api_key=decrypt(config.encrypted_api_key),
                base_url=config.api_base_url,
                temperature=temperature if temperature is not None else config.temperature,
                max_tokens=max_tokens if max_tokens is not None else config.max_tokens,
            )

        converted_messages = self._convert_messages(messages)

        def _invoke() -> str:
            response = chat_model.invoke(converted_messages)
            return response.content

        return self._retry_with_backoff(_invoke)

    def generate_structured_from_config(
        self,
        messages: List[Union[Dict[str, str], BaseMessage]],
        schema: Type[T],
        db: Session,
        config_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> T:
        """
        Generate structured output using a database-stored configuration.

        Convenience method that combines get_active_client and generate_structured.

        Args:
            messages: List of message dictionaries or LangChain message objects.
            schema: A Pydantic BaseModel class defining the expected structure.
            db: SQLAlchemy database session.
            config_name: Optional specific configuration name to use.
            temperature: Override temperature from config (optional).
            max_tokens: Override max_tokens from config (optional).

        Returns:
            T: An instance of the Pydantic model with the LLM's response.

        Raises:
            LLMConfigNotFoundError: If no active configuration is found.
            LLMGenerationError: If generation fails after all retries.
        """
        chat_model, config = self.get_active_client(db, config_name)

        # Override settings if provided
        if temperature is not None or max_tokens is not None:
            chat_model = self._create_chat_model(
                provider=config.provider,
                model=config.model_name,
                api_key=decrypt(config.encrypted_api_key),
                base_url=config.api_base_url,
                temperature=temperature if temperature is not None else config.temperature,
                max_tokens=max_tokens if max_tokens is not None else config.max_tokens,
            )

        converted_messages = self._convert_messages(messages)

        # Check if provider supports structured output
        STRUCTURED_OUTPUT_PROVIDERS = {AIProvider.OPENAI, "openai"}
        provider_str = (
            config.provider.value if hasattr(config.provider, "value") else str(config.provider)
        )

        if provider_str.lower() in [
            p.value if hasattr(p, "value") else str(p).lower() for p in STRUCTURED_OUTPUT_PROVIDERS
        ]:
            # Use native structured output
            structured_model = chat_model.with_structured_output(schema)

            def _invoke() -> T:
                return structured_model.invoke(converted_messages)

            return self._retry_with_backoff(_invoke)
        else:
            # Use JSON mode for providers that don't support structured output
            import json

            schema_json = schema.model_json_schema()
            json_instruction = f"\n\nIMPORTANT: You must respond with a valid JSON object that matches this schema:\n{json.dumps(schema_json, indent=2)}\n\nRespond ONLY with the JSON object, no other text."

            enhanced_messages = list(converted_messages)
            enhanced_messages.append(SystemMessage(content=json_instruction))

            def _invoke_json() -> T:
                response = chat_model.invoke(enhanced_messages)
                content = response.content

                if "```json" in content:
                    start = content.find("```json") + 7
                    end = content.find("```", start)
                    content = content[start:end].strip()
                elif "```" in content:
                    start = content.find("```") + 3
                    end = content.find("```", start)
                    content = content[start:end].strip()

                data = json.loads(content)
                return schema.model_validate(data)

            return self._retry_with_backoff(_invoke_json)


# Convenience function for quick usage
def get_llm_client(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
) -> LLMClient:
    """
    Get an LLM client instance with default settings.

    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay for exponential backoff.
        max_delay: Maximum delay between retries.

    Returns:
        LLMClient: A configured LLM client instance.
    """
    return LLMClient(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
    )
