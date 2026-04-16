#!/usr/bin/env python3
"""
分析 18 个未同步任务
检查这些任务的视频文件是否存在、是否已上传 COS 等
"""

import json
import sqlite3
import os
from cos_uploader import COSUploader
from dotenv import load_dotenv

load_dotenv('.env')
uploader = COSUploader()

DB_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/auto_analyze.db'
SAMPLE_REGISTRY_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/sample_registry.json'
MEDIA_DIR = '/home/admin/.openclaw/workspace/media/inbound'

print("="*70)
print("🔍 分析 18 个未同步任务")
print("="*70)
print()

# 1. 加载样本登记表
with open(SAMPLE_REGISTRY_PATH, 'r', encoding='utf-8') as f:
    registry = json.load(f)

# 构建文件名到 sample 的映射（包括没有 cos_key 的）
filename_to_sample = {}
for sample in registry:
    filename = sample.get('source_file_name')
    if filename:
        filename_to_sample[filename] = sample

# 2. 查询未同步的任务
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

rows = conn.execute('''
    SELECT t.id, t.task_id, t.video_file_id, t.status, t.cos_url,
           v.file_name, v.file_path
    FROM analysis_tasks t
    JOIN video_files v ON t.video_file_id = v.id
    WHERE t.status = 'failed'
''').fetchall()

# 找出未同步的任务（在 registry 中没有 cos_key）
unsynced_tasks = []
for row in rows:
    filename = row['file_name']
    if filename in filename_to_sample:
        sample = filename_to_sample[filename]
        if not sample.get('cos_key'):
            unsynced_tasks.append((row, sample))
    else:
        # 不在 registry 中
        unsynced_tasks.append((row, None))

conn.close()

print(f"未同步任务数：{len(unsynced_tasks)}")
print()

# 3. 分析每个任务
print("="*70)
print("📋 详细分析")
print("="*70)
print()

has_file = 0
no_file = 0
in_registry = 0
not_in_registry = 0

for row, sample in unsynced_tasks:
    filename = row['file_name']
    task_id = row['task_id']
    file_path = row['file_path']
    
    print(f"📹 {filename}")
    print(f"   Task ID: {task_id}")
    
    # 检查文件是否存在
    if os.path.exists(file_path):
        print(f"   ✅ 本地文件存在：{os.path.getsize(file_path) / 1024 / 1024:.2f}MB")
        has_file += 1
    else:
        print(f"   ❌ 本地文件不存在：{file_path}")
        no_file += 1
    
    # 检查是否在 registry 中
    if sample:
        print(f"   ✅ 在 sample_registry.json 中")
        print(f"      sample_id: {sample.get('sample_id', 'unknown')}")
        print(f"      分类：{sample.get('sample_category', 'unknown')}")
        print(f"      NTRP: {sample.get('ntrp_level', 'unknown')}")
        in_registry += 1
    else:
        print(f"   ❌ 不在 sample_registry.json 中")
        not_in_registry += 1
    
    # 尝试在 COS 中查找
    if os.path.exists(file_path):
        print(f"   🔍 尝试在 COS 中查找...")
        # 尝试几种可能的路径
        possible_keys = [
            f"analyzed/serve/2026-04-15/{task_id}_{filename}",
            f"analyzed/serve/2026-04-16/{task_id}_{filename}",
            f"analyzed/2026/04{task_id}/{filename}",
            f"golden/serve/2026-04-15/{task_id}_{filename}",
            f"typical_issues/serve/2026-04-15/{task_id}_{filename}",
        ]
        
        found_in_cos = False
        for key in possible_keys:
            try:
                url = uploader.get_public_url(key)
                import requests
                resp = requests.head(url, timeout=3)
                if resp.status_code == 200:
                    print(f"   ✅ 在 COS 中找到：{key}")
                    found_in_cos = True
                    break
            except:
                pass
        
        if not found_in_cos:
            print(f"   ❌ 在 COS 中未找到")
    
    print()

print("="*70)
print("📊 统计结果")
print("="*70)
print()
print(f"本地文件存在：{has_file}个")
print(f"本地文件不存在：{no_file}个")
print(f"在 registry 中：{in_registry}个")
print(f"不在 registry 中：{not_in_registry}个")
print()

# 4. 建议处理方案
print("="*70)
print("💡 建议处理方案")
print("="*70)
print()

if has_file > 0:
    print(f"✅ 有文件的 {has_file} 个任务：")
    print(f"   方案：重新上传到 COS，然后更新 registry 和 database")
    print()

if no_file > 0:
    print(f"❌ 无文件的 {no_file} 个任务：")
    print(f"   方案 1：标记为已删除，从失败任务中移除")
    print(f"   方案 2：如果已上传 COS，更新 COS URL 后标记为 completed")
    print()

if not_in_registry > 0:
    print(f"❌ 不在 registry 中的 {not_in_registry} 个任务：")
    print(f"   方案：补登记到 sample_registry.json")
    print()

print("="*70)
