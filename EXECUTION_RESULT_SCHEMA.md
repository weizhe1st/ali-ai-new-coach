# 📋 执行结果 Schema (Execution Result Schema)

**版本**: 1.0  
**最后更新**: 2026-04-15  
**用途**: 定义 TaskExecutor 输出结构，作为 ReplyBuilder 的输入契约

---

## 一、概述

`ExecutionResult` 是 `TaskExecutor` 执行任务后的**标准输出结构**，用于：
- 统一不同任务类型的返回格式
- 为 ReplyBuilder 提供稳定的输入契约
- 支持任务状态追踪和日志记录

### 调用关系

```
TaskExecutor.execute()
    ↓
ExecutionResult (返回)
    ↓
ReplyBuilder.build()
    ↓
渠道输出（钉钉/QQ）
```

---

## 二、核心结构

```typescript
interface ExecutionResult {
  // 核心字段（必填）
  task_id: string;
  task_type: string;
  status: 'success' | 'failed' | 'partial';
  current_stage: string;
  
  // 结果数据
  result?: any;
  error?: string;
  
  // 报告相关
  report?: string;
  structured_result?: any;
  
  // 源文件信息
  source_file_name?: string;
  source_file_path?: string;
  
  // 扩展字段
  metadata?: Record<string, any>;
}
```

---

## 三、字段定义

### 核心字段（必填）

| 字段名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `task_id` | string | ✅ | 任务唯一标识 | `test_20260415_001` |
| `task_type` | string | ✅ | 任务类型 | `video_analysis_serve`, `text_query` |
| `status` | string | ✅ | 执行状态 | `success`, `failed`, `partial` |
| `current_stage` | string | ✅ | 当前阶段 | `completed`, `video_input_ready`, `analysis_failed` |

### 结果数据字段

| 字段名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `result` | any | ⚠️ | 执行结果（原始数据） | 分析结果对象 |
| `error` | string | ⚠️ | 错误信息（失败时） | `视频文件不存在` |

### 报告相关字段

| 字段名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `report` | string | ⚠️ | 文本报告（用户可见） | `您的发球动作分析如下...` |
| `structured_result` | object | ⚠️ | 结构化结果 | 见下方结构 |

### 源文件信息字段

| 字段名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `source_file_name` | string | ⚠️ | 原始文件名 | `video-1776158122551.mp4` |
| `source_file_path` | string | ⚠️ | 本地文件路径 | `/home/admin/.../video.mp4` |

### 扩展字段

| 字段名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `metadata` | object | ⚠️ | 元数据（扩展用） | `{ duration: 5.2, frames: 150 }` |

---

## 四、status 枚举值

| 值 | 说明 | 使用场景 |
|----|------|----------|
| `success` | 执行成功 | 所有阶段完成，无错误 |
| `failed` | 执行失败 | 关键阶段失败，无法继续 |
| `partial` | 部分成功 | 部分阶段完成，但不影响核心功能 |

---

## 五、task_type 枚举值

| 值 | 说明 | 主链路 |
|----|------|--------|
| `video_analysis_serve` | 发球视频分析 | ✅ 主链路 |
| `video_analysis_forehand` | 正手视频分析 | ✅ 主链路 |
| `video_analysis_backhand` | 反手视频分析 | ✅ 主链路 |
| `text_query` | 文本问答 | ✅ 主链路 |
| `image_analysis` | 图片分析 | ⚠️ 备用 |

---

## 六、structured_result 结构（视频分析）

```json
{
  "ntrp_level": "3.5",
  "overall_score": 65,
  "phase_analysis": {
    "toss": {
      "score": 70,
      "issues": ["抛球高度稍低"]
    },
    "loading": {
      "score": 60,
      "issues": ["膝盖蓄力不足"]
    },
    "contact": {
      "score": 75,
      "issues": []
    },
    "follow_through": {
      "score": 65,
      "issues": ["随挥不够充分"]
    }
  },
  "key_issues": [
    {
      "issue": "膝盖蓄力不足",
      "severity": "high",
      "phase": "loading"
    }
  ],
  "metrics": {
    "knee_angle": 145,
    "elbow_angle": 160,
    "shoulder_rotation": 85
  }
}
```

### 字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `ntrp_level` | string | NTRP 等级评估 |
| `overall_score` | number | 整体评分（0-100） |
| `phase_analysis` | object | 各阶段分析 |
| `key_issues` | array | 关键问题列表 |
| `metrics` | object | 量化指标 |

---

## 七、完整示例

### 成功执行（视频分析）

```json
{
  "task_id": "test_20260415_001",
  "task_type": "video_analysis_serve",
  "status": "success",
  "current_stage": "completed",
  "result": {
    "success": true,
    "ntrp_level": "3.5",
    "overall_score": 65
  },
  "structured_result": {
    "ntrp_level": "3.5",
    "overall_score": 65,
    "key_issues": [
      {
        "issue": "膝盖蓄力不足",
        "severity": "high",
        "phase": "loading"
      }
    ]
  },
  "report": "您的发球动作分析已完成。整体评分：65 分（NTRP 3.5 级）。主要问题：膝盖蓄力不足...",
  "source_file_name": "video-1776158122551.mp4",
  "source_file_path": "/home/admin/.openclaw/workspace/media/inbound/video-1776158122551.mp4",
  "metadata": {
    "duration": 5.2,
    "frames": 150,
    "analysis_time": 12.5
  }
}
```

### 执行失败

```json
{
  "task_id": "test_20260415_002",
  "task_type": "video_analysis_serve",
  "status": "failed",
  "current_stage": "video_input_ready",
  "error": "视频文件不存在：/path/to/video.mp4",
  "source_file_name": "video-1776158122551.mp4",
  "source_file_path": "/path/to/video.mp4"
}
```

### 部分成功

```json
{
  "task_id": "test_20260415_003",
  "task_type": "video_analysis_serve",
  "status": "partial",
  "current_stage": "analysis_completed",
  "result": {
    "success": true,
    "warning": "视频质量较低，分析结果仅供参考"
  },
  "report": "分析已完成，但视频质量较低...",
  "metadata": {
    "warning": "low_quality_video"
  }
}
```

---

## 八、阶段定义 (current_stage)

### 视频分析任务

| 阶段 | 说明 |
|------|------|
| `task_created` | 任务已创建 |
| `video_input_ready` | 视频输入准备完成 |
| `analysis_running` | 分析进行中 |
| `analysis_completed` | 分析完成 |
| `report_generated` | 报告生成完成 |
| `archived` | 样本已归档 |
| `completed` | 全部完成 |

### 错误阶段

| 阶段 | 说明 |
|------|------|
| `video_input_failed` | 视频输入准备失败 |
| `analysis_failed` | 分析失败 |
| `report_generation_failed` | 报告生成失败 |

---

## 九、ReplyBuilder 输入契约

ReplyBuilder 依赖以下字段：

```typescript
interface ReplyBuilderInput {
  task_id: string;
  task_type: string;
  status: 'success' | 'failed' | 'partial';
  report?: string;
  error?: string;
  structured_result?: {
    ntrp_level?: string;
    overall_score?: number;
    key_issues?: Array<{
      issue: string;
      severity: string;
      phase: string;
    }>;
  };
  source_file_name?: string;
}
```

### ReplyBuilder 输出

根据 ExecutionResult 生成用户可见的回复：

- **成功**: 发送分析报告
- **失败**: 发送错误提示 + 解决建议
- **部分成功**: 发送报告 + 警告说明

---

## 十、维护说明

### 字段变更原则
1. **向后兼容**: 新增字段允许为空
2. **不删除**: 已使用的字段不删除，标记为 deprecated
3. **文档同步**: 字段变更需同步更新本文档

### 版本历史
- v1.0 (2026-04-15): 初始版本，固定核心字段

### 相关模块
- `task_executor.py` - 任务执行器（输出 ExecutionResult）
- `reply_builder.py` - 回复构建器（输入 ExecutionResult）
- `analysis_service.py` - 分析服务（返回分析结果）

---

**维护者**: 网球 AI 教练系统开发团队  
**联系方式**: 内部
