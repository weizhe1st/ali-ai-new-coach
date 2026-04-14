# 第六步指令单（MD版）
## 任务名称
补齐统一视频输入入链层（确保真实上传视频进入任务，不再依赖默认样例）

---

## 一、本步目标

第五步已经完成了以下基础能力：
- 已有统一消息结构 `UnifiedMessage`
- 已有统一任务结构 `UnifiedTask`
- 已有统一路由层 `MessageRouter`
- 已有渠道适配器（钉钉 / QQ）
- 已有统一任务执行层 `TaskExecutor`
- 已补充最小任务状态与日志记录能力

但是当前系统仍有一个非常关键的真实风险：

### 当前最大隐患
用户从钉钉 / QQ 发来的视频，是否真的进入了任务执行链，是否真的被下载、保存、并交给分析模块使用，这件事目前仍然不够清楚、不够标准化。

如果这一层不单独补齐，后面就容易出现以下问题：
1. 用户发了真实视频，但系统分析的是默认测试视频
2. 不同渠道的视频字段不统一，导致执行层拿不到真实文件
3. 视频路径、文件名、来源 URL、任务工作目录没有标准化
4. 后续排障时无法确认“本次任务分析的到底是哪一个文件”

### 本步唯一目标
新增一层**统一视频输入入链层**，确保视频任务进入执行层后，先经过：

```text
原始文件信息 -> 输入解析 -> 本地落盘 / 标准路径 -> 写入 UnifiedTask -> 再交旧分析能力
```

本步要做到：
- 统一解析视频输入来源
- 统一为任务生成工作目录
- 统一记录真实输入文件路径
- 严禁视频不可用时自动回退到默认样例视频
- 为下一步细化视频预处理、下载器、对象存储打基础

---

## 二、本步边界

### 本步要做
1. 梳理当前视频任务是如何拿到输入文件的
2. 为 `UnifiedTask` 补充最小视频输入字段（如缺失）
3. 新增统一视频输入处理模块
4. 在执行层中接入视频输入解析与落盘
5. 标准化任务工作目录
6. 标准化 `source_file_url` / `source_file_name` / `source_file_path`
7. 禁止自动回退默认测试视频
8. 提交并推送 GitHub

### 本步不要做
本步**不要**：
- 重写视频分析内核
- 深改 `simple_integration.py`
- 深改 `complete_analysis_service.py`
- 上复杂下载器框架
- 直接接阿里云 OSS / COS SDK
- 上异步大文件传输系统
- 做完整视频转码系统
- 做复杂抽帧逻辑
- 做正式对象存储生命周期管理

---

## 三、本步核心思想

### 先确保“分析的真的是用户的视频”
当前最重要的不是“分析更高级”，而是：
- 系统知道视频从哪里来
- 系统知道视频保存到了哪里
- 执行层拿到的是哪一个真实文件
- 日志里能追踪到这个文件

本步本质上是在补：
**输入层可信度**

---

## 四、执行步骤

---

## Step 1：梳理当前视频输入链路

请先检查当前仓库中，视频任务现在是如何获得输入文件的。

请重点检查：
- `adapters/` 中钉钉 / QQ 视频消息解析
- `router.py`
- `task_executor.py`
- `simple_integration.py`
- `complete_analysis_service.py`

请回答以下问题：

```text
当前视频输入来源字段：
当前视频输入是 URL、路径、还是其他标识：
当前执行层拿到的视频字段：
当前是否已有 source_file_path：
当前是否存在默认测试视频 fallback：
当前是否能明确知道“分析的是哪个真实文件”：
```

要求：
- 只基于当前真实仓库代码判断
- 不要猜测未提交逻辑
- 对不清楚的地方明确写“不明确”

---

## Step 2：统一 `UnifiedTask` 的视频输入字段

请检查当前 `UnifiedTask` 是否已具备以下字段：

- `source_file_url`
- `source_file_name`
- `source_file_path`

如果缺失，请补齐；如果已有，请统一含义：

### 字段语义要求
- `source_file_url`：原始来源地址（如果有）
- `source_file_name`：原始文件名（如果有）
- `source_file_path`：本地实际落盘路径（执行层真正交给分析模块使用的路径）

### 要求
- 不要同时出现多个语义重叠字段，例如：
  - `video_path`
  - `local_video`
  - `input_path`
  - `file_path`
  但又没人知道哪个是真正执行用路径

本步目标是：
**统一认定 `source_file_path` 为最终执行路径。**

---

## Step 3：新增统一视频输入处理模块

请新增一个专门处理视频输入入链的模块。

推荐命名：

```text
video_input_handler.py
```

如果项目已有 `services/` 目录，也可以使用：

```text
services/video_input_handler.py
```

### 这个模块至少负责三件事
1. 根据任务生成工作目录
2. 解析视频输入信息
3. 将真实视频文件整理到标准位置，并返回标准路径

### 建议提供函数
```python
def prepare_video_input(task: UnifiedTask, message: UnifiedMessage) -> UnifiedTask:
    ...
```

也可以拆分为：
```python
def build_task_workdir(task: UnifiedTask) -> str:
    ...

def resolve_video_source(task: UnifiedTask, message: UnifiedMessage) -> dict:
    ...

def prepare_video_input(task: UnifiedTask, message: UnifiedMessage) -> UnifiedTask:
    ...
```

---

## Step 4：标准化任务工作目录

请为每个视频任务生成一个标准工作目录。

建议目录结构示例：

```text
data/tasks/{task_id}/
  input/
    source.mp4
  output/
  logs/
```

或者最小版：

```text
data/tasks/{task_id}/
  source.mp4
```

### 要求
- 目录结构尽量简单
- 当前阶段不追求复杂分层
- 但必须让每个任务有独立工作目录
- 后续日志、抽帧、转码、报告都能往这个目录里放

### 建议
如果仓库中还没有 `data/tasks/` 相关约定，本步顺手建立基础约定，并补 `.gitignore`

---

## Step 5：实现最小视频来源解析规则

请在视频输入处理模块中，按以下优先级解析视频来源：

### 优先级建议
1. 如果 `UnifiedTask.source_file_path` 已存在且文件存在，优先使用
2. 否则，如果 `UnifiedMessage.file_url` 存在，先记录为来源 URL，并进入后续下载 / 复制逻辑
3. 否则，如果 `UnifiedMessage.extra` 中有本地可用路径，尝试使用
4. 否则，判定视频输入不可用，直接失败

### 重要要求
**严禁在视频输入不可用时自动切到默认测试视频。**

### 正确行为
如果没有真实视频输入，就应返回失败，例如：
- `VIDEO_INPUT_MISSING`
- `VIDEO_INPUT_NOT_FOUND`
- `VIDEO_INPUT_PREPARE_FAILED`

而不是伪造一个成功分析流程。

---

## Step 6：实现最小“本地可用文件准备”逻辑

本步不要求上完整下载器，但至少要让以下场景能被标准化处理：

### 场景 A：消息中已经给了本地文件路径
- 检查文件是否存在
- 复制 / 规范化到任务工作目录
- 写入 `task.source_file_path`

### 场景 B：消息中给了 URL
- 当前阶段如果项目还没有稳定下载器，可以：
  - 先记录来源 URL
  - 如果已有简单下载能力则调用
  - 如果没有下载能力，则明确失败并记录原因

### 场景 C：消息中什么都没有
- 直接失败
- 不允许 fallback 到样例视频

### 要求
- 当前重点是“标准化行为”
- 不是“一步到位支持所有下载协议”

---

## Step 7：在 `TaskExecutor` 视频任务执行前接入视频输入准备层

请在视频任务真正执行旧分析能力之前，插入视频输入准备步骤。

目标流程变成：

```text
TaskExecutor._execute_video(...)
    -> prepare_video_input(task, message)
    -> 校验 source_file_path
    -> 再调用旧分析能力
```

### 要求
- 旧分析模块最终只吃 `task.source_file_path`
- 不要再让旧分析能力自己去猜输入路径
- 执行层明确知道这次分析用的是什么文件

---

## Step 8：接入状态与日志

请将第五步的状态与日志能力接到本步新增流程中。

### 视频输入准备开始时
- `mark_running("preparing_video_input")`
- `log_task_event(..., event="video_input_prepare_started")`

### 准备成功时
- `log_task_event(..., event="video_input_prepare_succeeded")`

### 准备失败时
- `mark_failed("VIDEO_INPUT_PREPARE_FAILED", "...", stage="preparing_video_input")`
- `log_task_event(..., event="video_input_prepare_failed")`

### 如果最终进入视频执行
再进入：
- `executing_video`

### 目标
让日志里至少能看出：
- 是“视频还没准备好就失败了”
- 还是“视频已准备好，分析阶段才失败”

---

## Step 9：统一返回结构补充输入信息（适度）

请在统一返回结构中，适度补充和视频输入有关的信息。

不要求把全部路径细节都返回给用户，但建议至少在调试结构中保留：

- `task_id`
- `status`
- `current_stage`
- `source_file_name`
- `source_file_path`（可只在内部结果 / 调试字段中保留）

### 要求
- 返回结构不要过于臃肿
- 但要足够让你知道“分析的是哪个文件”

---

## Step 10：README 增加“Video Input Preparation”说明

请在 README 中补充一节，标题建议：

```md
## Video Input Preparation
```

说明以下内容：
- 视频任务会先经过输入准备层
- 统一解析来源 URL / 本地路径 / 文件名
- 统一生成任务工作目录
- 统一写入 `source_file_path`
- 不再允许视频缺失时自动回退到默认样例视频

### 同时检查 README 中旧描述
请顺手修正：
- 任何暗示“系统会自动兜底到本地样例视频”的说法
- 任何让人误解“输入路径随便传都行”的旧描述

---

## Step 11：新增测试，验证真实视频输入入链逻辑

请新增或完善测试脚本，建议命名：

```text
test_video_input_handler.py
```

至少覆盖以下场景：

### 1. 本地路径可用
- 构造一个临时文件
- 通过 `prepare_video_input(...)`
- 验证 `task.source_file_path` 被正确写入
- 验证文件被标准化到任务目录

### 2. URL 存在但当前无下载能力
- 验证系统返回失败或明确结果
- 不能伪装成功

### 3. 输入完全缺失
- 验证返回 `failed`
- 验证错误码合理
- 不能 fallback 到默认测试视频

### 4. 任务日志与状态
- 验证状态至少经历：
  - `preparing_video_input`
  - `executing_video` 或 `failed`

---

## Step 12：`.gitignore` 补充任务工作目录规则

如果本步引入了：
- `data/tasks/`
- 临时输入文件
- 任务输出目录

请补充 `.gitignore`，例如：

```gitignore
data/tasks/
```

如果需要保留目录结构，可使用：
- `data/tasks/.gitkeep`

### 要求
- 不要把真实测试视频、任务中间文件推到 GitHub
- 不要污染仓库

---

## Step 13：本地自检

完成后请做最小自检，至少验证：

1. `video_input_handler.py` 可正常 import
2. 视频任务可生成独立工作目录
3. 本地文件输入可被写入 `source_file_path`
4. 无输入时会明确失败
5. 不存在自动 fallback 到默认样例视频
6. `TaskExecutor` 已在视频执行前接入输入准备层
7. 状态与日志可区分“输入失败”和“执行失败”

如果可以，请输出类似：

```text
[PASS] video input handler import works
[PASS] task workdir creation works
[PASS] local file input preparation works
[PASS] missing input fails explicitly
[PASS] no default sample fallback
[PASS] executor integrates video input preparation
[PASS] task status distinguishes prepare stage and execute stage
```

---

## Step 14：提交并推送 GitHub

完成后请提交并推送到 GitHub。

建议 commit message：

```bash
feat: add unified video input preparation layer
```

或

```bash
feat: standardize real video input handling for video tasks
```

---

## 五、代码风格要求

### 要求
- 保持简单
- 优先做最小可用的视频输入入链层
- 不引入复杂下载器 / 转码框架
- 不重写分析内核
- 不为了“完整性”过度设计
- 所有视频执行最终只认 `source_file_path`

---

## 六、本步禁止事项

本步**禁止**：
- 自动回退默认测试视频
- 深改旧分析核心模块
- 一口气引入 OSS / COS / 对象存储框架
- 引入复杂视频处理流水线
- 把输入准备逻辑散落到适配器、路由器、分析模块各处
- 为了支持所有来源而把结构做乱

---

## 七、本步完成标准

只有满足以下条件，才算完成：

1. 已新增统一视频输入处理模块
2. `UnifiedTask` 的视频输入字段语义已统一
3. 每个视频任务已能生成标准工作目录
4. 视频执行前已接入输入准备层
5. 系统已明确使用 `source_file_path` 作为最终执行路径
6. 无真实视频输入时会明确失败
7. 已禁止默认样例视频 fallback
8. README 已补充视频输入准备说明
9. 已完成 GitHub 提交与推送

---

## 八、执行后回复格式

请严格按以下结构回复：

### A. 当前视频输入链路梳理
### B. 新增 / 修改的文件列表
### C. `UnifiedTask` 视频输入字段统一情况
### D. 视频输入处理模块实现说明
### E. 任务工作目录约定说明
### F. 执行层如何接入输入准备层
### G. 状态与日志接入情况
### H. 本地自检结果
### I. GitHub 提交与推送结果
### J. 下一步建议（只建议，不直接执行）
