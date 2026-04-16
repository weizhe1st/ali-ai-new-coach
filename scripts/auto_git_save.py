#!/usr/bin/env python3
"""
Git 自动保存机制
- 监控重要代码文件变化
- 自动提交到本地 Git
- 自动推送到 GitHub
- 记录会话状态
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

# 配置
PROJECT_ROOT = Path(__file__).parent.parent
GIT_REPO = PROJECT_ROOT / 'ai-coach'
IMPORTANT_FILES = [
    '*.py',  # Python 代码
    '*.json',  # 配置文件
    '*.md',  # 文档
]

# 会话状态文件
SESSION_STATE_FILE = PROJECT_ROOT / 'ai-coach' / '.session_state.json'


def run_command(cmd, cwd=None):
    """运行 shell 命令"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd or GIT_REPO,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, '', str(e)


def get_git_status():
    """获取 Git 状态"""
    success, stdout, stderr = run_command('git status --porcelain')
    if success:
        return [line for line in stdout.strip().split('\n') if line]
    return []


def save_session_state(message: str, files_changed: list):
    """保存会话状态"""
    state = {
        'timestamp': datetime.now().isoformat(),
        'message': message,
        'files_changed': files_changed,
        'git_commit': get_latest_commit()
    }
    
    with open(SESSION_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 会话状态已保存：{SESSION_STATE_FILE}")


def load_session_state():
    """加载会话状态"""
    if SESSION_STATE_FILE.exists():
        with open(SESSION_STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def get_latest_commit():
    """获取最新提交"""
    success, stdout, stderr = run_command('git log -1 --format="%H %s"')
    if success:
        return stdout.strip()
    return None


def auto_commit_and_push(message: str = "auto: 自动保存"):
    """自动提交并推送"""
    print(f"🔄 开始自动保存...")
    
    # 1. 检查 Git 状态
    changes = get_git_status()
    if not changes:
        print("✅ 没有需要保存的更改")
        return True
    
    print(f"📝 检测到 {len(changes)} 个文件变更:")
    for change in changes[:10]:
        print(f"   {change}")
    if len(changes) > 10:
        print(f"   ... 还有 {len(changes) - 10} 个文件")
    
    # 2. 添加所有更改
    success, stdout, stderr = run_command('git add -A')
    if not success:
        print(f"❌ Git add 失败：{stderr}")
        return False
    print("✅ 已添加所有文件")
    
    # 3. 提交
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    commit_msg = f"{message}\n\n自动保存时间：{timestamp}"
    success, stdout, stderr = run_command(f'git commit -m "{commit_msg}"')
    if not success:
        print(f"⚠️  Git commit 失败（可能没有新更改）：{stderr}")
    else:
        print("✅ 已提交到本地 Git")
    
    # 4. 推送
    print("🚀 推送到 GitHub...")
    success, stdout, stderr = run_command('git push origin master')
    if not success:
        print(f"⚠️  Git push 失败：{stderr}")
        print("   可以手动执行：cd ai-coach && git push origin master")
    else:
        print("✅ 已推送到 GitHub")
    
    # 5. 保存会话状态
    save_session_state(message, [line.split()[-1] for line in changes])
    
    return True


def main():
    """主函数"""
    if len(sys.argv) > 1:
        message = ' '.join(sys.argv[1:])
    else:
        message = "auto: 自动保存"
    
    auto_commit_and_push(message)


if __name__ == '__main__':
    main()
