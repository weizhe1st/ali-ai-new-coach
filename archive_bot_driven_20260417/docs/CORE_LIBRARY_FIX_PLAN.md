# 🔧 核心库完善性修复计划

**创建时间**: 2026-04-16 07:15  
**优先级**: 高  
**状态**: 待实施

---

## 📊 检查结果总结

### 黄金等级库（83 个样本）

#### ✅ 已完善
- 必填字段：98.8% 完整（仅 1 个 ntrp_level 缺失）
- COS 存储：100% 完整
- 审核状态：100% approved
- 细化率：100%
- 无重复文件

#### ⚠️ 需修复
1. **primary_issue 缺失 91.6%** (76/83)
   - 影响：无法快速识别主要问题
   - 修复：批量补充主要问题字段

2. **problem_category 缺失 43.4%** (36/83)
   - 影响：问题分类不完整
   - 修复：根据 tags 自动推断

3. **NTRP unknown 22.9%** (19/83)
   - 影响：等级分布不完整
   - 修复：人工复核或标记为 boundary_case

4. **tags 覆盖率 55.4%** (46/83)
   - 影响：教练知识点引用不足
   - 修复：补充技术标签

---

### 教练知识库

#### ✅ 已实现
- 知识点映射：4 个问题类型，每个 3 条教练提示 +3 条训练建议
- 教练提示：已实现在报告中
- 真人教练风格：已实现
- 区间输出：已实现
- 置信度：已实现

#### ⚠️ 需修复
1. **problem_index.json 知识点数为 0**
   - 问题：索引文件为空或格式不对
   - 修复：重新生成或修复索引

2. **知识库检索功能未实现**
   - 缺失：`retrieve_knowledge` 函数
   - 缺失：`compare_with_golden` 函数
   - 缺失：`generate_improvement_priority` 函数

3. **黄金标准对比未实现**
   - 影响：无法对比标准动作

4. **知识点映射只有 4 个**
   - 当前：toss_inconsistent, knee_bend_insufficient, rotation_insufficient, contact_point_late
   - 需要：覆盖所有常见问题类型

---

## 🛠️ 修复计划

### 阶段 1：黄金等级库补全（2026-04-16）

#### 1.1 补充 primary_issue 和 secondary_issue

**脚本**: `fix_missing_primary_issues.py`

```python
# 根据 sample_category 和 tags 自动推断
for sample in registry:
    if sample['sample_category'] == 'typical_issue':
        # 从 tags 中找出第一个问题标签
        issue_tags = [t for t in sample.get('tags', []) if 'insufficient' in t or 'inconsistent' in t]
        if issue_tags:
            sample['primary_issue'] = issue_tags[0]
            sample['secondary_issue'] = issue_tags[1] if len(issue_tags) > 1 else None
```

**预计修复**: 76 个样本  
**工作量**: 1-2 小时

---

#### 1.2 补充 problem_category

**脚本**: `fix_missing_problem_categories.py`

```python
# 根据 primary_issue 推断 problem_category
issue_to_category = {
    'toss_inconsistent': 'toss',
    'toss_height_low': 'toss',
    'knee_bend_insufficient': 'loading',
    'rotation_insufficient': 'loading',
    'contact_point_late': 'contact',
    'follow_through_insufficient': 'follow_through',
}

for sample in registry:
    if not sample.get('problem_category'):
        primary = sample.get('primary_issue')
        if primary:
            sample['problem_category'] = issue_to_category.get(primary, 'other')
```

**预计修复**: 36 个样本  
**工作量**: 0.5-1 小时

---

#### 1.3 补充 NTRP unknown 样本

**策略**:
- 18 个 unsynced_task_import → 已降级为 typical_issue，NTRP 标记为 3.0-3.5
- 1 个 legacy → 人工复核

**工作量**: 0.5 小时

---

#### 1.4 补充 tags

**脚本**: `fix_missing_tags.py`

```python
# 根据 ntrp_level 和 sample_category 补充基础 tags
for sample in registry:
    if not sample.get('tags'):
        if sample['sample_category'] == 'excellent_demo':
            sample['tags'] = ['ready_good', 'toss_consistent', 'rotation_good', 'follow_through_complete']
        elif sample['sample_category'] == 'typical_issue':
            # 根据 problem_category 补充
            if sample.get('problem_category') == 'toss':
                sample['tags'] = ['toss_inconsistent']
            elif sample.get('problem_category') == 'loading':
                sample['tags'] = ['rotation_insufficient']
```

**预计修复**: 37 个样本  
**工作量**: 1 小时

---

### 阶段 2：教练知识库完善（2026-04-17）

#### 2.1 修复 problem_index.json

**问题**: 当前知识点数为 0

**修复**:
```python
# 重新生成问题索引
problem_index = {
    'toss_inconsistent': [
        {'key': '抛球稳定性', 'content': '...'},
        {'key': '抛球高度控制', 'content': '...'},
    ],
    'knee_bend_insufficient': [...],
    # ... 所有问题类型
}
```

**工作量**: 2-3 小时

---

#### 2.2 实现知识库检索功能

**文件**: `knowledge_retrieval_service.py` (新建)

**功能**:
```python
def retrieve_knowledge(ntrp_level, phase, issue_tags):
    """根据 NTRP 等级、阶段、问题标签检索知识点"""
    # 1. 从 problem_index 检索
    # 2. 从 fused_knowledge 检索
    # 3. 返回匹配的知识点列表
    pass

def compare_with_golden(ntrp_level, phase_analysis):
    """对比黄金标准"""
    # 1. 加载对应 NTRP 等级的黄金标准
    # 2. 逐阶段对比
    # 3. 返回差异列表
    pass

def generate_improvement_priority(knowledge_results, phase_comparison):
    """生成改进优先级"""
    # 1. 根据差异严重程度排序
    # 2. 返回优先级列表
    pass
```

**工作量**: 3-4 小时

---

#### 2.3 扩展知识点映射

**文件**: `report_generation_integration.py`

**当前**: 4 个问题类型  
**目标**: 15-20 个问题类型

**新增映射**:
```python
ISSUE_TO_KNOWLEDGE = {
    # 抛球问题
    'toss_inconsistent': {...},
    'toss_height_low': {...},
    'toss_height_high': {...},
    'toss_position_front': {...},
    'toss_position_back': {...},
    
    # 蓄力问题
    'knee_bend_insufficient': {...},
    'rotation_insufficient': {...},
    'loading_insufficient': {...},
    'hip_rotation_insufficient': {...},
    
    # 击球点问题
    'contact_point_late': {...},
    'contact_point_early': {...},
    'contact_point_low': {...},
    'contact_point_high': {...},
    
    # 随挥问题
    'follow_through_insufficient': {...},
    'follow_through_incomplete': {...},
    'body_not_forward': {...},
}
```

**工作量**: 2-3 小时

---

### 阶段 3：报告生成整合（2026-04-18）

#### 3.1 整合知识库检索到报告生成

**文件**: `report_generation_integration.py`

**修改**:
```python
def generate_report(sample_id, ntrp_level):
    # ... 现有逻辑 ...
    
    # 新增：知识库检索
    knowledge_results = retrieve_knowledge(
        ntrp_level, 
        phase_weaknesses, 
        issue_tags
    )
    
    # 新增：黄金标准对比
    golden_comparison = compare_with_golden(
        ntrp_level,
        phase_analysis
    )
    
    # 新增：改进优先级
    priority_gaps = generate_improvement_priority(
        knowledge_results,
        golden_comparison
    )
    
    # 整合到报告
    report['knowledge_recall'] = knowledge_results
    report['golden_standard_comparison'] = golden_comparison
    report['priority_gaps'] = priority_gaps
```

**工作量**: 2-3 小时

---

#### 3.2 优化语言风格

**目标**: 更真人教练风格

**改进**:
1. 增加教练提示的使用频率
2. 增加鼓励性语言
3. 增加具体可执行的训练建议
4. 避免过于技术化的术语

**示例**:
```python
# 修改前
"建议改进抛球稳定性"

# 修改后
"抛球是发球的灵魂！球抛不稳，后面动作再好也白搭。
试试这个练习：站在发球线，连续抛球 10 次，目标是每次高度都一致。"
```

**工作量**: 1-2 小时

---

## 📅 时间安排

| 日期 | 任务 | 预计工时 | 负责人 |
|------|------|----------|--------|
| 2026-04-16 | 黄金等级库补全 | 3-4 小时 | AI Assistant |
| 2026-04-17 | 教练知识库完善 | 5-7 小时 | AI Assistant |
| 2026-04-18 | 报告生成整合 | 3-5 小时 | AI Assistant |
| 2026-04-19 | 测试验证 | 2-3 小时 | AI Assistant |
| 2026-04-20 | 上线部署 | 1-2 小时 | AI Assistant |

---

## 📊 预期效果

### 修复后指标

| 指标 | 当前 | 目标 | 提升 |
|------|------|------|------|
| **primary_issue 完整率** | 8.4% | 95%+ | 10 倍 + |
| **problem_category 完整率** | 56.6% | 95%+ | 70%↑ |
| **tags 覆盖率** | 55.4% | 90%+ | 60%↑ |
| **知识点映射数** | 4 个 | 15-20 个 | 4-5 倍 |
| **知识库检索功能** | ❌ | ✅ | 从无到有 |
| **黄金标准对比** | ❌ | ✅ | 从无到有 |

### 报告质量提升

- ✅ 更准确的 primary_issue 识别
- ✅ 更完整的 problem_category 分类
- ✅ 更丰富的教练知识点引用
- ✅ 更真人化的语言风格
- ✅ 更有针对性的训练建议

---

## ⚠️ 风险控制

### 技术风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 批量修改导致数据错误 | 中 | 高 | 修改前备份，逐批验证 |
| 知识库检索性能问题 | 低 | 中 | 添加缓存，优化索引 |
| 报告生成逻辑复杂化 | 中 | 中 | 模块化开发，单元测试 |

### 回滚方案

如修复后出现问题：
1. 恢复备份的 sample_registry.json
2. 回滚 report_generation_integration.py
3. 保留已验证的修复

---

## 📝 验收标准

### 黄金等级库
- [ ] primary_issue 完整率 ≥95%
- [ ] problem_category 完整率 ≥95%
- [ ] tags 覆盖率 ≥90%
- [ ] NTRP unknown ≤5%

### 教练知识库
- [ ] 知识点映射 ≥15 个问题类型
- [ ] 每个问题类型 ≥3 条教练提示
- [ ] 每个问题类型 ≥3 条训练建议
- [ ] problem_index.json 可正常加载

### 报告生成
- [ ] 知识库检索功能正常
- [ ] 黄金标准对比功能正常
- [ ] 改进优先级生成正常
- [ ] 语言风格真人化

---

**维护人**: AI Assistant  
**最后更新**: 2026-04-16 07:15  
**下次回顾**: 2026-04-16 晚间（阶段 1 完成后）
