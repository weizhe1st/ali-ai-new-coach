# 样本审核工具改造方案（MD版）
## 适用阶段
当前阶段：阿里云版 AI 网球教练系统已具备：
- 新视频自动归档到 COS
- 候选黄金样本自动标记
- 历史黄金样本补登记
- 统一 sample_registry
- 基础 review_status 字段（如 pending / imported_legacy）

本文目标：补齐一个**最小可用的样本审核工具**，让样本能从“进入登记表”走向“人工确认与正式使用”。

---

## 一、核心目标

现在系统已经能把样本沉淀下来，但还缺一个关键环节：

```text
样本进入 sample_registry
  -> 人工查看
    -> 审核
      -> approved / rejected
        -> 补充备注、分类、标签
          -> 正式进入可用黄金样本体系
```

### 本方案唯一目标
先做一个**简单可用的审核工具**，优先支持：
1. 查看样本
2. 审核样本
3. 补充审核备注
4. 补充分类 / 标签 / NTRP
5. 更新 review_status

---

## 二、为什么现在先做审核工具

### 1. 样本已经开始积累
现在你已经有：
- 新样本自动进入 sample_registry
- 历史样本补登记进 sample_registry

如果没有审核工具，这些样本会越积越多，但无法真正变成“可用黄金样本”。

### 2. 审核是样本运营的起点
只有审核动作完成后，你才能：
- 确认哪些样本真正高价值
- 把 pending 变成 approved
- 把 imported_legacy 再次确认归类
- 逐步建立高质量正式黄金样本库

### 3. 现在不需要一上来做后台
当前阶段最合适的是：
- 先做命令行审核工具
- 先把流程跑起来
- 后续再决定是否做 Web 审核后台

---

## 三、当前建议原则

### 原则 1：先做命令行工具
当前最合适的形态是：

```text
review_sample.py
```

通过命令行对样本进行：
- 查询
- 审核
- 更新元数据

### 原则 2：先让审核动作标准化
当前重点不是界面，而是：
- 审核状态字段统一
- 审核人字段统一
- 审核备注字段统一
- 分类与标签更新方式统一

### 原则 3：先支持单样本审核，再考虑批量
第一阶段建议先支持：
- 单个样本审核

批量审核可以后续再补。

---

## 四、建议支持的审核状态

当前建议 review_status 至少包含：

- `pending`
- `imported_legacy`
- `approved`
- `rejected`

### 含义建议

#### `pending`
新系统自动识别出来的候选样本，等待人工审核。

#### `imported_legacy`
从历史 COS 样本导入的旧样本，尚未重新人工确认。

#### `approved`
人工审核通过，可视为正式可用样本。

#### `rejected`
人工审核后判定不纳入正式黄金样本体系。

---

## 五、建议审核工具支持的最小功能

## 功能 1：查看单个样本
例如：

```bash
python review_sample.py show --sample-id legacy_0001
```

建议输出：
- sample_id
- source_type
- action_type
- source_file_name
- cos_key
- current review_status
- sample_category
- tags
- ntrp_level
- analysis_summary
- review_note
- reviewer
- reviewed_at

---

## 功能 2：审核通过
例如：

```bash
python review_sample.py approve --sample-id candidate_0001 --reviewer weizhe --note "动作完整，可作为发球参考样本"
```

效果：
- `golden_review_status = approved`
- `reviewer = weizhe`
- `reviewed_at = now`
- `golden_review_note = ...`

---

## 功能 3：审核拒绝
例如：

```bash
python review_sample.py reject --sample-id candidate_0002 --reviewer weizhe --note "遮挡严重，不适合作为黄金样本"
```

效果：
- `golden_review_status = rejected`
- 写入 reviewer / reviewed_at / note

---

## 功能 4：更新分类
例如：

```bash
python review_sample.py set-category --sample-id legacy_0001 --category excellent_demo
```

建议 sample_category 至少支持：
- `excellent_demo`
- `typical_issue`
- `boundary_case`
- `unknown`

---

## 功能 5：更新 NTRP 等级
例如：

```bash
python review_sample.py set-ntrp --sample-id legacy_0001 --ntrp 3.5
```

---

## 功能 6：更新标签
例如：

```bash
python review_sample.py add-tags --sample-id legacy_0001 --tags toss,timing,loading
```

建议：
- 支持逗号分隔
- 内部存储为数组
- 自动去重

---

## 功能 7：列出待审核样本
例如：

```bash
python review_sample.py list --status pending
python review_sample.py list --status imported_legacy
```

建议输出：
- sample_id
- action_type
- source_file_name
- review_status
- sample_category
- imported_at / created_at

---

## 六、建议新增字段（如当前仍不完整）

样本记录建议至少支持以下审核相关字段：

```json
{
  "golden_review_status": "pending",
  "golden_review_note": "",
  "reviewer": null,
  "reviewed_at": null,
  "sample_category": "unknown",
  "ntrp_level": null,
  "tags": []
}
```

### 必须字段
- `golden_review_status`
- `golden_review_note`
- `reviewer`
- `reviewed_at`

### 建议字段
- `sample_category`
- `ntrp_level`
- `tags`

---

## 七、建议工具文件结构

建议新增文件：

```text
review_sample.py
```

如果你想分层更清楚，也可以：

```text
sample_review_service.py
review_sample.py
```

### 推荐分工

#### `sample_review_service.py`
负责：
- 读取 sample_registry
- 修改样本记录
- 写回 sample_registry
- 做基本校验

#### `review_sample.py`
负责：
- 命令行参数解析
- 调用 service
- 输出结果

---

## 八、建议当前 sample_registry 的存储方式

如果当前是：

```text
data/sample_registry.json
```

那第一阶段就继续用 JSON 即可。  
不要为了审核工具先大改数据库。

### 原因
- 现在目标是把审核流程跑通
- JSON 已足够支撑小规模内部试运行
- 后续样本量大了再迁移 SQLite / DB 也不迟

---

## 九、建议审核输出格式

审核成功后建议输出清晰结果，例如：

```text
[OK] Sample updated
sample_id: candidate_0001
review_status: approved
reviewer: weizhe
reviewed_at: 2026-04-14T15:20:00Z
note: 动作完整，可作为发球标准参考样本
```

这样便于人工确认，不容易误操作。

---

## 十、建议的最小校验逻辑

审核工具建议至少做以下校验：

### 1. sample_id 必须存在
不存在就报错，不要静默失败。

### 2. review_status 合法
只能写：
- pending
- imported_legacy
- approved
- rejected

### 3. tags 自动去重
避免重复标签写入。

### 4. 审核动作必须写 reviewer
至少要求：
- approve / reject 时必须带 reviewer

---

## 十一、建议的当前阶段实施顺序

### 第一步：实现 show / list
目标：
- 能查看样本
- 能列出待审核样本

### 第二步：实现 approve / reject
目标：
- 能完成最核心审核动作

### 第三步：实现 set-category / set-ntrp / add-tags
目标：
- 让样本真正可运营

### 第四步：再考虑批量操作
例如：
- 批量 approve
- 批量加标签
- 批量迁移 imported_legacy 状态

---

## 十二、当前最不建议做的事

### 1. 不建议现在就做复杂 Web 后台
当前先把审核动作跑通最重要。

### 2. 不建议现在就做复杂权限系统
先默认由你或指定内部人员审核即可。

### 3. 不建议现在就做复杂批量自动审核
当前阶段仍应以人工审核为主。

---

## 十三、建议的当前阶段一句话结论

**当前样本体系已经完成“进入登记表”，下一步最该补的是“人工审核工具”，让样本真正能从 pending / imported_legacy 进入 approved / rejected。**

---

## 十四、一句话行动建议

**下一步优先实现：review_sample.py，先支持 show / list / approve / reject / set-category / set-ntrp / add-tags。**
