"""Gemini LLM provider implementation."""

from typing import List
from pathlib import Path
from io import BytesIO
from PIL import Image
from google import genai
from google.genai.types import Part, GenerateContentConfig

from llm_providers.base_provider import BaseLLMProvider, LLMResponse
from utils.logger import get_logger

logger = get_logger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Gemini provider using google-genai SDK."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash-exp",
        temperature: float = 0.0,
        timeout: int = 300,  # 5 minutes timeout
        max_image_size: int = 1024,  # Max image dimension
        rate_limit_delay: float = 1.0
    ):
        """Initialize Gemini provider.

        Args:
            api_key: Gemini API key
            model: Model name (default: gemini-2.0-flash-exp)
            temperature: Sampling temperature
            timeout: Request timeout in seconds
            max_image_size: Maximum image dimension (width/height) in pixels
            rate_limit_delay: Delay in seconds after each LLM call
        """
        super().__init__(model, temperature, rate_limit_delay)

        # Initialize Gemini client
        self.client = genai.Client(api_key=api_key)
        self.timeout = timeout
        self.max_image_size = max_image_size

        logger.info(f"已初始化 Gemini 提供商，使用模型 {model}")
        logger.info(f"超时设置: {timeout}秒, 最大图片尺寸: {max_image_size}px")

    def _resize_image(self, image_data: bytes) -> bytes:
        """Resize image if it's too large.

        Args:
            image_data: Original image bytes

        Returns:
            Resized image bytes
        """
        try:
            img = Image.open(BytesIO(image_data))
            original_format = img.format or 'PNG'
            
            # Check if resize is needed
            if max(img.size) <= self.max_image_size:
                return image_data
            
            # Calculate new size maintaining aspect ratio
            ratio = self.max_image_size / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            
            # Resize image
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert RGBA to RGB if saving as JPEG
            if img.mode == 'RGBA' and original_format == 'JPEG':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
                img = background
            
            # Save to bytes
            output = BytesIO()
            # Use PNG for RGBA images, JPEG for RGB
            if img.mode == 'RGBA':
                img.save(output, format='PNG', optimize=True)
            else:
                img.save(output, format='JPEG', quality=85, optimize=True)
            
            resized_data = output.getvalue()
            logger.debug(f"压缩图片: {len(image_data)} -> {len(resized_data)} bytes")
            
            return resized_data
            
        except Exception as e:
            logger.warning(f"图片压缩失败: {e}，使用原图")
            return image_data

    def _invoke_impl(self, prompt: str) -> LLMResponse:
        """Send a text prompt to Gemini.

        Args:
            prompt: Text prompt

        Returns:
            LLMResponse object
        """
        logger.debug(f"Invoking Gemini with prompt length: {len(prompt)}")

        # 打印提示词
        print("\n" + "="*80)
        print("【发送给 Gemini 的提示词】")
        print("="*80)
        print(prompt)
        print("="*80 + "\n")

        config = GenerateContentConfig(
            temperature=self.temperature,
            response_modalities=["TEXT"],
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config
        )

        # 打印返回结果
        print("\n" + "="*80)
        print("【Gemini 返回的结果】")
        print("="*80)
        print(response.text)
        print("="*80 + "\n")

        return LLMResponse(
            content=response.text,
            raw_response=response,
            model=self.model,
            provider=self.provider_name
        )

    def _invoke_with_images_impl(
        self,
        prompt: str,
        image_paths: List[str],
        max_images_per_request: int = 5
    ) -> LLMResponse:
        """Send a prompt with images to Gemini (multimodal).

        Args:
            prompt: Text prompt
            image_paths: List of paths to images
            max_images_per_request: Maximum number of images per request (to avoid timeout)

        Returns:
            LLMResponse object
        """
        logger.info(
            f"调用 Gemini 多模态，包含 {len(image_paths)} 张图片"
        )

        # Limit number of images to avoid timeout
        if len(image_paths) > max_images_per_request:
            logger.warning(
                f"图片数量 ({len(image_paths)}) 超过单次请求限制 ({max_images_per_request})，"
                f"将只使用前 {max_images_per_request} 张"
            )
            image_paths = image_paths[:max_images_per_request]

        # Build multimodal content
        parts = []

        # Add text prompt
        parts.append(prompt)

        # Add images with compression
        total_size = 0
        for idx, img_path in enumerate(image_paths):
            img_path_obj = Path(img_path)
            if not img_path_obj.exists():
                logger.warning(f"图片未找到: {img_path}，跳过")
                continue

            try:
                # Read and compress image data
                with open(img_path, 'rb') as f:
                    image_data = f.read()
                
                # Resize if needed
                image_data = self._resize_image(image_data)
                total_size += len(image_data)

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
                
                logger.debug(f"已添加图片 {idx}: {img_path_obj.name} ({len(image_data)} bytes)")
                
            except Exception as e:
                logger.warning(f"处理图片失败 {img_path}: {e}，跳过")
                continue

        logger.info(f"总共上传 {len([p for p in parts if isinstance(p, Part)])} 张图片，总大小: {total_size / 1024 / 1024:.2f} MB")

        # 打印多模态提示词
        print("\n" + "="*80)
        print("【发送给 Gemini 的多模态提示词】")
        print("="*80)
        print(f"文本内容: {prompt}")
        print(f"\n附带图片: {len([p for p in parts if isinstance(p, Part)])} 张")
        for idx, img_path in enumerate(image_paths[:len([p for p in parts if isinstance(p, Part)])]):
            print(f"  - 图片 {idx}: {Path(img_path).name}")
        print("="*80 + "\n")

        # Generate response with config
        config = GenerateContentConfig(
            temperature=self.temperature,
            response_modalities=["TEXT"],
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=parts,
                config=config
            )

            # 打印返回结果
            print("\n" + "="*80)
            print("【Gemini 多模态返回的结果】")
            print("="*80)
            print(response.text)
            print("="*80 + "\n")

            return LLMResponse(
                content=response.text,
                raw_response=response,
                model=self.model,
                provider=self.provider_name
            )
            
        except Exception as e:
            logger.error(f"Gemini 多模态调用失败: {e}")
            logger.info("建议: 1) 检查网络连接 2) 减少图片数量 3) 降低图片分辨率")
            raise

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def supports_multimodal(self) -> bool:
        # All Gemini models support multimodal
        return True
