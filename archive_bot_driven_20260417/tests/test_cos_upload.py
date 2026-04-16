#!/usr/bin/env python3
"""
COS 上传集成测试

测试分析成功后自动上传 COS 的功能
"""

import os
import sys

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from cos_uploader import COSUploader
from config import get_cos_config

print("="*60)
print("📦 COS 上传集成测试")
print("="*60)
print()

# 加载配置
config = get_cos_config()

print("📋 COS 配置")
print("-"*60)
print(f"启用：{config.enabled}")
print(f"Bucket: {config.bucket}")
print(f"Region: {config.region}")
print(f"SecretId: {config.secret_id[:15]}...")
print(f"当前前缀：{config.current_month_prefix}")
print()

# 测试上传
if config.enabled and config.bucket:
    print("🧪 测试上传...")
    print("-"*60)
    
    # 创建一个测试文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("测试内容")
        test_file = f.name
    
    try:
        uploader = COSUploader()
        
        # 测试上传
        cos_key = uploader.upload_file(test_file, f"test/{os.path.basename(test_file)}")
        
        if cos_key:
            print()
            print("✅ COS 上传测试成功！")
            print(f"   COS Key: {cos_key}")
        else:
            print()
            print("⚠️  COS 上传失败，请检查配置和网络")
    
    finally:
        # 清理测试文件
        os.unlink(test_file)
else:
    print("⚠️  COS 未配置，跳过测试")

print()
print("="*60)
