# 历史黄金样本整合方案（MD版）
## 适用阶段
当前阶段：阿里云版 AI 网球教练系统已完成主链路打通，并已具备：
- 分析成功后自动归档到 COS
- 候选黄金样本自动标记
- 样本登记表能力
- TaskExecutor 与样本归档集成

本文目标：将**历史已经存在于 COS 的黄金样本**与**新产生的候选 / 黄金样本**统一纳入同一个样本体系。

---

## 一、核心目标

当前系统已经开始对**新上传视频**进行：
- 分析
- COS 归档
- 候选黄金样本标记
- 样本登记

但你之前已经在 COS 中积累了一部分**历史黄金样本视频**。  
如果这些历史样本不补登记，那么当前样本体系仍然是割裂的：

```text
历史黄金样本（已在 COS）
  -> 分散存在
  -> 无统一 sample_id
  -> 无统一 metadata
  -> 无统一 review_status

新样本（新系统产生）
  -> 已纳入 sample_registry
  -> 已有 candidate_for_golden
  -> 已有 cos_key / analysis_summary / review_status
```

### 本方案唯一目标
把历史黄金样本补录进当前样本登记体系，使其与新样本统一管理。

---

## 二、为什么这一步很重要

### 1. 没有历史样本整合，样本库仍然是不完整的
你现在的新系统虽然开始沉淀样本，但如果旧黄金样本还散落在 COS 中，那：
- 检索不完整
- 审核不统一
- 对照不完整
- 样本统计不完整

### 2. 历史样本往往是最有价值的一批
它们通常是：
- 你已经积累过的较高质量样本
- 早期筛过或认可过的视频
- 对知识库、黄金标准最有参考价值的一批数据

### 3. 未来样本体系必须“新旧统一”
后续你想做：
- 样本检索
- 黄金标准对比
- 典型问题归类
- 规则提炼
- NTRP 分层参考

都必须依赖统一样本体系。

---

## 三、当前建议原则

### 原则 1：先做“补登记”，不要先做大搬家
当前阶段最推荐的是：
- 先扫描 COS 中历史黄金样本
- 给它们补 metadata
- 补 sample_id
- 写入 sample_registry

不建议一开始就：
- 大规模复制文件
- 大规模改目录
- 大规模重命名对象

### 原则 2：先统一索引，再逐步清洗
先做到：
- 看得见
- 找得到
- 能分类
- 能审核状态统一

之后再逐步做：
- 重命名
- 分类迁移
- 去重
- 再归档

### 原则 3：允许历史样本 metadata 不完整，但必须能追踪
历史样本可能没有：
- task_id
- 原始分析摘要
- NTRP 等级
- tags

当前可以允许先补最小字段，后续再慢慢完善。

---

## 四、历史样本整合的推荐流程

建议流程如下：

```text
扫描 COS 历史目录
  -> 列出历史黄金样本对象
    -> 过滤无效 / 非视频文件
      -> 为每个对象生成 sample_id
        -> 补充最小 metadata
          -> 写入 sample_registry
            -> review_status 标记为 imported_legacy
```

### 目标
先让历史样本全部进入统一登记表，  
而不是先要求它们“像新样本一样信息完整”。

---

## 五、建议识别的历史样本来源范围

请先明确历史样本来自哪些目录，例如：

```text
cos://bucket/golden/
cos://bucket/old_golden/
cos://bucket/coach_samples/
cos://bucket/serve_reference/
```

### 当前阶段建议做法
不要一上来扫描整个 COS bucket。  
建议只扫描你**明确知道是历史黄金样本或高质量样本**的几个目录。

### 原因
避免把：
- 测试文件
- 临时文件
- 非视频文件
- 未筛选素材
误导入 sample_registry。

---

## 六、建议的最小整合字段

历史样本补登记时，建议至少生成以下字段：

```json
{
  "sample_id": "legacy_0001",
  "source_type": "legacy_cos_import",
  "action_type": "serve",
  "sample_category": "unknown",
  "cos_key": "golden/old/sample001.mp4",
  "cos_url": "",
  "source_file_name": "sample001.mp4",
  "source_file_path": null,
  "task_id": null,
  "candidate_for_golden": false,
  "golden_review_status": "imported_legacy",
  "analysis_summary": "",
  "score": null,
  "ntrp_level": null,
  "tags": [],
  "reviewer": null,
  "reviewed_at": null,
  "imported_at": "2026-04-14T12:00:00Z"
}
```

### 建议至少保留
- `sample_id`
- `source_type`
- `action_type`
- `cos_key`
- `source_file_name`
- `golden_review_status`
- `imported_at`

### 当前允许为空的字段
- `task_id`
- `analysis_summary`
- `score`
- `ntrp_level`
- `tags`
- `reviewer`
- `reviewed_at`

---

## 七、建议的 review_status 设计

为了区分“历史导入样本”和“新系统审核样本”，建议使用：

### 历史样本
- `imported_legacy`

### 新候选样本
- `pending`

### 正式审核通过
- `approved`

### 拒绝入库
- `rejected`

这样你在后续检索时可以一眼区分：
- 哪些是旧样本补录
- 哪些是新系统自动候选
- 哪些是真正审核通过的正式黄金样本

---

## 八、sample_id 建议生成方式

建议不要直接用 COS 文件名作为 sample_id。  
应该统一生成内部编号，例如：

### 历史样本
```text
legacy_0001
legacy_0002
legacy_0003
```

### 新样本
```text
golden_0001
golden_0002
candidate_0001
```

### 好处
- 不依赖文件名质量
- 后续重命名 COS 对象也不影响内部引用
- 便于人工审核与管理

---

## 九、建议新增的整合工具

建议新增一个轻量脚本，例如：

```text
import_legacy_samples.py
```

### 建议职责
- 扫描指定 COS 前缀
- 列出视频对象
- 过滤非视频文件
- 为样本生成 metadata
- 写入 `sample_registry.json` 或 `sample_registry.sqlite`

### 当前阶段不要做得太复杂
先满足：
- 可运行
- 可重复执行
- 不重复导入
- 可输出导入结果摘要

---

## 十、建议的导入规则

历史样本导入时建议遵守以下规则：

### 1. 只导入视频文件
例如扩展名限制为：
- `.mp4`
- `.mov`
- `.mkv`（如有需要）

### 2. 过滤明显非样本文件
例如：
- `.txt`
- `.json`
- 缩略图
- 临时文件
- 日志文件

### 3. 尽量识别动作类型
如果历史目录本身就表示发球，可默认：
- `action_type = serve`

如果无法确认，可先：
- `action_type = unknown`

### 4. 不要在导入时强行补全所有标签
标签和 NTRP 等级后续可以再逐步补，不必一开始就追求完整。

---

## 十一、建议做“去重前置检查”

在导入历史样本时，不一定马上做复杂去重，但建议至少做最基本检查：

### 最小去重方式
按以下字段组合判断：
- `cos_key`
- `source_file_name`

如果 sample_registry 中已存在同一个 `cos_key`，就不要重复导入。

### 当前阶段先不要做
- 内容级视频相似度去重
- 视觉特征去重
- hash 全量比对
这些后续再做。

---

## 十二、建议的导入后输出结果

导入完成后，建议输出类似统计：

```text
历史样本扫描总数：120
有效视频数：93
成功导入：87
重复跳过：4
无效文件跳过：2

review_status=imported_legacy：87
action_type=serve：80
action_type=unknown：7
```

### 这样你可以快速知道
- 历史样本实际有多少
- 有多少成功纳入当前体系
- 有多少还需要人工后续补数据

---

## 十三、建议后续逐步补充的字段

历史样本导入完成后，后续可逐步补以下内容：

### 第一优先级
- `sample_category`
- `tags`
- `ntrp_level`

### 第二优先级
- `analysis_summary`
- `score`

### 第三优先级
- `reviewer`
- `reviewed_at`
- 更细的动作阶段标签

---

## 十四、建议与新样本统一后的使用方式

当历史样本和新样本都进入统一 registry 后，就可以逐步支持：

### 1. 按动作类型检索
例如只看发球样本

### 2. 按样本来源筛选
例如：
- `legacy_cos_import`
- `new_pipeline_candidate`
- `approved_golden`

### 3. 按 review_status 筛选
例如：
- `imported_legacy`
- `pending`
- `approved`

### 4. 按 NTRP 等级 / 标签筛选
后续再逐步完善

---

## 十五、当前最不建议做的事

### 1. 不建议现在就大规模重命名 COS 对象
因为可能会破坏你现在已有的引用关系。

### 2. 不建议一开始就强制要求历史样本字段完整
这会拖慢整合速度。

### 3. 不建议先做复杂 Web 后台
当前先把索引统一起来更重要。

---

## 十六、当前阶段最合理的实施顺序

### 第一步：导入历史黄金样本到 sample_registry
目标：
- 新旧样本统一可见

### 第二步：标记 imported_legacy
目标：
- 与新候选样本区分

### 第三步：逐步补分类、标签、NTRP
目标：
- 提升可检索性与可利用性

### 第四步：再做审核工具和去重
目标：
- 真正进入样本运营阶段

---

## 十七、建议的当前阶段一句话结论

**当前最优先不是再新增分析能力，而是先把 COS 中历史黄金样本补登记进统一 sample_registry，让旧样本和新样本进入同一个样本体系。**

---

## 十八、一句话行动建议

**下一步优先实现：扫描指定 COS 历史目录 → 过滤视频文件 → 生成 sample_id → 写入 sample_registry，并标记 review_status=imported_legacy。**
