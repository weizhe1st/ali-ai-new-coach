# 第四步指令单（MD版）
## 任务名称
引入统一任务执行服务层（不改分析内核，不上复杂队列）

---

## 一、本步目标

第三步已经完成了以下基础能力：
- 已有统一消息结构 `UnifiedMessage`
- 已有统一任务结构 `UnifiedTask`
- 已有统一路由层 `MessageRouter`
- 已有钉钉适配器与 QQ 适配器
- 渠道消息已能进入统一路由

但当前系统大概率仍然是：

```text
Channel Adapter -> MessageRouter -> 直接调用旧分析能力
```

这虽然能跑，但后面会出现几个问题：

1. 路由层会越来越重
2. 任务状态不好统一管理
3. 后续加日志、错误码、重试会很别扭
4. 文字任务和视频任务会越来越耦合在路由器里

### 本步唯一目标
在 **MessageRouter** 和 **旧分析能力** 之间，加一层**统一任务执行服务层**。

目标结构变成：

```text
Channel Adapter -> MessageRouter -> TaskExecutor -> 旧分析能力
```

本步要做的是：
- 新建统一任务执行服务
- 让路由层只负责“建任务 + 分发”
- 让执行层负责“真正执行任务”
- 先不重写分析内核
- 先不上复杂异步队列
- 为下一步增加任务状态、错误码、日志打基础

---

## 二、本步边界

### 本步要做
1. 梳理当前 `router.py` 中哪些逻辑属于“路由”，哪些其实已经是“执行”
2. 新建统一任务执行服务层
3. 把文本任务执行逻辑从路由层迁出
4. 把视频任务执行逻辑从路由层迁出
5. 保持旧分析能力接法基本不变
6. 统一执行结果格式
7. 提交并推送 GitHub

### 本步不要做
本步**不要**：
- 重写 `simple_integration.py`
- 重写 `complete_analysis_service.py`
- 深改 `mediapipe_analyzer.py`
- 改报告生成器内部结构
- 上 Celery / Redis / RabbitMQ
- 上数据库任务队列
- 上并发 worker
- 上任务重试机制
- 接真实生产 webhook
- 一口气把所有任务状态机做完

---

## 三、本步核心思想

### 路由层不该干“执行层”的活
`MessageRouter` 的职责应当是：
- 接收 `UnifiedMessage`
- 判断消息类型
- 生成 `UnifiedTask`
- 把任务交给执行器

而不应该：
- 亲自去跑视频分析
- 亲自处理文本业务
- 自己拼各种最终结果

### 执行层负责真正干活
新加的 `TaskExecutor` 或 `TaskExecutionService` 负责：
- 接收 `UnifiedTask`
- 根据 `task_type` 执行
- 调用旧分析能力
- 返回统一执行结果

这一步完成后，系统会更清楚地分成：

1. **适配层**：接收不同渠道消息
2. **路由层**：负责分流与建任务
3. **执行层**：负责真正执行任务
4. **分析层**：负责旧分析能力

---

## 四、执行步骤

---

## Step 1：梳理当前路由层中的“执行逻辑”

请先检查当前 `router.py` 或相关路由文件，识别以下内容：

- 哪些函数只是做消息分流
- 哪些函数其实已经直接在跑任务
- 哪些代码属于文本任务执行
- 哪些代码属于视频任务执行
- 当前返回结构是不是由路由层直接拼出来的

请输出：

```text
当前路由层中纯路由部分：
当前路由层中混入的执行逻辑：
当前文本任务执行位置：
当前视频任务执行位置：
当前返回结果是否由路由层直接生成：
```

要求：
- 只基于当前仓库真实代码判断
- 不要为了“证明结构好看”而掩盖耦合问题

---

## Step 2：新建统一任务执行服务文件

请新增一个专门执行任务的模块。

推荐命名：

```text
task_executor.py
```

如果项目已有 `services/` 目录，也可使用：

```text
services/task_executor.py
```

建议定义一个类：

```python
class TaskExecutor:
    def execute(self, task: UnifiedTask, message: UnifiedMessage):
        ...
```

也可以采用函数式写法：

```python
def execute_task(task: UnifiedTask, message: UnifiedMessage):
    ...
```

### 要求
- 职责清晰
- 不引入复杂框架
- 优先保持简单
- 执行层负责“真正干活”
- 路由层只负责“决定交给谁”

---

## Step 3：把文本任务执行迁入执行层

请把当前文本任务的处理逻辑从路由层迁移到执行层。

### 当前阶段允许的文本任务能力
本步仍然不要求接真正的大模型聊天链，  
但至少要做到：

- 接收文本任务
- 返回统一执行结果
- 包含 `task_id`
- 包含 `task_type`
- 包含 `status`
- 包含渠道信息
- 包含文本摘要或占位消息

### 建议返回格式

```python
{
    "task_id": task.task_id,
    "task_type": "chat",
    "status": "success",
    "channel": task.channel,
    "message_type": task.message_type,
    "result": {
        "message": "text task executed",
        "text": message.text[:100]
    }
}
```

要求：
- 文本任务执行逻辑放到执行层
- 路由层不要再自己拼文本结果

---

## Step 4：把视频任务执行迁入执行层

请把当前视频任务处理逻辑从路由层迁移到执行层。

### 重要原则
本步迁移的是**执行入口位置**，不是改分析内核。

也就是说：
- 视频怎么分析，暂时仍接旧能力
- 但是“由谁来调用旧能力”，改成执行层负责

### 正确结构
从：

```text
Router -> handle_video_message() -> 旧分析能力
```

改成：

```text
Router -> TaskExecutor.execute(...) -> 旧分析能力
```

### 要求
- 不改旧分析模块内部核心逻辑
- 不大改参数结构
- 只调整调用责任归属
- 路由层不直接写视频业务执行逻辑

---

## Step 5：统一执行结果结构

请让执行层统一返回结果格式，供钉钉 / QQ / 后续其他渠道共用。

建议统一结构：

```python
{
    "task_id": "...",
    "task_type": "video_analysis",
    "status": "success",
    "channel": "dingtalk",
    "message_type": "video",
    "result": ...,
    "error": None
}
```

失败时：

```python
{
    "task_id": "...",
    "task_type": "video_analysis",
    "status": "failed",
    "channel": "qq",
    "message_type": "video",
    "result": None,
    "error": {
        "code": "EXECUTION_ERROR",
        "message": "..."
    }
}
```

### 要求
- 文本任务和视频任务返回结构尽量一致
- 后续增加状态、日志、错误码时不要推翻重来
- 当前先保持最小可用

---

## Step 6：路由层改成“只建任务 + 交执行层”

请修改 `MessageRouter` 的职责，使其更纯粹。

### 路由层本步应负责
1. 接收 `UnifiedMessage`
2. 判断任务类型
3. 构建 `UnifiedTask`
4. 调用 `TaskExecutor`
5. 返回执行结果

### 路由层本步不应负责
- 亲自处理文本业务
- 亲自调用视频分析服务
- 自己定义多套返回格式
- 混入太多业务逻辑

### 目标效果
`route_message()` 变得更像：

```python
def route_message(self, message: UnifiedMessage):
    task = self.build_task_from_message(message)
    return self.executor.execute(task, message)
```

---

## Step 7：为后续状态扩展预留接口，但本步不做复杂状态机

本步不要求完整状态机，但请在执行层里预留一个最轻量的状态更新点。

例如：
- 执行前把任务视为 `running`
- 成功后返回 `success`
- 出错后返回 `failed`

### 可选做法
如果当前 `UnifiedTask` 已经有 `status` 字段，可以在执行层里直接更新：
- `created` -> `running`
- `running` -> `success`
- `running` -> `failed`

### 但注意
- 本步不要引入数据库级状态同步
- 本步不要写复杂持久化逻辑
- 只做内存态 / 结构态上的统一

---

## Step 8：加一层最小错误捕获

请在执行层里给文本任务和视频任务都加最基础的异常捕获。

### 目标
避免：
- 旧分析能力一抛异常，整个渠道直接炸掉
- 路由层和适配器无统一错误结果

### 要求
至少做到：
- 捕获异常
- 返回 `status="failed"`
- 返回最小 `error.code`
- 返回最小 `error.message`

### 当前阶段可接受的错误码
本步先允许使用较粗粒度错误码，例如：
- `TEXT_EXECUTION_ERROR`
- `VIDEO_EXECUTION_ERROR`
- `EXECUTION_ERROR`

后面再细化。

---

## Step 9：新增 / 更新测试，验证“路由层变薄，执行层接管”

请新增或更新测试脚本，建议：

```text
test_task_executor.py
```

至少覆盖以下场景：

### 1. 文本任务执行
- 构造 `UnifiedMessage`
- 通过 `MessageRouter` 进入系统
- 最终由 `TaskExecutor` 返回统一结果

### 2. 视频任务执行
- 构造视频消息
- 通过 `MessageRouter` 进入系统
- 验证视频任务确实由执行层负责调用旧能力

### 3. 异常场景
- 模拟旧分析能力抛异常
- 验证系统返回 `failed` 结构，而不是直接崩

### 4. 结构一致性
- 文本返回结构和视频返回结构字段一致
- 至少包含：
  - `task_id`
  - `task_type`
  - `status`
  - `channel`
  - `message_type`
  - `result`
  - `error`

---

## Step 10：更新 README，补上执行层说明

请在 README 中补充一节，标题建议：

```md
## Task Execution Layer
```

说明以下内容：
- 当前系统已从“适配器 -> 路由 -> 直接分析”升级为“适配器 -> 路由 -> 执行层 -> 分析层”
- `MessageRouter` 只负责分流与建任务
- `TaskExecutor` 负责真正执行任务
- 当前执行层仍复用旧分析能力
- 后续状态管理、日志、错误码会继续在执行层展开

### 同时修正文档口径
请顺手检查 README 中是否还有以下问题：
- 把已规划写成已实现
- 目录说明和真实仓库不一致
- 渠道说明和当前阿里云版本不一致

---

## Step 11：本地自检

完成后请做最小自检，至少验证：

1. `task_executor.py` 可正常 import
2. `MessageRouter` 可正常引用执行层
3. 文本任务不再由路由层直接执行
4. 视频任务不再由路由层直接执行
5. 视频任务仍能接到旧分析能力
6. 出错时能返回统一失败结构
7. 不破坏现有适配器 import

如果可以，请输出类似：

```text
[PASS] task executor import
[PASS] router delegates to executor
[PASS] text task execution moved out of router
[PASS] video task execution moved out of router
[PASS] old analysis still connected
[PASS] unified error structure works
```

---

## Step 12：提交并推送 GitHub

完成后请提交并推送到 GitHub。

建议 commit message：

```bash
feat: introduce task execution layer between router and analysis
```

或

```bash
refactor: move task execution out of router
```

---

## 五、代码风格要求

### 要求
- 保持简单
- 先做最小可用执行层
- 不引入重型框架
- 尽量复用已有 `UnifiedMessage` / `UnifiedTask` / `MessageRouter`
- 不为了“架构好看”而过度设计
- 执行层职责清晰，路由层职责变薄

---

## 六、本步禁止事项

本步**禁止**：
- 重写分析服务内核
- 引入复杂异步队列系统
- 引入数据库任务调度
- 接入真实生产 webhook 和密钥
- 新建第二套执行机制
- 让适配器层直接调用旧分析逻辑
- 让路由层继续承担主要业务执行职责

---

## 七、本步完成标准

只有满足以下条件，才算完成：

1. 已新增统一任务执行服务层
2. 文本任务执行已迁出路由层
3. 视频任务执行已迁出路由层
4. 路由层已变成“建任务 + 调执行层”
5. 执行结果结构已统一
6. 基础错误捕获已加上
7. README 已补充执行层说明
8. 已完成 GitHub 提交与推送

---

## 八、执行后回复格式

请严格按以下结构回复：

### A. 当前路由层与执行层边界梳理
### B. 新增 / 修改的文件列表
### C. 任务执行服务实现说明
### D. 文本任务如何迁入执行层
### E. 视频任务如何迁入执行层
### F. 统一结果结构说明
### G. 错误处理方式说明
### H. 本地自检结果
### I. GitHub 提交与推送结果
### J. 下一步建议（只建议，不直接执行）
