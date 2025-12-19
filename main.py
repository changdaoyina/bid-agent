"""Bid-agent: Intelligent image insertion agent for bid documents.

This agent uses LangChain, LangGraph and GLM to:
1. Extract images from source documents
2. Analyze target document structure
3. Use GLM to intelligently decide insertion positions
4. Insert images into the target document
"""

import sys
from pathlib import Path

import config
from agents.bid_coordinator import run_bid_agent
from utils.logger import get_logger

logger = get_logger(__name__)


def print_banner():
    """Print application banner."""
    print("\n" + "=" * 70)
    print("  BID-AGENT: Intelligent Document Image Insertion")
    print("  Powered by LangChain + LangGraph + Multi-LLM Support (GLM/Gemini)")
    print("=" * 70 + "\n")


def validate_environment() -> bool:
    """Validate that the environment is properly configured.

    Returns:
        True if valid, False otherwise
    """
    is_valid, errors = config.validate_config()

    if not is_valid:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        return False

    logger.info("✓ Configuration validated successfully")
    return True


def main() -> None:
    """Main entry point for the bid-agent application."""
    print_banner()

    # Print configuration summary
    print(config.get_config_summary())

    # Validate environment
    if not validate_environment():
        logger.error("\nPlease fix the configuration errors and try again.")
        logger.info("\nHint: Make sure you have:")
        logger.info("  1. Created a .env file with your API key (GLM_API_KEY or GEMINI_API_KEY)")
        logger.info("  2. Set LLM_PROVIDER to 'glm' or 'gemini' in .env")
        logger.info("  3. Placed source document in 'from/' directory")
        logger.info("  4. Placed target document in 'to/' directory")
        sys.exit(1)

    # Run the agent
    try:
        logger.info("Starting bid agent workflow...\n")

        result = run_bid_agent(
            source_path=str(config.SOURCE_DOC_PATH),
            target_path=str(config.TARGET_DOC_PATH)
        )

        # Print final result
        print("\n" + "=" * 70)
        print("  EXECUTION SUMMARY")
        print("=" * 70)

        if result.get("error"):
            print(f"\n✗ Status: FAILED")
            print(f"  Error: {result['error']}")
            sys.exit(1)
        elif result.get("completed"):
            print(f"\n✓ Status: SUCCESS")
            print(f"  LLM Provider: {result.get('llm_provider', 'unknown').upper()}")
            if result.get('used_multimodal'):
                print(f"  Multimodal: Yes (analyzed images with AI vision)")
            print(f"  Images extracted: {len(result.get('extracted_images', []))}")
            print(f"  Images inserted: {len(result.get('insertion_plan', []))}")
            print(f"  Output document: {result.get('output_path')}")
            if result.get('backup_path'):
                print(f"  Backup created: {result.get('backup_path')}")
            print("\nYou can now open the output document to see the results!")
        else:
            print(f"\n⚠ Status: INCOMPLETE")
            print(f"  Current step: {result.get('current_step')}")

        print("\n" + "=" * 70 + "\n")

    except KeyboardInterrupt:
        logger.info("\n\nWorkflow interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n\nUnexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
