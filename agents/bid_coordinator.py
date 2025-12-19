"""Main coordinator agent using LangGraph."""

from typing import Any, Dict

from langgraph.graph import StateGraph, END

from agents.state import BidAgentState
from skills.docx_extractor import DocxExtractorSkill
from skills.docx_analyzer import DocxAnalyzerSkill
from skills.llm_advisor import LLMAdvisorSkill
from skills.image_inserter import ImageInserterSkill
from utils.logger import get_logger

logger = get_logger(__name__)


# Initialize skills
extractor_skill = DocxExtractorSkill()
analyzer_skill = DocxAnalyzerSkill()
advisor_skill = LLMAdvisorSkill()
inserter_skill = ImageInserterSkill()


def extract_images_node(state: BidAgentState) -> BidAgentState:
    """Node 1: Extract images from source document.

    Args:
        state: Current agent state

    Returns:
        Updated state with extracted_images
    """
    logger.info("=" * 60)
    logger.info("NODE 1: Extracting images from source document")
    logger.info("=" * 60)

    return extractor_skill.run(state)


def analyze_target_node(state: BidAgentState) -> BidAgentState:
    """Node 2: Analyze target document structure.

    Args:
        state: Current agent state

    Returns:
        Updated state with target_structure
    """
    logger.info("=" * 60)
    logger.info("NODE 2: Analyzing target document structure")
    logger.info("=" * 60)

    return analyzer_skill.run(state)


def llm_decision_node(state: BidAgentState) -> BidAgentState:
    """Node 3: Use LLM to decide insertion positions.

    Args:
        state: Current agent state

    Returns:
        Updated state with insertion_plan
    """
    logger.info("=" * 60)
    logger.info("NODE 3: Using LLM to decide insertion positions")
    logger.info("=" * 60)

    return advisor_skill.run(state)


def insert_images_node(state: BidAgentState) -> BidAgentState:
    """Node 4: Insert images into target document.

    Args:
        state: Current agent state

    Returns:
        Updated state with completed=True
    """
    logger.info("=" * 60)
    logger.info("NODE 4: Inserting images into target document")
    logger.info("=" * 60)

    return inserter_skill.run(state)


def verify_result_node(state: BidAgentState) -> BidAgentState:
    """Node 5: Verify the final result.

    Args:
        state: Current agent state

    Returns:
        Final state
    """
    logger.info("=" * 60)
    logger.info("NODE 5: Verifying results")
    logger.info("=" * 60)

    if state.get("error"):
        logger.error(f"Workflow failed: {state['error']}")
    elif state.get("completed"):
        logger.info("✓ Workflow completed successfully!")
        logger.info(f"  Output: {state.get('output_path')}")
        if state.get('backup_path'):
            logger.info(f"  Backup: {state.get('backup_path')}")
        logger.info(f"  Images inserted: {len(state.get('insertion_plan', []))}")
    else:
        logger.warning("Workflow ended but not marked as completed")

    return state


def create_bid_agent() -> StateGraph:
    """Create the bid agent workflow using LangGraph.

    Returns:
        Compiled StateGraph application
    """
    logger.info("Creating bid agent workflow")

    # Create workflow
    workflow = StateGraph(BidAgentState)

    # Add nodes
    workflow.add_node("extract_images", extract_images_node)
    workflow.add_node("analyze_target", analyze_target_node)
    workflow.add_node("llm_decision", llm_decision_node)
    workflow.add_node("insert_images", insert_images_node)
    workflow.add_node("verify_result", verify_result_node)

    # Define edges (workflow sequence)
    workflow.set_entry_point("extract_images")
    workflow.add_edge("extract_images", "analyze_target")
    workflow.add_edge("analyze_target", "llm_decision")
    workflow.add_edge("llm_decision", "insert_images")
    workflow.add_edge("insert_images", "verify_result")
    workflow.add_edge("verify_result", END)

    # Compile workflow
    app = workflow.compile()

    logger.info("Bid agent workflow created successfully")

    return app


def run_bid_agent(source_path: str, target_path: str) -> Dict[str, Any]:
    """Run the bid agent workflow.

    Args:
        source_path: Path to source document with images
        target_path: Path to target document to modify

    Returns:
        Final agent state
    """
    from agents.state import create_initial_state

    # Create initial state
    initial_state = create_initial_state(source_path, target_path)

    # Create agent
    agent = create_bid_agent()

    # Run workflow
    logger.info("Starting bid agent workflow")
    logger.info(f"Source: {source_path}")
    logger.info(f"Target: {target_path}")

    final_state = agent.invoke(initial_state)

    logger.info("Workflow execution completed")

    return final_state


if __name__ == "__main__":
    # Test the agent
    import config

    result = run_bid_agent(
        str(config.SOURCE_DOC_PATH),
        str(config.TARGET_DOC_PATH)
    )

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"Completed: {result.get('completed')}")
    print(f"Error: {result.get('error')}")
    print(f"Output: {result.get('output_path')}")
    print(f"Images Inserted: {len(result.get('insertion_plan', []))}")
