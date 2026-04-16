#!/usr/bin/env python3
"""
批量上传视频到 COS
用于将本地/media/inbound/目录的视频上传到 COS
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# 配置
MEDIA_DIR = '/home/admin/.openclaw/workspace/media/inbound'
SAMPLE_REGISTRY_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/sample_registry.json'

# COS 配置
cos_secret_id = os.environ.get('COS_SECRET_ID')
cos_secret_key = os.environ.get('COS_SECRET_KEY')
cos_bucket = os.environ.get('COS_BUCKET', 'tennis-ai-1411340868')
cos_region = os.environ.get('COS_REGION', 'ap-shanghai')

# 如果没有环境变量，从.env 读取
if not cos_secret_id or not cos_secret_key:
    env_path = os.path.join(PROJECT_ROOT, '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('COS_SECRET_ID='):
                    cos_secret_id = line.split('=')[1].strip()
                elif line.startswith('COS_SECRET_KEY='):
                    cos_secret_key = line.split('=')[1].strip()

def upload_to_cos(local_path: str, cos_key: str) -> bool:
    """上传文件到 COS"""
    try:
        from qcloud_cos import CosConfig, CosS3Client
        
        config = CosConfig(
            Region=cos_region,
            SecretId=cos_secret_id,
            SecretKey=cos_secret_key
        )
        client = CosS3Client(config)
        
        with open(local_path, 'rb') as f:
            client.put_object(
                Bucket=cos_bucket,
                Body=f,
                Key=cos_key
            )
        
        cos_url = f"https://{cos_bucket}.cos.{cos_region}.myqcloud.com/{cos_key}"
        return True, cos_url
        
    except Exception as e:
        return False, str(e)

def main():
    print("="*60)
    print("📤 批量上传视频到 COS")
    print("="*60)
    print()
    
    # 1. 加载样本登记表
    print("📋 加载样本登记表...")
    if os.path.exists(SAMPLE_REGISTRY_PATH):
        with open(SAMPLE_REGISTRY_PATH, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        print(f"   样本数：{len(registry)}")
    else:
        registry = []
        print(f"   ⚠️  样本登记表不存在")
    print()
    
    # 2. 查找本地视频文件
    print("🔍 查找本地视频文件...")
    if not os.path.exists(MEDIA_DIR):
        print(f"   ❌ 媒体目录不存在：{MEDIA_DIR}")
        return
    
    video_files = [f for f in os.listdir(MEDIA_DIR) if f.endswith('.mp4')]
    print(f"   找到 {len(video_files)} 个视频文件")
    print()
    
    # 3. 匹配样本和视频
    print("📊 匹配样本和视频...")
    
    # 构建 sample_id 到 sample 的映射
    sample_map = {s.get('sample_id'): s for s in registry}
    
    # 构建文件名到 sample 的映射
    filename_to_sample = {}
    for sample in registry:
        filename = sample.get('source_file_name')
        if filename:
            filename_to_sample[filename] = sample
    
    # 统计需要上传的视频
    need_upload = []
    already_uploaded = []
    no_sample = []
    
    for filename in video_files:
        if filename in filename_to_sample:
            sample = filename_to_sample[filename]
            if sample.get('cos_url'):
                already_uploaded.append(filename)
            else:
                need_upload.append((filename, sample))
        else:
            no_sample.append(filename)
    
    print(f"   已上传：{len(already_uploaded)} 个")
    print(f"   需上传：{len(need_upload)} 个")
    print(f"   无样本：{len(no_sample)} 个")
    print()
    
    # 4. 批量上传
    if not need_upload:
        print("✅ 所有视频已上传到 COS！")
        return
    
    print("="*60)
    print("📤 开始批量上传...")
    print("="*60)
    print()
    
    uploaded_count = 0
    failed_count = 0
    
    for i, (filename, sample) in enumerate(need_upload[:20], 1):  # 限制前 20 个
        local_path = os.path.join(MEDIA_DIR, filename)
        sample_id = sample.get('sample_id', 'unknown')
        
        # 生成 COS Key
        ntrp = sample.get('ntrp_level', 'unknown')
        category = sample.get('sample_category', 'unknown')
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 根据分类确定目录
        if category == 'excellent_demo':
            cos_prefix = 'golden'
        elif category == 'typical_issue':
            cos_prefix = 'typical_issues'
        else:
            cos_prefix = 'analyzed'
        
        cos_key = f"{cos_prefix}/serve/{date_str}/{sample_id}_{filename}"
        
        # 上传
        print(f"[{i}/{len(need_upload)}] {filename}")
        print(f"   样本 ID: {sample_id}")
        print(f"   NTRP: {ntrp}")
        print(f"   分类：{category}")
        print(f"   COS Key: {cos_key}")
        
        success, result = upload_to_cos(local_path, cos_key)
        
        if success:
            cos_url = result
            uploaded_count += 1
            
            # 更新样本登记表
            sample['cos_key'] = cos_key
            sample['cos_url'] = cos_url
            
            print(f"   ✅ 上传成功")
            print(f"   URL: {cos_url[:80]}...")
        else:
            failed_count += 1
            print(f"   ❌ 上传失败：{result}")
        
        print()
    
    # 5. 保存更新后的样本登记表
    print("="*60)
    print("💾 保存样本登记表...")
    print("="*60)
    
    with open(SAMPLE_REGISTRY_PATH, 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ 已保存")
    print()
    
    # 6. 统计结果
    print("="*60)
    print("📊 上传结果统计")
    print("="*60)
    print()
    print(f"   成功：{uploaded_count} 个")
    print(f"   失败：{failed_count} 个")
    print(f"   总计：{uploaded_count + failed_count} 个")
    print()
    
    if uploaded_count > 0:
        print("✅ 批量上传完成！")
        print()
        print("下一步:")
        print("   1. 检查上传结果")
        print("   2. 修复自动上传流程")
        print("   3. 继续人工评估")
        print()
    else:
        print("⚠️  上传失败，请检查 COS 配置")

if __name__ == '__main__':
    main()
