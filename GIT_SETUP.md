# 📤 GitHub 推送指南

## ✅ 本地提交已完成

代码已经成功提交到本地 Git 仓库：
- 提交 ID: `79f254e`
- 提交信息：🎾 网球 AI 教练系统 v2.0 - 阿里云部署

---

## 🔐 配置 GitHub 认证

### 方法 1: 使用 Personal Access Token（推荐）

#### 步骤 1: 创建 Token

1. 登录 GitHub: https://github.com
2. 设置 → Developer settings → Personal access tokens → Tokens (classic)
3. 点击 "Generate new token (classic)"
4. 填写信息:
   - **Note**: `ali-ai-new-coach`
   - **Expiration**: 选择过期时间（建议 90 天）
   - **Select scopes**: 勾选 `repo` (完整仓库权限)
5. 点击 "Generate token"
6. **复制 Token**（只显示一次，格式如 `ghp_xxxxxxxxxxxx`）

#### 步骤 2: 配置 Git 使用 Token

```bash
cd /home/admin/.openclaw/workspace/ai-coach

# 方法 A: 临时使用（下次推送还需输入）
git push -u origin master
# 当提示输入密码时，粘贴 Token

# 方法 B: 保存 Token（推荐）
git config --global credential.helper store
git push -u origin master
# 输入一次后会自动保存
```

---

### 方法 2: 使用 SSH Key

#### 步骤 1: 生成 SSH Key

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# 一路回车即可
```

#### 步骤 2: 添加 SSH Key 到 GitHub

1. 复制公钥:
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```
2. GitHub → Settings → SSH and GPG keys → New SSH key
3. 粘贴公钥，保存

#### 步骤 3: 切换远程仓库为 SSH

```bash
cd /home/admin/.openclaw/workspace/ai-coach
git remote set-url origin git@github.com:weizhe1st/ali-ai-new-coach.git
git push -u origin master
```

---

## 📋 推送命令

### 首次推送（已配置 upstream）

```bash
cd /home/admin/.openclaw/workspace/ai-coach
git push -u origin master
```

### 后续推送

```bash
git push
```

### 查看状态

```bash
git status
git log --oneline -5
```

---

## 🔄 日常开发流程

### 1. 修改代码

```bash
# 编辑文件
vim some_file.py

# 查看修改
git status
git diff
```

### 2. 提交修改

```bash
# 添加到暂存区
git add .

# 或者只添加特定文件
git add some_file.py

# 提交
git commit -m "feat: 添加新功能"
```

### 3. 推送到 GitHub

```bash
git push
```

---

## 📝 提交信息规范

### 格式

```
<type>: <description>

[optional body]
```

### Type 类型

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具链相关

### 示例

```bash
git commit -m "feat: 添加 MediaPipe 量化分析"
git commit -m "fix: 修复视频上传兼容性问题"
git commit -m "docs: 更新 README.md"
git commit -m "refactor: 优化报告生成逻辑"
```

---

## 🎯 快速推送（推荐方式）

**最简单的方法**:

```bash
cd /home/admin/.openclaw/workspace/ai-coach

# 配置 Git 保存凭据（只需一次）
git config --global credential.helper store

# 推送（会提示输入 GitHub 用户名和 Token）
git push -u origin master

# 输入:
# Username: weizhe1st
# Password: ghp_xxxxxxxxxxxx (你的 Token)

# 以后推送只需:
git push
```

---

## ❓ 常见问题

### Q: 推送失败 "Permission denied"

**A**: 检查 Token 是否有 repo 权限，或者 SSH Key 是否正确配置。

### Q: 如何查看已提交的代码？

```bash
git log --oneline -10
git show 79f254e
```

### Q: 如何回退修改？

```bash
# 撤销工作区修改
git checkout -- filename

# 撤销暂存区修改
git reset HEAD filename

# 撤销上一次提交
git reset --soft HEAD~1
```

---

## 📊 当前仓库状态

- ✅ 本地仓库已初始化
- ✅ 代码已提交（commit: 79f254e）
- ⏳ 等待推送到 GitHub
- 📁 远程仓库：https://github.com/weizhe1st/ali-ai-new-coach.git

---

**下一步**: 选择一种认证方式，将代码推送到 GitHub！🚀
