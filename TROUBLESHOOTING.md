# 故障排除指南

## Gemini 多模态调用失败

### 问题症状
```
多模态调用失败: Server disconnected without sending a response.
```

### 常见原因

1. **图片数量过多**
   - 一次发送太多图片会导致请求超时
   - 默认限制为5张图片/请求

2. **图片尺寸过大**
   - 高分辨率图片会增加传输时间
   - 系统会自动压缩超过1024px的图片

3. **网络连接问题**
   - 国内访问Gemini API可能不稳定
   - 建议使用稳定的网络连接

4. **API配额限制**
   - 检查是否超出API调用配额
   - 查看 [Google AI Studio](https://aistudio.google.com/) 的配额使用情况

### 解决方案

#### 1. 调整配置参数

在 `.env` 文件中调整以下参数：

```bash
# 减少单次请求的图片数量
MAX_IMAGES_PER_REQUEST=3

# 降低图片最大尺寸
MAX_IMAGE_SIZE=800

# 增加超时时间（秒）
REQUEST_TIMEOUT=600
```

#### 2. 分批处理图片

如果图片数量很多，系统会自动只使用前N张图片（由`MAX_IMAGES_PER_REQUEST`控制）。

#### 3. 使用纯文本模式

如果多模态持续失败，可以禁用多模态：

```bash
# .env 文件
ENABLE_MULTIMODAL=false
```

系统会自动回退到纯文本分析模式。

#### 4. 切换到备用模型

尝试使用更稳定的Gemini模型：

```bash
# .env 文件
GEMINI_MODEL=gemini-1.5-flash
```

#### 5. 检查网络连接

```bash
# 测试是否能访问Google API
curl -I https://generativelanguage.googleapis.com/
```

### 配置优化建议

#### 最佳实践配置（推荐）

```bash
# .env 配置
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
TEMPERATURE=0
ENABLE_MULTIMODAL=true

# 优化的多模态配置
MAX_IMAGES_PER_REQUEST=5
MAX_IMAGE_SIZE=1024
REQUEST_TIMEOUT=300
```

#### 保守配置（网络不稳定时）

```bash
# .env 配置
MAX_IMAGES_PER_REQUEST=3
MAX_IMAGE_SIZE=800
REQUEST_TIMEOUT=600
ENABLE_MULTIMODAL=true
```

#### 快速配置（大量图片）

```bash
# .env 配置  
MAX_IMAGES_PER_REQUEST=2
MAX_IMAGE_SIZE=640
REQUEST_TIMEOUT=180
ENABLE_MULTIMODAL=true
```

### 日志分析

查看日志了解详细信息：

```bash
# 运行时会显示：
# - 压缩后的图片大小
# - 实际上传的图片数量
# - 总数据大小
# - 详细的错误信息
```

示例日志：
```
2025-12-19 17:26:57,608 - llm_providers.gemini_provider - INFO - 超时设置: 300秒, 最大图片尺寸: 1024px
2025-12-19 17:26:57,608 - llm_providers.gemini_provider - DEBUG - 压缩图片: 2500000 -> 850000 bytes
2025-12-19 17:26:57,608 - llm_providers.gemini_provider - INFO - 总共上传 5 张图片，总大小: 4.2 MB
```

### 性能优化

1. **图片预处理**
   - 图片会自动压缩到指定尺寸
   - 保持宽高比
   - 使用JPEG格式可以进一步减小体积

2. **批量策略**
   - 优先发送最重要的图片
   - 系统会截取前N张图片

3. **错误恢复**
   - 自动回退到纯文本模式
   - 不会中断整个工作流程

### 常见错误码

| 错误信息 | 原因 | 解决方法 |
|---------|------|---------|
| Server disconnected | 请求超时/图片过大 | 减少图片数量或尺寸 |
| 429 Too Many Requests | API配额用完 | 等待配额重置或升级 |
| 401 Unauthorized | API Key无效 | 检查.env中的API Key |
| 400 Bad Request | 图片格式不支持 | 确保使用JPEG/PNG格式 |

### 进一步帮助

如果问题仍未解决：

1. 查看 [Gemini API文档](https://ai.google.dev/docs)
2. 检查 [API状态页面](https://status.cloud.google.com/)
3. 在项目Issues中反馈问题

### 测试命令

测试多模态功能：

```bash
# 使用少量图片测试
python main.py

# 查看详细日志
LOG_LEVEL=DEBUG python main.py
```

## 其他常见问题

### GLM API 调用失败

参考 Gemini 的解决方案，GLM 配置类似。

### 文档处理错误

确保文档格式正确，路径无误。
