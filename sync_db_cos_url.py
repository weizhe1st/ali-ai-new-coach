#!/usr/bin/env python3
"""
同步数据库 COS URL
将 sample_registry.json 中的 cos_key/cos_url 同步到 analysis_tasks 表
"""

import json
import sqlite3
from datetime import datetime

DB_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/auto_analyze.db'
SAMPLE_REGISTRY_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/sample_registry.json'

print("="*70)
print("🔄 同步数据库 COS URL")
print("="*70)
print()

# 1. 加载样本登记表
print("📋 加载样本登记表...")
with open(SAMPLE_REGISTRY_PATH, 'r', encoding='utf-8') as f:
    registry = json.load(f)

# 构建文件名到 sample 的映射
filename_to_sample = {}
for sample in registry:
    filename = sample.get('source_file_name')
    if filename and sample.get('cos_key'):
        filename_to_sample[filename] = sample

print(f"   总样本数：{len(registry)}")
print(f"   有 COS Key 的样本：{len(filename_to_sample)}")
print()

# 2. 连接数据库
print("📊 连接数据库...")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# 查询所有失败任务
rows = conn.execute('''
    SELECT t.id, t.task_id, t.video_file_id, t.status, t.cos_url,
           v.file_name
    FROM analysis_tasks t
    JOIN video_files v ON t.video_file_id = v.id
    WHERE t.status = 'failed'
''').fetchall()

print(f"   失败任务数：{len(rows)}")
print()

# 3. 同步 COS URL
print("🔄 开始同步...")
print()

updated_count = 0
not_found_count = 0
already_synced_count = 0

for row in rows:
    task_id = row['task_id']
    filename = row['file_name']
    db_cos_url = row['cos_url']
    
    if filename in filename_to_sample:
        sample = filename_to_sample[filename]
        cos_key = sample.get('cos_key')
        cos_url = sample.get('cos_url')
        
        # 检查是否已同步
        if db_cos_url and cos_url in db_cos_url:
            already_synced_count += 1
            continue
        
        # 更新数据库
        conn.execute('''
            UPDATE analysis_tasks
            SET cos_url = ?,
                status = 'completed',
                completed_at = datetime('now'),
                updated_at = datetime('now')
            WHERE task_id = ?
        ''', (cos_url, task_id))
        
        updated_count += 1
        
        # 获取样本信息
        ntrp = sample.get('ntrp_level', 'unknown')
        category = sample.get('sample_category', 'unknown')
        review_status = sample.get('golden_review_status', 'unknown')
        
        print(f"   ✅ {filename}")
        print(f"      Task ID: {task_id}")
        print(f"      NTRP: {ntrp}")
        print(f"      分类：{category}")
        print(f"      审核状态：{review_status}")
        print(f"      COS URL: {cos_url[:80]}...")
        print()
    else:
        not_found_count += 1
        print(f"   ⚠️  {filename}")
        print(f"      Task ID: {task_id}")
        print(f"      未在 sample_registry.json 中找到 COS Key")
        print()

# 提交事务
conn.commit()
conn.close()

# 4. 统计结果
print("="*70)
print("📊 同步结果统计")
print("="*70)
print()
print(f"   ✅ 已同步：{updated_count} 个")
print(f"   ⏭️  已同步过：{already_synced_count} 个")
print(f"   ⚠️  未找到 COS Key: {not_found_count} 个")
print(f"   总计处理：{updated_count + already_synced_count + not_found_count} 个")
print()

if not_found_count > 0:
    print("⚠️  以下任务未找到 COS Key，需要手动处理：")
    print()

print("="*70)
print("✅ 数据库同步完成！")
print("="*70)
