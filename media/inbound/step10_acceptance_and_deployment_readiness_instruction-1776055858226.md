# 第十步指令单（MD版）
## 任务名称
联调验收与上线前清单（不再新增大架构，只做整链路验证与收尾）

---

## 一、本步目标

第九步已经完成了以下基础能力：
- 已有统一消息结构 `UnifiedMessage`
- 已有统一任务结构 `UnifiedTask`
- 已有统一路由层 `MessageRouter`
- 已有渠道适配器（钉钉 / QQ）
- 已有统一任务执行层 `TaskExecutor`
- 已有最小任务状态与日志能力
- 已有统一视频输入入链层
- 已有统一分析服务接入层 `AnalysisService`
- 已有统一结果回推层 `ReplyBuilder`
- 已有统一配置与环境管理层 `config.py`

到这里为止，系统主骨架已经基本完成。  
**本步不再做新的大架构改造。**

### 本步唯一目标
对当前主链路做一次**系统级联调验收**，并形成一份可执行的**上线前检查清单**。

目标不是继续“设计”，而是确认：
- 这套系统现在到底能不能稳定跑
- 哪些链路已经通
- 哪些仍是开发态
- 哪些风险在上线前必须处理
- 哪些问题可以列入后续优化

---

## 二、本步边界

### 本步要做
1. 梳理当前系统主链路
2. 建立验收测试清单
3. 验证文字任务链路
4. 验证视频任务链路
5. 验证失败场景处理
6. 验证配置层与环境变量
7. 验证日志、状态、回复层是否协同
8. 输出上线前风险清单
9. 更新 README / 验收文档
10. 提交并推送 GitHub

### 本步不要做
本步**不要**：
- 新增新的大架构层
- 重写分析内核
- 重写执行层
- 重写回复层
- 引入复杂队列
- 引入数据库任务系统
- 引入前端页面
- 做部署平台自动化
- 为了验收而重新设计系统

---

## 三、本步核心思想

### 现在不是继续“搭架子”，而是验证“架子有没有真站住”
前 1~9 步做的是系统骨架整理。  
第 10 步做的是：

- 看它在真实链路中能不能站住
- 把“能跑”和“可上线”区分开
- 给出清晰的上线前结论

本步的产出不只是代码，  
还应该包括：
- 验收脚本 / 测试
- 风险列表
- 上线前检查表
- 当前版本状态说明

---

## 四、执行步骤

---

## Step 1：梳理当前主链路并形成验收视图

请先基于当前仓库真实代码，梳理主链路，确认当前理论主流程应为：

```text
DingTalk / QQ payload
  -> Adapter
    -> UnifiedMessage
      -> MessageRouter
        -> UnifiedTask
          -> TaskExecutor
            -> VideoInputHandler（视频任务）
            -> AnalysisService（视频任务）
            -> ReplyBuilder
              -> 渠道输出
```

请输出：

```text
当前文字任务主链路：
当前视频任务主链路：
当前失败场景主链路：
当前 dev/prod 配置入口：
当前日志与状态入口：
```

要求：
- 只根据当前真实仓库代码判断
- 不要写理想架构
- 要写当前实际主链路

---

## Step 2：新增验收清单文档

请新增一个验收文档，命名建议：

```text
ACCEPTANCE_CHECKLIST.md
```

或

```text
DEPLOYMENT_READINESS_CHECKLIST.md
```

文档应至少包含：

### 1. 已完成能力
- 统一消息结构
- 统一任务结构
- 路由层
- 执行层
- 视频输入准备层
- 分析服务层
- 回复层
- 配置层

### 2. 需验证链路
- 文本任务
- 视频任务
- 视频输入失败
- 分析失败
- 配置缺失
- ReplyBuilder 输出一致性

### 3. 上线前风险项
- 临时 fallback 是否仍存在
- legacy 文件是否仍可能误调用
- 渠道真实回调是否已联通
- 生产环境变量是否齐全
- 日志是否足够排障

---

## Step 3：验证文字任务链路

请对文字任务做最小联调验证。

### 至少覆盖
1. 构造钉钉文字消息 payload
2. 经过 adapter -> router -> executor -> reply builder
3. 最终生成统一用户回复

同样对 QQ 文字消息做一次。

### 验收点
- 不报错
- 能生成 `UnifiedMessage`
- 能生成 `UnifiedTask`
- 能返回统一 reply
- 状态能标记为 success / failed
- 回复文案来自统一回复层，而不是 adapter 自己拼

---

## Step 4：验证视频任务链路

请对视频任务做最小联调验证。

### 至少覆盖
1. 构造钉钉视频消息 payload
2. 经过 adapter -> router -> executor
3. 进入 video input preparation
4. 写入 `source_file_path`
5. 调用 `AnalysisService`
6. 调用 `ReplyBuilder`
7. 返回统一用户回复

同样对 QQ 视频消息做一次。

### 验收点
- 视频任务工作目录生成正确
- `source_file_path` 被写入
- `AnalysisService` 只使用标准输入
- ReplyBuilder 输出统一
- 不再直接依赖旧 reply 逻辑

---

## Step 5：验证失败场景

请至少验证以下失败场景：

### 场景 A：视频输入缺失
- 无 `file_url`
- 无本地路径
- 无可用文件信息

预期：
- 任务失败
- 错误码清晰
- 回复层给出统一失败回复
- 不允许 fallback 到默认样例视频

### 场景 B：分析服务失败
- 模拟 `AnalysisService` 抛异常
- 或返回标准失败结构

预期：
- `TaskExecutor` 能捕获
- 状态标记为 failed
- 回复层给出统一错误回复

### 场景 C：配置缺失
- 缺少关键环境变量（如 DashScope API Key）

预期：
- 配置层或分析层明确失败
- 不允许静默退化
- 错误信息可排查

---

## Step 6：验证统一配置层

请对统一配置层做联调确认。

### 至少验证
1. `config.py` 可加载 dev 模式配置
2. `config.py` 可加载 prod 模式配置
3. `analysis_service.py` 使用配置层
4. adapter 不再直接散读环境变量（至少主链路优先如此）
5. 路径配置会正确生成工作目录
6. `.env.example` 与代码字段一致

### 验收结论需明确区分
- 哪些模块已完全接入配置层
- 哪些 legacy 文件仍未接入，但不在主链路

---

## Step 7：验证状态、日志、回复是否协同

请至少确认以下协同关系：

### 对文字任务
- 状态流转正常
- 日志可记录执行开始 / 成功 / 失败
- reply builder 输出与状态一致

### 对视频任务
- `preparing_video_input`
- `executing_video`
- `completed` / `failed`

### 验收点
- 状态、日志、回复三者不应相互矛盾
- 例如不能出现：
  - 状态 success，但 reply 是失败
  - 日志显示分析失败，但回复仍显示完成

---

## Step 8：整理 legacy / compatibility 文件清单

当前仓库中很可能还存在一些 legacy 文件，例如：
- `simple_integration.py`
- `complete_analysis_service.py`
- `qwen_analysis_service.py`
- `qwen_analysis_simple.py`
- 历史部署说明
- 旧 callback 示例

请新增一个简单文档，命名建议：

```text
LEGACY_FILES_STATUS.md
```

至少说明：
- 哪些文件仍参与主链路
- 哪些文件只作为兼容层存在
- 哪些文件属于历史遗留，不应作为主入口继续调用

### 目标
让后续维护者知道：
**主链路只有一条，其他文件不是并行主入口。**

---

## Step 9：README 增加“System Readiness / Deployment Status”说明

请在 README 中补充一节，标题建议：

```md
## System Readiness
```

说明以下内容：
- 当前系统主链路已完成到哪一步
- 当前支持的主渠道
- 当前仍属开发验证态还是可部署态
- 哪些能力已完成
- 哪些风险仍需上线前确认

### 同时顺手修正文档
请确认 README 不再出现：
- 旧主链路口径
- 多套并行主入口的暗示
- 未实现能力被写成已完成

---

## Step 10：新增验收测试脚本

请新增或完善一个总体验收测试脚本，命名建议：

```text
test_acceptance_flow.py
```

至少覆盖：
1. 钉钉文字消息联调
2. QQ 文字消息联调
3. 钉钉视频消息联调
4. QQ 视频消息联调
5. 视频输入失败场景
6. 分析失败场景
7. ReplyBuilder 输出一致性
8. 配置层加载

要求：
- 不追求真实网络调用
- 当前以本地可运行联调为主
- 不为测试重写主代码

---

## Step 11：形成“当前版本结论”

请在验收文档中明确给出当前版本结论，建议采用以下分类：

### A. 可直接用于开发联调
表示：
- 主链路可跑
- 架构清晰
- 适合继续调试和扩展

### B. 可小范围内部试运行
表示：
- 核心链路已通
- 但仍有少量风险需人工盯守

### C. 暂不建议正式上线
表示：
- 主链路仍有关键未验证点

### 要求
不要给模糊结论，要明确选择一个当前状态。

---

## Step 12：本地自检

完成后请做最小自检，至少验证：

1. 验收清单文档已生成
2. legacy 文件说明文档已生成
3. 文字任务联调通过
4. 视频任务联调通过
5. 视频输入失败场景处理符合预期
6. 分析失败场景处理符合预期
7. 配置层联调通过
8. 回复层输出一致
9. 主链路状态、日志、回复协同正常

如果可以，请输出类似：

```text
[PASS] acceptance checklist document created
[PASS] legacy file status document created
[PASS] dingtalk text flow verified
[PASS] qq text flow verified
[PASS] dingtalk video flow verified
[PASS] qq video flow verified
[PASS] video input failure handled correctly
[PASS] analysis failure handled correctly
[PASS] config integration verified
[PASS] reply consistency verified
[PASS] task status/log/reply coordination verified
```

---

## Step 13：提交并推送 GitHub

完成后请提交并推送到 GitHub。

建议 commit message：

```bash
docs: add system acceptance and deployment readiness checklist
```

或

```bash
test: verify end-to-end flow and deployment readiness
```

---

## 五、代码风格要求

### 要求
- 本步以验证和文档为主
- 不要继续大改架构
- 修 bug 可以，但不要顺手重构过多
- 验收结论必须真实
- 风险项要明确写出来，不要掩盖

---

## 六、本步禁止事项

本步**禁止**：
- 新增新的大架构层
- 为了“好看”而修改主链路定义
- 把未完成能力包装成已上线能力
- 跳过失败场景验证
- 只写文档不做最小联调验证

---

## 七、本步完成标准

只有满足以下条件，才算完成：

1. 已新增验收清单文档
2. 已新增 legacy 文件状态文档
3. 文字任务链路已验证
4. 视频任务链路已验证
5. 失败场景已验证
6. 配置层联调已验证
7. 回复层一致性已验证
8. README 已补充系统状态说明
9. 已形成当前版本结论
10. 已完成 GitHub 提交与推送

---

## 八、执行后回复格式

请严格按以下结构回复：

### A. 当前主链路梳理
### B. 新增 / 修改的文件列表
### C. 验收清单文档说明
### D. legacy 文件说明文档说明
### E. 文字任务联调结果
### F. 视频任务联调结果
### G. 失败场景验证结果
### H. 配置层联调结果
### I. 状态 / 日志 / 回复协同结果
### J. 当前版本结论
### K. GitHub 提交与推送结果
