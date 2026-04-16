#!/usr/bin/env python3
"""
QwenClient 完整测试脚本
测试项目：
1. 环境变量加载
2. COS 上传（公开读权限）
3. Qwen-VL 视频分析
4. 响应解析
"""

import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# 加载 .env
from dotenv import load_dotenv
env_path = os.path.join(PROJECT_ROOT, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"✅ 已加载环境变量：{env_path}")
else:
    print(f"⚠️  .env 文件不存在：{env_path}")

print("="*70)
print("🧪 QwenClient 完整测试")
print("="*70)
print()

# ==================== 1. 环境变量检查 ====================
print("1️⃣  环境变量检查")
print("-" * 70)
env_vars = {
    'DASHSCOPE_API_KEY': os.environ.get('DASHSCOPE_API_KEY', '')[:20] + '...',
    'COS_ENABLED': os.environ.get('COS_ENABLED'),
    'COS_BUCKET': os.environ.get('COS_BUCKET'),
    'COS_REGION': os.environ.get('COS_REGION'),
}

for key, value in env_vars.items():
    status = "✅" if value else "❌"
    print(f"   {status} {key}: {value}")
print()

# ==================== 2. COS 上传器测试 ====================
print("2️⃣  COS 上传器测试")
print("-" * 70)

from cos_uploader import COSUploader

uploader = COSUploader()
print(f"   COS Enabled: {uploader.config.enabled}")
print(f"   Bucket: {uploader.config.bucket}")
print(f"   Region: {uploader.config.region}")
print(f"   Client: {'✅ 已初始化' if uploader.client else '❌ 未初始化'}")
print()

# ==================== 3. QwenClient 初始化 ====================
print("3️⃣  QwenClient 初始化")
print("-" * 70)

from qwen_client import get_qwen_client, DASHSCOPE_AVAILABLE

print(f"   DashScope SDK: {'✅ 已安装' if DASHSCOPE_AVAILABLE else '⚠️  未安装（使用兼容模式）'}")

try:
    client = get_qwen_client()
    print(f"   ✅ QwenClient 初始化成功")
    print(f"   API Key: {client.api_key[:20]}...")
except Exception as e:
    print(f"   ❌ 初始化失败：{e}")
    sys.exit(1)
print()

# ==================== 4. 文本对话测试 ====================
print("4️⃣  文本对话测试（快速验证 API 连通性）")
print("-" * 70)

start = time.time()
response = client.chat_with_video(
    video_url='https://www.w3schools.com/html/mov_bbb.mp4',  # 公开测试视频
    prompt='Say hello in Chinese',
    model='qwen-vl-max',
    max_tokens=100,
    retry_count=1
)
elapsed = time.time() - start

if response.get('success'):
    print(f"   ✅ 调用成功（耗时：{elapsed:.1f}秒）")
    print(f"   回复：{response.get('content', '')[:100]}")
else:
    print(f"   ❌ 调用失败：{response.get('error')}")
print()

# ==================== 5. 真实视频上传 + 分析测试 ====================
print("5️⃣  真实视频上传 + 分析测试")
print("-" * 70)

# 找一个本地测试视频
test_videos = [
    '/home/admin/.openclaw/workspace/media/inbound/video-1776247171222.mp4',
    '/home/admin/.openclaw/workspace/media/inbound/video-1776247157028.mp4',
]

test_video = None
for v in test_videos:
    if os.path.exists(v):
        test_video = v
        break

if not test_video:
    print("   ⚠️  未找到测试视频，跳过此测试")
else:
    print(f"   测试视频：{os.path.basename(test_video)}")
    print(f"   文件大小：{os.path.getsize(test_video) / 1024 / 1024:.2f} MB")
    
    # 上传到 COS
    print("\n   📤 上传到 COS...")
    video_name = os.path.basename(test_video)
    cos_key = uploader.upload_video(test_video, 'test_qwen_client', video_name)
    
    if not cos_key:
        print("   ❌ 上传失败")
    else:
        print(f"   ✅ 上传成功：{cos_key}")
        
        # 获取公开 URL
        cos_url = uploader.get_public_url(cos_key)
        print(f"   📍 COS URL: {cos_url[:60]}...")
        
        # 测试 URL 可访问性
        print("\n   🔍 测试 URL 可访问性...")
        import requests
        try:
            resp = requests.head(cos_url, timeout=10)
            if resp.status_code == 200:
                print(f"   ✅ URL 可公开访问（HTTP {resp.status_code}）")
            else:
                print(f"   ⚠️  URL 访问受限（HTTP {resp.status_code}）")
        except Exception as e:
            print(f"   ⚠️  URL 测试失败：{e}")
        
        # Qwen-VL 分析
        print("\n   🤖 Qwen-VL 视频分析...")
        start = time.time()
        response = client.chat_with_video(
            video_url=cos_url,
            prompt='请用中文简要描述这个网球发球视频中的动作',
            model='qwen-vl-max',
            max_tokens=1000,
            retry_count=2,
            base_delay=5.0
        )
        elapsed = time.time() - start
        
        if response.get('success'):
            print(f"   ✅ 分析成功（耗时：{elapsed:.1f}秒）")
            content = response.get('content', '')
            print(f"\n   📝 AI 回复:\n   {'-'*60}")
            # 格式化输出
            for line in content.split('\n')[:10]:  # 最多显示 10 行
                print(f"   {line}")
            if len(content.split('\n')) > 10:
                print(f"   ...（还有更多内容）")
            print(f"   {'-'*60}")
        else:
            print(f"   ❌ 分析失败：{response.get('error')}")

print()
print("="*70)
print("✅ 测试完成！")
print("="*70)
