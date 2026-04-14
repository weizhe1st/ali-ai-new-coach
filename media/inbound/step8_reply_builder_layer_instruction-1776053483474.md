# 第八步指令单（MD版）
## 任务名称
引入统一结果回推层（让钉钉 / QQ 不再各自拼回复）

---

## 一、本步目标

第七步已经完成了以下基础能力：
- 已有统一消息结构 `UnifiedMessage`
- 已有统一任务结构 `UnifiedTask`
- 已有统一路由层 `MessageRouter`
- 已有渠道适配器（钉钉 / QQ）
- 已有统一任务执行层 `TaskExecutor`
- 已有最小任务状态与日志能力
- 已有统一视频输入入链层
- 已有统一分析服务接入层 `AnalysisService`

当前系统的主链路已经基本成型：

```text
Channel Adapter
  -> MessageRouter
    -> TaskExecutor
      -> AnalysisService
        -> Legacy Analysis
```

但现在大概率还有一个明显问题：

### 当前问题
钉钉和 QQ 最终如何回复用户，仍然可能是：
- 各自在适配器里拼字符串
- 各自判断成功 / 失败格式
- 各自决定如何展示分析结果
- 各自直接读取旧字段

这会导致：
1. 同一份分析结果，钉钉和 QQ 展示不一致
2. 失败提示不一致
3. 文本任务、视频任务、异常场景没有统一输出规范
4. 后续接网页端 / 小程序端时还得再写第三套返回逻辑

### 本步唯一目标
新增一层**统一结果回推层 / 回复格式化层**，让所有渠道都统一吃执行层返回结构，再由这一层决定如何生成对用户可见的回复内容。

目标结构变成：

```text
Channel Adapter
  -> MessageRouter
    -> TaskExecutor
      -> AnalysisService
        -> Legacy Analysis

TaskExecutor Result
  -> ReplyBuilder / PushService
    -> Dingtalk Output
    -> QQ Output
```

也就是说，本步要做到：
- 定义统一“用户可见回复对象”
- 定义统一结果格式化逻辑
- 钉钉 / QQ 不再自己拼复杂回复
- 成功、失败、处理中提示都有统一规范
- 为后续网页端 / API / 小程序输出留接口

---

## 二、本步边界

### 本步要做
1. 梳理当前钉钉 / QQ 是如何构造回复内容的
2. 新增统一回复构建模块
3. 统一文本任务回复格式
4. 统一视频分析任务回复格式
5. 统一失败回复格式
6. 让钉钉 / QQ 适配器改为调用统一回复层
7. 更新 README
8. 提交并推送 GitHub

### 本步不要做
本步**不要**：
- 重写分析内核
- 深改 `TaskExecutor`
- 深改 `AnalysisService`
- 接真实钉钉 webhook 推送接口
- 接真实 QQ 回调接口
- 做富文本卡片 / Markdown 高级渲染
- 做前端页面渲染
- 做多语言文案系统
- 做模板引擎平台

---

## 三、本步核心思想

### 让“执行结果”和“用户看到的话”分开
当前 `TaskExecutor` 返回的是系统内部执行结果，它适合程序流转，但不一定适合直接发给用户。

例如执行层返回结构可能是：

```python
{
    "task_id": "...",
    "task_type": "video_analysis",
    "status": "success",
    "current_stage": "completed",
    "result": {...},
    "error": None
}
```

但用户真正要看到的应该是：

```text
发球分析已完成

总评：
...

关键问题：
1. ...
2. ...

建议：
...
```

所以本步的目标是加一个中间层，把：
- **内部执行结果**
转换成
- **外部用户可见回复**

---

## 四、执行步骤

---

## Step 1：梳理当前回复生成方式

请先检查当前仓库中，钉钉 / QQ 的回复内容目前是在哪里拼装出来的。

重点检查：
- `adapters/dingtalk_adapter.py`
- `adapters/qq_adapter.py`
- `router.py`
- `task_executor.py`
- 其他可能直接拼 reply / message / report 的地方

请输出：

```text
当前钉钉回复生成位置：
当前QQ回复生成位置：
当前是否存在多个回复格式来源：
当前成功回复格式：
当前失败回复格式：
当前是否存在旧字段直读：
```

要求：
- 只根据当前真实仓库代码判断
- 不要猜测未提交代码
- 对不明确的地方写“不明确”

---

## Step 2：新增统一回复构建模块

请新增一个统一回复构建模块，命名建议：

```text
reply_builder.py
```

如果你更想强调渠道输出，也可以用：

```text
push_service.py
```

但本步建议先用 `reply_builder.py`，因为当前目标更偏“构建统一回复内容”，不是接真实推送网关。

### 建议结构
```python
class ReplyBuilder:
    def build_reply(self, execution_result: dict) -> dict:
        ...
```

也可以拆为：
```python
def build_text_reply(execution_result: dict) -> dict:
    ...

def build_video_reply(execution_result: dict) -> dict:
    ...

def build_error_reply(execution_result: dict) -> dict:
    ...
```

---

## Step 3：定义统一回复对象结构

请先定义一个最小可用的统一回复对象结构。

建议结构例如：

```python
{
    "success": True,
    "reply_type": "text",
    "title": "发球分析已完成",
    "message": "...",
    "details": [...],
    "raw_result": ...
}
```

失败时：

```python
{
    "success": False,
    "reply_type": "error",
    "title": "分析失败",
    "message": "本次视频未能成功分析",
    "details": ["错误码：...", "原因：..."],
    "raw_result": ...
}
```

### 要求
- 统一回复对象面向“渠道输出”
- 不要求一开始就做复杂富文本
- 重点是把结构统一下来
- `raw_result` 可选保留，便于调试

---

## Step 4：统一文本任务回复格式

请为文本任务定义统一回复格式。

当前阶段文本任务还不是重点，所以可以保持轻量，但要统一。

### 建议成功回复
```python
{
    "success": True,
    "reply_type": "text",
    "title": "文本任务已处理",
    "message": "...",
    "details": []
}
```

### 建议失败回复
```python
{
    "success": False,
    "reply_type": "error",
    "title": "文本任务处理失败",
    "message": "...",
    "details": [...]
}
```

### 要求
- 不要让钉钉 / QQ 各自拼文本任务回复
- 文本任务先统一格式，不追求复杂体验

---

## Step 5：统一视频任务回复格式

请为视频任务定义统一回复格式。

视频任务是当前主重点，建议至少包含：

### 建议成功回复内容
- 标题：如“发球分析已完成”
- 总评 / summary
- 核心问题列表
- 改进建议列表
- 任务编号（可选）
- 错误信息为空

### 建议统一结构
```python
{
    "success": True,
    "reply_type": "analysis_report",
    "title": "发球分析已完成",
    "message": "本次发球动作整体节奏基本建立，但抛球稳定性和击球点仍需优先修正。",
    "details": [
        "关键问题 1：抛球路径不稳定",
        "关键问题 2：击球点偏低",
        "建议：优先固定抛球出手点"
    ],
    "task_id": "...",
    "raw_result": ...
}
```

### 要求
- 不要求一次性做复杂报告模板
- 但至少保证不同渠道看到的核心内容一致
- 统一基于 `TaskExecutor` / `AnalysisService` 标准结果生成

---

## Step 6：统一失败回复格式

请为所有失败场景定义统一失败回复。

### 覆盖范围
- 文本任务失败
- 视频输入准备失败
- 视频分析失败
- 路由 / 执行异常

### 建议失败结构
```python
{
    "success": False,
    "reply_type": "error",
    "title": "任务执行失败",
    "message": "本次任务未成功完成，请检查输入或稍后重试。",
    "details": [
        "错误码：VIDEO_INPUT_PREPARE_FAILED",
        "阶段：preparing_video_input"
    ],
    "task_id": "..."
}
```

### 要求
- 用户可读
- 但不能暴露过多内部实现细节
- 渠道层不再自己决定错误文案

---

## Step 7：让钉钉 / QQ 适配器改为使用统一回复层

请修改钉钉 / QQ 适配器，使其流程变成：

```text
payload
  -> UnifiedMessage
    -> MessageRouter
      -> TaskExecutor result
        -> ReplyBuilder
          -> 渠道最终输出
```

### 要求
- 适配器只负责：
  - 接收原始 payload
  - 转成 `UnifiedMessage`
  - 调用路由
  - 调用统一回复层
  - 返回渠道可发出的内容

### 禁止
- 适配器自己直接解析执行结果拼复杂文案
- 适配器自己各写一套分析报告格式

---

## Step 8：为不同渠道保留最小格式适配，但不改内容逻辑

钉钉和 QQ 的回复格式可能略有差异，例如：
- 钉钉可能更适合简单文本
- QQ 可能也只返回纯文本

本步允许在适配器末端做**极薄的格式适配**，例如：
- 把统一回复对象转成一个字符串
- 或转成一个渠道要求的最小字典结构

但**内容逻辑必须来自统一回复层**，不能再散落回各个渠道里。

---

## Step 9：为统一回复层增加一个“纯文本渲染器”

建议顺手加一个最小纯文本渲染函数，例如：

```python
def render_reply_as_text(reply: dict) -> str:
    ...
```

这样可以让钉钉、QQ 当前都先走纯文本格式。

### 目标
先把内容统一起来，再考虑：
- Markdown
- 卡片消息
- 富文本
- 小程序页面

---

## Step 10：README 增加“Reply Builder / Push Layer”说明

请在 README 中补充一节，标题建议：

```md
## Reply Builder Layer
```

说明以下内容：
- 执行层返回的是内部执行结果
- 统一回复层负责把内部结果转成用户可见回复
- 钉钉 / QQ 不再各自拼分析报告
- 当前主要输出为统一纯文本回复
- 后续可扩展为富文本 / 卡片 / 网页端 / API 输出

### 同时顺手检查 README
请修正任何仍在暗示：
- 渠道层直接拼分析结果
- 不同渠道各有独立回复模板
- 执行层结果可直接发给用户
的描述

---

## Step 11：新增测试，验证统一回复层

请新增或完善测试脚本，建议命名：

```text
test_reply_builder.py
```

至少覆盖以下场景：

### 1. 文本任务成功回复
- 输入一个文本任务成功的执行结果
- 验证统一回复对象结构正确
- 验证可渲染为纯文本

### 2. 视频任务成功回复
- 输入一个视频分析成功结果
- 验证标题 / message / details 可正确生成

### 3. 视频任务失败回复
- 输入一个失败结果
- 验证统一错误文案结构正确

### 4. 渠道接入
- 验证钉钉 / QQ 适配器都通过 `ReplyBuilder`
- 不再直接拼复杂报告字符串

---

## Step 12：本地自检

完成后请做最小自检，至少验证：

1. `reply_builder.py` 可正常 import
2. 文本任务可生成统一回复对象
3. 视频任务可生成统一回复对象
4. 失败任务可生成统一失败回复
5. 统一回复对象可被渲染为纯文本
6. 钉钉适配器已接入统一回复层
7. QQ 适配器已接入统一回复层

如果可以，请输出类似：

```text
[PASS] reply builder import works
[PASS] text task reply building works
[PASS] video task reply building works
[PASS] failure reply building works
[PASS] plain text renderer works
[PASS] dingtalk adapter uses reply builder
[PASS] qq adapter uses reply builder
```

---

## Step 13：提交并推送 GitHub

完成后请提交并推送到 GitHub。

建议 commit message：

```bash
feat: add unified reply builder layer for channel outputs
```

或

```bash
refactor: standardize dingtalk and qq replies through reply builder
```

---

## 五、代码风格要求

### 要求
- 保持简单
- 优先做最小可用统一回复层
- 不引入复杂模板引擎
- 不做过重富文本系统
- 钉钉 / QQ 当前先统一纯文本回复即可
- 内容逻辑统一，渠道格式差异最小化

---

## 六、本步禁止事项

本步**禁止**：
- 重写分析内核
- 深改任务执行层
- 适配器继续各自拼复杂文案
- 一口气引入卡片 / 富文本 / 多端模板系统
- 为了不同渠道展示差异而重新分裂回复逻辑

---

## 七、本步完成标准

只有满足以下条件，才算完成：

1. 已新增统一回复构建模块
2. 已定义统一回复对象结构
3. 已统一文本任务回复格式
4. 已统一视频任务回复格式
5. 已统一失败回复格式
6. 钉钉适配器已接入统一回复层
7. QQ 适配器已接入统一回复层
8. README 已补充统一回复层说明
9. 已完成 GitHub 提交与推送

---

## 八、执行后回复格式

请严格按以下结构回复：

### A. 当前回复生成方式梳理
### B. 新增 / 修改的文件列表
### C. 统一回复构建模块实现说明
### D. 文本任务回复统一情况
### E. 视频任务回复统一情况
### F. 失败回复统一情况
### G. 钉钉 / QQ 如何接入统一回复层
### H. 本地自检结果
### I. GitHub 提交与推送结果
### J. 下一步建议（只建议，不直接执行）
