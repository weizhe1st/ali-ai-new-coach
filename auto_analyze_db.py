#!/usr/bin/env python3
"""
视频分析状态管理数据库
用于去重、状态机、失败重试、幂等控制
"""

import os
import sqlite3
import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, Any

DB_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/auto_analyze.db'


def get_db_connection():
    """获取数据库连接"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 视频文件表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS video_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            file_name TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            file_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 分析任务表（状态机）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_file_id INTEGER NOT NULL,
            task_id TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            -- 状态：pending | analyzing | uploaded_cos | reported | completed | failed
            ntrp_level TEXT,
            sample_category TEXT,
            primary_issue TEXT,
            secondary_issue TEXT,
            cos_key TEXT,
            cos_url TEXT,
            sample_id TEXT,
            report_sent BOOLEAN DEFAULT FALSE,
            retry_count INTEGER DEFAULT 0,
            last_error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (video_file_id) REFERENCES video_files(id)
        )
    ''')
    
    # 消息发送记录表（幂等控制）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS message_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            channel TEXT NOT NULL,
            recipient_id TEXT NOT NULL,
            message_type TEXT NOT NULL,
            message_id TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            -- 状态：pending | sent | failed
            error_message TEXT,
            sent_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES analysis_tasks(task_id)
        )
    ''')
    
    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON analysis_tasks(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_video ON analysis_tasks(video_file_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_task ON message_logs(task_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_status ON message_logs(status)')
    
    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")


def compute_file_hash(file_path: str) -> str:
    """计算文件哈希值（用于去重）"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_or_create_video_file(file_path: str) -> Optional[int]:
    """
    获取或创建视频文件记录
    
    Returns:
        video_file_id: 视频文件 ID，如果已存在且已处理完成则返回 None
    """
    if not os.path.exists(file_path):
        return None
    
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    file_hash = compute_file_hash(file_path)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查是否已存在
    cursor.execute('SELECT id FROM video_files WHERE file_hash = ?', (file_hash,))
    row = cursor.fetchone()
    
    if row:
        # 文件已存在，检查是否已有完成的任务
        video_file_id = row['id']
        cursor.execute('''
            SELECT id FROM analysis_tasks 
            WHERE video_file_id = ? AND status = 'completed'
        ''', (video_file_id,))
        if cursor.fetchone():
            # 已有完成的任务，跳过
            conn.close()
            return None
        
        # 更新文件信息（如果路径变化）
        cursor.execute('''
            UPDATE video_files 
            SET file_path = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (file_path, video_file_id))
        conn.commit()
        conn.close()
        return video_file_id
    
    # 创建新记录
    cursor.execute('''
        INSERT INTO video_files (file_path, file_name, file_size, file_hash)
        VALUES (?, ?, ?, ?)
    ''', (file_path, file_name, file_size, file_hash))
    
    video_file_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return video_file_id


def create_analysis_task(video_file_id: int) -> Optional[str]:
    """
    创建分析任务
    
    Returns:
        task_id: 任务 ID，如果创建失败返回 None
    """
    import uuid
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查是否已有进行中的任务
    cursor.execute('''
        SELECT id FROM analysis_tasks 
        WHERE video_file_id = ? AND status IN ('pending', 'analyzing')
    ''', (video_file_id,))
    
    if cursor.fetchone():
        # 已有进行中的任务，不重复创建
        conn.close()
        return None
    
    task_id = f"auto_{uuid.uuid4().hex[:12]}"
    
    cursor.execute('''
        INSERT INTO analysis_tasks (video_file_id, task_id, status)
        VALUES (?, ?, 'pending')
    ''', (video_file_id, task_id))
    
    conn.commit()
    conn.close()
    
    return task_id


def update_task_status(task_id: str, status: str, **kwargs):
    """更新任务状态"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    update_fields = ['status = ?', 'updated_at = CURRENT_TIMESTAMP']
    values = [status]
    
    for key, value in kwargs.items():
        if key in ['ntrp_level', 'sample_category', 'primary_issue', 
                   'secondary_issue', 'cos_key', 'cos_url', 'sample_id', 
                   'last_error', 'report_sent']:
            update_fields.append(f'{key} = ?')
            values.append(value)
    
    if status == 'completed':
        update_fields.append('completed_at = CURRENT_TIMESTAMP')
    elif status == 'failed':
        update_fields.append('retry_count = retry_count + 1')
    
    values.append(task_id)
    
    cursor.execute(f'''
        UPDATE analysis_tasks 
        SET {', '.join(update_fields)}
        WHERE task_id = ?
    ''', values)
    
    conn.commit()
    conn.close()


def get_pending_tasks(limit: int = 10):
    """获取待处理的任务"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t.*, v.file_path, v.file_name
        FROM analysis_tasks t
        JOIN video_files v ON t.video_file_id = v.id
        WHERE t.status = 'pending'
        ORDER BY t.created_at
        LIMIT ?
    ''', (limit,))
    
    tasks = cursor.fetchall()
    conn.close()
    
    return tasks


def get_failed_tasks(max_retries: int = 3):
    """获取失败可重试的任务"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t.*, v.file_path, v.file_name
        FROM analysis_tasks t
        JOIN video_files v ON t.video_file_id = v.id
        WHERE t.status = 'failed' AND t.retry_count < ?
        ORDER BY t.updated_at
        LIMIT 10
    ''', (max_retries,))
    
    tasks = cursor.fetchall()
    conn.close()
    
    return tasks


def log_message_sent(task_id: str, channel: str, recipient_id: str, 
                     message_type: str, message_id: str, status: str = 'sent'):
    """记录消息发送日志（幂等控制）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查是否已发送
    cursor.execute('''
        SELECT id FROM message_logs 
        WHERE task_id = ? AND channel = ? AND recipient_id = ? AND message_type = ?
    ''', (task_id, channel, recipient_id, message_type))
    
    if cursor.fetchone():
        # 已发送，不重复记录
        conn.close()
        return
    
    cursor.execute('''
        INSERT INTO message_logs 
        (task_id, channel, recipient_id, message_type, message_id, status, sent_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (task_id, channel, recipient_id, message_type, message_id, status))
    
    conn.commit()
    conn.close()


def get_task_statistics():
    """获取任务统计"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # 按状态统计
    cursor.execute('''
        SELECT status, COUNT(*) as count 
        FROM analysis_tasks 
        GROUP BY status
    ''')
    stats['by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
    
    # 按 NTRP 等级统计
    cursor.execute('''
        SELECT ntrp_level, COUNT(*) as count 
        FROM analysis_tasks 
        WHERE ntrp_level IS NOT NULL
        GROUP BY ntrp_level
    ''')
    stats['by_ntrp'] = {row['ntrp_level']: row['count'] for row in cursor.fetchall()}
    
    # 按分类统计
    cursor.execute('''
        SELECT sample_category, COUNT(*) as count 
        FROM analysis_tasks 
        WHERE sample_category IS NOT NULL
        GROUP BY sample_category
    ''')
    stats['by_category'] = {row['sample_category']: row['count'] for row in cursor.fetchall()}
    
    conn.close()
    
    return stats


if __name__ == '__main__':
    # 初始化数据库
    init_db()
    print("✅ 数据库初始化完成")
    
    # 显示统计
    stats = get_task_statistics()
    print("\n📊 当前统计:")
    print(f"   按状态：{stats.get('by_status', {})}")
