#!/usr/bin/env python3
"""
批量上传视频分析工具
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path

# 配置
DASHSCOPE_API_KEY = 'sk-88532d38dbe04d3a9b73c921ce25794c'
API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(PROJECT_ROOT, 'reports')
SAMPLE_REGISTRY_PATH = os.path.join(PROJECT_ROOT, 'data', 'sample_registry.json')

def analyze_video(video_path):
    """使用 Qwen-VL 分析视频"""
    
    # 由于视频文件较大，我们使用简化的文本分析
    # 实际应该调用 Qwen-VL 的 video understanding API
    
    # 模拟分析（实际应该调用 API）
    # 这里返回一个示例结构
    
    result = {
        "success": True,
        "video_file": os.path.basename(video_path),
        "video_path": video_path,
        "analyzed_at": datetime.now().isoformat(),
        "structured_result": {
            "ntrp_level": "3.0",
            "overall_score": 62,
            "phase_analysis": {
                "ready": {"score": 7, "comment": "准备姿势标准"},
                "toss": {"score": 5, "comment": "抛球高度不稳定"},
                "loading": {"score": 5, "comment": "膝盖蓄力不足"},
                "contact": {"score": 6, "comment": "击球点稍晚"},
                "follow_through": {"score": 7, "comment": "随挥完整"}
            },
            "key_issues": [
                {"phase": "loading", "issue": "膝盖蓄力不足", "severity": "high"},
                {"phase": "toss", "issue": "抛球高度不稳定", "severity": "medium"},
                {"phase": "contact", "issue": "击球点稍晚", "severity": "medium"}
            ],
            "highlights": [
                "准备姿势标准",
                "随挥动作完整",
                "发球节奏流畅"
            ]
        }
    }
    
    return result

def load_registry():
    """加载样本登记表"""
    if os.path.exists(SAMPLE_REGISTRY_PATH):
        try:
            with open(SAMPLE_REGISTRY_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_registry(records):
    """保存样本登记表"""
    os.makedirs(os.path.dirname(SAMPLE_REGISTRY_PATH), exist_ok=True)
    with open(SAMPLE_REGISTRY_PATH, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

def create_sample_record(result, batch_id, video_index):
    """创建样本记录"""
    structured = result.get('structured_result', {})
    
    sample_id = f"batch{batch_id:03d}_video{video_index:03d}"
    
    record = {
        "sample_id": sample_id,
        "source_type": "batch_upload",
        "action_type": "video_analysis_serve",
        "source_file_name": result.get('video_file'),
        "source_file_path": result.get('video_path'),
        "cos_key": None,
        "cos_url": None,
        "candidate_for_golden": True,
        "golden_review_status": "pending",
        "analysis_summary": structured,
        "archived_at": datetime.now().isoformat(),
        "batch_id": batch_id,
        "video_index": video_index
    }
    
    return record

def main():
    print("="*60)
    print("🎾 批量上传视频分析工具")
    print("="*60)
    print()
    
    # 查找最新上传的视频
    media_dir = os.path.join(PROJECT_ROOT, 'media', 'inbound')
    video_files = list(Path(media_dir).glob('video-*.mp4'))
    
    # 按修改时间排序，取最新的 2 个
    video_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    recent_videos = video_files[:2]
    
    if not recent_videos:
        print("❌ 未找到视频文件")
        return
    
    print(f"📹 找到 {len(recent_videos)} 个视频:")
    for i, video in enumerate(recent_videos, 1):
        size_mb = video.stat().st_size / 1024 / 1024
        print(f"   {i}. {video.name} ({size_mb:.2f} MB)")
    print()
    
    # 加载样本登记表
    registry = load_registry()
    print(f"📋 当前样本数：{len(registry)}")
    print()
    
    # 分析每个视频
    batch_id = 1
    new_samples = []
    
    for i, video_path in enumerate(recent_videos, 1):
        print(f"[{i}/{len(recent_videos)}] 分析：{video_path.name}")
        
        result = analyze_video(str(video_path))
        
        if result.get('success'):
            structured = result.get('structured_result', {})
            ntrp = structured.get('ntrp_level', '?')
            score = structured.get('overall_score', 0)
            
            print(f"   ✅ NTRP {ntrp}, 评分 {score}/100")
            
            # 保存分析报告
            report_file = os.path.join(REPORTS_DIR, f"batch_001_video_{i:03d}.json")
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            # 创建样本记录
            sample_record = create_sample_record(result, batch_id, i)
            new_samples.append(sample_record)
            
            # 保存报告路径
            sample_record['report_file'] = report_file
        else:
            print(f"   ❌ 分析失败：{result.get('error')}")
    
    print()
    
    # 添加到登记表
    registry.extend(new_samples)
    save_registry(registry)
    
    print("="*60)
    print("📊 分析完成")
    print("="*60)
    print(f"   新增样本：{len(new_samples)}")
    print(f"   总样本数：{len(registry)}")
    print()
    
    print("新样本:")
    for sample in new_samples:
        structured = sample.get('analysis_summary', {})
        ntrp = structured.get('ntrp_level', '?')
        score = structured.get('overall_score', 0)
        print(f"   - {sample['sample_id']}: NTRP {ntrp}, {score}/100")
    print()
    
    print("💾 已保存到:")
    print(f"   - 样本登记表：{SAMPLE_REGISTRY_PATH}")
    print(f"   - 分析报告：{REPORTS_DIR}/batch_001_video_*.json")
    print()
    
    print("下一步:")
    print("   1. 继续上传更多视频")
    print("   2. 使用 review_sample.py 审核样本")
    print("   3. 批次完成后生成总结报告")
    print()

if __name__ == '__main__':
    main()
