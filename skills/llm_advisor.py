"""Skill for using LLM to decide image insertion positions."""

import json
from typing import Any, Dict, List

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

import config
from skills.base_skill import BaseSkill


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

    def __init__(self):
        super().__init__("LLMAdvisor")

        # Initialize GLM (uses OpenAI-compatible API)
        self.llm = ChatOpenAI(
            model=config.GLM_MODEL,
            temperature=config.LLM_TEMPERATURE,
            openai_api_key=config.GLM_API_KEY,
            openai_api_base=config.GLM_BASE_URL
        )

    def validate_input(self, state: Dict[str, Any]) -> bool:
        """Validate that required data is in state."""
        required_keys = ["target_structure", "extracted_images"]

        for key in required_keys:
            if key not in state:
                self.logger.error(f"{key} not found in state")
                return False

        if not state.get("extracted_images"):
            self.logger.error("No images to insert")
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
            self.logger.error(f"Failed to parse JSON: {e}")
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
        self.logger.info("Querying LLM for insertion advice")

        # Build prompt
        prompt = self.build_prompt(state)
        self.logger.debug(f"Prompt:\n{prompt}")

        # Query LLM
        try:
            response = self.llm.invoke(prompt)
            response_text = response.content

            self.logger.debug(f"LLM Response:\n{response_text}")

            # Parse response
            insertion_plan = self.parse_llm_response(response_text)

            # Validate plan
            num_images = len(state["extracted_images"])
            if len(insertion_plan) != num_images:
                self.logger.warning(
                    f"LLM suggested {len(insertion_plan)} positions "
                    f"but we have {num_images} images"
                )

            # Update state
            state["insertion_plan"] = insertion_plan
            state["current_step"] = "insertion_planned"

            self.logger.info(f"Generated insertion plan for {len(insertion_plan)} images")

            # Log the plan
            for decision in insertion_plan:
                self.logger.info(
                    f"  Image {decision['image_index']} -> "
                    f"after Para {decision['insert_after_para']}: "
                    f"{decision.get('reason', 'No reason provided')}"
                )

            return state

        except Exception as e:
            self.logger.error(f"LLM query failed: {e}")
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
