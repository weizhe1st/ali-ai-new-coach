#!/usr/bin/env python3
"""
会话连续性管理
- 在对话开始时自动加载上次会话状态
- 在对话结束时自动保存当前状态
- 提供会话历史查询
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

SESSION_STATE_FILE = Path(__file__).parent / '.session_state.json'
MEMORY_DIR = Path(__file__).parent.parent / 'memory'


def load_session_state():
    """加载会话状态"""
    if SESSION_STATE_FILE.exists():
        with open(SESSION_STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_session_state(message: str, files_changed: list = None):
    """保存会话状态"""
    state = {
        'timestamp': datetime.now().isoformat(),
        'message': message,
        'files_changed': files_changed or [],
        'git_commit': get_latest_commit()
    }
    
    with open(SESSION_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 会话状态已保存")
    return state


def get_latest_commit():
    """获取最新 Git 提交"""
    import subprocess
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%H %s'],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return None


def check_session_continuity():
    """检查会话连续性"""
    state = load_session_state()
    
    if not state:
        return {
            'status': 'new',
            'message': '首次会话，没有历史记录'
        }
    
    last_time = datetime.fromisoformat(state['timestamp'])
    now = datetime.now()
    time_diff = now - last_time
    
    # 判断是否长时间未对话
    if time_diff > timedelta(hours=24):
        return {
            'status': 'long_break',
            'message': f'距离上次对话已 {time_diff.days} 天',
            'last_commit': state.get('git_commit', '未知'),
            'last_message': state.get('message', '未知'),
            'files_changed': state.get('files_changed', []),
            'suggestion': '建议先查看 Git 提交历史和会话状态'
        }
    elif time_diff > timedelta(hours=1):
        return {
            'status': 'short_break',
            'message': f'距离上次对话已 {int(time_diff.total_seconds() / 60)} 分钟',
            'last_commit': state.get('git_commit', '未知'),
            'last_message': state.get('message', '未知'),
            'suggestion': '可以继续上次的工作'
        }
    else:
        return {
            'status': 'continuous',
            'message': '连续对话中',
            'last_commit': state.get('git_commit', '未知'),
            'last_message': state.get('message', '未知')
        }


def get_session_summary():
    """获取会话摘要"""
    state = load_session_state()
    
    if not state:
        return "没有会话历史记录"
    
    last_time = datetime.fromisoformat(state['timestamp'])
    time_ago = datetime.now() - last_time
    
    summary = []
    summary.append(f"📅 上次保存时间：{last_time.strftime('%Y-%m-%d %H:%M:%S')}")
    summary.append(f"⏰ 距今：{int(time_ago.total_seconds() / 60)} 分钟")
    summary.append(f"📝 提交信息：{state.get('message', '未知')}")
    
    if state.get('git_commit'):
        summary.append(f"💾 Git 提交：{state['git_commit'][:50]}...")
    
    if state.get('files_changed'):
        summary.append(f"📁 变更文件：{len(state['files_changed'])} 个")
        for file in state['files_changed'][:5]:
            summary.append(f"   - {file}")
        if len(state['files_changed']) > 5:
            summary.append(f"   ... 还有 {len(state['files_changed']) - 5} 个文件")
    
    return '\n'.join(summary)


def main():
    """主函数"""
    print("="*70)
    print("📊 会话连续性检查")
    print("="*70)
    print()
    
    result = check_session_continuity()
    
    print(f"状态：{result['status']}")
    print(f"消息：{result['message']}")
    print()
    
    if result['status'] == 'long_break':
        print("💡 建议:")
        print(f"   {result.get('suggestion', '')}")
        print()
        print("📋 上次会话详情:")
        print(get_session_summary())
    elif result['status'] == 'short_break':
        print("💡 建议:")
        print(f"   {result.get('suggestion', '')}")
    else:
        print("📋 当前会话:")
        print(get_session_summary())
    
    print()
    print("="*70)


if __name__ == '__main__':
    main()
