#!/usr/bin/env python3
"""
自动分析服务测试脚本
用于验证服务是否正常工作
"""

import os
import sys
import time

# 添加项目路径
sys.path.insert(0, '/home/admin/.openclaw/workspace/ai-coach')

from auto_analyze_db import (
    init_db,
    get_or_create_video_file,
    create_analysis_task,
    update_task_status,
    get_pending_tasks,
    get_task_statistics
)

def test_database():
    """测试数据库功能"""
    print("="*60)
    print("🧪 测试数据库功能")
    print("="*60)
    print()
    
    # 初始化数据库
    init_db()
    print("✅ 数据库初始化成功")
    
    # 测试统计
    stats = get_task_statistics()
    print(f"📊 当前统计：{stats}")
    print()

def test_scan():
    """测试扫描功能"""
    print("="*60)
    print("🧪 测试扫描功能")
    print("="*60)
    print()
    
    media_dir = '/home/admin/.openclaw/workspace/media/inbound'
    
    # 查找最近 5 分钟内的视频
    import time
    from pathlib import Path
    
    current_time = time.time()
    time_threshold = current_time - 300  # 5 分钟
    
    recent_videos = []
    for file_path in Path(media_dir).glob('*.mp4'):
        if file_path.stat().st_mtime > time_threshold:
            recent_videos.append({
                'file_path': str(file_path),
                'file_name': file_path.name,
                'mtime': file_path.stat().st_mtime
            })
    
    print(f"📹 找到 {len(recent_videos)} 个最近视频:")
    for video in recent_videos[:10]:
        print(f"   - {video['file_name']}")
    
    if len(recent_videos) > 10:
        print(f"   ... 还有 {len(recent_videos) - 10} 个")
    print()

def test_task_lifecycle():
    """测试任务生命周期"""
    print("="*60)
    print("🧪 测试任务生命周期")
    print("="*60)
    print()
    
    # 使用一个测试视频
    test_video = '/home/admin/.openclaw/workspace/media/inbound/video-1776269075682.mp4'
    
    if not os.path.exists(test_video):
        print(f"⚠️  测试视频不存在：{test_video}")
        print("   请使用实际存在的视频文件")
        return
    
    # 1. 创建视频文件记录
    video_file_id = get_or_create_video_file(test_video)
    if video_file_id:
        print(f"✅ 创建视频文件记录：ID={video_file_id}")
    else:
        print(f"⚠️  视频文件已存在或创建失败")
        return
    
    # 2. 创建分析任务
    task_id = create_analysis_task(video_file_id)
    if task_id:
        print(f"✅ 创建分析任务：Task ID={task_id}")
    else:
        print(f"⚠️  任务已存在或创建失败")
        return
    
    # 3. 更新状态：pending -> analyzing
    update_task_status(task_id, 'analyzing')
    print(f"✅ 更新状态：analyzing")
    
    # 4. 更新状态：analyzing -> uploaded_cos
    update_task_status(
        task_id, 
        'uploaded_cos',
        cos_key='test/serve/2026-04-16/test.mp4',
        cos_url='https://test.cos.com/test.mp4',
        ntrp_level='3.0',
        sample_category='typical_issue'
    )
    print(f"✅ 更新状态：uploaded_cos")
    
    # 5. 更新状态：uploaded_cos -> completed
    update_task_status(task_id, 'completed', report_sent=True)
    print(f"✅ 更新状态：completed")
    
    # 6. 查看统计
    stats = get_task_statistics()
    print(f"📊 当前统计：{stats}")
    print()

def main():
    """主测试函数"""
    print("\n")
    print("="*60)
    print("🧪 自动分析服务测试")
    print("="*60)
    print()
    
    # 测试 1: 数据库功能
    test_database()
    
    # 测试 2: 扫描功能
    test_scan()
    
    # 测试 3: 任务生命周期
    test_task_lifecycle()
    
    print("="*60)
    print("✅ 测试完成！")
    print("="*60)
    print()
    print("下一步:")
    print("   1. 启动服务：systemctl --user start auto-analyze")
    print("   2. 查看日志：journalctl --user -u auto-analyze -f")
    print("   3. 查看状态：systemctl --user status auto-analyze")
    print()

if __name__ == '__main__':
    main()
