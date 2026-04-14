# 第三步指令单（MD版）
## 任务名称
钉钉主入口与 QQ 辅入口接入统一路由层（不改分析内核）

---

## 一、本步目标

第二步已经完成了以下基础能力：
- 已有统一消息结构 `UnifiedMessage`
- 已有统一任务结构 `UnifiedTask`
- 已有统一路由层 `MessageRouter`
- 视频任务已能接到旧分析能力
- 文本任务已有最小占位能力

本步开始做真正的**渠道接入统一化**。

### 本步唯一目标
把**钉钉主入口**和**QQ 辅入口**，正式接到：

```text
渠道原始消息 -> UnifiedMessage -> MessageRouter -> UnifiedTask -> 现有处理逻辑
```

也就是说，本步要完成的是：

- 钉钉入口适配器
- QQ 入口适配器
- 两个渠道统一走路由层
- 不再让渠道代码直接调用深层分析逻辑

---

## 二、本步边界

### 本步要做
1. 梳理当前仓库中是否已有钉钉 / QQ 入口相关代码残留
2. 新建“渠道适配器”模块
3. 把钉钉原始消息转换为 `UnifiedMessage`
4. 把 QQ 原始消息转换为 `UnifiedMessage`
5. 调用 `MessageRouter` 统一分发
6. 统一输出基础响应结果
7. 为后续接真实 webhook / 机器人 SDK 预留清晰接口
8. 提交并推送到 GitHub

### 本步不要做
本步**不要**：
- 重写 `complete_analysis_service.py`
- 重写 `simple_integration.py`
- 深改 `mediapipe_analyzer.py`
- 改报告生成器内部逻辑
- 改 `fused_knowledge` 知识库结构
- 上复杂异步队列
- 上数据库状态机
- 直接接入生产环境密钥
- 直接做长连接 / 公网部署细节

---

## 三、本步核心思想

当前系统已经有“统一消息模型”和“统一路由器”，  
但**真正的钉钉 / QQ 入口还没有正式纳入这条总线**。

所以本步重点不是“增强分析能力”，而是：

### 把渠道层做薄
以后钉钉和 QQ 只负责三件事：
1. 接收原始消息
2. 转换成 `UnifiedMessage`
3. 把消息交给 `MessageRouter`

分析怎么做、任务怎么建、最终调用谁，**都不应该由渠道层决定**。

---

## 四、执行步骤

### Step 1：梳理当前仓库中的渠道入口现状

请先检查当前 GitHub 仓库中，是否还存在以下情况：

- 残留的钉钉入口逻辑命名痕迹
- 残留的 QQ 入口逻辑命名痕迹
- 旧的机器人 handler 风格代码
- README 中与渠道入口相关的描述
- 第二步新增的 `from_dingtalk()` / `from_qq()` 是否只是静态方法，还是已经可被真正复用

请输出：

```text
当前钉钉入口现状：
当前QQ入口现状：
当前是否已有独立适配器层：
当前渠道代码是否仍与分析逻辑耦合：
当前README是否准确描述了渠道接入方式：
```

要求：
- 只基于当前仓库真实代码判断
- 不要猜测未提交代码
- 不要把未来计划当作已实现能力

---

### Step 2：新建渠道适配器目录或模块

请为“钉钉 / QQ 渠道适配”建立单独模块。

推荐目录方案：

```text
adapters/
  dingtalk_adapter.py
  qq_adapter.py
```

如果当前项目不适合建目录，也可以先使用：

```text
dingtalk_adapter.py
qq_adapter.py
```

要求：
- 渠道适配代码与分析代码分离
- 渠道适配器只负责“解析原始消息 -> UnifiedMessage”
- 不要在适配器里直接写视频分析业务

---

### Step 3：实现钉钉消息适配器

请在钉钉适配器中实现最小可用转换函数。

建议函数命名：

```python
def parse_dingtalk_message(payload: dict) -> UnifiedMessage:
    ...
```

目标：
把钉钉原始 payload 解析成统一消息对象。

#### 至少支持两类消息
1. 文字消息
2. 视频 / 文件消息

#### 输出结构需映射到
- `channel="dingtalk"`
- `message_type`
- `user_id`
- `conversation_id`
- `text`
- `file_url`
- `file_name`
- `extra`

#### 注意
由于当前未必已经接入真实完整钉钉 SDK，本步允许先按“预期 payload 结构”写成兼容函数，但要求：
- 不要瞎编太复杂字段
- 字段提取逻辑要清晰
- 对缺失字段有兜底
- 对未知消息类型要返回 `message_type="unknown"`

建议同时加一个辅助函数：

```python
def handle_dingtalk_payload(payload: dict, router: MessageRouter):
    message = parse_dingtalk_message(payload)
    return router.route_message(message)
```

---

### Step 4：实现 QQ 消息适配器

请在 QQ 适配器中实现最小可用转换函数。

建议函数命名：

```python
def parse_qq_message(payload: dict) -> UnifiedMessage:
    ...
```

目标：
把 QQ 原始 payload 解析成统一消息对象。

#### 至少支持两类消息
1. 文字消息
2. 视频 / 文件消息

#### 输出映射要求
- `channel="qq"`
- `message_type`
- `user_id`
- `conversation_id`
- `text`
- `file_url`
- `file_name`
- `extra`

同样建议加一个入口函数：

```python
def handle_qq_payload(payload: dict, router: MessageRouter):
    message = parse_qq_message(payload)
    return router.route_message(message)
```

---

### Step 5：不要把渠道适配器写成“伪业务层”

#### 强制要求
以下写法禁止出现：

##### 错误示例 1
在 `dingtalk_adapter.py` 中直接：
- new 分析服务
- 调用 `complete_analysis_service`
- 调用 `simple_integration`
- 拼报告
- 直接决定返回格式

##### 错误示例 2
在 `qq_adapter.py` 中写大量业务判断：
- 如果视频就直接走某个分析脚本
- 如果文字就直接回复固定逻辑
- 自己创建一套任务结构

#### 正确做法
适配器只做：

```text
原始消息 -> UnifiedMessage -> Router
```

真正业务统一交给：
- `MessageRouter`
- `UnifiedTask`
- 旧分析能力

---

### Step 6：给路由层补充“统一结果包装”

当前 `MessageRouter` 已经存在。  
本步请顺手补充一个最小统一返回结构，方便后续钉钉 / QQ 共用。

建议最终 `route_message()` 返回统一字典结构，例如：

```python
{
    "task_id": "...",
    "task_type": "video_analysis",
    "status": "success",
    "channel": "dingtalk",
    "message_type": "video",
    "result": ...
}
```

或文本消息返回：

```python
{
    "task_id": "...",
    "task_type": "chat",
    "status": "success",
    "channel": "qq",
    "message_type": "text",
    "result": {
        "message": "..."
    }
}
```

要求：
- 返回结构尽量统一
- 不要求一次性设计得非常完整
- 重点是让两个渠道都能拿到一致的“路由结果格式”

---

### Step 7：给文本消息增加一个更明确的基础回包

第二步里文字任务还是占位。  
本步可以稍微升级一点，但仍保持轻量。

例如：
- 返回 `router received text message`
- 带上 `task_id`
- 带上渠道信息
- 带上原始文本摘要

示例：

```python
{
    "task_id": task.task_id,
    "task_type": "chat",
    "status": "success",
    "channel": message.channel,
    "result": {
        "message": f"received text message from {message.channel}",
        "text": message.text[:100]
    }
}
```

要求：
- 不要在本步里完成真正聊天大模型调用
- 只把链路先打通

---

### Step 8：视频消息仍然只接旧能力，不改内核

再次强调：

#### 本步对视频消息的目标
是让“钉钉 / QQ -> 统一路由 -> 旧视频分析能力”这条链跑通。

#### 本步禁止
- 重写视频分析内核
- 大改参数结构
- 改 MediaPipe 评分逻辑
- 改报告模板机制

#### 正确方式
在 `handle_video_message()` 中继续接现有能力，  
但现在入口变成来自统一适配器，不再假设某个脚本自己就是入口。

---

### Step 9：新增测试文件，验证两个渠道都能进统一路由

请新增或完善测试脚本，命名建议：

```text
test_adapters.py
```

至少测试以下场景：

#### 钉钉
1. 钉钉文字消息 payload -> 成功转成 `UnifiedMessage`
2. 钉钉视频消息 payload -> 成功转成 `UnifiedMessage`
3. 钉钉消息进入 `MessageRouter` 后能得到统一结果结构

#### QQ
4. QQ 文字消息 payload -> 成功转成 `UnifiedMessage`
5. QQ 视频消息 payload -> 成功转成 `UnifiedMessage`
6. QQ 消息进入 `MessageRouter` 后能得到统一结果结构

#### 额外建议
再加一个“未知消息类型”测试，确保不会直接报错。

要求：
- 不追求复杂测试框架
- 有最小可运行验证即可
- 不要为了测试去强行改现有核心逻辑

---

### Step 10：补充 README 渠道接入说明

请更新 `README.md`，新增或补充一节，标题建议：

```md
## Channel Adapters
```

需写清楚：
- 当前系统以钉钉为主入口，QQ 为辅入口
- 钉钉 / QQ 原始消息先转换成 `UnifiedMessage`
- 然后交给 `MessageRouter`
- 渠道层不直接负责分析逻辑
- 当前视频分析仍复用旧能力
- 当前文字处理仍为轻量版本

#### 同时修正文档不一致问题
请顺手修正：
- README 中与真实目录不符的结构描述
- README 中“飞书支持”之类与当前阿里云版本不一致的表述
- README 中任何把“已计划”写成“已实现”的内容

---

### Step 11：清理第二步遗留的小问题

请在本步顺手处理以下明显问题：

#### 1. 清理 `__pycache__`
如果仓库已跟踪 `__pycache__`，请：
- 从 Git 跟踪中移除
- 保留 `.gitignore` 屏蔽规则
- 确保后续不再提交

#### 2. 检查 `.gitignore`
确认以下至少还在：

```gitignore
__pycache__/
*.pyc
*.pyo
```

#### 3. 不要提交新的本地缓存
包括：
- 测试缓存
- 编译缓存
- 临时结果文件

---

### Step 12：本地自检

完成后请做最小自检，至少验证：

1. `dingtalk_adapter.py` 可正常 import
2. `qq_adapter.py` 可正常 import
3. 文本 payload 可转成 `UnifiedMessage`
4. 视频 payload 可转成 `UnifiedMessage`
5. 两个渠道都能把消息送入 `MessageRouter`
6. 返回结果结构一致
7. 不破坏现有旧分析模块 import

如果可以，请输出简短自检结果，例如：

```text
[PASS] dingtalk text payload parsing
[PASS] dingtalk video payload parsing
[PASS] qq text payload parsing
[PASS] qq video payload parsing
[PASS] router integration
[PASS] old analysis imports intact
```

---

### Step 13：提交并推送 GitHub

完成后请提交并推送。

建议 commit message：

```bash
feat: add dingtalk and qq channel adapters
```

或

```bash
feat: connect dingtalk and qq inputs to unified router
```

---

## 五、代码风格要求

### 要求
- 代码保持简单
- 适配器职责单一
- 尽量复用现有 `UnifiedMessage` / `UnifiedTask` / `MessageRouter`
- 不要引入复杂框架
- 不要为了“高级感”过度设计
- 错误处理清楚，但不过度臃肿

---

## 六、本步禁止事项

本步**禁止**：
- 直接接入生产 webhook 和真实密钥
- 深改分析服务内部逻辑
- 在渠道适配器里直接写业务处理
- 新建第二套路由机制
- 把渠道层和模型层重新耦合起来
- 擅自把钉钉 / QQ 写成两套不同任务结构

---

## 七、本步完成标准

只有满足以下条件，才算本步完成：

1. 已新增钉钉适配器
2. 已新增 QQ 适配器
3. 两个适配器都能产出 `UnifiedMessage`
4. 两个渠道都能接入 `MessageRouter`
5. 返回结果结构已统一
6. README 已更新为符合当前阿里云版本实际情况
7. `__pycache__` 等无关文件已清理
8. 已完成 GitHub 提交与推送

---

## 八、执行后回复格式

请严格按以下结构回复：

### A. 当前渠道入口现状梳理
### B. 新增 / 修改的文件列表
### C. 钉钉适配器实现说明
### D. QQ 适配器实现说明
### E. 如何接入统一路由层
### F. 统一返回结构说明
### G. README 修正情况
### H. 本地自检结果
### I. GitHub 提交与推送结果
### J. 下一步建议（只建议，不直接执行）
