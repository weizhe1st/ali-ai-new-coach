# 🚀 系统入口说明 (System Entrypoints)

**版本**: 1.0  
**最后更新**: 2026-04-15  
**目的**: 明确系统主入口，避免误调用 Legacy 文件

---

## 一、主链路入口（唯一推荐）

### 消息流程

```
用户消息（钉钉/QQ）
    ↓
OpenClaw Gateway（渠道插件）
    ↓
渠道适配器（adapters/dingtalk_adapter.py 或 adapters/qq_adapter.py）
    ↓
消息路由器（router.py - MessageRouter）
    ↓
任务执行器（task_executor.py - TaskExecutor）
    ↓
视频输入处理（video_input_handler.py - VideoInputHandler）
    ↓
分析服务（analysis_service.py - AnalysisService）
    ↓
分析内核（complete_analysis_service.py）
    ↓
回复构建器（reply_builder.py - ReplyBuilder）
    ↓
渠道输出（钉钉/QQ）
```

### 核心模块（主链路）

| 模块 | 文件 | 职责 |
|------|------|------|
| **渠道适配器** | `adapters/dingtalk_adapter.py`<br>`adapters/qq_adapter.py` | 解析渠道消息，调用 ReplyBuilder |
| **路由器** | `router.py` | 接收 UnifiedMessage，创建 UnifiedTask |
| **执行器** | `task_executor.py` | 执行任务，管理任务状态 |
| **视频处理** | `video_input_handler.py` | 解析视频来源，准备工作目录 |
| **分析服务** | `analysis_service.py` | 调用分析内核，规范化返回 |
| **回复构建** | `reply_builder.py` | 生成用户可见回复 |

### 配置入口

| 配置 | 文件 | 说明 |
|------|------|------|
| **统一配置** | `config.py` | 管理模型/渠道/路径/运行模式配置 |
| **环境变量** | `.env` | 敏感配置（不提交到 Git） |
| **配置模板** | `.env.example` | 环境变量模板（可提交） |

---

## 二、分析链入口

### 主分析链（推荐）

```
AnalysisService.analyze_video()
    ↓
complete_analysis_service.AnalysisService()
    ↓
Qwen-VL 视觉分析
    ↓
知识库检索（knowledge_gold_analyzer.py）
    ↓
黄金标准对比
    ↓
返回结构化结果
```

### 文件路径

- **接入层**: `analysis_service.py`
- **分析内核**: `complete_analysis_service.py`
- **知识库**: `knowledge_gold_analyzer.py`
- **配置**: `config.py` → `core.py`（间接）

### 配置项

```python
# config.py
ANALYSIS_BACKEND = 'legacy'  # legacy | simple | qwen_vl
VIDEO_MODEL_NAME = 'qwen-vl-max'
```

---

## 三、样本归档入口

### 归档流程

```
分析成功
    ↓
SampleArchiveService.archive_after_analysis()
    ↓
上传到 COS（cos_uploader.py）
    ↓
标记候选黄金样本
    ↓
记录到 sample_registry.json
    ↓
完成归档
```

### 文件路径

- **归档服务**: `sample_archive_service.py`
- **COS 上传**: `cos_uploader.py`
- **审核工具**: `review_sample.py`
- **审核服务**: `sample_review_service.py`
- **登记表**: `data/sample_registry.json`

### 触发时机

- 分析成功后自动触发
- 在 `task_executor.py` 中调用

---

## 四、不应使用的旧入口（Legacy）

### ❌ 禁止直接调用

| 文件 | 问题 | 替代方案 |
|------|------|----------|
| `simple_integration.py` | 独立监听脚本，非主链路 | 使用 OpenClaw Gateway + 渠道适配器 |
| `qwen_analysis_service.py` | 独立分析脚本，配置散落 | 使用 `analysis_service.py` |
| `qwen_analysis_simple.py` | 简化分析脚本，功能不完整 | 使用 `analysis_service.py` |
| `dingtalk_callback_minimal.py` | 独立回调服务，与 OpenClaw 冲突 | 使用 OpenClaw 内置渠道 |
| `dingtalk_integrated_service.py` | 独立服务，已废弃 | 使用 OpenClaw 内置渠道 |

### ❌ 错误调用示例

```bash
# 错误：直接运行监听脚本
python3.8 simple_integration.py

# 错误：直接调用分析服务
python3.8 qwen_analysis_service.py

# 错误：启动独立回调服务
python3.8 dingtalk_callback_minimal.py
```

### ✅ 正确调用方式

```bash
# 正确：通过 OpenClaw Gateway 启动渠道
openclaw gateway start

# 正确：渠道消息自动路由到主链路
# 用户在钉钉/QQ 发送视频 → 自动触发分析
```

---

## 五、开发/调试入口

### 本地测试

```bash
# 1. 查看配置
python3.8 -c "from config import Config; print(Config.get_model_config())"

# 2. 测试 COS 上传
python3.8 test_cos_upload.py

# 3. 测试分析服务（本地视频）
python3.8 -c "
from analysis_service import AnalysisService
service = AnalysisService()
result = service.analyze_video('/path/to/video.mp4')
print(result)
"

# 4. 测试样本审核工具
python3.8 review_sample.py list --status pending
python3.8 review_sample.py show --sample-id xxx
```

### 日志查看

```bash
# 查看最新日志
tail -f logs/app.log

# 查看任务日志
cat data/tasks/{task_id}/task.log
```

---

## 六、配置加载顺序

### 优先级（从高到低）

1. **环境变量**（`.env` 文件）
2. **config.py 默认值**
3. **core.py 硬编码**（Legacy，逐步迁移）

### 配置读取流程

```
模块请求配置
    ↓
config.py（统一配置层）
    ↓
检查环境变量
    ↓
使用默认值
    ↓
返回配置
```

### 配置分类

| 配置类型 | 文件 | 说明 |
|----------|------|------|
| 模型配置 | `config.py` | DashScope API Key、模型名称 |
| 渠道配置 | `config.py` | 钉钉/QQ 配置 |
| 路径配置 | `config.py` | 数据目录、日志目录 |
| 运行模式 | `config.py` | 开发/生产、调试模式 |
| COS 配置 | `config.py` + 环境变量 | 腾讯云密钥、存储桶 |

---

## 七、模块依赖关系

### 核心依赖

```
config.py（最底层，无依赖）
    ↑
video_input_handler.py
    ↑
analysis_service.py
    ↑
task_executor.py
    ↑
router.py
    ↑
adapters/
    ↑
reply_builder.py
```

### 辅助模块

```
config.py
    ↑
cos_uploader.py
    ↑
sample_archive_service.py
    ↑
task_executor.py（调用归档）
```

```
config.py
    ↑
knowledge_gold_analyzer.py
    ↑
complete_analysis_service.py
    ↑
analysis_service.py
```

---

## 八、运行环境

### 生产环境

```bash
# 环境变量
APP_ENV=prod
DEBUG=false
ALLOW_TEMP_ANALYSIS_FALLBACK=false

# 启动
openclaw gateway start
```

### 开发环境

```bash
# 环境变量
APP_ENV=dev
DEBUG=true
ALLOW_TEMP_ANALYSIS_FALLBACK=true

# 启动
openclaw gateway start

# 或直接测试
python3.8 test_*.py
```

---

## 九、故障排查入口

### 问题定位流程

```
1. 查看日志
   ↓
   logs/app.log
   data/tasks/{task_id}/task.log
   
2. 检查配置
   ↓
   python3.8 -c "from config import Config; print(Config.all())"
   
3. 测试分析服务
   ↓
   使用本地视频测试 analysis_service.py
   
4. 检查 COS 连接
   ↓
   python3.8 test_cos_upload.py
```

### 常见问题入口

| 问题 | 检查点 | 相关文件 |
|------|--------|----------|
| 渠道无响应 | OpenClaw Gateway 状态 | `openclaw gateway status` |
| 分析失败 | 分析服务日志 | `logs/app.log` |
| COS 上传失败 | COS 配置 | `config.py`, `.env` |
| 样本未归档 | 归档服务日志 | `task.log` |

---

## 十、维护说明

### 新增入口原则

1. **优先复用**: 优先使用现有主链路模块
2. **文档同步**: 新增入口需更新本文档
3. **避免重复**: 不创建功能重复的入口

### 入口变更

- 新增主入口：需经过评审
- 废弃旧入口：标记为 deprecated，保留至少 1 个版本周期
- 修改入口行为：需更新文档和测试用例

### 版本历史

- v1.0 (2026-04-15): 初始版本，明确主链路入口

---

**维护者**: 网球 AI 教练系统开发团队  
**联系方式**: 内部
