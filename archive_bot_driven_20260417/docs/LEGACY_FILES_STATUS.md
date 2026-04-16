# 📁 Legacy 文件状态说明

**更新日期**: 2026-04-13  
**目的**: 明确主链路与 Legacy 文件，避免误调用

---

## 一、主链路文件（应优先维护）

这些文件是当前系统的**核心主链路**，所有新功能应基于这些文件开发：

### 配置层
- ✅ `config.py` - 统一配置模块
  - **状态**: 主链路
  - **用途**: 管理模型/渠道/路径/运行模式配置
  - **调用方**: analysis_service, video_input_handler, 其他模块

### 消息与任务层
- ✅ `models/message.py` - 统一消息结构
- ✅ `models/task.py` - 统一任务结构
- ✅ `router.py` - 消息路由器
  - **状态**: 主链路
  - **用途**: 接收 UnifiedMessage，创建 UnifiedTask，交给 TaskExecutor

### 执行层
- ✅ `task_executor.py` - 统一任务执行器
  - **状态**: 主链路
  - **用途**: 执行视频/文本/图片任务，管理任务状态
  - **依赖**: AnalysisService, VideoInputHandler

### 视频处理层
- ✅ `video_input_handler.py` - 视频输入准备
  - **状态**: 主链路
  - **用途**: 解析视频来源，创建工作目录，写入 source_file_path
  - **依赖**: config.py (路径配置)

### 分析层
- ✅ `analysis_service.py` - 分析服务接入层
  - **状态**: 主链路
  - **用途**: 调用旧分析能力，规范化返回结构
  - **依赖**: config.py (模型配置)

### 回复层
- ✅ `reply_builder.py` - 统一回复构建器
  - **状态**: 主链路
  - **用途**: 将执行结果转换为用户可见回复
  - **调用方**: adapters/dingtalk_adapter.py, adapters/qq_adapter.py

### 渠道适配器
- ✅ `adapters/dingtalk_adapter.py` - 钉钉适配器
  - **状态**: 主链路
  - **用途**: 解析钉钉消息，调用 ReplyBuilder
- ✅ `adapters/qq_adapter.py` - QQ 适配器
  - **状态**: 主链路
  - **用途**: 解析 QQ 消息，调用 ReplyBuilder

### 辅助模块
- ✅ `task_logger.py` - 任务日志记录
- ✅ `models/` - 数据模型目录

---

## 二、Legacy 文件（不推荐直接使用）

这些文件是**历史遗留**或**兼容层**，不应作为新功能的入口：

### 旧配置模块
- ⚠️  `core.py` - 旧配置模块
  - **状态**: Legacy（仍被 complete_analysis_service 引用）
  - **问题**: 配置散落，硬编码 MODEL_NAME
  - **替代**: 使用 `config.py`
  - **计划**: 待 complete_analysis_service 迁移后移除

### 旧分析脚本
- ⚠️  `complete_analysis_service.py` - 旧分析内核
  - **状态**: Legacy（仍在使用，但通过 analysis_service 调用）
  - **问题**: 通过 core.py 读取配置
  - **替代**: 未来应迁移到 config.py
  - **计划**: 逐步迁移配置读取

- ⚠️  `qwen_analysis_service.py` - Qwen 分析服务
  - **状态**: Legacy（独立脚本，不推荐直接使用）
  - **问题**: 直接从环境变量读取配置
  - **替代**: 使用 analysis_service.py
  - **计划**: 标记为 deprecated

- ⚠️  `qwen_analysis_simple.py` - 简化 Qwen 分析
  - **状态**: Legacy（独立脚本，不推荐直接使用）
  - **问题**: 直接从环境变量读取配置
  - **替代**: 使用 analysis_service.py
  - **计划**: 标记为 deprecated

### 临时监听脚本
- ⚠️  `simple_integration.py` - 简化集成监听
  - **状态**: Legacy（临时使用）
  - **问题**: 直接从环境变量读取配置，非主链路
  - **替代**: 应通过渠道适配器 + OpenClaw Gateway
  - **计划**: 移除或重构

### 历史部署文件
- ⚠️  `dingtalk_callback_minimal.py` - 钉钉回调（旧版）
  - **状态**: Legacy（已不使用）
  - **问题**: 独立回调服务，与 OpenClaw 渠道冲突
  - **替代**: 使用 OpenClaw 内置渠道
  - **计划**: 移除

- ⚠️  `dingtalk_integrated_service.py` - 钉钉集成服务（旧版）
  - **状态**: Legacy（已不使用）
  - **问题**: 独立服务，与 OpenClaw 渠道冲突
  - **替代**: 使用 OpenClaw 内置渠道
  - **计划**: 移除

### 测试与工具脚本
- ℹ️  `test_*.py` - 测试脚本
  - **状态**: 测试工具
  - **用途**: 验证功能
  - **说明**: 保留用于回归测试

- ℹ️  `integration_test_step7.py` - Step7 集成测试
  - **状态**: 历史测试
  - **用途**: 验证 Step7 功能
  - **计划**: 可归档

### 文档与备份
- ℹ️  `*_SUMMARY.md` - 历史总结文档
  - **状态**: 历史文档
  - **用途**: 记录开发过程
  - **说明**: 保留用于参考

- ℹ️  `*.tar.gz` - 备份文件
  - **状态**: 历史备份
  - **计划**: 可清理或归档到单独目录

---

## 三、主链路调用关系

**正确的主链路调用**:

```
钉钉/QQ 消息
  ↓
adapters/dingtalk_adapter.py 或 adapters/qq_adapter.py
  ↓
router.py (MessageRouter)
  ↓
task_executor.py (TaskExecutor)
  ↓
video_input_handler.py (视频任务)
  ↓
analysis_service.py
  ↓
complete_analysis_service.py (旧分析内核，通过 analysis_service 调用)
  ↓
reply_builder.py
  ↓
渠道输出
```

**错误的调用方式**（应避免）:

```
❌ 直接调用 simple_integration.py
❌ 直接调用 qwen_analysis_service.py
❌ 直接调用 qwen_analysis_simple.py
❌ 启动独立的 dingtalk_callback_minimal.py 服务
```

---

## 四、迁移计划

### 已完成
- ✅ 配置层统一（config.py）
- ✅ 回复层统一（reply_builder.py）
- ✅ 渠道适配器接入 ReplyBuilder
- ✅ analysis_service.py 接入 config.py
- ✅ video_input_handler.py 接入 config.py

### 待完成
- [ ] complete_analysis_service.py 迁移到 config.py
- [ ] 移除 core.py 的配置功能
- [ ] 标记或移除 qwen_analysis_service.py
- [ ] 标记或移除 qwen_analysis_simple.py
- [ ] 移除或重构 simple_integration.py
- [ ] 清理历史部署脚本

---

## 五、维护建议

### 新功能开发
- **应基于**: 主链路文件
- **不应基于**: Legacy 文件

### Bug 修复
- **优先修复**: 主链路文件
- **逐步修复**: Legacy 文件（如仍在使用）

### 代码清理
- **可立即移除**: 已确认不使用的历史文件
- **需谨慎**: 仍被引用的 Legacy 文件（如 complete_analysis_service.py）

---

**更新原则**:
- 主链路文件应保持稳定，避免频繁重构
- Legacy 文件应逐步清理，但需确保不影响现有功能
- 新增功能应基于主链路，不应依赖 Legacy 文件

---

**最后更新**: 2026-04-13  
**维护者**: 网球 AI 教练系统开发团队
