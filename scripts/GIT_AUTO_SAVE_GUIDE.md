# Git 自动保存机制

## 📋 功能说明

自动监控代码变化，自动提交到本地 Git 并推送到 GitHub，保证代码安全和对话连续性。

---

## 🔧 使用方法

### 手动触发
```bash
cd /home/admin/.openclaw/workspace/ai-coach
python3.8 scripts/auto_git_save.py "提交信息"
```

### 自动触发（推荐）

在以下情况自动触发保存：
1. 修改重要代码文件后
2. 创建新文件后
3. 会话结束前
4. 每天定时（凌晨 3 点）

---

## 📁 重要文件监控列表

### Python 代码
- `*.py` - 所有 Python 文件
- 特别是：
  - `auto_analyze_service.py`
  - `complete_analysis_service.py`
  - `qwen_client.py`
  - `report_generation_integration.py`
  - `analysis_result_saver.py`

### 配置文件
- `*.json` - 所有 JSON 配置
- 特别是：
  - `data/sample_registry.json`
  - `data/analysis_results.json`
  - `data/problem_index.json`

### 文档
- `*.md` - 所有 Markdown 文档
- 特别是：
  - `MEMORY.md`
  - `memory/*.md`
  - 决策文档

---

## 💾 会话状态文件

**位置**: `ai-coach/.session_state.json`

**内容**:
```json
{
  "timestamp": "2026-04-16T11:45:43",
  "message": "完整修复网球 AI 教练系统",
  "files_changed": [
    "M complete_analysis_service.py",
    "M qwen_client.py",
    "?? analysis_result_saver.py"
  ],
  "git_commit": "f2146b1d8d525bc59bbf0a2a758f763ee4f9dbdd 完整修复网球 AI 教练系统"
}
```

---

## 🔄 恢复会话流程

### 长时间后再次开启对话

1. **自动检查会话状态**
```bash
python3.8 scripts/auto_git_save.py --check-session
```

2. **读取上次状态**
```python
from scripts.auto_git_save import load_session_state
state = load_session_state()
print(f"上次保存时间：{state['timestamp']}")
print(f"提交信息：{state['message']}")
```

3. **恢复工作上下文**
- 查看上次修改的文件
- 查看 Git 提交历史
- 继续未完成的工作

---

## ⏰ 定时任务配置

### Crontab 配置
```bash
# 每天凌晨 3 点自动保存
0 3 * * * cd /home/admin/.openclaw/workspace/ai-coach && python3.8 scripts/auto_git_save.py "daily: 每日自动保存" >> logs/auto_git.log 2>&1

# 每小时检查会话状态
0 * * * * cd /home/admin/.openclaw/workspace/ai-coach && python3.8 scripts/auto_git_save.py --check-session >> logs/auto_git.log 2>&1
```

---

## 🛡️ 安全机制

### 1. 提交前检查
- 检查是否有敏感信息（API Key、密码等）
- 检查 `.env` 文件是否在 `.gitignore` 中
- 检查文件大小（避免提交大文件）

### 2. 推送前验证
- 验证 Git 仓库连接
- 验证远程仓库存在
- 验证权限正确

### 3. 错误处理
- 提交失败时保留本地更改
- 推送失败时记录日志
- 网络问题时重试机制

---

## 📊 监控日志

**日志位置**: `ai-coach/logs/auto_git.log`

**日志内容**:
```
2026-04-16 11:45:43 - 开始自动保存
2026-04-16 11:45:44 - 检测到 84 个文件变更
2026-04-16 11:45:45 - 已添加所有文件
2026-04-16 11:45:46 - 已提交到本地 Git
2026-04-16 11:45:50 - 已推送到 GitHub
2026-04-16 11:45:51 - 会话状态已保存
```

---

## 🎯 最佳实践

### 1. 重要改动后立即保存
```bash
# 修改关键代码后
python3.8 scripts/auto_git_save.py "feat: 修复 Qwen API 调用问题"
```

### 2. 会话结束前保存
```bash
# 对话结束前
python3.8 scripts/auto_git_save.py "session: 会话结束保存"
```

### 3. 定期查看提交历史
```bash
git log --oneline -20
```

### 4. 恢复工作时先检查状态
```bash
python3.8 scripts/auto_git_save.py --check-session
```

---

## 🔍 常用命令

### 检查会话状态
```bash
python3.8 scripts/auto_git_save.py --check-session
```

### 查看上次保存时间
```bash
cat ai-coach/.session_state.json | python3.8 -m json.tool
```

### 手动保存
```bash
python3.8 scripts/auto_git_save.py "自定义提交信息"
```

### 查看提交历史
```bash
git log --oneline --graph -20
```

### 恢复特定提交
```bash
git checkout <commit-hash>
```

---

## ⚠️ 注意事项

1. **不要提交敏感信息**
   - API Key、密码等放在 `.env` 文件
   - `.env` 已加入 `.gitignore`

2. **大文件不要提交**
   - 视频文件、模型文件等不要提交
   - 使用 COS 或其他对象存储

3. **定期清理 Git 历史**
   - 避免 Git 仓库过大
   - 定期清理测试文件

4. **备份重要数据**
   - 数据库文件定期备份
   - 样本库定期导出

---

**创建时间**: 2026-04-16  
**最后更新**: 2026-04-16  
**维护人**: AI Assistant
