"""Configuration management for bid-agent."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.absolute()

# GLM API Configuration (智谱AI)
GLM_API_KEY = os.getenv("GLM_API_KEY", "")
GLM_BASE_URL = os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")
GLM_MODEL = os.getenv("GLM_MODEL", "GLM-4.6")

# Document Paths
SOURCE_DOC_DIR = PROJECT_ROOT / "from"
TARGET_DOC_DIR = PROJECT_ROOT / "to"
OUTPUT_DOC_DIR = PROJECT_ROOT / "output"
TEMP_DIR = PROJECT_ROOT / "temp"

# Default document names
SOURCE_DOC_NAME = "华夏银行信用卡中心营销权益平台建设项目软件开发合同.docx"
TARGET_DOC_NAME = "0000000.docx"

# Full paths
SOURCE_DOC_PATH = SOURCE_DOC_DIR / SOURCE_DOC_NAME
TARGET_DOC_PATH = TARGET_DOC_DIR / TARGET_DOC_NAME

# Image Processing Configuration
MAX_IMAGE_WIDTH_INCHES = 6.0  # Maximum width for inserted images
IMAGE_ALIGNMENT = "center"     # Image alignment: left, center, right

# LLM Configuration
LLM_TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))  # Use 0 for deterministic output
LLM_MAX_RETRIES = 3  # Maximum retries for LLM calls

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def validate_config() -> tuple[bool, list[str]]:
    """Validate configuration settings.

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Check GLM API key
    if not GLM_API_KEY:
        errors.append("GLM_API_KEY is not set in .env file")

    # Check source document exists
    if not SOURCE_DOC_PATH.exists():
        errors.append(f"Source document not found: {SOURCE_DOC_PATH}")

    # Check target document exists
    if not TARGET_DOC_PATH.exists():
        errors.append(f"Target document not found: {TARGET_DOC_PATH}")

    # Ensure output directory exists
    if not OUTPUT_DOC_DIR.exists():
        OUTPUT_DOC_DIR.mkdir(parents=True, exist_ok=True)

    # Check temp directory exists
    if not TEMP_DIR.exists():
        errors.append(f"Temp directory not found: {TEMP_DIR}")

    return len(errors) == 0, errors


def get_config_summary() -> str:
    """Get a summary of current configuration.

    Returns:
        String summary of configuration
    """
    return f"""
Bid-Agent Configuration:
========================
Project Root: {PROJECT_ROOT}
Source Document: {SOURCE_DOC_PATH}
Target Document: {TARGET_DOC_PATH}
Output Directory: {OUTPUT_DOC_DIR}
Temp Directory: {TEMP_DIR}
LLM Provider: GLM (智谱AI)
GLM Model: {GLM_MODEL}
GLM Base URL: {GLM_BASE_URL}
API Key Set: {'Yes' if GLM_API_KEY else 'No'}
Temperature: {LLM_TEMPERATURE}
Max Image Width: {MAX_IMAGE_WIDTH_INCHES} inches
Image Alignment: {IMAGE_ALIGNMENT}
"""


if __name__ == "__main__":
    # Test configuration
    print(get_config_summary())
    is_valid, errors = validate_config()
    if is_valid:
        print("\n✓ Configuration is valid")
    else:
        print("\n✗ Configuration errors:")
        for error in errors:
            print(f"  - {error}")
