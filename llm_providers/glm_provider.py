"""GLM (智谱AI) LLM provider implementation."""

from typing import List
from langchain_openai import ChatOpenAI

from llm_providers.base_provider import BaseLLMProvider, LLMResponse
from utils.logger import get_logger

logger = get_logger(__name__)


class GLMProvider(BaseLLMProvider):
    """GLM provider using LangChain's ChatOpenAI adapter."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str = "GLM-4.6",
        temperature: float = 0.0
    ):
        """Initialize GLM provider.

        Args:
            api_key: GLM API key
            base_url: GLM API base URL
            model: Model name (default: GLM-4.6)
            temperature: Sampling temperature
        """
        super().__init__(model, temperature)

        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=api_key,
            openai_api_base=base_url
        )

        logger.info(f"Initialized GLM provider with model {model}")

    def invoke(self, prompt: str) -> LLMResponse:
        """Send a text prompt to GLM.

        Args:
            prompt: Text prompt

        Returns:
            LLMResponse object
        """
        logger.debug(f"Invoking GLM with prompt length: {len(prompt)}")

        response = self.llm.invoke(prompt)

        return LLMResponse(
            content=response.content,
            raw_response=response,
            model=self.model,
            provider=self.provider_name
        )

    def invoke_with_images(
        self,
        prompt: str,
        image_paths: List[str]
    ) -> LLMResponse:
        """GLM multimodal support (if available).

        Note: GLM-4V supports images, but GLM-4 does not.
        For now, this falls back to text-only.

        Args:
            prompt: Text prompt
            image_paths: Image paths (ignored for GLM-4)

        Returns:
            LLMResponse object
        """
        logger.warning(
            f"GLM multimodal not implemented, using text-only for {len(image_paths)} images"
        )
        return self.invoke(prompt)

    @property
    def provider_name(self) -> str:
        return "glm"

    @property
    def supports_multimodal(self) -> bool:
        # GLM-4V supports images, but not GLM-4
        return "4v" in self.model.lower() or "vision" in self.model.lower()
