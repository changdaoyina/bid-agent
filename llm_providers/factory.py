"""Factory for creating LLM providers."""

from typing import Optional
import config
from llm_providers.base_provider import BaseLLMProvider
from llm_providers.glm_provider import GLMProvider
from llm_providers.gemini_provider import GeminiProvider
from utils.logger import get_logger

logger = get_logger(__name__)


class LLMProviderFactory:
    """Factory for creating LLM provider instances."""

    @staticmethod
    def create_provider(
        provider_name: Optional[str] = None
    ) -> BaseLLMProvider:
        """Create an LLM provider based on configuration.

        Args:
            provider_name: Override provider from config (default: use config.LLM_PROVIDER)

        Returns:
            BaseLLMProvider instance

        Raises:
            ValueError: If provider is not supported or not configured
        """
        provider = provider_name or config.LLM_PROVIDER
        provider = provider.lower()

        logger.info(f"创建 LLM 提供商: {provider}")

        if provider == "glm":
            if not config.GLM_API_KEY:
                raise ValueError("GLM_API_KEY not set in configuration")

            return GLMProvider(
                api_key=config.GLM_API_KEY,
                base_url=config.GLM_BASE_URL,
                model=config.GLM_MODEL,
                temperature=config.LLM_TEMPERATURE
            )

        elif provider == "gemini":
            if not config.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not set in configuration")

            return GeminiProvider(
                api_key=config.GEMINI_API_KEY,
                model=config.GEMINI_MODEL,
                temperature=config.LLM_TEMPERATURE
            )

        else:
            raise ValueError(
                f"Unsupported LLM provider: {provider}. "
                f"Supported providers: glm, gemini"
            )

    @staticmethod
    def get_available_providers() -> list[str]:
        """Get list of available providers based on config.

        Returns:
            List of provider names that have API keys configured
        """
        providers = []

        if config.GLM_API_KEY:
            providers.append("glm")

        if config.GEMINI_API_KEY:
            providers.append("gemini")

        return providers


def create_llm_provider(provider_name: Optional[str] = None) -> BaseLLMProvider:
    """Convenience function to create LLM provider.

    Args:
        provider_name: Override provider from config

    Returns:
        BaseLLMProvider instance
    """
    return LLMProviderFactory.create_provider(provider_name)
