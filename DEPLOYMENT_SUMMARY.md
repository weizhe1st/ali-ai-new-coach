# 🎾 飞书→COS→Qwen 完整分析流程 - 部署总结

## ✅ 已完成的工作

### 1. 环境准备 ✅
- ✅ COS SDK 安装成功 (`cos-python-sdk-v5`)
- ✅ Flask 框架安装成功
- ✅ Qwen API 配置完成 (API Key: `sk-88532d38dbe04d3a9b73c921ce25794c`)
- ✅ 腾讯 COS 连接测试成功 (找到 20 个视频文件)

### 2. 代码开发 ✅
创建了以下核心文件：

| 文件 | 功能 | 状态 |
|------|------|------|
| `cos_qwen_analyzer.py` | COS 视频读取 + Qwen 分析 | ✅ 测试通过 |
| `feishu_cos_analyzer.py` | 飞书回调 + 完整流程 | ✅ 已创建 |
| `qwen_analysis_simple.py` | Qwen 分析简化版 | ✅ 测试通过 |
| `start_feishu_service.sh` | 服务启动脚本 | ✅ 已创建 |

### 3. 文档创建 ✅
- ✅ `FEISHU_COS_DEPLOYMENT.md` - 详细部署文档
- ✅ `DEPLOYMENT_SUMMARY.md` - 本文件

---

## 🚀 快速启动

### 方式一：使用启动脚本（推荐）

```bash
cd /home/admin/.openclaw/workspace/ai-coach
./start_feishu_service.sh
```

### 方式二：手动启动

```bash
cd /home/admin/.openclaw/workspace/ai-coach
python3 feishu_cos_analyzer.py server
```

---

## 📱 飞书配置步骤

### 1. 创建飞书应用
1. 访问：https://open.feishu.cn/app
2. 点击"创建应用"
3. 填写应用名称（如"网球 AI 教练"）
4. 进入应用管理后台

### 2. 获取凭证
在"凭证与基础信息"页面获取：
- **App ID** (格式：`cli_xxxxxxxxxxxxxxxx`)
- **App Secret**

### 3. 配置权限
在"权限管理"页面添加：
- `im:message` - 读取和发送消息
- `im:resource` - 下载文件资源

### 4. 配置事件订阅
1. 进入"事件订阅"页面
2. 订阅以下事件：
   - `im.message.receive_v1` (接收消息)
3. 填写订阅地址：
   ```
   http://你的服务器 IP:5003/feishu/callback
   ```
4. 点击"完成"，系统会发送验证请求

### 5. 配置机器人
1. 进入"机器人"页面
2. 创建机器人（如"网球 AI 教练"）
3. 将机器人添加到群聊或启用私聊

### 6. 更新配置
编辑 `feishu_cos_analyzer.py`，更新飞书配置：

```python
FEISHU_CONFIG = {
    'app_id': 'cli_你的 App ID',
    'app_secret': '你的 App Secret',
}
```

---

## 🧪 测试流程

### 1. 启动服务
```bash
./start_feishu_service.sh
```

### 2. 查看日志
```bash
tail -f feishu_server.log
```

### 3. 发送测试视频
在飞书中：
1. 找到机器人（私聊或群聊）
2. 发送一个网球发球视频（MP4 格式）
3. 等待回复

### 4. 预期结果
```
✅ 视频已收到，正在分析中...（约 1-2 分钟）

---

🎾 网球发球分析报告

🏆 NTRP 等级：3.0 (基础级)
📊 置信度：75%
💯 综合评分：55/100

⚠️ 关键问题:
🔴 膝盖蓄力严重不足
🟡 抛球方向偏向身体内侧

💡 训练建议:
1. 优先改善膝盖蓄力
2. 抛球稳定性专项练习
...
```

---

## 📊 架构图

```
┌─────────┐      ┌──────────┐      ┌─────────────┐
│  飞书   │      │  Python   │      │   腾讯 COS   │
│  用户   │ ──→  │   服务    │ ──→  │  (存储视频)  │
│  (视频) │      │ (5003 端口) │      │             │
└─────────┘      └────┬─────┘      └──────┬──────┘
                      │                   │
                      │                   ↓
                      │            ┌─────────────┐
                      │            │ 预签名 URL   │
                      │            │ (1 小时有效) │
                      │            └──────┬──────┘
                      │                   │
                      ↓                   ↓
                ┌─────────────────────────┐
                │     Qwen API 分析       │
                │  (三步分析法 + 知识库)   │
                └───────────┬─────────────┘
                            │
                            ↓
                      ┌─────────────┐
                      │  数据库保存  │
                      │ (分析结果)   │
                      └──────┬──────┘
                             │
                             ↓
                      ┌──────────┐
                      │ 飞书回复  │
                      │ (分析报告)│
                      └──────────┘
```

---

## 🔧 配置检查清单

在启动服务前，请确认：

- [ ] COS SecretId 和 SecretKey 已配置
- [ ] COS Bucket 和 Region 正确
- [ ] Dashscope API Key 已配置
- [ ] 飞书 App ID 和 App Secret 已配置
- [ ] 飞书事件订阅地址已设置
- [ ] 服务器 5003 端口可访问（防火墙）
- [ ] 数据库目录存在 (`data/`)

---

## 📝 数据库说明

### 位置
```
/home/admin/.openclaw/workspace/ai-coach/data/xiaolongxia_learning.db
```

### 表结构
```sql
CREATE TABLE video_analysis_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT UNIQUE,          -- 视频唯一 ID
    cos_key TEXT,                   -- COS 存储路径
    user_open_id TEXT,              -- 用户飞书 ID
    ntrp_level TEXT,                -- NTRP 等级
    confidence REAL,                -- 置信度
    overall_score INTEGER,          -- 综合评分
    analysis_result TEXT,           -- 完整分析结果 (JSON)
    status TEXT DEFAULT 'completed',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 查询分析结果
```bash
sqlite3 data/xiaolongxia_learning.db
SELECT * FROM video_analysis_tasks ORDER BY created_at DESC LIMIT 10;
```

---

## 📈 COS 存储管理

### 查看已上传视频
```bash
python3 cos_qwen_analyzer.py
```

### 存储路径
```
tennis-ai-1411340868.cos.ap-shanghai.myqcloud.com/
└── private-ai-learning/
    └── raw_videos/
        ├── 2026-03-31/
        │   └── {video_id}.mp4
        └── 2026-04-08/
            └── {video_id}.mp4
```

### 访问方式
- **私有读**：通过预签名 URL 访问（推荐）
- **公有读**：修改 Bucket 权限（不推荐）

---

## 🐛 常见问题

### 1. 飞书消息收不到
**检查**:
- 事件订阅是否配置正确
- 订阅地址是否可公网访问
- 服务器防火墙是否开放 5003 端口

**解决**:
```bash
# 查看服务是否运行
ps aux | grep feishu_cos_analyzer

# 查看日志
tail -f feishu_server.log
```

### 2. COS 上传失败
**检查**:
- SecretId/SecretKey 是否正确
- Bucket 名称是否正确
- 网络连接是否正常

**测试**:
```bash
python3 cos_qwen_analyzer.py
```

### 3. Qwen 分析超时
**原因**: 视频过大或网络问题

**解决**:
- 限制视频大小（建议 < 20MB）
- 增加 API timeout 设置
- 检查视频 URL 是否可访问

### 4. 数据库不存在
**解决**:
```bash
mkdir -p data
# 首次运行时会自动创建表
```

---

## 🚀 下一步优化建议

### 1. 性能优化
- [ ] 使用异步任务队列（Celery）
- [ ] 视频分析超时控制
- [ ] COS CDN 加速

### 2. 功能增强
- [ ] 支持视频查询命令（查视频 [video_id]）
- [ ] 支持历史分析对比
- [ ] 支持多人对战分析

### 3. 监控告警
- [ ] 服务健康检查
- [ ] API 调用失败告警
- [ ] COS 存储容量监控

### 4. 安全加固
- [ ] 创建 COS 子账号（最小权限）
- [ ] 设置 IP 白名单
- [ ] 请求签名验证

---

## 📞 技术支持

### 日志文件
- 服务日志：`feishu_server.log`
- COS 日志：`cos_upload.log`
- Qwen 日志：`qwen_analysis.log`

### 关键配置
- 飞书配置：`feishu_cos_analyzer.py` (FEISHU_CONFIG)
- COS 配置：`feishu_cos_analyzer.py` (COS_CONFIG)
- Qwen 配置：`feishu_cos_analyzer.py` (DASHSCOPE_API_KEY)

### 数据库备份
```bash
# 备份数据库
cp data/xiaolongxia_learning.db data/backup_$(date +%Y%m%d).db

# 恢复数据库
cp data/backup_20260408.db data/xiaolongxia_learning.db
```

---

**创建时间**: 2026-04-08  
**版本**: v1.0  
**状态**: ✅ 部署就绪

---

## 🎯 立即开始

```bash
# 1. 启动服务
cd /home/admin/.openclaw/workspace/ai-coach
./start_feishu_service.sh

# 2. 配置飞书（在飞书开放平台）
# 3. 发送测试视频
# 4. 查看分析结果！
```

**祝你使用愉快！** 🎾🚀
