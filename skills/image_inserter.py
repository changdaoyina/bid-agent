"""Skill for inserting images into DOCX documents."""

from pathlib import Path
from typing import Any, Dict

import config
from skills.base_skill import BaseSkill
from utils.docx_utils import insert_images_batch


class ImageInserterSkill(BaseSkill):
    """Inserts images into a target document based on an insertion plan."""

    def __init__(self):
        super().__init__("ImageInserter")

    def validate_input(self, state: Dict[str, Any]) -> bool:
        """Validate that required data is in state."""
        required_keys = ["target_path", "insertion_plan", "extracted_images"]

        for key in required_keys:
            if key not in state:
                self.logger.error(f"{key} not found in state")
                return False

        if not state.get("insertion_plan"):
            self.logger.error("Insertion plan is empty")
            return False

        target_path = Path(state["target_path"])
        if not target_path.exists():
            self.logger.error(f"Target document does not exist: {target_path}")
            return False

        return True

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Insert images into the target document.

        Args:
            state: Must contain 'target_path', 'insertion_plan', 'extracted_images'

        Returns:
            State updated with 'completed' = True
        """
        target_path = Path(state["target_path"])
        insertion_plan = state["insertion_plan"]
        extracted_images = state["extracted_images"]

        self.logger.info(f"Inserting {len(insertion_plan)} images into {target_path}")

        # Build the insertion plan for insert_images_batch
        batch_plan = []
        for decision in insertion_plan:
            image_index = decision["image_index"]

            # Get the image path
            if image_index >= len(extracted_images):
                self.logger.warning(
                    f"Image index {image_index} out of range, skipping"
                )
                continue

            image_info = extracted_images[image_index]
            image_path = Path(image_info["temp_path"])

            if not image_path.exists():
                self.logger.warning(
                    f"Image file not found: {image_path}, skipping"
                )
                continue

            batch_plan.append({
                "image_path": image_path,
                "insert_after_para": decision["insert_after_para"]
            })

        # Create output path in the independent output directory
        output_dir = config.OUTPUT_DOC_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate output filename (e.g., original_name_result.docx)
        output_path = output_dir / f"{target_path.stem}_result{target_path.suffix}"

        self.logger.info(f"Saving final result to: {output_path}")

        # Insert images (using target_path as source, saving to output_path)
        insert_images_batch(
            doc_path=target_path,
            output_path=output_path,
            insertion_plan=batch_plan,
            width_inches=config.MAX_IMAGE_WIDTH_INCHES,
            alignment=config.IMAGE_ALIGNMENT
        )

        # Update state
        state["completed"] = True
        state["current_step"] = "images_inserted"
        state["output_path"] = str(output_path)
        state["backup_path"] = None  # No backup needed as we don't modify original

        self.logger.info(f"Successfully inserted {len(batch_plan)} images")
        self.logger.info(f"Output saved to: {output_path}")

        return state


if __name__ == "__main__":
    # Test the skill
    print("This skill requires a complete state from previous skills.")
    print("Run the full agent workflow to test image insertion.")
