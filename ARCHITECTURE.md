# 🎾 网球 AI 教练系统 - 完整架构流程

**版本**: v2.0 (2026-04-17)  
**文档**: 从视频上传到输出结果的完整流程

---

## 📊 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        网球 AI 教练系统完整流程                          │
└─────────────────────────────────────────────────────────────────────────┘

【1. 视频上传层】
    │
    ├─ 用户通过钉钉/微信上传视频
    │  └─ OpenClaw Gateway → media/inbound/
    │
    └─ 视频文件落盘
       └─ video-xxxxxxxxxxx.mp4

【2. 自动扫描层】(auto_analyze_service.py)
    │
    ├─ 定时扫描 (每 60 秒)
    │  ├─ 第一层：扫描未处理视频文件
    │  └─ 第二层：扫描未完成任务
    │
    └─ 数据库记录
       ├─ video_files 表 (文件元数据)
       └─ analysis_tasks 表 (任务状态)

【3. 分析执行层】(complete_analysis_service.py)
    │
    ├─ 步骤 1: 视频预处理
    │  ├─ 提取关键帧 (12 帧)
    │  └─ 帧选择策略 (均匀分布)
    │
    ├─ 步骤 2: MediaPipe 姿态估计
    │  ├─ 人体关键点检测 (33 个点)
    │  ├─ 关节角度计算
    │  └─ 动作阶段识别
    │
    ├─ 步骤 3: Qwen-VL 视觉分析
    │  ├─ 上传关键帧到 Qwen
    │  ├─ 姿势描述生成
    │  └─ 问题识别
    │
    └─ 步骤 4: NTRP 等级评估
       ├─ 动作质量评分
       └─ 等级判定 (2.0-5.0)

【4. 知识增强层】(knowledge_gold_analyzer.py)
    │
    ├─ 黄金样本库对比
    │  ├─ 169 条教练知识库检索
    │  ├─ 7 个 NTRP 等级黄金标准
    │  └─ 相似度匹配
    │
    └─ 改进建议生成
       ├─ 主要问题 (Primary Issue)
       ├─ 次要问题 (Secondary Issue)
       └─ 优先级排序

【5. 报告生成层】(complete_report_generator.py)
    │
    ├─ 结构化数据整合
    │  ├─ 姿势描述
    │  ├─ 问题列表
    │  ├─ NTRP 等级
    │  └─ 改进建议
    │
    ├─ 自然语言报告
    │  ├─ 整体评价
    │  ├─ 详细分析
    │  └─ 训练建议
    │
    └─ 报告格式化
       ├─ Markdown 格式
       └─ 钉钉消息适配

【6. 存储归档层】(sample_archive_service.py)
    │
    ├─ COS 对象存储
    │  ├─ 原始视频上传
    │  ├─ 关键帧图片上传
    │  └─ 分析报告上传
    │
    ├─ 样本登记
    │  ├─ sample_registry.json
    │  ├─ 元数据记录
    │  └─ 状态标记 (pending/approved/rejected)
    │
    └─ 数据库更新
       ├─ 任务状态 → completed
       ├─ NTRP 等级记录
       └─ 样本分类标记

【7. 结果输出层】
    │
    ├─ 钉钉消息推送
    │  ├─ 分析完成通知
    │  └─ 完整报告发送
    │
    └─ 样本审核队列
       └─ review_sample.py (人工审核工具)
```

---

## 🔄 详细流程说明

### 阶段 1: 视频上传 (User → System)

**触发方式**:
- 用户在钉钉聊天中发送视频
- OpenClaw Gateway 接收消息
- 视频保存到 `media/inbound/` 目录

**文件命名**: `video-<timestamp>.mp4`

**数据库操作**:
```sql
-- 此时尚未创建记录，等待 auto_analyze_service 扫描
```

---

### 阶段 2: 自动扫描 (auto_analyze_service.py)

**扫描频率**: 每 60 秒

**第一层扫描 - 新视频检测**:
```python
def scan_unprocessed_videos():
    # 扫描 media/inbound/*.mp4
    # 检查 video_files 表是否已有记录
    # 如果没有 → 创建视频文件记录 + 分析任务
```

**第二层扫描 - 未完成任务**:
```python
def scan_incomplete_tasks():
    # 查询 status='pending' 的任务
    # 查询 status='failed' 且 retry_count<3 的任务
    # 返回待处理任务列表
```

**数据库表结构**:
```sql
-- video_files 表
id, file_path, file_hash, file_size, duration, upload_time

-- analysis_tasks 表
id, task_id, video_file_id, status, retry_count, 
ntrp_level, sample_category, primary_issue, 
secondary_issue, created_at, updated_at
```

---

### 阶段 3: 视频分析 (complete_analysis_service.py)

**输入**: 任务信息 (task_id, file_path, file_name)

**步骤 1 - 视频预处理**:
```python
def extract_keyframes(video_path, num_frames=12):
    # 使用 OpenCV 提取关键帧
    # 策略：均匀分布，覆盖完整动作周期
    # 输出：12 帧关键帧图片
```

**步骤 2 - MediaPipe 姿态估计**:
```python
def extract_pose_landmarks(frame):
    # MediaPipe Pose 模型
    # 33 个身体关键点
    # 计算关节角度 (肩、肘、腕、髋、膝、踝)
    # 识别动作阶段 (准备、抛球、挥拍、随挥)
```

**步骤 3 - Qwen-VL 视觉分析**:
```python
def analyze_with_qwen_vl(keyframes, prompt):
    # 上传关键帧到 Qwen-VL
    # Prompt: "分析这个网球发球动作..."
    # 返回：姿势描述、问题识别、改进建议
```

**步骤 4 - NTRP 等级评估**:
```python
def evaluate_ntrp_level(analysis_result):
    # 基于动作质量评分
    # 对照 7 个等级黄金标准 (2.0-5.0)
    # 输出：NTRP 等级 + 置信度
```

---

### 阶段 4: 知识增强 (knowledge_gold_analyzer.py)

**知识库检索**:
```python
def search_knowledge_base(query, top_k=5):
    # 169 条教练知识库
    # 语义相似度检索
    # 返回：相关知识点
```

**黄金样本对比**:
```python
def compare_with_gold_samples(ntrp_level, features):
    # 加载对应 NTRP 等级的黄金样本
    # 特征向量对比
    # 输出：差异分析
```

**改进建议生成**:
```python
def generate_improvement_suggestions(issues, knowledge):
    # 整合问题列表 + 知识库
    # 生成优先级建议
    # 输出：主要问题 + 次要问题
```

---

### 阶段 5: 报告生成 (complete_report_generator.py)

**结构化数据**:
```python
{
    "ntrp_level": "3.0",
    "overall_score": 75,
    "primary_issue": "抛球位置不稳定",
    "secondary_issue": "挥拍轨迹不完整",
    "pose_description": "...",
    "improvement_suggestions": [...]
}
```

**自然语言报告**:
```markdown
## 🎾 网球发球动作分析报告

### 整体评价
您的发球动作评估为 NTRP 3.0 水平...

### 主要问题
1. **抛球位置不稳定** - 抛球高度变化较大...

### 改进建议
1. 练习固定抛球点...
```

---

### 阶段 6: 存储归档 (sample_archive_service.py)

**COS 上传**:
```python
def upload_to_cos(file_path, category):
    # 原始视频 → cos://analyzed/YYYY/MM/task_id/video.mp4
    # 关键帧 → cos://analyzed/YYYY/MM/task_id/frames/
    # 报告 → cos://analyzed/YYYY/MM/task_id/report.md
```

**样本登记**:
```json
{
    "sample_id": "auto_b7ab16f25f55",
    "video_path": "cos://...",
    "ntrp_level": "3.0",
    "category": "typical_issue",
    "status": "pending",
    "created_at": "2026-04-17T06:17:53+08:00"
}
```

**数据库更新**:
```sql
UPDATE analysis_tasks 
SET status='completed', 
    ntrp_level='3.0',
    sample_category='typical_issue',
    updated_at=NOW()
WHERE task_id='auto_b7ab16f25f55';
```

---

### 阶段 7: 结果输出

**钉钉推送**:
```python
def send_report_via_dingtalk(task_id, report):
    # 发送 Markdown 格式报告
    # 包含关键帧缩略图
    # 附带 COS 下载链接
```

**样本审核队列**:
```bash
# 人工审核工具
python review_sample.py auto_b7ab16f25f55 --approve
python review_sample.py auto_b7ab16f25f55 --reject
python review_sample.py auto_b7ab16f25f55 --set-ntrp 3.5
```

---

## 📁 核心文件清单

| 文件 | 职责 | 行数 |
|------|------|------|
| `auto_analyze_service.py` | 自动扫描与任务调度 | ~500 |
| `complete_analysis_service.py` | 视频分析核心逻辑 | ~600 |
| `knowledge_gold_analyzer.py` | 知识库检索与对比 | ~400 |
| `complete_report_generator.py` | 报告生成 | ~350 |
| `sample_archive_service.py` | COS 归档与样本登记 | ~300 |
| `auto_analyze_db.py` | 数据库模型与操作 | ~250 |
| `review_sample.py` | 样本审核命令行工具 | ~150 |

---

## 🔧 配置项

**环境变量** (`.env`):
```bash
# 数据库
DB_PATH=/home/admin/.openclaw/workspace/ai-coach/data/auto_analyze.db

# COS 存储
COS_BUCKET=tennis-ai-1411340868
COS_REGION=ap-shanghai
COS_SECRET_ID=xxx
COS_SECRET_KEY=xxx

# Qwen API
DASHSCOPE_API_KEY=xxx

# 媒体目录
MEDIA_DIR=/home/admin/.openclaw/workspace/media/inbound

# 扫描间隔
SCAN_INTERVAL=60
```

---

## 📊 数据流图

```
用户 → 钉钉 → OpenClaw → media/inbound/
                              ↓
                    auto_analyze_service.py
                              ↓
                    ┌─────────────────┐
                    │   数据库记录     │
                    │ video_files     │
                    │ analysis_tasks  │
                    └─────────────────┘
                              ↓
                    complete_analysis_service.py
                              ↓
                    ┌─────────────────┐
                    │   MediaPipe     │ → 关键点
                    │   Qwen-VL       │ → 分析
                    │   NTRP 评估     │ → 等级
                    └─────────────────┘
                              ↓
                    knowledge_gold_analyzer.py
                              ↓
                    complete_report_generator.py
                              ↓
                    sample_archive_service.py
                              ↓
                    ┌─────────────────┐
                    │   COS 存储       │
                    │   样本登记       │
                    └─────────────────┘
                              ↓
                    钉钉推送报告 + 审核队列
```

---

## 🎯 关键设计决策

1. **数据库驱动**: 不再依赖时间窗口扫描，使用数据库状态管理
2. **两层扫描**: 新视频检测 + 未完成任务重试
3. **黄金样本库**: 169 条知识库 + 7 个 NTRP 等级标准
4. **自动归档**: 分析成功后自动上传 COS 并登记
5. **人工审核**: 候选样本需人工审核后进入正式库
6. **重试机制**: 失败任务最多重试 3 次

---

**更新时间**: 2026-04-17 06:33  
**维护者**: AI Coach Team
