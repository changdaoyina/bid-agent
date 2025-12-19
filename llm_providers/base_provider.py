"""Base LLM provider interface."""

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

    def __init__(self, model: str, temperature: float = 0.0):
        """Initialize the LLM provider.

        Args:
            model: Model identifier
            temperature: Sampling temperature (0-1)
        """
        self.model = model
        self.temperature = temperature

    @abstractmethod
    def invoke(self, prompt: str) -> LLMResponse:
        """Send a prompt and get a response.

        Args:
            prompt: Text prompt to send

        Returns:
            LLMResponse object
        """
        pass

    @abstractmethod
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
        pass

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
