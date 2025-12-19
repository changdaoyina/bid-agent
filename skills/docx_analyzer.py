"""Skill for analyzing DOCX document structure."""

from pathlib import Path
from typing import Any, Dict

from skills.base_skill import BaseSkill
from utils.docx_utils import analyze_document_structure, get_document_summary


class DocxAnalyzerSkill(BaseSkill):
    """Analyzes the structure of a target DOCX document."""

    def __init__(self):
        super().__init__("DocxAnalyzer")

    def validate_input(self, state: Dict[str, Any]) -> bool:
        """Validate that target_path is provided."""
        if "target_path" not in state:
            self.logger.error("状态中未找到 target_path")
            return False

        target_path = Path(state["target_path"])
        if not target_path.exists():
            self.logger.error(f"目标文档不存在: {target_path}")
            return False

        return True

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the target document structure.

        Args:
            state: Must contain 'target_path'

        Returns:
            State updated with 'target_structure' dict
        """
        target_path = Path(state["target_path"])

        self.logger.info(f"分析文档结构: {target_path}")

        # Analyze document
        structure = analyze_document_structure(target_path)

        # Convert to dict for state storage
        structure_dict = {
            "total_paragraphs": structure.total_paragraphs,
            "paragraphs": [
                {
                    "index": p.index,
                    "text": p.text,
                    "style": p.style,
                    "is_heading": p.is_heading,
                    "heading_level": p.heading_level
                }
                for p in structure.paragraphs
            ],
            "headings": [
                {
                    "index": h.index,
                    "text": h.text,
                    "style": h.style,
                    "heading_level": h.heading_level
                }
                for h in structure.headings
            ],
            "empty_paragraphs": structure.empty_paragraphs,
            "summary": get_document_summary(structure)
        }

        # Update state
        state["target_structure"] = structure_dict
        state["current_step"] = "target_analyzed"

        self.logger.info(
            f"已分析文档: {structure.total_paragraphs} 个段落, "
            f"{len(structure.headings)} 个标题"
        )

        return state


if __name__ == "__main__":
    # Test the skill
    import config

    test_state = {
        "target_path": str(config.TARGET_DOC_PATH),
        "messages": []
    }

    skill = DocxAnalyzerSkill()
    result = skill.run(test_state)

    if "target_structure" in result:
        print(result["target_structure"]["summary"])
