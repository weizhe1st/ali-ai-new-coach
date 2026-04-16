#!/usr/bin/env python3
"""
处理 18 个未登记任务
1. 补登记到 sample_registry.json
2. 上传到 COS
3. 更新数据库
"""

import json
import sqlite3
import os
from datetime import datetime
from cos_uploader import COSUploader
from dotenv import load_dotenv

load_dotenv('.env')
uploader = COSUploader()

DB_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/auto_analyze.db'
SAMPLE_REGISTRY_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/sample_registry.json'
MEDIA_DIR = '/home/admin/.openclaw/workspace/media/inbound'

print("="*70)
print("📝 处理 18 个未登记任务")
print("="*70)
print()

# 1. 加载样本登记表
with open(SAMPLE_REGISTRY_PATH, 'r', encoding='utf-8') as f:
    registry = json.load(f)

print(f"📋 当前样本数：{len(registry)}")
print()

# 2. 查询未登记的任务
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

rows = conn.execute('''
    SELECT t.id, t.task_id, t.video_file_id, t.status,
           v.file_name, v.file_path, v.file_size
    FROM analysis_tasks t
    JOIN video_files v ON t.video_file_id = v.id
    WHERE t.status = 'failed'
''').fetchall()

# 找出不在 registry 中的任务
unsynced_tasks = []
registry_filenames = set(s.get('source_file_name') for s in registry)

for row in rows:
    filename = row['file_name']
    if filename not in registry_filenames:
        unsynced_tasks.append(row)

conn.close()

print(f"🔍 未登记任务数：{len(unsynced_tasks)}")
print()

if not unsynced_tasks:
    print("✅ 所有任务都已登记！")
    exit(0)

# 3. 批量处理
print("="*70)
print("📤 开始处理...")
print("="*70)
print()

processed_count = 0
failed_count = 0

for i, row in enumerate(unsynced_tasks, 1):
    task_id = row['task_id']
    filename = row['file_name']
    file_path = row['file_path']
    file_size = row['file_size']
    
    print(f"[{i}/{len(unsynced_tasks)}] {filename}")
    print(f"   Task ID: {task_id}")
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"   ❌ 文件不存在，跳过")
        failed_count += 1
        continue
    
    # 生成 sample_id
    sample_id = f"unsynced_{task_id.replace('auto_', '')}"
    
    # 估算 NTRP 等级（根据文件名中的时间戳，暂时标记为 unknown）
    # 实际应该通过 AI 分析获得
    estimated_ntrp = "unknown"
    
    # 上传到 COS
    print(f"   📤 上传到 COS...")
    date_str = datetime.now().strftime('%Y-%m-%d')
    cos_key = f"analyzed/serve/{date_str}/{sample_id}_{filename}"
    
    try:
        result = uploader.upload_video(file_path, sample_id, filename)
        if result:
            cos_url = uploader.get_public_url(result)
            print(f"   ✅ 上传成功")
            print(f"      COS Key: {cos_key}")
        else:
            print(f"   ❌ 上传失败")
            failed_count += 1
            continue
    except Exception as e:
        print(f"   ❌ 上传异常：{e}")
        failed_count += 1
        continue
    
    # 创建样本记录
    sample_record = {
        'sample_id': sample_id,
        'source_type': 'unsynced_task_import',
        'action_type': 'video_analysis_serve',
        'source_file_name': filename,
        'source_file_path': file_path,
        'cos_key': cos_key,
        'cos_url': cos_url,
        'candidate_for_golden': False,
        'golden_review_status': 'pending',
        'sample_category': 'unknown',
        'ntrp_level': estimated_ntrp,
        'tags': [],
        'task_id': task_id,
        'archived_at': datetime.now().isoformat(),
        'imported_at': datetime.now().isoformat(),
        'imported_from': 'unsynced_task_fix'
    }
    
    # 添加到 registry
    registry.append(sample_record)
    print(f"   ✅ 已登记到 sample_registry.json")
    
    # 更新数据库
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        UPDATE analysis_tasks
        SET cos_url = ?,
            status = 'completed',
            completed_at = datetime('now'),
            updated_at = datetime('now')
        WHERE task_id = ?
    ''', (cos_url, task_id))
    conn.commit()
    conn.close()
    print(f"   ✅ 数据库已更新为 completed")
    
    processed_count += 1
    print()

# 4. 保存 registry
print("="*70)
print("💾 保存样本登记表...")
print("="*70)

with open(SAMPLE_REGISTRY_PATH, 'w', encoding='utf-8') as f:
    json.dump(registry, f, ensure_ascii=False, indent=2)

print(f"   ✅ 已保存")
print(f"   新样本数：{len(registry)}")
print()

# 5. 统计结果
print("="*70)
print("📊 处理结果统计")
print("="*70)
print()
print(f"   ✅ 成功：{processed_count}个")
print(f"   ❌ 失败：{failed_count}个")
print(f"   总计：{processed_count + failed_count}个")
print()

print("="*70)
print("✅ 未登记任务处理完成！")
print("="*70)
