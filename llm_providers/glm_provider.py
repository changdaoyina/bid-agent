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
        temperature: float = 0.0,
        rate_limit_delay: float = 1.0
    ):
        """Initialize GLM provider.

        Args:
            api_key: GLM API key
            base_url: GLM API base URL
            model: Model name (default: GLM-4.6)
            temperature: Sampling temperature
            rate_limit_delay: Delay in seconds after each LLM call
        """
        super().__init__(model, temperature, rate_limit_delay)

        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=api_key,
            openai_api_base=base_url
        )

        logger.info(f"已初始化 GLM 提供商，使用模型 {model}")

    def _invoke_impl(self, prompt: str) -> LLMResponse:
        """Send a text prompt to GLM.

        Args:
            prompt: Text prompt

        Returns:
            LLMResponse object
        """
        logger.debug(f"Invoking GLM with prompt length: {len(prompt)}")

        # 打印提示词
        print("\n" + "="*80)
        print("【发送给 GLM 的提示词】")
        print("="*80)
        print(prompt)
        print("="*80 + "\n")

        response = self.llm.invoke(prompt)

        # 打印返回结果
        print("\n" + "="*80)
        print("【GLM 返回的结果】")
        print("="*80)
        print(response.content)
        print("="*80 + "\n")

        return LLMResponse(
            content=response.content,
            raw_response=response,
            model=self.model,
            provider=self.provider_name
        )

    def _invoke_with_images_impl(
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
            f"GLM 多模态未实现，对 {len(image_paths)} 张图片使用纯文本模式"
        )
        
        # 打印多模态请求信息（即使回退到纯文本模式）
        print("\n" + "="*80)
        print("【发送给 GLM 的多模态请求（回退到纯文本模式）】")
        print("="*80)
        print(f"文本内容: {prompt}")
        print(f"\n尝试附带图片: {len(image_paths)} 张（将被忽略）")
        print("="*80 + "\n")
        
        return self._invoke_impl(prompt)

    @property
    def provider_name(self) -> str:
        return "glm"

    @property
    def supports_multimodal(self) -> bool:
        # GLM-4V supports images, but not GLM-4
        return "4v" in self.model.lower() or "vision" in self.model.lower()
