# 🎾 飞书→COS→Qwen 完整分析流程

## 📋 架构设计

```
用户 (飞书) → 飞书机器人 → Python 服务 → 腾讯 COS → Qwen API → 返回结果
```

## 🔧 部署步骤

### 1. 安装依赖

```bash
cd /home/admin/.openclaw/workspace/ai-coach
pip3 install --user flask cos-python-sdk-v5 requests
```

### 2. 启动服务

```bash
# 后台运行
nohup python3 feishu_cos_analyzer.py server > feishu_server.log 2>&1 &

# 查看日志
tail -f feishu_server.log
```

### 3. 飞书配置

#### 3.1 创建飞书应用
- 访问：https://open.feishu.cn/app
- 创建新应用
- 获取 `App ID` 和 `App Secret`

#### 3.2 配置权限
需要以下权限：
- `im:message` - 读取和发送消息
- `im:resource` - 下载文件资源

#### 3.3 配置事件订阅
- 事件类型：`im.message.receive_v1`
- 订阅地址：`http://your-server-ip:5003/feishu/callback`

#### 3.4 配置机器人
- 在应用中添加机器人
- 发布到群聊或私聊

## 📱 使用方式

### 用户上传视频
1. 用户在飞书私聊或群聊中发送视频文件
2. 机器人自动接收并开始处理

### 处理流程
```
1. 下载飞书视频 → 临时文件
2. 上传到腾讯 COS → 生成永久存储
3. 生成预签名 URL → 临时访问链接（1 小时有效）
4. Qwen API 分析 → 网球动作分析
5. 保存结果到数据库 → 便于后续查询
6. 发送分析报告 → 飞书消息回复
```

### 用户收到的消息
```
✅ 视频已收到，正在分析中...（约 1-2 分钟）

---

🎾 网球发球分析报告

🏆 NTRP 等级：3.0 (基础级)
📊 置信度：75%
💯 综合评分：55/100

⚠️ 关键问题:
🔴 膝盖蓄力严重不足（约 150 度）
🟡 抛球方向偏向身体内侧
🟢 旋内动作幅度不足

💡 训练建议:
1. 优先改善膝盖蓄力：对镜子练习奖杯姿势
2. 抛球稳定性专项：每天 50 次单独抛球练习
3. 旋内专项：握短拍练习旋内击球

视频 ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

## 🗄️ 数据库

分析结果保存到：`/home/admin/.openclaw/workspace/ai-coach/data/xiaolongxia_learning.db`

### 表结构
```sql
CREATE TABLE video_analysis_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT UNIQUE,
    cos_key TEXT,
    user_open_id TEXT,
    ntrp_level TEXT,
    confidence REAL,
    overall_score INTEGER,
    analysis_result TEXT,
    status TEXT DEFAULT 'completed',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 📊 COS 存储结构

```
tennis-ai-1411340868.cos.ap-shanghai.myqcloud.com/
└── private-ai-learning/
    └── raw_videos/
        └── 2026-04-08/
            ├── {video_id_1}.mp4
            ├── {video_id_2}.mp4
            └── ...
```

## 🔐 安全配置

### COS 权限
- 当前使用主账号 SecretId/SecretKey
- 建议创建**子账号**，只给 COS 读写权限
- 设置 IP 白名单（如果可能）

### 飞书权限
- 使用 tenant_access_token（应用级）
- 定期更新 App Secret

## 🧪 测试

### 测试上传
```bash
python3 cos_qwen_analyzer.py 1
```

### 测试服务
```bash
python3 feishu_cos_analyzer.py server
```

## 📝 配置文件

编辑 `feishu_cos_analyzer.py` 中的配置：

```python
# 腾讯 COS 配置
COS_CONFIG = {
    'secret_id': '你的 SecretId',
    'secret_key': '你的 SecretKey',
    'bucket': 'tennis-ai-1411340868',
    'region': 'ap-shanghai',
}

# 飞书配置
FEISHU_CONFIG = {
    'app_id': '你的 App ID',
    'app_secret': '你的 App Secret',
}

# Qwen API 配置
DASHSCOPE_API_KEY = '你的 Dashscope API Key'
```

## 🚀 生产环境建议

1. **使用进程管理**
   ```bash
   # 使用 systemd
   sudo systemctl enable feishu-analyzer
   sudo systemctl start feishu-analyzer
   ```

2. **日志轮转**
   ```bash
   # 配置 logrotate
   /var/log/feishu-analyzer/*.log {
       daily
       rotate 7
       compress
   }
   ```

3. **监控告警**
   - 监控服务端口
   - 监控 COS 存储使用量
   - 监控 API 调用失败率

4. **性能优化**
   - 使用异步任务队列（Celery）
   - 视频分析超时设置
   - COS CDN 加速

## 📞 问题排查

### 飞书消息收不到
- 检查事件订阅配置
- 检查订阅地址是否可访问
- 查看服务器日志

### COS 上传失败
- 检查 SecretId/SecretKey
- 检查 Bucket 权限
- 检查网络连接

### Qwen 分析失败
- 检查 API Key 是否有效
- 检查视频 URL 是否可访问
- 查看 API 返回错误

---

**创建时间**: 2026-04-08  
**版本**: v1.0  
**作者**: AI Assistant