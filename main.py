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
        logger.error("配置验证失败:")
        for error in errors:
            logger.error(f"  - {error}")
        return False

    logger.info("✓ 配置验证成功")
    return True


def main() -> None:
    """Main entry point for the bid-agent application."""
    print_banner()

    # Print configuration summary
    print(config.get_config_summary())

    # Validate environment
    if not validate_environment():
        logger.error("\n请修复配置错误后重试。")
        logger.info("\n提示: 请确保:")
        logger.info("  1. 已创建 .env 文件并设置 API 密钥 (GLM_API_KEY 或 GEMINI_API_KEY)")
        logger.info("  2. 在 .env 中设置 LLM_PROVIDER 为 'glm' 或 'gemini'")
        logger.info("  3. 将源文档放在 'from/' 目录")
        logger.info("  4. 将目标文档放在 'to/' 目录")
        sys.exit(1)

    # Run the agent
    try:
        logger.info("启动招投标代理工作流...\n")

        result = run_bid_agent(
            source_path=str(config.SOURCE_DOC_PATH),
            target_path=str(config.TARGET_DOC_PATH)
        )

        # Print final result
        print("\n" + "=" * 70)
        print("  EXECUTION SUMMARY")
        print("=" * 70)

        if result.get("error"):
            print(f"\n✗ 状态: 失败")
            print(f"  错误: {result['error']}")
            sys.exit(1)
        elif result.get("completed"):
            print(f"\n✓ 状态: 成功")
            print(f"  LLM 提供商: {result.get('llm_provider', 'unknown').upper()}")
            if result.get('used_multimodal'):
                print(f"  多模态: 是 (使用 AI 视觉分析图片)")
            print(f"  已提取图片: {len(result.get('extracted_images', []))} 张")
            print(f"  已插入图片: {len(result.get('insertion_plan', []))} 张")
            print(f"  输出文档: {result.get('output_path')}")
            if result.get('backup_path'):
                print(f"  已创建备份: {result.get('backup_path')}")
            print("\n现在可以打开输出文档查看结果！")
        else:
            print(f"\n⚠ 状态: 未完成")
            print(f"  当前步骤: {result.get('current_step')}")

        print("\n" + "=" * 70 + "\n")

    except KeyboardInterrupt:
        logger.info("\n\n用户中断工作流")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n\n意外错误: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
