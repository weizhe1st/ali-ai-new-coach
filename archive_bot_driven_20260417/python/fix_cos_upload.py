#!/usr/bin/env python3
"""
修复 complete_analysis_service.py 中的 COS 上传逻辑
"""

import os

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'complete_analysis_service.py')

# 读取文件
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 要替换的旧代码
old_code = """        # 根据提供商选择视频传入方式
        if MODEL_PROVIDER == 'qwen':
            # Qwen-VL：直接传 COS URL（视频已在 COS 上）
            # 从 task_id 或 video_path 推断 COS URL
            cos_url = _get_cos_url_for_video(video_path, task_id)
            print(f"\\n[4/8] Qwen-VL 视觉分析（COS URL）...")
            print(f"  视频 URL: {cos_url[:60]}...")
            video_content = {"type": "video_url", "video_url": {"url": cos_url}}
            file_object = None  # Qwen-VL 不需要上传"""

# 新代码（添加 COS 上传步骤）
new_code = """        # 根据提供商选择视频传入方式
        if MODEL_PROVIDER == 'qwen':
            # Qwen-VL：先上传视频到 COS，然后传 COS URL
            print(f"\\n[3/8] 上传视频到 COS...")
            cos_key = None
            cos_url = None
            
            try:
                uploader = COSUploader()
                if uploader.config.enabled:
                    video_name = os.path.basename(video_path)
                    cos_key = uploader.upload_video(video_path, task_id or 'unknown', video_name)
                    if cos_key:
                        cos_url = uploader.get_public_url(cos_key)
                        print(f"  ✓ 上传成功：{cos_key}")
                        print(f"  ✓ COS URL: {cos_url[:60]}...")
                    else:
                        print("  ⚠ 上传失败，使用备用 URL")
                else:
                    print("  ⚠ COS 上传已禁用")
            except Exception as e:
                print(f"  ⚠ 上传异常：{e}")
            
            # 如果上传失败，尝试从数据库获取已有 URL
            if not cos_url:
                cos_url = _get_cos_url_for_video(video_path, task_id)
                print(f"  ⚠ 使用备用 COS URL: {cos_url[:60] if cos_url else 'None'}...")
            
            print(f"\\n[4/8] Qwen-VL 视觉分析...")
            if not cos_url:
                raise Exception("视频上传失败且无备用 URL，无法继续分析")
            print(f"  视频 URL: {cos_url[:60]}...")
            video_content = {"type": "video_url", "video_url": {"url": cos_url}}
            file_object = None"""

# 替换
if old_code in content:
    content = content.replace(old_code, new_code)
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 修复成功！已添加 COS 上传步骤")
else:
    print("❌ 未找到要替换的代码")
    print("可能文件已被修改或格式不匹配")
