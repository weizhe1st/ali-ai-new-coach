# 📋 Git 自动保存机制 - 快速使用指南

## ✅ 已配置完成

### 1️⃣ 自动保存脚本
- **位置**: `scripts/auto_git_save.py`
- **功能**: 自动检测代码变化，提交到 Git，推送到 GitHub
- **触发**: 手动或定时（每天凌晨 3 点）

### 2️⃣ 会话连续性管理
- **位置**: `scripts/session_continuity.py`
- **功能**: 保存会话状态，恢复长时间未对话的上下文
- **触发**: 对话开始时自动检查

### 3️⃣ 会话状态文件
- **位置**: `ai-coach/.session_state.json`
- **内容**: 上次保存时间、提交信息、变更文件列表

---

## 🚀 快速使用

### 手动保存代码
```bash
cd /home/admin/.openclaw/workspace/ai-coach
python3.8 scripts/auto_git_save.py "提交信息"
```

### 检查会话状态
```bash
python3.8 scripts/session_continuity.py
```

### 查看上次保存
```bash
cat .session_state.json | python3.8 -m json.tool
```

---

## ⏰ 定时任务

已配置 crontab：
- **每天凌晨 3 点**: 自动保存代码
- **对话开始时**: 检查会话状态

查看定时任务：
```bash
crontab -l
```

---

## 📊 使用场景

### 场景 1：重要代码改动后
```bash
# 修改完关键代码后
python3.8 scripts/auto_git_save.py "feat: 修复 Qwen API 调用问题"
```

### 场景 2：长时间后再次对话
```bash
# 对话开始时自动检查
python3.8 scripts/session_continuity.py

# 输出示例：
# 状态：long_break
# 距离上次对话已 3 天
# 建议：先查看 Git 提交历史和会话状态
```

### 场景 3：会话结束前
```bash
# 保存当前状态
python3.8 scripts/auto_git_save.py "session: 会话结束保存"
```

---

## 📁 监控的重要文件

### Python 代码
- `auto_analyze_service.py`
- `complete_analysis_service.py`
- `qwen_client.py`
- `report_generation_integration.py`
- `analysis_result_saver.py`
- 所有 `*.py` 文件

### 配置文件
- `data/sample_registry.json`
- `data/analysis_results.json`
- `data/problem_index.json`
- 所有 `*.json` 文件

### 文档
- `memory/*.md`
- 决策文档
- 所有 `*.md` 文件

---

## 🔍 日志查看

**日志位置**: `logs/auto_git.log`

查看日志：
```bash
tail -50 logs/auto_git.log
```

---

## 💡 最佳实践

1. **重要改动后立即保存**
   - 修改关键代码后
   - 添加新功能后
   - 修复 bug 后

2. **会话结束前保存**
   - 对话结束前
   - 离开前

3. **恢复工作时检查**
   - 长时间后再次对话
   - 不确定上次做了什么

4. **定期查看历史**
   - `git log --oneline -20`
   - 了解代码演变

---

## ⚠️ 注意事项

1. **不要提交敏感信息**
   - `.env` 已在 `.gitignore` 中
   - API Key、密码等不要硬编码

2. **大文件不要提交**
   - 视频文件使用 COS
   - 模型文件使用对象存储

3. **定期清理**
   - 清理测试文件
   - 避免 Git 仓库过大

---

## 📞 遇到问题

### 推送失败
```bash
# 检查网络连接
ping github.com

# 手动推送
cd ai-coach && git push origin master
```

### 会话状态丢失
```bash
# 查看 Git 历史恢复
git log --oneline -10
git show <commit-hash>
```

---

**创建时间**: 2026-04-16 11:50  
**状态**: ✅ 已配置完成并测试通过
