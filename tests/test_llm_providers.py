"""Tests for LLM providers."""

import pytest
from pathlib import Path
from llm_providers import create_llm_provider, GLMProvider, GeminiProvider
import config


class TestLLMProviders:
    """Test LLM provider implementations."""

    def test_glm_provider_creation(self):
        """Test GLM provider can be created."""
        if not config.GLM_API_KEY:
            pytest.skip("GLM_API_KEY not configured")

        provider = GLMProvider(
            api_key=config.GLM_API_KEY,
            base_url=config.GLM_BASE_URL,
            model=config.GLM_MODEL
        )

        assert provider.provider_name == "glm"
        assert provider.model == config.GLM_MODEL

    def test_gemini_provider_creation(self):
        """Test Gemini provider can be created."""
        if not config.GEMINI_API_KEY:
            pytest.skip("GEMINI_API_KEY not configured")

        provider = GeminiProvider(
            api_key=config.GEMINI_API_KEY,
            model=config.GEMINI_MODEL
        )

        assert provider.provider_name == "gemini"
        assert provider.model == config.GEMINI_MODEL
        assert provider.supports_multimodal is True

    def test_factory_creates_correct_provider(self):
        """Test factory creates the right provider."""
        original_provider = config.LLM_PROVIDER

        try:
            # Test GLM
            if config.GLM_API_KEY:
                config.LLM_PROVIDER = "glm"
                provider = create_llm_provider()
                assert isinstance(provider, GLMProvider)

            # Test Gemini
            if config.GEMINI_API_KEY:
                config.LLM_PROVIDER = "gemini"
                provider = create_llm_provider()
                assert isinstance(provider, GeminiProvider)

        finally:
            config.LLM_PROVIDER = original_provider

    def test_glm_text_invocation(self):
        """Test GLM can handle text prompts."""
        if not config.GLM_API_KEY:
            pytest.skip("GLM_API_KEY not configured")

        provider = create_llm_provider("glm")
        response = provider.invoke("Say 'test' in one word")

        assert response.content
        assert response.provider == "glm"
        assert response.model == config.GLM_MODEL

    def test_gemini_text_invocation(self):
        """Test Gemini can handle text prompts."""
        if not config.GEMINI_API_KEY:
            pytest.skip("GEMINI_API_KEY not configured")

        provider = create_llm_provider("gemini")
        response = provider.invoke("Say 'test' in one word")

        assert response.content
        assert response.provider == "gemini"
        assert response.model == config.GEMINI_MODEL
