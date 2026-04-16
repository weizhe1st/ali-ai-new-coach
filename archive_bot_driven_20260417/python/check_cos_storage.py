#!/usr/bin/env python3
"""
检查 COS 中已上传的视频文件
"""
from cos_uploader import COSUploader
from dotenv import load_dotenv
import requests
import sqlite3

load_dotenv('.env')
uploader = COSUploader()

db_path = 'data/auto_analyze.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# 获取所有失败任务的视频文件
rows = conn.execute('''
    SELECT t.task_id, v.file_name
    FROM analysis_tasks t
    JOIN video_files v ON t.video_file_id = v.id
    WHERE t.status = 'failed'
    ORDER BY t.created_at DESC
''').fetchall()

print(f"共有 {len(rows)} 个失败任务，检查 COS 中的存储情况...")
print("="*80)

found_count = 0
not_found_count = 0

# 可能的路径规则
def generate_possible_keys(task_id, filename):
    """生成所有可能的 COS Key"""
    return [
        # 规则 1: sample_archive_service.py (按动作 + 日期)
        f"analyzed/serve/2026-04-15/{task_id}_{filename}",
        f"analyzed/other/2026-04-15/{task_id}_{filename}",
        
        # 规则 2: cos_uploader.py (按年月 + task_id)
        f"analyzed/2026/04{task_id}/{filename}",
        
        # 规则 3: 简单路径
        f"analyzed/{filename}",
        f"raw/{filename}",
        
        # 规则 4: 黄金样本
        f"candidate_golden/serve/2026-04-15/{task_id}_{filename}",
        f"golden/serve/2026-04-15/{task_id}_{filename}",
    ]

# 检查前 10 个文件
for i, row in enumerate(rows[:10]):
    task_id = row['task_id']
    filename = row['file_name']
    
    possible_keys = generate_possible_keys(task_id, filename)
    
    found = False
    for key in possible_keys:
        try:
            url = uploader.get_public_url(key)
            resp = requests.head(url, timeout=3)
            if resp.status_code == 200:
                print(f"✅ {filename}")
                print(f"   Task ID: {task_id}")
                print(f"   COS Key: {key}")
                print(f"   URL: {url[:80]}...")
                print()
                found = True
                found_count += 1
                break
        except:
            pass
    
    if not found:
        print(f"❌ {filename}")
        print(f"   Task ID: {task_id}")
        print(f"   未在 COS 中找到")
        print()
        not_found_count += 1

print("="*80)
print(f"检查结果：{found_count} 个已上传，{not_found_count} 个未找到")
print(f"（仅检查前 10 个文件）")

conn.close()
