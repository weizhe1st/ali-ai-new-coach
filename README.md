# 🎾 网球 AI 教练系统

**阿里云部署版本** | 基于原腾讯云系统迁移优化

---

## 📊 系统功能

- ✅ **视频分析**：上传网球发球视频，AI 自动分析动作
- ✅ **NTRP 评级**：精准评估球员等级（3.0-5.0）
- ✅ **知识库对照**：169 条专业教练知识点
- ✅ **量化指标**：MediaPipe 姿态分析（膝盖/肘部/肩部角度）
- ✅ **通俗报告**：通俗易懂的改进建议
- ✅ **多渠道路由**：钉钉/QQ 支持（飞书已禁用）

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- OpenClaw Gateway
- 阿里云服务器

### 安装依赖

```bash
# Python 3.8 环境
sudo pip3.8 install -r requirements.txt
```

### 启动服务

```bash
# 1. 确保 OpenClaw Gateway 运行中
openclaw gateway status

# 2. 启动视频分析服务
cd /home/admin/.openclaw/workspace/ai-coach
python3.8 simple_integration.py &

# 3. 测试
在钉钉中发送网球发球视频
```

---

## 📁 项目结构

```
ai-coach/
├── models/                    # 数据模型
│   ├── message.py             # 统一消息结构
│   └── task.py                # 统一任务结构
├── adapters/                  # 渠道适配器
│   ├── dingtalk_adapter.py    # 钉钉适配器
│   └── qq_adapter.py          # QQ 适配器
├── router.py                  # 路由层
├── task_executor.py           # 执行层
├── 核心模块
│   ├── core.py                # 核心配置
│   ├── complete_analysis_service.py  # 主分析服务
│   └── complete_report_generator.py  # 报告生成器
├── 知识库
│   └── fused_knowledge/       # 169 条融合知识
├── data/db/                   # 数据库
│   └── app.db                 # 含黄金标准表
├── reports/                   # 分析报告
├── media/inbound/             # 输入视频（临时）
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🎯 核心功能

### 1. MediaPipe 姿态分析

```python
from mediapipe_analyzer import MediaPipeAnalyzer

analyzer = MediaPipeAnalyzer()
metrics = analyzer.analyze_video('video.mp4')

# 输出：
# - 膝盖角度：145.3° (平均)
# - 肘部角度：172.2° (最大)
# - 肩部旋转：76.0°
```

### 2. AI 视频分析

使用 `qwen-vl-max` 进行视觉分析：
- 三步分析法（观察 → 对照 → 输出）
- 169 条教练知识库对照
- NTRP 黄金标准评级

### 3. 通俗化报告生成

```
🎾 网球发球分析报告

📊 综合评估
  NTRP 等级：3.0
  置信度：85%
  综合评分：68/100

✅ 做得好的地方
  ✓ 抛球手释放时手指自然张开
  ✓ 完成完整挥拍路径

⚠️ 需要改进
  🟠 [抛球] 抛球方向偏了
  🟠 [蓄力] 手肘抬得不够高

💪 训练建议
  1. 调整抛球方向
  2. 强化奖杯姿势训练
```

---

## 📊 技术架构

```
钉钉用户 → OpenClaw Gateway → 视频保存
                                    ↓
                          simple_integration.py
                                    ↓
                          ├─ MediaPipe 量化分析
                          ├─ qwen-vl-max 视觉分析
                          └─ 知识库对照
                                    ↓
                          生成通俗化报告
                                    ↓
                          保存到 reports/
```

---

## 🔧 配置说明

### 模型配置

编辑 `core.py`:
```python
MODEL_NAME = 'qwen-max'  # 文本分析
# 或
MODEL_NAME = 'qwen-vl-max'  # 视频分析
```

### API Key 配置

```bash
export DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxx"
```

### 数据库配置

```python
DB_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/db/app.db'
```

---

## 🏗️ 系统架构

### 分层设计

系统采用四层架构：

```
┌─────────────────────────────────────┐
│  接入层 (Adapters)                   │
│  - 钉钉适配器 (adapters/dingtalk_adapter.py) │
│  - QQ 适配器 (adapters/qq_adapter.py)        │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│  路由层 (router.py)                  │
│  - 接收 UnifiedMessage               │
│  - 创建 UnifiedTask                  │
│  - 交给 TaskExecutor                 │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│  执行层 (task_executor.py)           │
│  - 执行视频分析任务                  │
│  - 执行文本处理任务                  │
│  - 统一错误处理                      │
│  - 统一结果包装                      │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│  分析层 (核心模块)                    │
│  - complete_analysis_service.py      │
│  - complete_report_generator.py      │
│  - mediapipe_analyzer.py             │
│  - fused_knowledge/                  │
└─────────────────────────────────────┘
```

### 各层职责

**接入层**:
- 接收渠道原始消息（钉钉/QQ）
- 转换为 UnifiedMessage
- 不处理业务逻辑

**路由层**:
- 接收 UnifiedMessage
- 创建 UnifiedTask
- 交给 TaskExecutor 执行
- 不直接执行业务

**执行层**:
- 接收 UnifiedTask
- 根据 task_type 执行
- 调用旧分析能力
- 统一错误处理
- 统一结果包装

**分析层**:
- 视频分析核心逻辑
- MediaPipe 姿态分析
- 报告生成
- 知识库处理

### 渠道接入说明

当前系统支持以下渠道：

1. **钉钉（主入口）**
   - 适配器：`adapters/dingtalk_adapter.py`
   - 消息类型：文本、视频、图片、文件
   - 状态：✅ 已接入统一路由

2. **QQ（辅入口）**
   - 适配器：`adapters/qq_adapter.py`
   - 消息类型：文本、视频、图片、文件
   - 状态：✅ 已接入统一路由

**消息流转流程**:
```
渠道原始消息 → 适配器 → UnifiedMessage → Router → UnifiedTask → 分析服务
```

**渠道适配器职责**:
- 只负责解析原始消息
- 转换为统一消息格式
- 不处理业务逻辑
- 不直接调用分析服务

**注意**:
- 当前视频分析复用现有分析能力
- 当前文本处理为轻量版本（占位）
- 飞书渠道已禁用（阿里云版本）

### 消息流转

1. **渠道消息** → 适配器 → `UnifiedMessage`
2. **UnifiedMessage** → 路由器 → `UnifiedTask`
3. **UnifiedTask** → 分析服务 → 报告

---

## 📝 使用示例

### 发送视频分析

1. 在钉钉中找到网球 AI 教练机器人
2. 发送网球发球视频（MP4 格式，< 20MB）
3. 等待 1-2 分钟
4. 收到 AI 分析报告

### 代码示例

```python
from router import MessageRouter, from_dingtalk

# 创建路由器（包含 TaskExecutor）
router = MessageRouter()

# 注册视频分析处理器（可选）
router.register_video_handler(your_video_handler)

# 接收钉钉消息
message = from_dingtalk(
    user_id='user_123',
    text='帮我分析这个发球',
    file_path='/path/to/video.mp4'
)

# 路由处理（自动交给 TaskExecutor 执行）
result = router.route_message(message)

# 获取统一结果
print(f"任务状态：{result['status']}")
print(f"任务 ID: {result['task_id']}")
print(f"分析报告：{result['report']}")
```

**返回结果结构**:
```python
{
  "task_id": "uuid",
  "task_type": "video_analysis",
  "status": "success",
  "channel": "dingtalk",
  "message_type": "video",
  "result": {...},
  "report": "分析报告",
  "error": None
}
```

### 查看历史报告

```bash
ls -lt /home/admin/.openclaw/workspace/ai-coach/reports/
```

### 查询数据库

```bash
sqlite3 data/db/app.db
SELECT * FROM video_analysis_tasks ORDER BY created_at DESC LIMIT 10;
```

---

## 🐛 故障排查

### 服务未运行

```bash
# 检查进程
ps aux | grep simple_integration

# 重启服务
python3.8 simple_integration.py &
```

### MediaPipe 无法加载

```bash
# 检查 Python 版本
python3.8 --version  # 需要 3.8+

# 重新安装
sudo pip3.8 install mediapipe==0.10.11 --no-deps
```

### 视频分析失败

检查日志：
```bash
tail -f simple_integration.log
```

---

## 📈 性能指标

| 指标 | 值 |
|------|-----|
| 视频分析时间 | 30-60 秒 |
| MediaPipe 检测率 | > 95% |
| 报告生成时间 | < 5 秒 |
| 支持视频格式 | MP4, MOV, AVI |
| 最大视频大小 | 20MB |

---

## 📚 知识库来源

- **杨超教练**: 71 条（NTRP 分级标准）
- **赵凌曦教练**: 41 条（节奏与纠错）
- **Yellow 教练**: 57 条（动作细节）

总计：**169 条**专业教练知识

---

## 🔄 版本历史

### v2.0 (2026-04-09) - 阿里云版本
- ✅ 迁移到阿里云
- ✅ Python 3.8 升级
- ✅ MediaPipe 集成
- ✅ 报告通俗化优化
- ✅ OpenClaw 集成

### v1.0 (2026-04-01) - 腾讯云版本
- ✅ 初始版本
- ✅ 三步分析法
- ✅ 知识库融合
- ✅ 黄金标准数据库

---

## 🤝 协作开发

### Git 工作流

```bash
# 1. 克隆仓库
git clone https://github.com/weizhe1st/ali-ai-new-coach.git

# 2. 创建分支
git checkout -b feature/new-feature

# 3. 提交修改
git add .
git commit -m "feat: 添加新功能"

# 4. 推送
git push origin feature/new-feature

# 5. 创建 Pull Request
```

---

## 📞 联系方式

- **GitHub**: https://github.com/weizhe1st/ali-ai-new-coach
- **问题反馈**: 请在 GitHub 提交 Issue

---

## 📄 许可证

本项目仅供学习和研究使用。

---

**🎾 享受网球，享受 AI 带来的便利！**
