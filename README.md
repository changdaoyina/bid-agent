# bid-agent (智能投标文档图片插入代理)

这是一个基于 **LangChain**、**LangGraph** 和 **智谱AI (GLM)** 构建的智能文档处理代理。它能够自动从源文档中提取图片，并利用大语言模型的逻辑推理能力，智能地将这些图片插入到目标投标文档的合适位置。

## 核心功能

- **自动图片提取**：从源 DOCX 文档（如合同、证明材料）中自动识别并提取所有嵌入的图片。
- **文档结构分析**：深度解析目标文档的段落、标题层级和空行，为 AI 提供详细的上下文。
- **AI 智能决策**：利用 GLM-4.5-Air 模型分析文档逻辑，自动决定每张图片最适合插入的段落位置。
- **自动化批量插入**：根据 AI 生成的计划，自动调整图片大小并插入目标文档，同时保留原始备份。

## 技术栈

- **工作流编排**：[LangGraph](https://github.com/langchain-ai/langgraph)
- **大语言模型**：[智谱AI (GLM)](https://open.bigmodel.cn/)
- **文档处理**：`python-docx`
- **图像处理**：`Pillow`
- **开发语言**：Python 3.10+

## 项目结构

```text
agents/           # LangGraph 工作流定义与状态管理
skills/           # 原子能力模块（提取、分析、决策、插入）
utils/            # 底层工具类（DOCX 操作、日志等）
from/             # 源文档存放目录（包含图片的文档）
to/               # 目标文档存放目录（待插入图片的文档）
temp/             # 临时图片存放目录
config.py         # 项目全局配置
main.py           # 程序入口
```

## 快速开始

### 1. 环境准备

创建并激活 Conda 环境：
```bash
conda env create -f environment.yml
conda activate bid-agent
```

### 2. 配置 API Key

复制环境变量模板并编辑：
```bash
cp .env.example .env
# 在 .env 文件中填入你的 GLM_API_KEY
```

### 3. 准备文档

1. 将包含图片的源文档放入 `from/` 目录。
2. 将需要插入图片的目标文档放入 `to/` 目录。
3. (可选) 在 `config.py` 中修改 `SOURCE_DOC_NAME` 和 `TARGET_DOC_NAME` 为你的文件名。

### 4. 运行代理

```bash
python main.py
```

## 工作流程

1. **提取 (Extract)**：从源文件中提取所有图片并保存至临时目录。
2. **分析 (Analyze)**：扫描目标文件的标题和段落结构。
3. **决策 (Advise)**：AI 根据文档结构，为每张图片规划最佳插入点。
4. **执行 (Insert)**：程序自动执行插入操作，并生成备份文件。
5. **验证 (Verify)**：确认执行结果并输出最终文档路径。

## 配置项说明 (.env)

### 基础配置

- `LLM_PROVIDER`: LLM 提供商选择（`glm` 或 `gemini`）
- `TEMPERATURE`: 模型温度（默认：0，确保决策稳定性）
- `ENABLE_MULTIMODAL`: 启用多模态图片理解（默认：false）

### GLM 配置（智谱AI）

- `GLM_API_KEY`: 智谱AI API 密钥
- `GLM_BASE_URL`: API 终结点（默认：https://open.bigmodel.cn/api/paas/v4/）
- `GLM_MODEL`: 使用的模型（默认：GLM-4.6）

### Gemini 配置（Google）

- `GEMINI_API_KEY`: Google Gemini API 密钥
- `GEMINI_MODEL`: 使用的模型（默认：gemini-2.5-flash）

### 多模态配置（重要）

启用 `ENABLE_MULTIMODAL=true` 时，以下配置控制图片处理行为：

- `MAX_IMAGES_PER_REQUEST`: 单次请求最大图片数（默认：5）
  - **作用**：限制每次发送到LLM的图片数量，避免超时
  - **建议**：网络不稳定时设为 2-3
  
- `MAX_IMAGE_SIZE`: 图片最大尺寸（像素，默认：1024）
  - **作用**：自动压缩超过此尺寸的图片
  - **建议**：网络慢时设为 800 或更小
  
- `REQUEST_TIMEOUT`: 请求超时时间（秒，默认：300）
  - **作用**：等待API响应的最长时间
  - **建议**：图片多时可增加到 600

### 配置示例

**标准配置（推荐）**
```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_api_key
ENABLE_MULTIMODAL=true
MAX_IMAGES_PER_REQUEST=5
MAX_IMAGE_SIZE=1024
REQUEST_TIMEOUT=300
```

**保守配置（网络不稳定）**
```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_api_key
ENABLE_MULTIMODAL=true
MAX_IMAGES_PER_REQUEST=3
MAX_IMAGE_SIZE=800
REQUEST_TIMEOUT=600
```

**纯文本模式（避免多模态问题）**
```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_api_key
ENABLE_MULTIMODAL=false
```

## 故障排除

如果遇到 **"Server disconnected without sending a response"** 错误，请参考 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 详细排查指南。

常见解决方案：
1. 减少 `MAX_IMAGES_PER_REQUEST` 到 3
2. 降低 `MAX_IMAGE_SIZE` 到 800
3. 增加 `REQUEST_TIMEOUT` 到 600
4. 临时禁用多模态：`ENABLE_MULTIMODAL=false`
