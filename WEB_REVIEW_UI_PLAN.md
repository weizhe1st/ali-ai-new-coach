# Web 审核界面实施计划

**创建时间**: 2026-04-15  
**优先级**: P2（优化项）  
**状态**: 📋 规划完成，待实施

---

## 📊 当前状态评估

### 样本数量
- **总样本数**: 2
- **待审核**: 0
- **已审核**: 2

### CLI 工具状态
- ✅ 单样本审核工具可用
- ✅ 支持 approve/reject
- ✅ 支持分类/NTRP/标签编辑
- ✅ 支持多维度检索

### 实施时机判断

| 因素 | 当前状态 | 建议 |
|------|----------|------|
| 样本数量 | 2 个 | CLI 足够 |
| 审核频率 | 低 | CLI 足够 |
| 协作需求 | 无 | 暂不需要 |
| 技术准备 | 充分 | 可以开始 |

**结论**: 当前 CLI 完全够用，但可以**提前设计架构，分阶段实施**。

---

## 🎯 实施原则（按方案文档）

### 原则 1：只做运营工具，不改主分析链路 ✅
- Web 界面只负责样本审核
- 不参与视频分析/回复生成

### 原则 2：先做只读 + 少量可写操作 ✅
- 第一阶段：列表页 + 详情页（只读）
- 第二阶段：approve/reject
- 第三阶段：编辑元数据

### 原则 3：后端复用现有审核逻辑 ✅
- Web API 调用 `sample_review_service.py`
- CLI 和 Web 共享同一套逻辑

---

## 📋 分阶段实施计划

### 阶段 1：最小可用版本（MVP）

**目标**: 能查看样本列表和详情

**功能**:
- [ ] 样本列表页（只读）
- [ ] 样本详情页（只读）
- [ ] 基础筛选（status/category）

**技术**:
- Flask 或 FastAPI
- 简单 HTML 模板
- 内网访问

**预计工作量**: 4-6 小时

---

### 阶段 2：核心审核功能

**目标**: 能完成 approve/reject 操作

**功能**:
- [ ] Approve 按钮
- [ ] Reject 按钮
- [ ] 审核备注输入
- [ ] 审核状态实时更新

**技术**:
- 表单提交
- 调用 `sample_review_service.approve_sample()`
- 调用 `sample_review_service.reject_sample()`

**预计工作量**: 4-6 小时

---

### 阶段 3：元数据编辑

**目标**: 能编辑分类/NTRP/标签

**功能**:
- [ ] 编辑 sample_category
- [ ] 编辑 NTRP 等级
- [ ] 编辑标签（添加/删除）
- [ ] 编辑审核备注

**技术**:
- PATCH API
- 调用 `sample_review_service` 对应方法

**预计工作量**: 6-8 小时

---

### 阶段 4：增强功能（可选）

**功能**:
- [ ] 批量审核
- [ ] 视频在线预览
- [ ] 高级筛选（按 tags）
- [ ] 统计图表
- [ ] Basic Auth 认证

**预计工作量**: 8-16 小时

---

## 🏗️ 技术架构设计

### 推荐技术栈

| 组件 | 技术选型 | 理由 |
|------|----------|------|
| Web 框架 | Flask | 轻量、快速、易部署 |
| 模板引擎 | Jinja2 | Flask 内置 |
| CSS 框架 | Bootstrap 5 | 快速构建 UI |
| 部署方式 | 内网服务 | 简单、安全 |

### 文件结构

```
ai-coach/
├── sample_review_service.py    # 现有服务层
├── web/                         # 新增 Web 目录
│   ├── app.py                   # Flask 应用入口
│   ├── routes.py                # 路由定义
│   ├── templates/
│   │   ├── base.html            # 基础模板
│   │   ├── sample_list.html     # 列表页
│   │   └── sample_detail.html   # 详情页
│   └── static/
│       └── style.css            # 自定义样式
└── data/
    └── sample_registry.json     # 样本登记表
```

### API 设计

```python
# 获取样本列表
GET /api/samples?status=pending&page=1&page_size=20

# 获取样本详情
GET /api/samples/<sample_id>

# 审核通过
POST /api/samples/<sample_id>/approve
{
  "reviewer": "weizhe",
  "note": "动作完整，可作为参考样本"
}

# 审核拒绝
POST /api/samples/<sample_id>/reject
{
  "reviewer": "weizhe",
  "note": "遮挡严重，不适合"
}

# 更新元数据
PATCH /api/samples/<sample_id>
{
  "sample_category": "excellent_demo",
  "ntrp_level": "3.5",
  "tags": ["toss", "loading"],
  "golden_review_note": "备注..."
}
```

---

## 📝 实施建议

### 当前阶段建议

**推荐**: 先完成阶段 1 的设计，暂不实施

**理由**:
1. 样本数量少，CLI 足够
2. 先把主链路跑稳更重要
3. 可以等样本数增长到 10+ 再实施

**例外情况**:
- 如果需要演示给其他人看
- 如果想提前体验 Web 审核流程
- 如果有协作审核需求

可以立即开始实施。

---

## 🚀 快速启动方案（如果决定实施）

### 第一步：创建 Web 目录结构

```bash
cd /home/admin/.openclaw/workspace/ai-coach
mkdir -p web/templates web/static
```

### 第二步：安装 Flask

```bash
pip3.8 install flask
```

### 第三步：创建最小应用

```python
# web/app.py
from flask import Flask, render_template
import sys
sys.path.insert(0, '..')
from sample_review_service import SampleReviewService

app = Flask(__name__)
service = SampleReviewService()

@app.route('/')
def sample_list():
    samples = service.list_samples()
    return render_template('sample_list.html', samples=samples)

@app.route('/sample/<sample_id>')
def sample_detail(sample_id):
    sample = service.get_sample(sample_id)
    return render_template('sample_detail.html', sample=sample)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### 第四步：启动服务

```bash
cd web
python3.8 app.py
```

访问：`http://localhost:5000`

---

## ✅ 验收标准

### 阶段 1 验收
- [ ] 能访问列表页
- [ ] 能访问详情页
- [ ] 数据正确显示
- [ ] 筛选功能正常

### 阶段 2 验收
- [ ] Approve 按钮可用
- [ ] Reject 按钮可用
- [ ] 审核状态正确更新
- [ ] sample_registry 正确保存

### 阶段 3 验收
- [ ] 分类编辑可用
- [ ] NTRP 编辑可用
- [ ] 标签编辑可用
- [ ] 备注编辑可用

### 整体验收
- [ ] CLI 工具仍然可用
- [ ] Web 和 CLI 数据一致
- [ ] 无破坏性变更
- [ ] 内网访问安全

---

## 📊 优先级评估

### 当前优先级：P2（优化项）

**原因**:
- 不是主链路阻塞点
- CLI 工具已完全可用
- 样本数量较少

**触发实施的条件**:
- 样本数 > 10 个
- 审核频率 > 每天 5 次
- 有协作审核需求
- 需要演示给其他人看

---

## 🎯 决策建议

### 如果现在实施
**优点**:
- 提前体验 Web 审核流程
- 为未来扩展打基础
- 可以作为演示工具

**缺点**:
- 占用开发时间
- 当前使用频率低
- 可能过度设计

### 如果暂缓实施
**优点**:
- 专注主链路优化
- 等需求明确再实施
- 避免过度工程

**缺点**:
- 样本增长后需要紧急开发
- 无法提前发现问题

### 推荐方案：**设计先行，分阶段实施**

1. **现在**: 完成架构设计（本文档）
2. **样本数 < 10**: 使用 CLI 工具
3. **样本数 > 10**: 启动阶段 1 实施
4. **样本数 > 20**: 启动阶段 2-3 实施

---

## 📝 相关文档

- `simple_web_review_ui_plan.md` - Web 审核界面方案（输入）
- `SAMPLE_REGISTRY_SCHEMA.md` - 样本登记表 Schema
- `sample_review_service.py` - 样本审核服务
- `review_sample.py` - CLI 审核工具

---

**维护者**: 网球 AI 教练系统开发团队  
**最后更新**: 2026-04-15  
**状态**: 📋 规划完成，待实施
