# 第七步指令单（MD版）
## 任务名称
标准化旧分析能力接入层（让执行层只调用统一分析服务，不直接耦合旧脚本）

---

## 一、本步目标

第六步已经完成了以下基础能力：
- 已有统一消息结构 `UnifiedMessage`
- 已有统一任务结构 `UnifiedTask`
- 已有统一路由层 `MessageRouter`
- 已有渠道适配器（钉钉 / QQ）
- 已有统一任务执行层 `TaskExecutor`
- 已补充最小任务状态与日志记录能力
- 已补齐统一视频输入入链层，能把真实视频写入 `source_file_path`

但是当前系统很可能仍存在一个问题：

### 当前问题
虽然执行层已经更规范了，但视频分析真正调用的能力，仍然可能是：
- 直接调 `simple_integration.py`
- 直接调 `complete_analysis_service.py`
- 或其他旧脚本 / 旧函数入口

这会带来几个风险：
1. `TaskExecutor` 仍然知道太多旧分析模块细节
2. 旧分析模块输入格式不统一
3. 旧分析模块返回格式不统一
4. 后续替换模型、替换实现、增加知识库对照时，会继续在执行层里越堆越乱

### 本步唯一目标
新增一层**统一分析服务接入层**，把旧分析能力包起来，让执行层只依赖一个标准分析接口。

目标结构变成：

```text
Channel Adapter
  -> MessageRouter
    -> TaskExecutor
      -> AnalysisFacade / AnalysisServiceAdapter
        -> 旧分析能力（simple_integration / complete_analysis_service / 其他）
```

也就是说，本步要做到：
- 新增统一分析服务接入层
- 执行层不再直接耦合旧分析脚本
- 视频分析统一吃 `task.source_file_path`
- 视频分析统一返回标准结构
- 为后续替换千问模型调用策略、接知识库、换分析内核留接口

---

## 二、本步边界

### 本步要做
1. 梳理当前执行层是如何调用旧分析能力的
2. 新增统一分析服务接入层
3. 标准化视频分析输入
4. 标准化视频分析输出
5. 让 `TaskExecutor` 改为调用统一分析服务
6. 保留旧分析能力不重写
7. 提交并推送 GitHub

### 本步不要做
本步**不要**：
- 重写 `simple_integration.py` 内核
- 重写 `complete_analysis_service.py` 内核
- 深改 MediaPipe 分析逻辑
- 重写报告生成器
- 引入复杂多模型编排
- 一口气接完整知识库对照
- 做完整评分体系重构
- 做复杂前端渲染输出

---

## 三、本步核心思想

### 执行层不该直接“懂旧脚本”
`TaskExecutor` 的职责是：
- 管任务执行
- 管状态更新
- 管错误捕获
- 管统一返回结构

它不应该知道：
- 哪个旧脚本要传什么特殊参数
- 哪个旧模块返回什么杂乱字段
- 哪个旧实现还带 fallback 逻辑

这些都应该收口到：
**统一分析服务接入层**

---

## 四、执行步骤

---

## Step 1：梳理当前旧分析能力调用位置

请先检查当前仓库中，视频任务最终是怎么调用旧分析能力的。

重点检查：
- `task_executor.py`
- `simple_integration.py`
- `complete_analysis_service.py`
- 其他与视频分析相关的核心文件

请输出：

```text
当前视频分析调用入口：
当前执行层直接依赖的旧模块：
当前视频分析输入字段：
当前视频分析输出结构：
当前是否存在多个旧入口并行：
当前是否存在默认样例 / fallback 逻辑残留：
```

要求：
- 只根据当前真实仓库代码判断
- 不要猜测外部未提交代码
- 对不明确的点明确写“不明确”

---

## Step 2：新建统一分析服务接入层模块

请新增一个专门承接旧分析能力的模块。

推荐命名：

```text
analysis_service.py
```

如果你更想表达“适配旧能力”，也可以使用：

```text
analysis_adapter.py
```

### 建议结构
```python
class AnalysisService:
    def analyze_video(self, task: UnifiedTask) -> dict:
        ...
```

或：

```python
def analyze_video(task: UnifiedTask) -> dict:
    ...
```

### 要求
- 统一分析服务接入层只负责：
  - 接收标准任务输入
  - 调用旧分析能力
  - 规范化返回结构
- 不要在这一层加入太多业务判断
- 不要一开始做太复杂的抽象

---

## Step 3：统一视频分析输入规范

请在统一分析服务接入层中明确规定：

### 视频分析唯一可信输入
- `task.source_file_path`

### 可选辅助输入
- `task.source_file_name`
- `task.source_file_url`
- `task.extra`

### 强制要求
分析服务接入层不应再自己去猜：
- 默认视频路径
- 测试样例路径
- 某个写死的本地 mp4 路径

如果 `task.source_file_path` 不存在或文件不存在，应明确失败，例如：
- `VIDEO_SOURCE_PATH_MISSING`
- `VIDEO_SOURCE_PATH_NOT_FOUND`

**禁止自动 fallback 到默认样例视频。**

---

## Step 4：统一视频分析输出规范

请定义统一分析结果结构，不要求一次性非常复杂，但要足够稳定。

建议返回结构：

```python
{
    "success": True,
    "analysis_type": "video",
    "summary": "...",
    "report": "...",
    "structured_result": {
        "action_type": "...",
        "issues": [...],
        "advice": [...]
    },
    "raw_result": ...,
    "error": None
}
```

失败时：

```python
{
    "success": False,
    "analysis_type": "video",
    "summary": "",
    "report": None,
    "structured_result": None,
    "raw_result": None,
    "error": {
        "code": "VIDEO_ANALYSIS_FAILED",
        "message": "..."
    }
}
```

### 要求
- `TaskExecutor` 最终只吃这套标准结构
- 不要让执行层继续兼容多个旧返回格式
- 当前先统一最小可用输出

---

## Step 5：在统一分析服务接入层中包裹旧分析能力

请把当前已有旧分析能力包进去。

例如可能是以下任一种：
- 调 `simple_integration.py` 中已有方法
- 调 `complete_analysis_service.py` 中已有方法
- 调某个旧 analyzer / report generator 组合
- 其他已存在的视频分析入口

### 要求
- 尽量不改旧分析内核
- 通过适配层把输入 / 输出统一
- 如果旧模块输入需要特殊格式，也在这一层做转换
- 如果旧模块返回杂乱结构，也在这一层统一整理

### 目标
让后续替换旧实现时，只需要改统一分析服务接入层，而不是改执行层。

---

## Step 6：让 `TaskExecutor` 改为调用统一分析服务

请修改 `TaskExecutor._execute_video(...)`，使其不再直接依赖旧分析脚本，而是改为：

```text
TaskExecutor
  -> AnalysisService.analyze_video(task)
```

### 要求
- 执行层只负责：
  - 更新状态
  - 记日志
  - 捕获异常
  - 调统一分析服务
  - 包装统一结果
- 不再在执行层里混入旧分析模块细节

---

## Step 7：分析服务接入层接入状态与日志（轻量）

本步不要求把所有日志打满，但至少补最小事件：

### 开始分析时
- `log_task_event(..., event="video_analysis_started")`

### 分析成功时
- `log_task_event(..., event="video_analysis_succeeded")`

### 分析失败时
- `log_task_event(..., event="video_analysis_failed")`

### 可选
如果方便，可在分析服务接入层中记录：
- 使用的分析入口名称
- 使用的核心模块名称

例如：
- `entry="simple_integration"`
- `entry="complete_analysis_service"`

这样后续排障时更清楚。

---

## Step 8：收口旧 fallback / 样例逻辑

请检查旧分析能力里是否还有以下风险：

- 默认本地样例视频路径
- 测试演示视频
- 视频不存在时自动切样例
- 旧腾讯云 / 微信环境的写死路径

### 处理原则
本步不要求彻底删除所有旧代码，但至少要做到：
- 生产主链路不再自动走 fallback
- 如果有 fallback，只能保留在开发测试模式，且必须明确隔离
- 统一分析服务接入层不能默认启用 fallback

### 目标
让主链路始终优先真实任务输入。

---

## Step 9：README 增加“Analysis Service Layer”说明

请在 README 中补充一节，标题建议：

```md
## Analysis Service Layer
```

说明以下内容：
- 当前执行层不再直接依赖旧分析脚本
- 已新增统一分析服务接入层
- 统一分析服务接入层负责：
  - 吃标准输入 `source_file_path`
  - 调用旧分析能力
  - 输出标准分析结果
- 后续切换实现或增强分析流程时，优先在这一层演进

### 同时顺手检查 README 中旧口径
请修正任何仍在暗示：
- 执行层直接调用旧脚本
- 视频路径可随便传
- 默认样例视频会自动兜底
的表述

---

## Step 10：新增测试，验证统一分析服务接入层

请新增或完善测试脚本，建议命名：

```text
test_analysis_service.py
```

至少覆盖以下场景：

### 1. 正常视频输入
- 构造带 `source_file_path` 的任务
- 调用统一分析服务
- 验证能返回标准结构

### 2. 输入路径缺失
- 验证返回失败
- 错误码明确
- 不允许伪造成功

### 3. 旧分析能力抛异常
- 模拟旧模块报错
- 验证统一分析服务返回标准失败结构

### 4. 执行层集成
- 验证 `TaskExecutor` 现在是通过统一分析服务调用视频分析
- 不再直接依赖旧脚本细节

---

## Step 11：本地自检

完成后请做最小自检，至少验证：

1. `analysis_service.py` 可正常 import
2. 视频分析唯一执行输入为 `task.source_file_path`
3. 输入路径缺失时会明确失败
4. 执行层已改为通过统一分析服务进行视频分析
5. 统一分析输出结构可用
6. 不存在自动 fallback 到默认样例视频
7. 状态与日志可反映分析开始 / 成功 / 失败

如果可以，请输出类似：

```text
[PASS] analysis service import works
[PASS] video analysis input uses source_file_path only
[PASS] missing source path fails explicitly
[PASS] executor delegates video analysis to analysis service
[PASS] unified analysis result structure works
[PASS] no default sample fallback in main path
[PASS] analysis status and log events work
```

---

## Step 12：提交并推送 GitHub

完成后请提交并推送到 GitHub。

建议 commit message：

```bash
feat: add unified analysis service layer for video tasks
```

或

```bash
refactor: decouple executor from legacy video analysis entrypoints
```

---

## 五、代码风格要求

### 要求
- 保持简单
- 优先做最小可用统一分析服务接入层
- 不重写旧分析内核
- 不过度抽象
- 不为了“架构图好看”而制造太多中间层
- 执行层和旧分析能力之间只隔一层即可

---

## 六、本步禁止事项

本步**禁止**：
- 重写分析核心算法
- 直接在执行层继续堆旧分析细节
- 自动 fallback 到默认样例视频
- 一口气把知识库、评分、报告系统全部重构
- 为了兼容旧代码而让统一分析服务层失去标准化意义

---

## 七、本步完成标准

只有满足以下条件，才算完成：

1. 已新增统一分析服务接入层
2. 视频分析输入已统一为 `source_file_path`
3. 视频分析输出已统一为标准结构
4. 执行层已改为通过统一分析服务调用视频分析
5. 主链路已禁止默认样例 fallback
6. README 已补充统一分析服务层说明
7. 已完成 GitHub 提交与推送

---

## 八、执行后回复格式

请严格按以下结构回复：

### A. 当前旧分析能力调用梳理
### B. 新增 / 修改的文件列表
### C. 统一分析服务接入层实现说明
### D. 视频分析输入统一情况
### E. 视频分析输出统一情况
### F. 执行层如何接入统一分析服务
### G. fallback / 样例逻辑收口情况
### H. 本地自检结果
### I. GitHub 提交与推送结果
### J. 下一步建议（只建议，不直接执行）
