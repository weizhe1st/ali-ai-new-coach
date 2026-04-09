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

```
钉钉用户 → OpenClaw Gateway → 视频保存
                                    ↓
                          simple_integration.py
                                    ↓
                          ├─ MediaPipe 量化分析
                          ├─ qwen-vl-max 视觉分析
                          └─ 知识库对照
                                    ↓
                          生成通俗化报告
                                    ↓
                          保存到 reports/
```

---

## 🔧 配置说明

### 模型配置

编辑 `core.py`:
```python
MODEL_NAME = 'qwen-max'  # 文本分析
# 或
MODEL_NAME = 'qwen-vl-max'  # 视频分析
```

### API Key 配置

```bash
export DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxx"
```

### 数据库配置

```python
DB_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/db/app.db'
```

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

### Task Execution Layer（执行层）

**职责**:
- 接收 UnifiedTask
- 根据 task_type 分发执行
- 调用旧分析能力
- 统一错误处理
- 统一结果包装
- **任务状态跟踪**
- **任务日志记录**

**关键类**:
```python
class TaskExecutor:
    def execute(task, message) -> dict:
        # 根据 task_type 执行
        if task.task_type == "video_analysis":
            return _execute_video(task, message)
        elif task.task_type == "chat":
            return _execute_text(task, message)
        # ...
```

**统一返回结构**:
```python
{
  "task_id": "uuid",
  "task_type": "video_analysis",
  "status": "success",           # created/running/success/failed
  "current_stage": "completed",  # 当前执行阶段
  "channel": "dingtalk",
  "result": {...},
  "report": "分析报告",
  "error": None,
  "started_at": "2026-04-09T...",
  "completed_at": "2026-04-09T..."
}
```

---

## Task Status and Logging（任务状态与日志）

### 任务状态管理

**UnifiedTask 状态字段**:
- `status`: created → running → success/failed
- `current_stage`: 当前执行阶段（如 executing_video, executing_text）
- `error_code`: 错误码（失败时）
- `error_message`: 错误信息（失败时）
- `started_at`: 开始时间
- `completed_at`: 完成时间

**状态更新方法**:
```python
task.mark_running("executing_video")
task.mark_success("completed", result=..., report=...)
task.mark_failed("VIDEO_EXECUTION_ERROR", "错误信息", "executing_video")
```

### 任务日志记录

**轻量日志模块**: `task_logger.py`

**日志函数**:
```python
log_task_start(task, stage)
log_task_success(task, stage)
log_task_failure(task, error_code, error_message)
log_video_execution_start(task)
log_video_execution_success(task)
log_video_execution_failure(task, code, msg)
log_text_execution_start(task)
log_text_execution_success(task)
log_text_execution_failure(task, code, msg)
```

**日志输出**:
```
[2026-04-09T03:33:55.394] Task[4bc5b861] text_execution_started - Starting text task execution
[2026-04-09T03:33:55.394] Task[4bc5b861] text_execution_succeeded - Text task completed successfully
```

### 当前实现说明

- ✅ 已实现最小任务状态管理
- ✅ 已实现轻量日志记录
- ✅ TaskExecutor 是统一状态流转入口
- ✅ 日志当前为简单打印，后续可升级为正式日志系统
- ❌ 未引入数据库任务表
- ❌ 未引入异步队列

---

## Video Input Preparation（视频输入准备）

### 视频输入处理流程

视频任务进入执行层后，先经过输入准备层：

```
原始消息 → video_input_handler → 工作目录 → source_file_path → 旧分析能力
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
4. ⚠️ `message.file_url` 存在（当前不支持，明确失败）
5. ❌ 无输入（明确失败，**不允许 fallback 到默认样例**）

### 错误处理

**输入缺失**:
```python
task.mark_failed("VIDEO_INPUT_MISSING", "...", "preparing_video_input")
```

**URL 不支持**:
```python
task.mark_failed("VIDEO_URL_NOT_SUPPORTED", "...", "preparing_video_input")
```

**文件复制失败**:
```python
task.mark_failed("VIDEO_FILE_COPY_FAILED", "...", "preparing_video_input")
```

### 状态流转

```
created → preparing_video_input → executing_video → success/failed
```

### 日志记录

```
[timestamp] Task[task_id] workdir_created - Task workdir created at ...
[timestamp] Task[task_id] video_file_copied - Video file copied from ... to ...
[timestamp] Task[task_id] video_input_prepared - Video input prepared at ...
```

### 当前实现说明

- ✅ 统一解析视频输入来源
- ✅ 统一生成任务工作目录
- ✅ 统一写入 source_file_path
- ✅ 明确失败，不回退到默认样例
- ❌ 未实现 URL 下载器（后续可扩展）
- ❌ 未实现对象存储集成

### 各层职责

**接入层**:
- 接收渠道原始消息（钉钉/QQ）
- 转换为 UnifiedMessage
- 不处理业务逻辑

**路由层**:
- 接收 UnifiedMessage
- 创建 UnifiedTask
- 交给 TaskExecutor 执行
- 不直接执行业务

**执行层**:
- 接收 UnifiedTask
- 根据 task_type 执行
- 调用旧分析能力
- 统一错误处理
- 统一结果包装

**分析层**:
- 视频分析核心逻辑
- MediaPipe 姿态分析
- 报告生成
- 知识库处理

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

### 代码示例

```python
from router import MessageRouter, from_dingtalk

# 创建路由器（内部包含 TaskExecutor）
router = MessageRouter()

# 注册视频分析处理器（连接到旧分析能力）
def my_video_handler(task):
    # 调用旧分析能力
    from complete_analysis_service import analyze_video_complete
    return analyze_video_complete(task.video_path)

router.register_video_handler(my_video_handler)

# 接收钉钉消息
message = from_dingtalk(
    user_id='user_123',
    text='帮我分析这个发球',
    file_path='/path/to/video.mp4'
)

# 路由处理
# MessageRouter -> TaskExecutor -> 旧分析能力
result = router.route_message(message)

# 获取统一结果
print(f"任务状态：{result['status']}")
print(f"任务 ID: {result['task_id']}")
print(f"分析报告：{result['report']}")
```

**返回结果结构**:
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
