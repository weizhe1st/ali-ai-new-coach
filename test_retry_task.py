#!/usr/bin/env python3
"""
手动重试一个失败任务，验证 COS 上传和 Qwen API
"""

import os
import sys
import sqlite3

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# 加载 .env
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

print("="*60)
print("🔍 测试 COS 上传和 Qwen API")
print("="*60)
print()

# 检查环境变量
print("环境变量检查:")
print(f"  COS_ENABLED: {os.environ.get('COS_ENABLED')}")
print(f"  COS_BUCKET: {os.environ.get('COS_BUCKET')}")
print(f"  COS_REGION: {os.environ.get('COS_REGION')}")
print(f"  DASHSCOPE_API_KEY: {os.environ.get('DASHSCOPE_API_KEY', '')[:20]}...")
print()

# 测试 COS 上传器
print("测试 COS 上传器:")
from cos_uploader import COSUploader
uploader = COSUploader()
print(f"  COS Enabled: {uploader.config.enabled}")
print(f"  Bucket: {uploader.config.bucket}")
print(f"  Region: {uploader.config.region}")
print(f"  Client: {'✅ Initialized' if uploader.client else '❌ Not initialized'}")
print()

# 获取一个失败任务
db_path = os.path.join(PROJECT_ROOT, 'data', 'auto_analyze.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# 查询一个失败任务
row = conn.execute('''
    SELECT t.id, t.task_id, t.video_file_id, t.last_error, v.file_path, v.file_name
    FROM analysis_tasks t
    JOIN video_files v ON t.video_file_id = v.id
    WHERE t.status = 'failed'
    ORDER BY t.updated_at DESC
    LIMIT 1
''').fetchone()

if row:
    print(f"找到失败任务:")
    print(f"  Task ID: {row['task_id']}")
    print(f"  File: {row['file_name']}")
    print(f"  Path: {row['file_path']}")
    print(f"  Error: {row['last_error'][:100] if row['last_error'] else 'None'}")
    print()
    
    # 检查文件是否存在
    if os.path.exists(row['file_path']):
        print(f"✅ 视频文件存在: {os.path.getsize(row['file_path'])} bytes")
        
        # 测试上传
        print("\n测试上传到 COS:")
        video_name = row['file_name']
        task_id = row['task_id'] or 'test'
        
        cos_key = uploader.upload_video(row['file_path'], task_id, video_name)
        if cos_key:
            cos_url = uploader.get_public_url(cos_key)
            print(f"  ✅ 上传成功!")
            print(f"  COS Key: {cos_key}")
            print(f"  COS URL: {cos_url}")
            
            # 测试 Qwen API
            print("\n测试 Qwen-VL API:")
            from qwen_client import get_qwen_client
            
            client = get_qwen_client()
            response = client.chat_with_video(
                video_url=cos_url,
                prompt="Describe this video briefly",
                model='qwen-vl-max',
                max_tokens=500,
                retry_count=1
            )
            
            if response.get('success'):
                print(f"  ✅ Qwen API 调用成功!")
                print(f"  Response: {response.get('content', '')[:200]}...")
            else:
                print(f"  ❌ Qwen API 失败: {response.get('error')}")
        else:
            print(f"  ❌ 上传失败")
    else:
        print(f"❌ 视频文件不存在: {row['file_path']}")
else:
    print("没有找到失败任务")

conn.close()
print("\n" + "="*60)
