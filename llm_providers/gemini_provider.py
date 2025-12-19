"""Gemini LLM provider implementation."""

from typing import List
from pathlib import Path
from google import genai
from google.genai.types import Part

from llm_providers.base_provider import BaseLLMProvider, LLMResponse
from utils.logger import get_logger

logger = get_logger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Gemini provider using google-genai SDK."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash-exp",
        temperature: float = 0.0
    ):
        """Initialize Gemini provider.

        Args:
            api_key: Gemini API key
            model: Model name (default: gemini-2.0-flash-exp)
            temperature: Sampling temperature
        """
        super().__init__(model, temperature)

        # Initialize Gemini client
        self.client = genai.Client(api_key=api_key)

        logger.info(f"已初始化 Gemini 提供商，使用模型 {model}")

    def invoke(self, prompt: str) -> LLMResponse:
        """Send a text prompt to Gemini.

        Args:
            prompt: Text prompt

        Returns:
            LLMResponse object
        """
        logger.debug(f"Invoking Gemini with prompt length: {len(prompt)}")

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "temperature": self.temperature,
            }
        )

        return LLMResponse(
            content=response.text,
            raw_response=response,
            model=self.model,
            provider=self.provider_name
        )

    def invoke_with_images(
        self,
        prompt: str,
        image_paths: List[str]
    ) -> LLMResponse:
        """Send a prompt with images to Gemini (multimodal).

        Args:
            prompt: Text prompt
            image_paths: List of paths to images

        Returns:
            LLMResponse object
        """
        logger.info(
            f"调用 Gemini 多模态，包含 {len(image_paths)} 张图片"
        )

        # Build multimodal content
        parts = []

        # Add text prompt
        parts.append(Part(text=prompt))

        # Add images
        for img_path in image_paths:
            img_path_obj = Path(img_path)
            if not img_path_obj.exists():
                logger.warning(f"图片未找到: {img_path}，跳过")
                continue

            # Read image data
            with open(img_path, 'rb') as f:
                image_data = f.read()

            # Determine MIME type
            ext = img_path_obj.suffix.lower()
            mime_type = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }.get(ext, 'image/jpeg')

            # Add image part
            parts.append(Part(
                inline_data={
                    'mime_type': mime_type,
                    'data': image_data
                }
            ))

        # Generate response
        response = self.client.models.generate_content(
            model=self.model,
            contents=parts,
            config={
                "temperature": self.temperature,
            }
        )

        return LLMResponse(
            content=response.text,
            raw_response=response,
            model=self.model,
            provider=self.provider_name
        )

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def supports_multimodal(self) -> bool:
        # All Gemini models support multimodal
        return True
