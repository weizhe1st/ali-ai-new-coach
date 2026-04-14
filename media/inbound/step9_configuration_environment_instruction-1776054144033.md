# 第九步指令单（MD版）
## 任务名称
统一配置与环境收口（模型 / 渠道 / 路径 / 开发生产模式）

---

## 一、本步目标

第八步已经完成了以下基础能力：
- 已有统一消息结构 `UnifiedMessage`
- 已有统一任务结构 `UnifiedTask`
- 已有统一路由层 `MessageRouter`
- 已有渠道适配器（钉钉 / QQ）
- 已有统一任务执行层 `TaskExecutor`
- 已有最小任务状态与日志能力
- 已有统一视频输入入链层
- 已有统一分析服务接入层 `AnalysisService`
- 已有统一结果回推层 `ReplyBuilder`

当前主链路已经比较完整了，但大概率还有一个常见问题：

### 当前问题
配置项可能仍然散落在多个地方，例如：
- `analysis_service.py` 里读模型配置
- `simple_integration.py` 里读环境变量
- `qwen_analysis_service.py` 里又有一套配置
- 钉钉 / QQ 各自读自己的 token / webhook / app key
- 路径配置在多个文件里写死
- 开发模式 / 生产模式没有统一开关

这会带来几个后果：
1. 环境切换容易出错
2. 模型切换容易漏改
3. 不同模块对同一个配置项命名不一致
4. 新人接手时很难知道“到底该改哪个地方”
5. 安全风险更高，容易把敏感配置散落在仓库里

### 本步唯一目标
新增一层**统一配置与环境管理层**，把：
- 模型配置
- 渠道配置
- 路径配置
- 运行模式配置（dev / prod）
- 临时开关配置

统一收口到一处管理。

目标结构变成：

```text
Config / Settings Layer
  -> Channel Adapter
  -> TaskExecutor
  -> AnalysisService
  -> ReplyBuilder
  -> VideoInputHandler
```

也就是说，本步要做到：
- 新增统一配置模块
- 各模块不再各自散读环境变量
- 开发 / 生产模式有清晰区分
- 路径约定集中管理
- 敏感配置统一走环境变量
- 为后续部署和联调打基础

---

## 二、本步边界

### 本步要做
1. 梳理当前仓库中配置散落情况
2. 新增统一配置模块
3. 统一模型配置读取方式
4. 统一渠道配置读取方式
5. 统一路径配置
6. 统一运行模式（dev / prod）配置
7. 更新 `.env.example`
8. 更新 README
9. 提交并推送 GitHub

### 本步不要做
本步**不要**：
- 重写分析内核
- 深改任务执行层
- 深改回复层
- 接真实线上 webhook
- 做复杂配置中心
- 引入第三方配置平台
- 做完整密钥轮换系统
- 做 Kubernetes / Docker Compose 部署体系
- 做完整 CI/CD

---

## 三、本步核心思想

### 让“环境切换”成为可控行为
现在你这个系统已经不是一个单脚本 demo 了。  
当它具备：
- 钉钉 / QQ 双渠道
- 视频分析
- 千问模型
- 旧分析兼容
- 开发 / 生产两种模式

配置如果不统一，后面非常容易混乱。

本步的目标不是“做一个很高级的配置系统”，  
而是做一个**简单、集中、可读、可维护**的统一配置层。

---

## 四、执行步骤

---

## Step 1：梳理当前配置散落情况

请先检查当前仓库中，以下配置项分别散落在哪些文件里：

### 模型相关
- DashScope / Qwen API Key
- 模型名（如 `qwen-vl-max`、`qwen-plus` 等）
- 分析服务开关
- 临时 fallback 开关

### 渠道相关
- 钉钉机器人配置
- QQ 机器人配置
- webhook / token / secret / app key 等

### 路径相关
- 视频任务目录
- 临时目录
- 日志目录
- 默认数据目录

### 运行模式相关
- 开发 / 生产模式
- 是否允许临时 fallback
- 是否启用调试日志

请输出：

```text
当前模型配置散落位置：
当前渠道配置散落位置：
当前路径配置散落位置：
当前运行模式配置散落位置：
当前是否存在重复命名 / 重复读取：
```

要求：
- 只基于当前真实仓库代码判断
- 不要猜测外部环境
- 对不明确的地方写“不明确”

---

## Step 2：新增统一配置模块

请新增统一配置模块，推荐命名：

```text
config.py
```

如果你更想明确分层，也可以用：

```text
settings.py
```

### 建议结构
```python
import os
from dataclasses import dataclass

@dataclass
class AppConfig:
    ...

def load_config() -> AppConfig:
    ...
```

### 或分组结构
```python
@dataclass
class ModelConfig:
    ...

@dataclass
class ChannelConfig:
    ...

@dataclass
class PathConfig:
    ...

@dataclass
class RuntimeConfig:
    ...

@dataclass
class AppConfig:
    model: ModelConfig
    channel: ChannelConfig
    paths: PathConfig
    runtime: RuntimeConfig
```

### 要求
- 先做最小可用版本
- 不要过度设计
- 结构清晰即可

---

## Step 3：统一模型配置

请把模型相关配置统一收口，例如：

### 建议字段
- `dashscope_api_key`
- `video_model_name`
- `text_model_name`
- `enable_temp_qwen_fallback`
- `analysis_backend`

### 要求
- 敏感信息只从环境变量读取
- 模型名不要再散落在多个文件里硬编码
- 统一分析服务层从配置模块拿模型配置
- 如果当前仍需要 temporary fallback，请通过明确配置控制，而不是写死在代码流里

---

## Step 4：统一渠道配置

请把渠道相关配置统一收口，例如：

### 建议字段
- `dingtalk_enabled`
- `dingtalk_webhook` / `dingtalk_token` / `dingtalk_secret`
- `qq_enabled`
- `qq_bot_token` / `qq_app_id` / `qq_secret`（按当前项目实际字段）

### 要求
- 不要让 adapter 自己去散读环境变量
- adapter 应通过统一配置模块获取渠道配置
- 当前不要求接真实线上调用，但字段和读取方式要统一

---

## Step 5：统一路径配置

请把路径约定集中到统一配置模块，例如：

### 建议字段
- `base_data_dir`
- `task_data_dir`
- `log_dir`
- `temp_dir`

### 要求
- `video_input_handler.py`
- `task_logger.py`
- 其他读写文件的模块
都尽量通过统一配置拿路径，而不是各自写死。

### 当前最重要的
统一“任务工作目录”的根路径来源，不要多个文件自己决定 `data/tasks/` 在哪里。

---

## Step 6：统一运行模式与开关

请新增最小运行模式配置，例如：

### 建议字段
- `app_env`（`dev` / `prod`）
- `debug`
- `allow_temp_analysis_fallback`
- `verbose_task_logging`

### 要求
- 让开发 / 生产差异通过统一配置体现
- 不要散落在各个文件里用 `if debug:`、`if os.getenv(...)` 自己判断
- 当前不追求复杂 profile 系统，先集中管理

---

## Step 7：让关键模块改为依赖统一配置层

请修改以下关键模块，使其尽量不再各自散读环境变量：

### 优先改造模块
- `analysis_service.py`
- `task_executor.py`
- `video_input_handler.py`
- `adapters/dingtalk_adapter.py`
- `adapters/qq_adapter.py`

### 目标
这些模块应尽量改为：
- import 配置模块
- 使用统一配置对象
- 不再自己拼环境变量读取逻辑

### 要求
- 不要求一次性改掉所有 legacy 文件
- 但主链路必须优先统一

---

## Step 8：更新 `.env.example`

请补齐或修正 `.env.example`，至少体现：

### 模型相关
```env
DASHSCOPE_API_KEY=
VIDEO_MODEL_NAME=qwen-vl-max
TEXT_MODEL_NAME=qwen-plus
ANALYSIS_BACKEND=legacy
ENABLE_TEMP_QWEN_FALLBACK=false
```

### 渠道相关
```env
DINGTALK_ENABLED=false
DINGTALK_WEBHOOK=
DINGTALK_TOKEN=
DINGTALK_SECRET=

QQ_ENABLED=false
QQ_BOT_TOKEN=
QQ_APP_ID=
QQ_SECRET=
```

### 路径相关
```env
BASE_DATA_DIR=./data
TASK_DATA_DIR=./data/tasks
LOG_DIR=./logs
TEMP_DIR=./tmp
```

### 运行模式相关
```env
APP_ENV=dev
DEBUG=true
ALLOW_TEMP_ANALYSIS_FALLBACK=false
VERBOSE_TASK_LOGGING=true
```

### 要求
- 字段名与统一配置模块保持一致
- 不要再保留历史无关字段
- 不要把真实密钥写进去

---

## Step 9：README 增加“Configuration & Environment”说明

请在 README 中补充一节，标题建议：

```md
## Configuration and Environment
```

说明以下内容：
- 当前系统已引入统一配置层
- 模型配置、渠道配置、路径配置、运行模式配置都集中管理
- 敏感配置统一从环境变量读取
- `.env.example` 仅作为模板，不含真实密钥
- 主链路模块优先依赖统一配置对象

### 同时检查 README 中旧描述
请修正任何仍然暗示：
- 各文件自己读环境变量
- 模型名 / token 在各处硬编码
- 开发 / 生产模式没有区分
的表述

---

## Step 10：新增测试，验证统一配置层

请新增或完善测试脚本，建议命名：

```text
test_config.py
```

至少覆盖以下场景：

### 1. 默认配置加载
- 在无完整环境变量时，配置对象能正常构建（不含必须密钥的功能模块可延迟校验）

### 2. 环境变量覆盖
- 设置环境变量
- 验证配置对象能正确读取

### 3. 布尔开关解析
- `true/false`
- `1/0`
- `yes/no`
都能正确解析（如果你愿意实现）

### 4. 主链路模块可使用配置对象
- 至少验证 `analysis_service.py`、adapter 等关键模块可正常接配置

---

## Step 11：本地自检

完成后请做最小自检，至少验证：

1. `config.py` / `settings.py` 可正常 import
2. 配置对象可正常加载
3. `analysis_service.py` 已不再散读环境变量
4. adapter 已开始依赖统一配置层
5. `video_input_handler.py` 已使用统一路径配置
6. `.env.example` 与代码字段一致
7. 主链路运行不被破坏

如果可以，请输出类似：

```text
[PASS] config module import works
[PASS] unified config loads correctly
[PASS] analysis service uses unified config
[PASS] adapters use unified channel config
[PASS] video input handler uses unified path config
[PASS] env example matches config fields
[PASS] main execution path remains intact
```

---

## Step 12：提交并推送 GitHub

完成后请提交并推送到 GitHub。

建议 commit message：

```bash
feat: add unified configuration and environment layer
```

或

```bash
refactor: centralize model, channel, path and runtime settings
```

---

## 五、代码风格要求

### 要求
- 保持简单
- 优先做最小可用统一配置层
- 不引入复杂配置框架
- 不做过重抽象
- 不要求一次性清理所有 legacy 文件
- 主链路优先统一即可

---

## 六、本步禁止事项

本步**禁止**：
- 重写分析内核
- 引入复杂配置中心
- 做完整部署系统
- 继续在主链路里散读环境变量
- 为了兼容旧文件把配置层做得失去意义

---

## 七、本步完成标准

只有满足以下条件，才算完成：

1. 已新增统一配置模块
2. 已统一模型配置读取方式
3. 已统一渠道配置读取方式
4. 已统一路径配置
5. 已统一运行模式配置
6. 主链路关键模块已开始依赖统一配置层
7. `.env.example` 已更新
8. README 已补充配置与环境说明
9. 已完成 GitHub 提交与推送

---

## 八、执行后回复格式

请严格按以下结构回复：

### A. 当前配置散落情况梳理
### B. 新增 / 修改的文件列表
### C. 统一配置模块实现说明
### D. 模型配置统一情况
### E. 渠道配置统一情况
### F. 路径配置统一情况
### G. 运行模式与开关统一情况
### H. `.env.example` 更新情况
### I. 本地自检结果
### J. GitHub 提交与推送结果
### K. 下一步建议（只建议，不直接执行）
