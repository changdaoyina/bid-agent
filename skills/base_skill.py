"""Base class for all skills."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from utils.logger import get_logger


class BaseSkill(ABC):
    """Abstract base class for all skills."""

    def __init__(self, name: str):
        """Initialize the skill.

        Args:
            name: Name of the skill
        """
        self.name = name
        self.logger = get_logger(f"skill.{name}")

    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the skill's main functionality.

        Args:
            state: Current agent state

        Returns:
            Updated agent state
        """
        pass

    def validate_input(self, state: Dict[str, Any]) -> bool:
        """Validate that the state has required inputs for this skill.

        Args:
            state: Current agent state

        Returns:
            True if valid, False otherwise
        """
        return True

    def handle_error(self, error: Exception, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle errors that occur during execution.

        Args:
            error: The exception that occurred
            state: Current agent state

        Returns:
            Updated state with error information
        """
        error_msg = f"{self.name} failed: {str(error)}"
        self.logger.error(error_msg)

        state["error"] = error_msg
        state["current_step"] = "error"
        return state

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the skill with validation and error handling.

        Args:
            state: Current agent state

        Returns:
            Updated agent state
        """
        self.logger.info(f"Running skill: {self.name}")

        # Validate input
        if not self.validate_input(state):
            return self.handle_error(
                ValueError(f"Invalid input state for {self.name}"),
                state
            )

        # Execute with error handling
        try:
            return self.execute(state)
        except Exception as e:
            return self.handle_error(e, state)


if __name__ == "__main__":
    # Test with a simple implementation
    class TestSkill(BaseSkill):
        def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
            state["test_executed"] = True
            return state

    skill = TestSkill("test")
    result = skill.run({"messages": []})
    print(f"Test skill result: {result}")
