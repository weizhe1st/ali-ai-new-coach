# 📊 样本登记表 Schema (Sample Registry Schema)

**版本**: 1.0  
**最后更新**: 2026-04-15  
**文件位置**: `data/sample_registry.json`

---

## 一、概述

`sample_registry.json` 是网球 AI 教练系统的**黄金样本登记表**，记录所有已归档的视频样本及其元数据。

### 用途
- 样本归档记录
- 黄金样本审核管理
- 样本检索与统计
- 样本运营分析

### 文件位置
```
ai-coach/data/sample_registry.json
```

### 注意事项
- ⚠️ **运行态文件**：实际运行时的 registry 不应提交到 Git
- ✅ **模板文件**：Git 仓库中只保留空模板或示例
- 🔒 **数据备份**：建议定期备份到 COS 或其他存储

---

## 二、字段定义

### 核心字段（必填）

| 字段名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `sample_id` | string | ✅ | 样本唯一标识 | `sample_20260415_abc123` |
| `source_type` | string | ✅ | 样本来源类型 | `new_archive`, `legacy_cos_import` |
| `action_type` | string | ✅ | 动作类型 | `video_analysis_serve`, `video_analysis_forehand` |
| `source_file_name` | string | ✅ | 原始文件名 | `video-1776158122551.mp4` |
| `cos_key` | string | ✅ | COS 存储键 | `analyzed/serve/2026-04-14/xxx.mp4` |
| `cos_url` | string | ✅ | COS 公开访问 URL | `https://...` |
| `golden_review_status` | string | ✅ | 黄金样本审核状态 | `pending`, `approved`, `rejected` |

### 样本分类字段（推荐）

| 字段名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `sample_category` | string | ⚠️ | 样本分类 | `excellent_demo`, `typical_issue`, `boundary_case` |
| `ntrp_level` | string | ⚠️ | NTRP 等级 | `3.0`, `3.5`, `4.0` |
| `tags` | array | ⚠️ | 标签列表 | `["toss", "loading", "contact"]` |

### 审核相关字段（审核时填写）

| 字段名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `reviewer` | string | ⚠️ | 审核人 | `weizhe` |
| `reviewed_at` | string (ISO 8601) | ⚠️ | 审核时间 | `2026-04-15T07:19:40` |
| `golden_review_note` | string | ⚠️ | 审核备注 | `动作完整，可作为 3.5 级参考` |

### 分析结果字段（分析成功后自动填充）

| 字段名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `analysis_summary` | object | ⚠️ | 分析结果摘要 | 见下方结构 |
| `task_id` | string | ⚠️ | 关联任务 ID | `test_20260414_180000_abc123` |
| `user_id` | string | ⚠️ | 用户 ID | `user_001` |

### 时间戳字段（自动生成）

| 字段名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `archived_at` | string (ISO 8601) | ✅ | 归档时间 | `2026-04-14T19:28:11` |
| `imported_at` | string (ISO 8601) | ⚠️ | 历史样本导入时间 | `2026-04-14T20:03:43` |

### 其他字段

| 字段名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `source_file_path` | string | ⚠️ | 本地文件路径（运行态） | `/home/admin/.../video.mp4` |
| `candidate_for_golden` | boolean | ✅ | 是否候选黄金样本 | `true`, `false` |
| `candidate_cos_key` | string | ⚠️ | 候选样本 COS Key | `candidate_golden/serve/...` |
| `size` | string | ⚠️ | 文件大小（字节） | `699400` |
| `last_modified` | string (ISO 8601) | ⚠️ | 最后修改时间 | `2026-04-13T07:27:34` |

---

## 三、analysis_summary 结构

```json
{
  "ntrp_level": "3.5",
  "overall_score": 65,
  "key_issues": [
    {
      "issue": "膝盖蓄力不足",
      "severity": "high",
      "phase": "loading"
    }
  ]
}
```

### 字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `ntrp_level` | string | NTRP 等级评估 |
| `overall_score` | number | 整体评分（0-100） |
| `key_issues` | array | 关键问题列表 |

#### key_issues 数组项

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `issue` | string | 问题描述 |
| `severity` | string | 严重程度：`low`, `medium`, `high` |
| `phase` | string | 发球阶段：`toss`, `loading`, `contact`, `follow_through` |

---

## 四、枚举值定义

### source_type（样本来源）

| 值 | 说明 |
|----|------|
| `new_archive` | 新归档样本（分析成功后自动归档） |
| `legacy_cos_import` | 历史样本导入（从 COS 扫描导入） |

### action_type（动作类型）

| 值 | 说明 |
|----|------|
| `video_analysis_serve` | 发球动作分析 |
| `video_analysis_forehand` | 正手动作分析 |
| `video_analysis_backhand` | 反手动作分析 |
| `video_analysis_unknown` | 未知动作类型 |

### golden_review_status（审核状态）

| 值 | 说明 | 流转 |
|----|------|------|
| `pending` | 待审核 | → `approved` 或 `rejected` |
| `imported_legacy` | 历史导入待确认 | → `approved` 或 `rejected` |
| `approved` | 审核通过（正式黄金样本） | 终态 |
| `rejected` | 审核拒绝 | 终态 |

### sample_category（样本分类）

| 值 | 说明 |
|----|------|
| `unknown` | 未分类 |
| `excellent_demo` | 优秀示范（标准动作） |
| `typical_issue` | 典型问题（常见错误） |
| `boundary_case` | 边界案例（特殊场景） |

---

## 五、完整示例

```json
{
  "sample_id": "sample_20260415_abc123",
  "source_type": "new_archive",
  "action_type": "video_analysis_serve",
  "source_file_name": "video-1776158122551.mp4",
  "source_file_path": "/home/admin/.openclaw/workspace/media/inbound/video-1776158122551.mp4",
  "cos_key": "analyzed/serve/2026-04-14/test_20260414_180000_abc123_video-1776158122551.mp4",
  "cos_url": "https://tennis-ai-1411340868.cos.ap-shanghai.myqcloud.com/analyzed/serve/2026-04-14/test_20260414_180000_abc123_video-1776158122551.mp4",
  "candidate_cos_key": "candidate_golden/serve/2026-04-14/test_20260414_180000_abc123_video-1776158122551.mp4",
  "candidate_for_golden": true,
  "golden_review_status": "approved",
  "analysis_summary": {
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
  "archived_at": "2026-04-14T19:28:11.525954",
  "golden_review_note": "动作完整，膝盖蓄力问题明显，可作为 3.5 级典型问题样本",
  "reviewer": "weizhe",
  "reviewed_at": "2026-04-15T07:19:40.746209",
  "sample_category": "typical_issue",
  "tags": ["loading", "knee", "power"]
}
```

---

## 六、样本 ID 生成规则

### 新归档样本
```
sample_YYYYMMDD_XXXXXX
```
- `YYYYMMDD`: 归档日期
- `XXXXXX`: 任务 ID 后 6 位

示例：`sample_20260415_abc123`

### 历史导入样本
```
legacy_XXXX
```
- `XXXX`: 4 位数字序号

示例：`legacy_0001`, `legacy_0002`

---

## 七、相关工具

### 样本审核工具
```bash
# 查看样本
python3.8 review_sample.py show --sample-id sample_20260415_abc123

# 列出样本（支持过滤）
python3.8 review_sample.py list --status pending
python3.8 review_sample.py list --category typical_issue
python3.8 review_sample.py list --ntrp 3.5

# 审核通过
python3.8 review_sample.py approve --sample-id xxx --reviewer weizhe --note "..."

# 审核拒绝
python3.8 review_sample.py reject --sample-id xxx --reviewer weizhe --note "..."

# 设置分类
python3.8 review_sample.py set-category --sample-id xxx --category excellent_demo

# 设置 NTRP
python3.8 review_sample.py set-ntrp --sample-id xxx --ntrp 3.5

# 添加标签
python3.8 review_sample.py add-tags --sample-id xxx --tags toss,loading,contact

# 查看统计
python3.8 review_sample.py summary
```

### 相关服务
- `sample_archive_service.py` - 样本归档服务
- `sample_review_service.py` - 样本审核服务
- `import_legacy_samples.py` - 历史样本导入

---

## 八、维护说明

### 字段变更
- 新增字段：向后兼容，允许为空
- 删除字段：需确保无工具依赖
- 修改字段：需同步更新所有读写点

### 数据迁移
如需修改 schema，应：
1. 备份现有 registry
2. 编写迁移脚本
3. 验证迁移结果
4. 更新本文档

### 版本历史
- v1.0 (2026-04-15): 初始版本，固定核心字段

---

**维护者**: 网球 AI 教练系统开发团队  
**联系方式**: 内部
