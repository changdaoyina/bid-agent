"""Skill for extracting images from DOCX documents."""

from pathlib import Path
from typing import Any, Dict

import config
from skills.base_skill import BaseSkill
from utils.docx_utils import extract_images_from_docx


class DocxExtractorSkill(BaseSkill):
    """Extracts images from a source DOCX document."""

    def __init__(self):
        super().__init__("DocxExtractor")

    def validate_input(self, state: Dict[str, Any]) -> bool:
        """Validate that source_path is provided."""
        if "source_path" not in state:
            self.logger.error("状态中未找到 source_path")
            return False

        source_path = Path(state["source_path"])
        if not source_path.exists():
            self.logger.error(f"源文档不存在: {source_path}")
            return False

        return True

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract images from the source document.

        Args:
            state: Must contain 'source_path'

        Returns:
            State updated with 'extracted_images' list
        """
        source_path = Path(state["source_path"])
        output_dir = config.TEMP_DIR

        self.logger.info(f"从 {source_path} 提取图片")

        # Extract images
        images = extract_images_from_docx(source_path, output_dir)

        # Convert ImageInfo objects to dictionaries
        images_dict = [
            {
                "index": img.index,
                "filename": img.filename,
                "temp_path": str(img.temp_path),
                "size_bytes": img.size_bytes,
                "width": img.width,
                "height": img.height,
                "content_type": img.content_type
            }
            for img in images
        ]

        # Update state
        state["extracted_images"] = images_dict
        state["current_step"] = "images_extracted"

        self.logger.info(f"成功提取 {len(images)} 张图片")

        return state


if __name__ == "__main__":
    # Test the skill
    import config

    test_state = {
        "source_path": str(config.SOURCE_DOC_PATH),
        "messages": []
    }

    skill = DocxExtractorSkill()
    result = skill.run(test_state)

    print(f"Extracted {len(result.get('extracted_images', []))} images")
    for img in result.get('extracted_images', []):
        print(f"  - {img['filename']}: {img['size_bytes']} bytes")
