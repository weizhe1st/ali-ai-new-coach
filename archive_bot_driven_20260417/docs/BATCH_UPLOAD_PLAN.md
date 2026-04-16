# 黄金样本批次上传计划

**创建时间**: 2026-04-15  
**目标**: 系统性建设 NTRP 各等级黄金样本库

---

## 📊 批次规划

### 批次结构

| 批次 | NTRP 等级 | 计划数量 | 动作类型 | 状态 |
|------|----------|----------|----------|------|
| Batch 001 | 2.0 | 5-6 个 | 发球 (Serve) | ⏳ 待上传 |
| Batch 002 | 2.5 | 5-6 个 | 发球 (Serve) | ⏳ 待上传 |
| Batch 003 | 3.0 | 5-6 个 | 发球 (Serve) | ⏳ 待上传 |
| Batch 004 | 3.5 | 5-6 个 | 发球 (Serve) | ⏳ 待上传 |
| Batch 005 | 4.0 | 5-6 个 | 发球 (Serve) | ⏳ 待上传 |

### 扩展计划（后续）

| 批次 | NTRP 等级 | 动作类型 | 状态 |
|------|----------|----------|------|
| Batch 006+ | 2.0-4.0 | 正手 (Forehand) | 规划中 |
| Batch 007+ | 2.0-4.0 | 反手 (Backhand) | 规划中 |

---

## 📦 批次处理流程

### 步骤 1：上传视频

用户上传 5-6 个水平相近的发球视频

**要求**:
- 视频清晰，能看到完整动作
- 最好包含准备、抛球、击球、随挥全过程
- 每个视频标注预期 NTRP 等级

### 步骤 2：批量分析

AI 逐个分析每个视频

**分析内容**:
- NTRP 等级评估
- 整体评分（0-100）
- 各阶段分析（toss/loading/contact/follow-through）
- 关键问题识别
- 技术亮点识别

### 步骤 3：定级确认

根据 AI 分析结果确认 NTRP 等级

**确认方式**:
- AI 评估等级 vs 用户预期等级
- 偏差 > 0.5 时人工复核
- 记录定级依据

### 步骤 4：分类标记

设置样本分类

**分类标准**:
- `excellent_demo` - 优秀示范（该等级的标准动作）
- `typical_issue` - 典型问题（该等级常见问题）
- `boundary_case` - 边界案例（两个等级之间的案例）

### 步骤 5：添加标签

标记关键技术特征

**标签体系**:

#### 抛球阶段 (Toss)
- `toss_consistent` - 抛球稳定
- `toss_inconsistent` - 抛球不稳定
- `toss_height_good` - 抛球高度合适
- `toss_height_low` - 抛球偏低
- `toss_position_good` - 抛球位置好
- `toss_position_front` - 抛球偏前
- `toss_position_back` - 抛球偏后

#### 蓄力阶段 (Loading)
- `loading_good` - 蓄力充分
- `loading_insufficient` - 蓄力不足
- `knee_bend_good` - 膝盖弯曲好
- `knee_bend_insufficient` - 膝盖蓄力不足
- `rotation_good` - 转体充分
- `rotation_insufficient` - 转体不充分

#### 击球阶段 (Contact)
- `contact_point_good` - 击球点好
- `contact_point_late` - 击球点偏晚
- `contact_point_low` - 击球点偏低
- `racket_face_good` - 拍面控制好
- `racket_face_open` - 拍面打开
- `racket_face_closed` - 拍面关闭

#### 随挥阶段 (Follow-through)
- `follow_through_complete` - 随挥完整
- `follow_through_insufficient` - 随挥不充分
- `finish_position_good` - 收尾位置好

### 步骤 6：入库归档

正式加入黄金样本库

**归档内容**:
- 上传到 COS（`golden/` 目录）
- 登记到 `sample_registry.json`
- 审核状态设为 `approved`
- 记录审核人和审核时间

### 步骤 7：批次总结

生成批次统计报告

**报告内容**:
- 批次基本信息
- NTRP 等级分布
- 分类统计
- 标签统计
- 常见问题汇总
- 优秀案例推荐

---

## 📊 批次记录模板

### Batch 001 - NTRP 2.0 发球

**上传时间**: YYYY-MM-DD  
**视频数量**: X 个  
**处理状态**: ⏳ 待上传 / 🔄 处理中 / ✅ 已完成

#### 样本列表

| 序号 | 文件名 | AI 定级 | 分类 | 标签 | 状态 |
|------|--------|--------|------|------|------|
| 1 | video-xxx.mp4 | 2.0 | typical_issue | knee_bend_insufficient | ✅ |
| 2 | video-xxx.mp4 | 2.0 | excellent_demo | toss_consistent | ✅ |
| ... | ... | ... | ... | ... | ... |

#### 批次统计

- **总数量**: X 个
- **分类分布**:
  - excellent_demo: X 个
  - typical_issue: X 个
  - boundary_case: X 个
- **常见问题**:
  1. 膝盖蓄力不足（X 个）
  2. 抛球不稳定（X 个）
  3. 转体不充分（X 个）

---

## 🎯 质量标准

### 入库标准

**必须满足**:
- ✅ 视频清晰，能看到完整动作
- ✅ AI 分析成功
- ✅ NTRP 等级明确
- ✅ 分类和标签完整

**优先入库**:
- ⭐ 动作完整，特征明显
- ⭐ 代表该等级典型水平
- ⭐ 常见问题清晰

**谨慎入库**:
- ⚠️ 视频质量较差
- ⚠️ 动作不完整
- ⚠️ 等级边界模糊

---

## 📈 进度追踪

### 总体进度

```
NTRP 2.0: [          ] 0/6
NTRP 2.5: [          ] 0/6
NTRP 3.0: [          ] 0/6
NTRP 3.5: [          ] 0/6
NTRP 4.0: [          ] 0/6
总计：    [          ] 0/30
```

### 里程碑

- [ ] 批次 001 完成（NTRP 2.0）
- [ ] 批次 002 完成（NTRP 2.5）
- [ ] 批次 003 完成（NTRP 3.0）
- [ ] 批次 004 完成（NTRP 3.5）
- [ ] 批次 005 完成（NTRP 4.0）
- [ ] 黄金样本库初版建成（30 个样本）

---

## 🔧 工具支持

### 现有工具

- `review_sample.py` - 样本审核工具
- `rebuild_registry_from_reports.py` - 从报告重建登记表
- `sample_archive_service.py` - 样本归档服务

### 计划新增

- `batch_upload_processor.py` - 批量上传处理工具
- `batch_summary_generator.py` - 批次总结生成器
- `sample_quality_checker.py` - 样本质量检查工具

---

## 📝 使用说明

### 开始上传

1. 确认当前批次（如 Batch 001 - NTRP 2.0）
2. 准备 5-6 个水平相近的发球视频
3. 逐个或批量上传视频
4. 等待 AI 分析和入库处理
5. 查看批次总结报告

### 查看进度

```bash
cd /home/admin/.openclaw/workspace/ai-coach

# 查看样本统计
python3.8 review_sample.py summary

# 查看待审核样本
python3.8 review_sample.py list --status pending

# 查看某分类样本
python3.8 review_sample.py list --category excellent_demo

# 查看某 NTRP 等级样本
python3.8 review_sample.py list --ntrp 2.0
```

---

**维护者**: 网球 AI 教练系统开发团队  
**最后更新**: 2026-04-15  
**状态**: 📋 准备就绪，等待上传
