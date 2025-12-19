"""Skill for using LLM to decide image insertion positions."""

import json
from typing import Any, Dict, List
from pathlib import Path

from pydantic import BaseModel, Field

import config
from skills.base_skill import BaseSkill
from llm_providers import create_llm_provider, BaseLLMProvider


class InsertionDecision(BaseModel):
    """Model for a single image insertion decision."""
    image_index: int = Field(description="Index of the image (0-based)")
    insert_after_para: int = Field(description="Paragraph index to insert after")
    reason: str = Field(description="Reasoning for this insertion position")


class InsertionPlan(BaseModel):
    """Model for the complete insertion plan."""
    decisions: List[InsertionDecision] = Field(description="List of insertion decisions")


class LLMAdvisorSkill(BaseSkill):
    """Uses LLM to analyze document structure and suggest image insertion positions."""

    def __init__(self, provider: BaseLLMProvider = None):
        super().__init__("LLMAdvisor")

        # Use provided provider or create one from config
        self.llm = provider or create_llm_provider()

        self.logger.info(
            f"已初始化 {self.llm.provider_name} 提供商 "
            f"(模型: {self.llm.model}, 多模态: {self.llm.supports_multimodal})"
        )

    def validate_input(self, state: Dict[str, Any]) -> bool:
        """Validate that required data is in state."""
        required_keys = ["target_structure", "extracted_images"]

        for key in required_keys:
            if key not in state:
                self.logger.error(f"状态中未找到 {key}")
                return False

        if not state.get("extracted_images"):
            self.logger.error("没有需要插入的图片")
            return False

        return True

    def build_prompt(self, state: Dict[str, Any]) -> str:
        """Build the prompt for LLM.

        Args:
            state: Agent state with target_structure and extracted_images

        Returns:
            Formatted prompt string
        """
        structure = state["target_structure"]
        images = state["extracted_images"]

        # Build paragraph list
        para_descriptions = []
        for para in structure["paragraphs"]:
            prefix = f"Para {para['index']}"
            if para["is_heading"]:
                prefix += f" ({para['style']})"
            else:
                prefix += " (Normal)"

            text_preview = para["text"][:60] if para["text"] else "[empty]"
            para_descriptions.append(f"  - {prefix}: {text_preview}")

        paragraphs_text = "\n".join(para_descriptions)

        prompt = f"""You are a professional document formatting assistant. You need to insert {len(images)} project contract images into a bidding document.

Target Document Structure:
Total Paragraphs: {structure['total_paragraphs']}
Total Headings: {len(structure['headings'])}
Empty Paragraphs: {len(structure['empty_paragraphs'])}

Paragraph Details:
{paragraphs_text}

Source Images:
- Total: {len(images)} images from a contract document
- Images are contract pages, screenshots, or project evidence

Task: Analyze the document structure and suggest the best insertion position for each image.

Requirements:
1. Images should be inserted after relevant section headings
2. Utilize empty paragraphs (indices: {structure['empty_paragraphs']}) when possible
3. Distribute images reasonably, 1-2 images per section
4. Avoid inserting in the middle of important headings
5. Consider the logical flow of the document

Return a JSON array with this format:
[
  {{
    "image_index": 0,
    "insert_after_para": 6,
    "reason": "Insert after the project section heading"
  }},
  ...
]

Provide your insertion plan:"""

        return prompt

    def build_multimodal_prompt(self, state: Dict[str, Any]) -> str:
        """Build an enhanced prompt for multimodal LLMs with image understanding.

        Args:
            state: Agent state with target_structure and extracted_images

        Returns:
            Formatted prompt string for multimodal analysis
        """
        structure = state["target_structure"]
        images = state["extracted_images"]

        # Build paragraph list
        para_descriptions = []
        for para in structure["paragraphs"]:
            prefix = f"Para {para['index']}"
            if para["is_heading"]:
                prefix += f" ({para['style']})"
            else:
                prefix += " (Normal)"

            text_preview = para["text"][:60] if para["text"] else "[empty]"
            para_descriptions.append(f"  - {prefix}: {text_preview}")

        paragraphs_text = "\n".join(para_descriptions)

        prompt = f"""You are a professional document formatting assistant with image understanding capabilities.

I will show you {len(images)} images from a project contract that need to be inserted into a bidding document.

Target Document Structure:
Total Paragraphs: {structure['total_paragraphs']}
Total Headings: {len(structure['headings'])}
Empty Paragraphs: {len(structure['empty_paragraphs'])}

Paragraph Details:
{paragraphs_text}

Task: Analyze the provided images AND the document structure to suggest the best insertion position for each image.

You will see {len(images)} images below. Use your vision capabilities to:
1. Understand what each image shows (contract pages, screenshots, diagrams, etc.)
2. Identify the most relevant section in the document for each image
3. Consider the logical flow and context

Requirements:
1. Match image content to relevant section headings when possible
2. Utilize empty paragraphs (indices: {structure['empty_paragraphs']}) when appropriate
3. Distribute images reasonably, 1-2 images per section
4. Avoid inserting in the middle of important content
5. Maintain the logical narrative flow

Return a JSON array with this exact format:
[
  {{
    "image_index": 0,
    "insert_after_para": 6,
    "reason": "This contract signature page fits well after the agreements section"
  }},
  ...
]

Analyze the images below and provide your insertion plan:"""

        return prompt

    def parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into insertion plan.

        Args:
            response: JSON string from LLM

        Returns:
            List of insertion decisions
        """
        try:
            # Try to parse as JSON
            data = json.loads(response)

            # Validate structure
            if not isinstance(data, list):
                raise ValueError("Response must be a JSON array")

            insertion_plan = []
            for item in data:
                if not all(k in item for k in ["image_index", "insert_after_para"]):
                    raise ValueError(f"Missing required keys in: {item}")

                insertion_plan.append({
                    "image_index": item["image_index"],
                    "insert_after_para": item["insert_after_para"],
                    "reason": item.get("reason", "")
                })

            return insertion_plan

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 解析失败: {e}")
            # Fallback: try to extract JSON from markdown code block
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
                return self.parse_llm_response(json_str)
            raise

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to decide image insertion positions.

        Args:
            state: Must contain 'target_structure' and 'extracted_images'

        Returns:
            State updated with 'insertion_plan' list
        """
        self.logger.info("查询 LLM 获取插入建议")

        # Check if we should use multimodal features
        use_multimodal = (
            config.ENABLE_MULTIMODAL and
            self.llm.supports_multimodal
        )

        if use_multimodal:
            self.logger.info("使用多模态分析，包含图片理解")
            prompt = self.build_multimodal_prompt(state)

            # Get image paths
            image_paths = [
                img["temp_path"]
                for img in state["extracted_images"]
                if Path(img["temp_path"]).exists()
            ]

            self.logger.info(f"向 LLM 发送 {len(image_paths)} 张图片")

            try:
                response = self.llm.invoke_with_images(prompt, image_paths)
                response_text = response.content
            except Exception as e:
                self.logger.warning(
                    f"多模态调用失败: {e}。回退到纯文本模式。"
                )
                use_multimodal = False

        if not use_multimodal:
            self.logger.info("使用纯文本分析")
            prompt = self.build_prompt(state)
            response = self.llm.invoke(prompt)
            response_text = response.content

        self.logger.debug(f"Prompt:\n{prompt}")
        self.logger.debug(f"LLM Response:\n{response_text}")

        # Parse response
        try:
            insertion_plan = self.parse_llm_response(response_text)

            # Validate plan
            num_images = len(state["extracted_images"])
            if len(insertion_plan) != num_images:
                self.logger.warning(
                    f"LLM 建议 {len(insertion_plan)} 个位置，"
                    f"但我们有 {num_images} 张图片"
                )

            # Update state
            state["insertion_plan"] = insertion_plan
            state["current_step"] = "insertion_planned"
            state["used_multimodal"] = use_multimodal

            self.logger.info(
                f"为 {len(insertion_plan)} 张图片生成插入计划 "
                f"(多模态: {use_multimodal})"
            )

            # Log the plan
            for decision in insertion_plan:
                self.logger.info(
                    f"  图片 {decision['image_index']} -> "
                    f"插入到段落 {decision['insert_after_para']} 之后: "
                    f"{decision.get('reason', '未提供原因')}"
                )

            return state

        except Exception as e:
            self.logger.error(f"LLM 查询失败: {e}")
            raise


if __name__ == "__main__":
    # Test the skill
    import config
    from skills.docx_extractor import DocxExtractorSkill
    from skills.docx_analyzer import DocxAnalyzerSkill

    # Prepare state
    test_state = {
        "source_path": str(config.SOURCE_DOC_PATH),
        "target_path": str(config.TARGET_DOC_PATH),
        "messages": []
    }

    # Extract images
    extractor = DocxExtractorSkill()
    test_state = extractor.run(test_state)

    # Analyze target
    analyzer = DocxAnalyzerSkill()
    test_state = analyzer.run(test_state)

    # Get LLM advice
    advisor = LLMAdvisorSkill()
    result = advisor.run(test_state)

    print("\nInsertion Plan:")
    for decision in result.get("insertion_plan", []):
        print(f"  Image {decision['image_index']} -> Para {decision['insert_after_para']}")
