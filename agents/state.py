"""State definition for the bid agent."""

from typing import TypedDict, Annotated, List, Any, Optional
from langgraph.graph.message import add_messages


class BidAgentState(TypedDict):
    """State for the bid document processing agent.

    This state is passed between nodes in the LangGraph workflow.
    """

    # Messages for LangChain conversation
    messages: Annotated[list, add_messages]

    # Document paths
    source_path: str  # Path to source DOCX with images
    target_path: str  # Path to target DOCX to insert into

    # Extracted data
    extracted_images: List[dict]  # List of image info dicts

    # Document analysis
    target_structure: dict  # Structure analysis of target document

    # LLM decision
    insertion_plan: List[dict]  # Plan for where to insert each image

    # Execution state
    current_step: str  # Current step in the workflow
    error: Optional[str]  # Error message if any
    completed: bool  # Whether the workflow is complete

    # Output
    output_path: Optional[str]  # Path to the final output document
    backup_path: Optional[str]  # Path to the backup of original target


def create_initial_state(source_path: str, target_path: str) -> BidAgentState:
    """Create an initial state for the agent.

    Args:
        source_path: Path to source document with images
        target_path: Path to target document to modify

    Returns:
        Initial BidAgentState
    """
    return BidAgentState(
        messages=[],
        source_path=source_path,
        target_path=target_path,
        extracted_images=[],
        target_structure={},
        insertion_plan=[],
        current_step="initialized",
        error=None,
        completed=False,
        output_path=None,
        backup_path=None
    )


if __name__ == "__main__":
    # Test state creation
    import config

    state = create_initial_state(
        str(config.SOURCE_DOC_PATH),
        str(config.TARGET_DOC_PATH)
    )

    print("Initial State:")
    for key, value in state.items():
        if key != "messages":  # Skip messages for cleaner output
            print(f"  {key}: {value}")
