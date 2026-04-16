#!/usr/bin/env python3
"""
自动清理失败的视频文件
- 清理失败超过 7 天的任务
- 清理 COS 上对应的文件（可选）
- 清理数据库记录
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'auto_analyze.db')

# 配置
FAILED_TASK_RETENTION_DAYS = 7  # 失败任务保留天数
CLEANUP_COS_FILES = False  # 是否清理 COS 文件（谨慎使用）

def cleanup_failed_tasks():
    """清理失败的任務"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # 计算清理阈值
    cleanup_threshold = datetime.now() - timedelta(days=FAILED_TASK_RETENTION_DAYS)
    
    # 查找需要清理的失败任务
    failed_tasks = conn.execute("""
        SELECT t.task_id, t.status, t.created_at, v.file_name, v.file_path
        FROM analysis_tasks t
        JOIN video_files v ON t.video_file_id = v.id
        WHERE t.status = 'failed'
        AND t.created_at < ?
        ORDER BY t.created_at DESC
    """, (cleanup_threshold.isoformat(),)).fetchall()
    
    if not failed_tasks:
        print(f"✅ 没有需要清理的失败任务（保留最近 {FAILED_TASK_RETENTION_DAYS} 天）")
        conn.close()
        return
    
    print(f"找到 {len(failed_tasks)} 个失败任务（超过 {FAILED_TASK_RETENTION_DAYS} 天）")
    print()
    
    # 删除本地文件
    deleted_files = 0
    for task in failed_tasks:
        if task['file_path'] and os.path.exists(task['file_path']):
            try:
                os.remove(task['file_path'])
                print(f"  🗑️  已删除：{task['file_name']}")
                deleted_files += 1
            except Exception as e:
                print(f"  ❌ 删除失败：{task['file_name']} - {e}")
    
    print()
    print(f"✅ 已删除 {deleted_files} 个本地文件")
    
    # 删除数据库记录
    task_ids = [t['task_id'] for t in failed_tasks]
    conn.execute("DELETE FROM analysis_tasks WHERE task_id IN ({})".format(','.join('?' * len(task_ids))), task_ids)
    conn.execute("DELETE FROM video_files WHERE id NOT IN (SELECT video_file_id FROM analysis_tasks)")
    conn.commit()
    print(f"✅ 已删除 {len(failed_tasks)} 条数据库记录")
    
    conn.close()
    print()
    print("✅ 清理完成！")


if __name__ == '__main__':
    cleanup_failed_tasks()
