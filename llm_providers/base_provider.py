"""Base LLM provider interface."""

import time
from abc import ABC, abstractmethod
from typing import Any, List, Optional
from pydantic import BaseModel


class LLMMessage(BaseModel):
    """Unified message format for LLM communication."""
    role: str  # "user", "assistant", "system"
    content: str


class LLMResponse(BaseModel):
    """Unified response format from LLM."""
    content: str
    raw_response: Optional[Any] = None
    model: str
    provider: str


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, model: str, temperature: float = 0.0, rate_limit_delay: float = 1.0):
        """Initialize the LLM provider.

        Args:
            model: Model identifier
            temperature: Sampling temperature (0-1)
            rate_limit_delay: Delay in seconds after each LLM call
        """
        self.model = model
        self.temperature = temperature
        self.rate_limit_delay = rate_limit_delay
        self._last_call_time = 0.0

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting by waiting if necessary."""
        if self._last_call_time > 0:
            elapsed = time.time() - self._last_call_time
            if elapsed < self.rate_limit_delay:
                wait_time = self.rate_limit_delay - elapsed
                time.sleep(wait_time)
        self._last_call_time = time.time()

    @abstractmethod
    def _invoke_impl(self, prompt: str) -> LLMResponse:
        """Internal implementation of invoke.

        Args:
            prompt: Text prompt to send

        Returns:
            LLMResponse object
        """
        pass

    def invoke(self, prompt: str) -> LLMResponse:
        """Send a prompt and get a response.

        Args:
            prompt: Text prompt to send

        Returns:
            LLMResponse object
        """
        response = self._invoke_impl(prompt)
        self._apply_rate_limit()
        return response

    @abstractmethod
    def _invoke_with_images_impl(
        self,
        prompt: str,
        image_paths: List[str]
    ) -> LLMResponse:
        """Internal implementation of invoke_with_images.

        Args:
            prompt: Text prompt
            image_paths: List of paths to images

        Returns:
            LLMResponse object
        """
        pass

    def invoke_with_images(
        self,
        prompt: str,
        image_paths: List[str]
    ) -> LLMResponse:
        """Send a prompt with images (multimodal).

        Args:
            prompt: Text prompt
            image_paths: List of paths to images

        Returns:
            LLMResponse object
        """
        response = self._invoke_with_images_impl(prompt, image_paths)
        self._apply_rate_limit()
        return response

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name."""
        pass

    @property
    @abstractmethod
    def supports_multimodal(self) -> bool:
        """Whether this provider supports image inputs."""
        pass
