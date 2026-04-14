# 第五步指令单（MD版）
## 任务名称
为统一执行层补充最小任务状态与日志记录能力（不改分析内核，不上数据库队列）

---

## 一、本步目标

第四步已经完成了以下基础能力：
- 已有统一消息结构 `UnifiedMessage`
- 已有统一任务结构 `UnifiedTask`
- 已有统一路由层 `MessageRouter`
- 已有渠道适配器（钉钉 / QQ）
- 已引入统一任务执行层 `TaskExecutor`
- 路由层已把任务交给执行层执行

但当前系统仍然缺一层非常关键的能力：

### 当前缺口
当任务执行时，我们仍然很难快速回答这些问题：
1. 这个任务当前处于什么状态？
2. 它卡在了哪一步？
3. 失败时具体是哪里出错？
4. 本次任务分析的是否是用户真实输入？
5. 日志是否足够让后续排障？

### 本步唯一目标
在**不引入数据库队列、不引入复杂异步系统**的前提下，补充一套**最小可用的任务状态与日志记录能力**。

目标结构变成：

```text
Channel Adapter -> MessageRouter -> TaskExecutor -> Analysis Layer
                                ↘ Task Status / Task Log
```

也就是说，本步要做到：
- 任务在执行过程中有基础状态变化
- 任务有“当前阶段”字段
- 执行层会记录最小日志
- 成功和失败都能留下统一记录
- 后续要接数据库、对象存储、队列时，不需要推翻重来

---

## 二、本步边界

### 本步要做
1. 梳理当前 `UnifiedTask` 是否已具备基本状态字段
2. 为任务补充最小状态字段 / 阶段字段 / 错误字段
3. 新增一个轻量任务日志模块或任务记录工具
4. 在 `TaskExecutor` 中接入状态更新
5. 在文本任务执行中接入最小日志
6. 在视频任务执行中接入最小日志
7. 统一记录成功 / 失败结果
8. 提交并推送 GitHub

### 本步不要做
本步**不要**：
- 上数据库任务表
- 上 Redis / Celery / RabbitMQ
- 上复杂异步队列
- 重写分析内核
- 深改 `simple_integration.py`
- 深改 `complete_analysis_service.py`
- 深改 MediaPipe 分析逻辑
- 做完整可观测平台
- 做分布式日志系统
- 接真实线上监控平台

---

## 三、本步核心思想

### 先让系统“知道自己在干什么”
当前系统已经能执行任务，但如果没有基础状态和日志，就会出现：
- 用户说“怎么没回”
- 你不知道是消息没进来、路由没分发、执行层报错，还是分析卡住了

所以本步目标不是“让系统更强”，而是让系统先具备最基础的**自我描述能力**。

---

## 四、执行步骤

---

## Step 1：检查当前 `UnifiedTask` 结构

请先检查当前仓库中的 `UnifiedTask` 定义，确认目前已有字段，并判断以下字段是否存在：

- `task_id`
- `task_type`
- `status`
- `channel`
- `message_type`
- `user_id`
- `source_file_url`
- `source_file_name`
- `created_at`
- `extra`

然后判断本步是否需要新增以下字段：

- `current_stage`
- `error_code`
- `error_message`
- `started_at`
- `finished_at`

请输出：

```text
UnifiedTask 当前已有字段：
UnifiedTask 缺失但建议新增字段：
本步准备如何补充：
```

要求：
- 以当前真实代码为准
- 不要为了最小改动而故意跳过明显缺失字段

---

## Step 2：扩展 `UnifiedTask` 的最小状态字段

请在不做大改的前提下，为 `UnifiedTask` 增加最小可用字段。

建议至少补充：

```python
current_stage: str = "created"
error_code: Optional[str] = None
error_message: Optional[str] = None
started_at: Optional[str] = None
finished_at: Optional[str] = None
```

### 建议状态语义
- `created`
- `running`
- `success`
- `failed`

### 建议阶段语义
文本任务可以简单使用：
- `created`
- `executing_text`
- `completed`

视频任务可以先粗粒度使用：
- `created`
- `executing_video`
- `completed`

### 要求
- 不引入复杂状态机
- 先保证字段存在且语义清晰
- 便于后续继续细化阶段

---

## Step 3：给 `UnifiedTask` 增加轻量状态更新方法

如果当前 `UnifiedTask` 是 dataclass，建议顺手补几个最小方法，例如：

```python
def mark_running(self, stage: str):
    ...

def mark_success(self, stage: str = "completed"):
    ...

def mark_failed(self, error_code: str, error_message: str, stage: str = "failed"):
    ...
```

这些方法的目标是：
- 统一更新 `status`
- 统一更新 `current_stage`
- 统一写入 `started_at` / `finished_at`
- 统一写入错误字段

### 要求
- 方法尽量简单
- 不要引入复杂依赖
- 不要做数据库持久化
- 先做结构内统一

---

## Step 4：新增轻量任务日志模块

请新增一个轻量日志模块，命名建议：

```text
task_logger.py
```

或如果已有工具目录：

```text
utils/task_logger.py
```

这个模块目标不是做专业日志平台，而是提供最小可用的结构化记录能力。

### 建议能力
至少提供一个函数，例如：

```python
def log_task_event(task: UnifiedTask, event: str, detail: str = "", extra: dict | None = None):
    ...
```

### 日志至少应包含
- 时间
- task_id
- task_type
- status
- current_stage
- channel
- message_type
- event
- detail

### 当前阶段可接受的输出方式
- 标准输出 `print`
- Python `logging`
- 简单文本日志

要求：
- 保持简单
- 不要上复杂 logging 配置系统
- 后续能替换成正式日志系统即可

---

## Step 5：在 `TaskExecutor` 中接入状态流转

请在 `TaskExecutor.execute()` 中加入最小状态流转。

### 执行前
- 将任务标记为 `running`
- 设置 `current_stage`

### 成功后
- 将任务标记为 `success`
- 设置 `finished_at`
- 记录成功日志

### 失败后
- 将任务标记为 `failed`
- 记录 `error_code`
- 记录 `error_message`
- 设置 `finished_at`
- 记录失败日志

### 目标
让执行层成为统一的任务状态更新入口。

---

## Step 6：文本任务接入最小状态与日志

请在文本任务执行逻辑中加入：

### 执行开始时
- `mark_running("executing_text")`
- `log_task_event(..., event="text_execution_started")`

### 执行成功时
- `mark_success("completed")`
- `log_task_event(..., event="text_execution_succeeded")`

### 执行失败时
- `mark_failed("TEXT_EXECUTION_ERROR", "...", stage="executing_text")`
- `log_task_event(..., event="text_execution_failed")`

要求：
- 不改变文本任务当前“轻量占位”定位
- 只是让状态和日志链完整起来

---

## Step 7：视频任务接入最小状态与日志

请在视频任务执行逻辑中加入：

### 执行开始时
- `mark_running("executing_video")`
- `log_task_event(..., event="video_execution_started")`

### 如果存在输入文件信息
尽量额外记录：
- `source_file_url`
- `source_file_name`

### 执行成功时
- `mark_success("completed")`
- `log_task_event(..., event="video_execution_succeeded")`

### 执行失败时
- `mark_failed("VIDEO_EXECUTION_ERROR", "...", stage="executing_video")`
- `log_task_event(..., event="video_execution_failed")`

### 注意
本步不要深挖视频内部多阶段（下载、预处理、分析、报告），  
这里只做“视频任务整体执行级别”的最小状态与日志。

---

## Step 8：统一返回结构中补充任务状态信息

请确保 `TaskExecutor` 的统一返回结构中，除了已有字段外，还能体现任务状态相关信息。

建议至少包含：

```python
{
    "task_id": "...",
    "task_type": "...",
    "status": "...",
    "current_stage": "...",
    "channel": "...",
    "message_type": "...",
    "result": ...,
    "error": {
        "code": "...",
        "message": "..."
    } or None
}
```

如果方便，也可以补充：
- `started_at`
- `finished_at`

### 要求
- 不追求一次性返回所有元信息
- 但至少让外层能看见“任务现在处于什么结果状态”

---

## Step 9：README 增加“Task Status & Logging”说明

请在 README 中补充一节，标题建议：

```md
## Task Status and Logging
```

说明以下内容：
- 当前系统已具备最小任务状态管理能力
- `UnifiedTask` 会记录 `status`、`current_stage`、错误信息、开始/结束时间
- `TaskExecutor` 是统一状态流转入口
- 任务日志当前为轻量实现，后续可升级为正式日志系统
- 当前仍未引入数据库任务表和异步队列

### 同时修正 README 中可能存在的问题
请顺手检查：
- 当前 README 是否还缺少最新架构图
- 是否仍有和当前实际代码不一致的旧描述
- 是否把“计划中”写成“已实现”

---

## Step 10：新增测试，验证状态与日志行为

请新增或完善测试脚本，建议命名：

```text
test_task_status.py
```

至少覆盖以下场景：

### 1. 文本任务成功
验证：
- 状态从 `created` -> `running` -> `success`
- `current_stage` 合理变化
- 返回结构包含状态字段

### 2. 视频任务成功
验证：
- 状态从 `created` -> `running` -> `success`
- 返回结构包含状态字段

### 3. 文本任务失败
模拟异常，验证：
- `status="failed"`
- `error.code` 存在
- `error.message` 存在

### 4. 视频任务失败
模拟异常，验证：
- `status="failed"`
- `current_stage` 合理
- 错误结构完整

### 5. 日志函数不报错
即便只是简单输出，也要确保能被正常调用

要求：
- 不追求复杂测试框架
- 最小可运行验证即可
- 不要为了测试去重构核心逻辑

---

## Step 11：本地自检

完成后请做最小自检，至少验证：

1. `UnifiedTask` 新字段可正常使用
2. `mark_running()` / `mark_success()` / `mark_failed()` 可正常调用
3. `task_logger.py` 可正常 import
4. 文本任务执行时能更新状态
5. 视频任务执行时能更新状态
6. 返回结构包含 `current_stage`
7. 失败时能返回 `error.code` 与 `error.message`

如果可以，请输出类似：

```text
[PASS] unified task status fields added
[PASS] task state transition helpers work
[PASS] task logger import works
[PASS] text task status updates work
[PASS] video task status updates work
[PASS] unified result includes current_stage
[PASS] unified failure result includes error details
```

---

## Step 12：提交并推送 GitHub

完成后请提交并推送到 GitHub。

建议 commit message：

```bash
feat: add minimal task status and logging support
```

或

```bash
feat: track task state and execution logs in executor layer
```

---

## 五、代码风格要求

### 要求
- 保持简单
- 优先做最小可用状态和日志能力
- 不引入复杂框架
- 不引入数据库持久化
- 不为了“可观测平台”而过度设计
- 状态字段和日志结构尽量清晰、统一、可扩展

---

## 六、本步禁止事项

本步**禁止**：
- 引入数据库任务表
- 引入 Redis / Celery / RabbitMQ
- 引入复杂监控平台
- 深改分析内核
- 深改视频处理逻辑
- 把日志系统做得过重
- 把状态流转做成复杂状态机
- 为了日志而破坏当前执行链

---

## 七、本步完成标准

只有满足以下条件，才算完成：

1. `UnifiedTask` 已补充最小状态与错误字段
2. 已有轻量状态更新方法
3. 已新增轻量任务日志模块
4. `TaskExecutor` 已接入状态流转
5. 文本任务已接入最小状态与日志
6. 视频任务已接入最小状态与日志
7. 返回结构已补充任务状态信息
8. README 已补充状态与日志说明
9. 已完成 GitHub 提交与推送

---

## 八、执行后回复格式

请严格按以下结构回复：

### A. `UnifiedTask` 字段扩展情况
### B. 新增 / 修改的文件列表
### C. 状态更新方法实现说明
### D. 轻量日志模块实现说明
### E. 文本任务状态与日志接入情况
### F. 视频任务状态与日志接入情况
### G. 统一返回结构更新说明
### H. 本地自检结果
### I. GitHub 提交与推送结果
### J. 下一步建议（只建议，不直接执行）
