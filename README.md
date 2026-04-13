# 🎾 网球 AI 教练系统

**阿里云部署版本** | 基于原腾讯云系统迁移优化

---

## 📊 系统功能

- ✅ **视频分析**：上传网球发球视频，AI 自动分析动作
- ✅ **NTRP 评级**：精准评估球员等级（3.0-5.0）
- ✅ **知识库对照**：169 条专业教练知识点
- ✅ **量化指标**：MediaPipe 姿态分析（膝盖/肘部/肩部角度）
- ✅ **通俗报告**：通俗易懂的改进建议
- ✅ **多渠道路由**：钉钉/QQ 支持

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- OpenClaw Gateway
- 阿里云服务器

### 安装依赖

```bash
# Python 3.8 环境
sudo pip3.8 install -r requirements.txt
```

### 启动服务

```bash
# 1. 确保 OpenClaw Gateway 运行中
openclaw gateway status

# 2. 系统已集成到 OpenClaw 渠道
# 消息流程：钉钉/QQ → 适配器 → 路由器 → 执行层 → 分析层

# 3. 测试
在钉钉中发送网球发球视频
```

---

## 📁 项目结构

```
ai-coach/
├── models/                    # 数据模型
│   ├── message.py             # 统一消息结构
│   └── task.py                # 统一任务结构
├── adapters/                  # 渠道适配器
│   ├── dingtalk_adapter.py    # 钉钉适配器
│   └── qq_adapter.py          # QQ 适配器
├── router.py                  # 路由层
├── task_executor.py           # 执行层
├── 核心模块
│   ├── core.py                # 核心配置
│   ├── complete_analysis_service.py  # 主分析服务
│   └── complete_report_generator.py  # 报告生成器
├── 知识库
│   └── fused_knowledge/       # 169 条融合知识
├── data/db/                   # 数据库
│   └── app.db                 # 含黄金标准表
├── reports/                   # 分析报告
├── media/inbound/             # 输入视频（临时）
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🎯 核心功能

### 1. MediaPipe 姿态分析

```python
from mediapipe_analyzer import MediaPipeAnalyzer

analyzer = MediaPipeAnalyzer()
metrics = analyzer.analyze_video('video.mp4')

# 输出：
# - 膝盖角度：145.3° (平均)
# - 肘部角度：172.2° (最大)
# - 肩部旋转：76.0°
```

### 2. AI 视频分析

使用 `qwen-vl-max` 进行视觉分析：
- 三步分析法（观察 → 对照 → 输出）
- 169 条教练知识库对照
- NTRP 黄金标准评级

### 3. 通俗化报告生成

```
🎾 网球发球分析报告

📊 综合评估
  NTRP 等级：3.0
  置信度：85%
  综合评分：68/100

✅ 做得好的地方
  ✓ 抛球手释放时手指自然张开
  ✓ 完成完整挥拍路径

⚠️ 需要改进
  🟠 [抛球] 抛球方向偏了
  🟠 [蓄力] 手肘抬得不够高

💪 训练建议
  1. 调整抛球方向
  2. 强化奖杯姿势训练
```

---

## 📊 技术架构

### 当前架构（v2.0）

```
钉钉用户 → OpenClaw Gateway → 视频保存到 media/inbound/
                                    ↓
                          simple_integration.py (监听)
                                    ↓
                          video_input_handler → source_file_path
                                    ↓
                          TaskExecutor → AnalysisService
                                    ↓
                          ├─ complete_analysis_service (主要)
                          ├─ qwen_vl_temp (临时备用)
                          └─ 知识库对照
                                    ↓
                          ReplyBuilder → 统一回复格式
                                    ↓
                          钉钉/QQ 渠道输出
```

### 架构说明

- **simple_integration.py**: 监听服务，检测新视频并触发分析流程
- **video_input_handler**: 视频输入准备层，统一处理视频来源
- **TaskExecutor**: 执行层，负责任务分发和状态管理
- **AnalysisService**: 统一分析服务接入层，调用旧分析能力
- **complete_analysis_service**: 主要分析内核（包含 MediaPipe + Qwen-VL + 知识库）
- **ReplyBuilder**: 统一回复构建层，将执行结果转换为用户可见回复

---

## Configuration and Environment（配置与环境）

### 统一配置层

当前系统已引入统一配置层（`config.py`），集中管理：
- 模型配置（DashScope/Qwen）
- 渠道配置（钉钉/QQ）
- 路径配置（数据/日志/临时目录）
- 运行模式配置（dev/prod）

所有配置统一从环境变量读取，不再散落在各个文件中。

### 环境变量配置

**1. 复制配置模板**

```bash
cd /home/admin/.openclaw/workspace/ai-coach
cp .env.example .env
```

**2. 编辑 .env 文件**

```bash
# 模型配置
DASHSCOPE_API_KEY=sk-your-api-key-here
VIDEO_MODEL_NAME=qwen-vl-max
TEXT_MODEL_NAME=qwen-max
ANALYSIS_BACKEND=legacy

# 运行模式
APP_ENV=dev  # 或 prod
DEBUG=true

# 路径配置（使用默认值即可）
BASE_DATA_DIR=./data
TASK_DATA_DIR=./data/tasks
LOG_DIR=./logs
```

**3. 加载环境变量**

```bash
# 方式 1：使用 direnv（推荐）
direnv allow

# 方式 2：手动导出
export $(cat .env | xargs)

# 方式 3：Python 自动加载（config 模块会自动读取）
```

### 配置字段说明

#### 模型配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DASHSCOPE_API_KEY` | 阿里云 DashScope API Key（必需） | - |
| `VIDEO_MODEL_NAME` | 视频分析模型 | `qwen-vl-max` |
| `TEXT_MODEL_NAME` | 文本处理模型 | `qwen-max` |
| `ANALYSIS_BACKEND` | 分析后端（legacy/simple/qwen_vl） | `legacy` |
| `ENABLE_TEMP_QWEN_FALLBACK` | 允许临时 fallback | `false` |

#### 渠道配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DINGTALK_ENABLED` | 启用钉钉渠道 | `true` |
| `DINGTALK_APP_KEY` | 钉钉 App Key | - |
| `DINGTALK_APP_SECRET` | 钉钉 App Secret | - |
| `DINGTALK_AGENT_ID` | 钉钉 Agent ID | - |
| `QQ_ENABLED` | 启用 QQ 渠道 | `true` |
| `QQ_APP_ID` | QQ App ID | - |

#### 路径配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `BASE_DATA_DIR` | 基础数据目录 | `./data` |
| `TASK_DATA_DIR` | 任务工作目录 | `./data/tasks` |
| `LOG_DIR` | 日志目录 | `./logs` |
| `TEMP_DIR` | 临时目录 | `./tmp` |
| `DB_PATH` | 数据库路径 | `./data/db/app.db` |

#### 运行模式配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `APP_ENV` | 运行环境（dev/prod） | `dev` |
| `DEBUG` | 调试模式 | `true`（dev）/`false`（prod） |
| `VERBOSE_TASK_LOGGING` | 详细任务日志 | `true` |
| `MAX_VIDEO_SIZE_MB` | 最大视频大小（MB） | `50` |
| `VIDEO_ANALYSIS_TIMEOUT` | 分析超时时间（秒） | `120` |

### 开发/生产模式

**开发模式**（`APP_ENV=dev`）:
- ✅ 启用详细日志
- ✅ 启用调试模式
- ✅ 自动创建目录
- ⚠️  不适合高并发

**生产模式**（`APP_ENV=prod`）:
- ✅ 精简日志
- ✅ 关闭调试模式
- ✅ 优化性能
- ⚠️  需要正确配置所有环境变量

### 敏感配置安全

**重要**:
- ⚠️  `.env` 文件已在 `.gitignore` 中，不会提交到 Git
- ✅ 使用 `.env.example` 作为模板，不含真实密钥
- ✅ 所有敏感配置统一从环境变量读取
- ✅ 代码中不再硬编码 API Key 或密钥

### 配置模块使用

**在代码中使用配置**:

```python
from config import get_config, get_model_config

# 获取总配置
config = get_config()
print(config.model.video_model_name)

# 获取模型配置
model_config = get_model_config()
print(model_config.dashscope_api_key)

# 获取路径配置
path_config = get_path_config()
print(path_config.task_data_dir)
```

### 旧配置方式（已废弃）

以下配置方式已不再使用：
- ❌ 在 `core.py` 中硬编码 `MODEL_NAME`
- ❌ 在各文件中直接 `os.environ.get('DASHSCOPE_API_KEY')`
- ❌ 在代码中写死绝对路径

应改为：
- ✅ 使用 `config.py` 统一配置模块
- ✅ 通过 `.env` 文件管理环境变量
- ✅ 使用相对路径（config 会自动转换为绝对路径）

---

## 🏗️ 系统架构

### 分层设计

系统采用四层架构：

```
┌─────────────────────────────────────┐
│  接入层 (Adapters)                   │
│  - 钉钉适配器 (adapters/dingtalk_adapter.py) │
│  - QQ 适配器 (adapters/qq_adapter.py)        │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│  路由层 (router.py)                  │
│  - 接收 UnifiedMessage               │
│  - 创建 UnifiedTask                  │
│  - 交给 TaskExecutor                 │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│  执行层 (task_executor.py)           │  ← Task Execution Layer
│  - TaskExecutor 类                   │
│  - 执行视频分析任务                  │
│  - 执行文本处理任务                  │
│  - 统一错误处理                      │
│  - 统一结果包装                      │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│  分析层 (核心模块)                    │
│  - complete_analysis_service.py      │
│  - complete_report_generator.py      │
│  - mediapipe_analyzer.py             │
│  - fused_knowledge/                  │
└─────────────────────────────────────┘
```

### 执行层（TaskExecutor）

**职责**:
- 接收 UnifiedTask
- 根据 task_type 分发执行
- 调用 AnalysisService
- 统一错误处理
- 统一结果包装

**关键方法**:
```python
class TaskExecutor:
    def execute(task, message) -> dict:
        # 根据 task_type 执行
        if task.task_type == "video_analysis":
            return _execute_video(task, message)
        elif task.task_type == "chat":
            return _execute_text(task, message)
```

---

## Analysis Service Layer（统一分析服务层）

### 分析服务架构

执行层不再直接调用旧分析脚本，而是通过统一分析服务接入层：

```
TaskExecutor → AnalysisService → 旧分析能力
```

### 核心模块

**文件**: `analysis_service.py`

**关键类**:
```python
class AnalysisService:
    def analyze_video(task: UnifiedTask) -> dict:
        """
        统一视频分析接口
        
        流程：
        1. 校验输入（task.source_file_path）
        2. 调用旧分析能力（_call_legacy_analysis）
        3. 规范化返回结构（_normalize_result）
        """
```

### 统一输入规范

**唯一可信输入**:
- `task.source_file_path` - 视频文件本地路径

**强制要求**:
- ❌ 不允许 fallback 到默认样例视频
- ❌ 输入缺失时明确失败

### 统一输出结构

```python
{
  "success": True,
  "analysis_type": "video",
  "entry": "complete_analysis_service",  # 使用的分析入口
  "summary": "NTRP 3.0 级（置信度 85%），综合评分 68/100",
  "report": "🎾 网球发球分析报告\n...",
  "structured_result": {...},
  "detailed_analysis": {...},
  "coach_references": {...},
  "raw_result": {...},
  "error": None
}
```

### 错误处理

```python
{
  "success": False,
  "analysis_type": "video",
  "error": {
    "code": "VIDEO_SOURCE_PATH_MISSING",
    "message": "task.source_file_path is not set"
  }
}
```

**错误码**:
- `VIDEO_SOURCE_PATH_MISSING` - 输入路径未设置
- `VIDEO_SOURCE_PATH_NOT_FOUND` - 文件不存在
- `VIDEO_ANALYSIS_FAILED` - 分析失败

### Legacy Adapter（旧分析能力适配）

**当前支持**:
- ✅ `complete_analysis_service` - 主要分析内核
- ⚠️  `qwen_vl_temp` - 临时备用实现（应尽快移除）

**调用流程**:
```python
AnalysisService._call_legacy_analysis(task)
  ├─ 尝试 complete_analysis_service.analyze_video_complete()
  └─ 备用：_analyze_with_qwen_vl_temp(task)  # 临时实现
```

**注意**:
- ✅ 优先使用 `complete_analysis_service`
- ⚠️  `qwen_vl_temp` 是临时实现，标记为应移除
- ❌ 执行层不直接调用任何分析内核

### 视频输入处理流程

视频任务进入执行层后，先经过输入准备层：

```
原始消息 → video_input_handler → 工作目录 → source_file_path → AnalysisService
```

### 核心模块

**文件**: `video_input_handler.py`

**关键函数**:
```python
prepare_video_input(task, message) -> UnifiedTask
build_task_workdir(task) -> str
resolve_video_source(task, message) -> dict
```

### 工作目录结构

```
data/tasks/{task_id}/
├── input/
│   └── source.mp4      # 视频输入文件
├── output/              # 分析输出
└── logs/                # 任务日志
```

### 视频来源解析优先级

1. ✅ `task.source_file_path` 已存在且文件存在
2. ✅ `message.file_path` 存在
3. ✅ `message.extra` 中有路径信息
4. ❌ 无输入（明确失败，**不允许 fallback 到默认样例**）

### 错误处理

**输入缺失**:
```python
task.mark_failed("VIDEO_INPUT_MISSING", "...", "preparing_video_input")
```

### 各层职责

**接入层**: 接收渠道原始消息 → 转换为 UnifiedMessage  
**路由层**: 接收 UnifiedMessage → 创建 UnifiedTask → 交给 TaskExecutor  
**执行层**: 接收 UnifiedTask → 调用 AnalysisService → 统一错误处理  
**分析层**: AnalysisService → 旧分析能力 → 规范化结果  
**回复层**: ReplyBuilder → 将执行结果转换为用户可见回复

---

## Reply Builder Layer（统一回复构建层）

### 设计目标

当前系统存在一个问题：钉钉和 QQ 适配器各自拼装回复内容，导致：
- 同一份分析结果，不同渠道展示不一致
- 失败提示不一致
- 没有统一的输出规范

Reply Builder Layer 解决这个问题：
- **统一回复格式**：所有渠道使用相同的回复结构
- **内容与格式分离**：执行结果和用户可见回复分开
- **渠道适配最小化**：渠道层只做薄格式转换，不改内容逻辑

### 核心模块

**文件**: `reply_builder.py`

**关键类**:
```python
class ReplyBuilder:
    def build_reply(execution_result: dict) -> dict:
        """将 TaskExecutor 执行结果转换为统一回复对象"""
    
    def render_reply_as_text(reply: dict) -> str:
        """将统一回复对象渲染为纯文本"""
    
    def render_reply_for_channel(reply: dict, channel: str) -> dict:
        """为特定渠道渲染回复格式"""
```

### 统一回复对象结构

**成功回复**:
```python
{
    "success": True,
    "reply_type": "analysis_report",  # 或 "text", "error"
    "title": "🎾 发球分析已完成",
    "message": "NTRP 3.5 级，综合评分 72/100",
    "details": ["关键问题 1", "关键问题 2", "建议 1"],
    "task_id": "uuid",
    "channel": "dingtalk",
    "raw_result": {...}  # 保留原始执行结果供调试
}
```

**失败回复**:
```python
{
    "success": False,
    "reply_type": "error",
    "title": "❌ 任务执行失败",
    "message": "本次任务未成功完成，请检查输入或稍后重试。",
    "details": ["错误码：VIDEO_INPUT_MISSING", "错误信息：..."],
    "task_id": "uuid"
}
```

### 渠道接入流程

```
TaskExecutor Result
        ↓
  ReplyBuilder.build_reply()
        ↓
  统一回复对象
        ↓
  ReplyBuilder.render_reply_for_channel()
        ↓
  渠道输出格式（钉钉/QQ）
```

### 当前实现

- ✅ 统一文本任务回复格式
- ✅ 统一视频分析任务回复格式
- ✅ 统一失败回复格式
- ✅ 纯文本渲染器
- ✅ 钉钉适配器已接入
- ✅ QQ 适配器已接入

### 后续扩展

- 富文本/Markdown 渲染
- 卡片消息支持
- 网页端/API 输出
- 多语言文案系统

---

### 渠道接入说明

当前系统支持以下渠道：

1. **钉钉（主入口）**
   - 适配器：`adapters/dingtalk_adapter.py`
   - 状态：✅ 已接入 ReplyBuilder
   - 输出格式：纯文本

2. **QQ（辅入口）**
   - 适配器：`adapters/qq_adapter.py`
   - 状态：✅ 已接入 ReplyBuilder
   - 输出格式：纯文本

**渠道适配器职责**:
- 只负责解析原始消息
- 转换为统一消息格式
- 调用统一回复层生成回复
- 不直接拼装复杂文案

### 渠道接入说明

当前系统支持以下渠道：

1. **钉钉（主入口）**
   - 适配器：`adapters/dingtalk_adapter.py`
   - 消息类型：文本、视频、图片、文件
   - 状态：✅ 已接入统一路由

2. **QQ（辅入口）**
   - 适配器：`adapters/qq_adapter.py`
   - 消息类型：文本、视频、图片、文件
   - 状态：✅ 已接入统一路由

**消息流转流程**:
```
渠道原始消息 → 适配器 → UnifiedMessage → Router → UnifiedTask → 分析服务
```

**渠道适配器职责**:
- 只负责解析原始消息
- 转换为统一消息格式
- 不处理业务逻辑
- 不直接调用分析服务

**注意**:
- 当前视频分析复用现有分析能力
- 当前文本处理为轻量版本（占位）


### 消息流转

1. **渠道消息** → 适配器 → `UnifiedMessage`
2. **UnifiedMessage** → 路由器 → `UnifiedTask`
3. **UnifiedTask** → 分析服务 → 报告

---

## 📝 使用示例

### 发送视频分析

1. 在钉钉中找到网球 AI 教练机器人
2. 发送网球发球视频（MP4 格式，< 20MB）
3. 等待 1-2 分钟
4. 收到 AI 分析报告

### 代码流程示例

```python
# 1. 渠道消息 → 适配器 → UnifiedMessage
from adapters.dingtalk_adapter import parse_dingtalk_message

message = parse_dingtalk_message(raw_message)

# 2. UnifiedMessage → Router → UnifiedTask
from router import MessageRouter

router = MessageRouter()
task = router.create_task(message, task_type='video_analysis')

# 3. UnifiedTask → TaskExecutor → AnalysisService
from task_executor import TaskExecutor

executor = TaskExecutor()
result = executor.execute(task, message)

# 4. AnalysisService → 旧分析能力 → 规范化结果
# 内部流程：
#   AnalysisService.analyze_video(task)
#     → _call_legacy_analysis(task)
#       → complete_analysis_service.analyze_video_complete()
#     → _normalize_result(result)
```

**完整数据流**:
```
钉钉消息 → 适配器 → UnifiedMessage
                      ↓
              router.py (创建 UnifiedTask)
                      ↓
              task_executor.py (TaskExecutor)
                      ↓
              analysis_service.py (AnalysisService)
                      ↓
              complete_analysis_service.py (旧分析能力)
                      ↓
              规范化结果 → 返回给执行层
```

**注意**:
- ❌ 不使用 `task.video_path`（已废弃）
- ✅ 使用 `task.source_file_path`（标准字段）
- ❌ 不调用 `router.register_video_handler()`（已废弃）
- ✅ 使用 `TaskExecutor.execute()` 统一执行
```python
{
  "task_id": "uuid",
  "task_type": "video_analysis",
  "status": "success",
  "channel": "dingtalk",
  "message_type": "video",
  "result": {...},
  "report": "分析报告",
  "error": None
}
```

**流程说明**:
```
钉钉消息 → adapters/dingtalk_adapter.py → UnifiedMessage
                                      ↓
                              router.py (MessageRouter)
                                      ↓
                              task_executor.py (TaskExecutor)
                                      ↓
                              complete_analysis_service.py
```

### 查看历史报告

```bash
ls -lt /home/admin/.openclaw/workspace/ai-coach/reports/
```

### 查询数据库

```bash
sqlite3 data/db/app.db
SELECT * FROM video_analysis_tasks ORDER BY created_at DESC LIMIT 10;
```

---

## 🐛 故障排查

### 服务未运行

```bash
# 检查进程
ps aux | grep simple_integration

# 重启服务
python3.8 simple_integration.py &
```

### MediaPipe 无法加载

```bash
# 检查 Python 版本
python3.8 --version  # 需要 3.8+

# 重新安装
sudo pip3.8 install mediapipe==0.10.11 --no-deps
```

### 视频分析失败

检查日志：
```bash
tail -f simple_integration.log
```

---

## 📈 性能指标

| 指标 | 值 |
|------|-----|
| 视频分析时间 | 30-60 秒 |
| MediaPipe 检测率 | > 95% |
| 报告生成时间 | < 5 秒 |
| 支持视频格式 | MP4, MOV, AVI |
| 最大视频大小 | 20MB |

---

## 📚 知识库来源

- **杨超教练**: 71 条（NTRP 分级标准）
- **赵凌曦教练**: 41 条（节奏与纠错）
- **Yellow 教练**: 57 条（动作细节）

总计：**169 条**专业教练知识

---

## 🔄 版本历史

### v2.0 (2026-04-09) - 阿里云版本
- ✅ 迁移到阿里云
- ✅ Python 3.8 升级
- ✅ MediaPipe 集成
- ✅ 报告通俗化优化
- ✅ OpenClaw 集成

### v1.0 (2026-04-01) - 腾讯云版本
- ✅ 初始版本
- ✅ 三步分析法
- ✅ 知识库融合
- ✅ 黄金标准数据库

---

## 🤝 协作开发

### Git 工作流

```bash
# 1. 克隆仓库
git clone https://github.com/weizhe1st/ali-ai-new-coach.git

# 2. 创建分支
git checkout -b feature/new-feature

# 3. 提交修改
git add .
git commit -m "feat: 添加新功能"

# 4. 推送
git push origin feature/new-feature

# 5. 创建 Pull Request
```

---

## 📞 联系方式

- **GitHub**: https://github.com/weizhe1st/ali-ai-new-coach
- **问题反馈**: 请在 GitHub 提交 Issue

---

## 📄 许可证

本项目仅供学习和研究使用。

---

**🎾 享受网球，享受 AI 带来的便利！**
