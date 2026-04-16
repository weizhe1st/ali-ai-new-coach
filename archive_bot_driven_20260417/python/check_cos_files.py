#!/usr/bin/env python3
from cos_uploader import COSUploader
import requests
import os
from dotenv import load_dotenv

load_dotenv('.env')
uploader = COSUploader()

# 检查几个视频文件是否在 COS 中
test_files = [
    'video-1776248347160.mp4',
    'video-1776247171222.mp4',
    'video-1776235656208.mp4',
]

print("检查 COS 中的视频文件：")
for filename in test_files:
    # 尝试构造可能的 COS key
    possible_keys = [
        f'analyzed/2026/04{filename}',
        f'raw/2026/04{filename}',
        f'analyzed/serve/2026-04-15/{filename}',
    ]
    
    for key in possible_keys:
        try:
            url = uploader.get_public_url(key)
            resp = requests.head(url, timeout=5)
            if resp.status_code == 200:
                print(f"✅ {filename}")
                print(f"   COS Key: {key}")
                print(f"   URL: {url[:80]}...")
                break
        except:
            pass
    else:
        print(f"❌ {filename} - 未在 COS 中找到")
