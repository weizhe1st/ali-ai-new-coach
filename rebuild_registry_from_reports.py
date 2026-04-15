#!/usr/bin/env python3
"""
从历史报告重建样本登记表

用途：
- 扫描 reports/ 目录下的所有分析报告
- 从报告文件名提取时间戳
- 匹配对应的视频文件
- 重建样本登记表
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path

# 项目路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(PROJECT_ROOT, 'reports')
MEDIA_INBOUND_DIR = os.path.join(PROJECT_ROOT, 'media', 'inbound')
SAMPLE_REGISTRY_PATH = os.path.join(PROJECT_ROOT, 'data', 'sample_registry.json')


def load_existing_registry():
    """加载现有样本登记表"""
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


def scan_reports():
    """扫描所有分析报告"""
    reports = []
    
    # 扫描 JSON 报告
    for report_file in Path(REPORTS_DIR).glob('*.json'):
        if 'daily_report' in report_file.name:
            continue  # 跳过日报
        
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
                
            # 从文件名提取时间戳
            match = re.search(r'(\d{8}_\d{6})', report_file.name)
            if match:
                timestamp_str = match.group(1)
                created_at = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S').isoformat()
            else:
                created_at = datetime.fromtimestamp(report_file.stat().st_mtime).isoformat()
            
            reports.append({
                'report_file': str(report_file),
                'report_data': report_data,
                'created_at': created_at,
                'type': 'json'
            })
        except Exception as e:
            print(f"   ⚠️  读取报告失败 {report_file.name}: {e}")
    
    # 扫描 TXT 报告
    for report_file in Path(REPORTS_DIR).glob('report_*.txt'):
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 从文件名提取时间戳
            match = re.search(r'(\d{8}_\d{6})', report_file.name)
            if match:
                timestamp_str = match.group(1)
                created_at = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S').isoformat()
            else:
                created_at = datetime.fromtimestamp(report_file.stat().st_mtime).isoformat()
            
            # 从 TXT 中提取 NTRP 和评分
            ntrp_match = re.search(r'NTRP 等级：(\d+\.?\d*)', content)
            score_match = re.search(r'综合评分：(\d+)/100', content)
            
            report_data = {
                'ntrp_level': ntrp_match.group(1) if ntrp_match else 'unknown',
                'overall_score': int(score_match.group(1)) if score_match else None,
            }
            
            reports.append({
                'report_file': str(report_file),
                'report_data': report_data,
                'created_at': created_at,
                'type': 'txt'
            })
        except Exception as e:
            print(f"   ⚠️  读取报告失败 {report_file.name}: {e}")
    
    return reports


def match_video_to_report(report_created_at):
    """根据时间戳匹配视频文件"""
    report_time = datetime.fromisoformat(report_created_at)
    
    # 查找时间接近的视频文件（前后 5 分钟）
    for video_file in Path(MEDIA_INBOUND_DIR).glob('*.mp4'):
        video_time = datetime.fromtimestamp(video_file.stat().st_mtime)
        time_diff = abs((video_time - report_time).total_seconds())
        
        if time_diff < 300:  # 5 分钟内
            return {
                'source_file_name': video_file.name,
                'source_file_path': str(video_file),
                'video_mtime': video_time.isoformat()
            }
    
    return None


def generate_sample_id(index, timestamp):
    """生成样本 ID"""
    return f"legacy_report_{index:04d}"


def main():
    print("="*60)
    print("📦 从历史报告重建样本登记表")
    print("="*60)
    print()
    
    # 加载现有样本登记表
    print("📋 加载现有样本登记表...")
    registry = load_existing_registry()
    print(f"   现有样本数：{len(registry)}")
    print()
    
    # 扫描报告
    print("🔍 扫描分析报告...")
    reports = scan_reports()
    print(f"   找到报告数：{len(reports)}")
    print()
    
    # 重建样本记录
    print("📊 重建样本记录...")
    migrated_count = 0
    
    for i, report in enumerate(reports, start=1):
        # 匹配视频文件
        video_info = match_video_to_report(report['created_at'])
        
        report_data = report['report_data']
        
        # 创建样本记录
        sample_record = {
            'sample_id': generate_sample_id(i, report['created_at']),
            'source_type': 'legacy_report_import',
            'action_type': 'video_analysis_serve',
            'source_file_name': video_info['source_file_name'] if video_info else 'unknown',
            'source_file_path': video_info['source_file_path'] if video_info else None,
            'cos_key': None,
            'cos_url': None,
            'candidate_for_golden': False,
            'golden_review_status': 'imported_legacy',
            'analysis_summary': {
                'ntrp_level': report_data.get('ntrp_level', 'unknown'),
                'overall_score': report_data.get('overall_score'),
            },
            'imported_at': datetime.now().isoformat(),
            'golden_review_note': f'从历史报告导入 ({report["type"]} 格式)，待确认分类和审核状态'
        }
        
        registry.append(sample_record)
        migrated_count += 1
        print(f"   ✅ 已登记：{sample_record['sample_id']} - NTRP {sample_record['analysis_summary']['ntrp_level']} - {sample_record['source_file_name']}")
    
    print()
    print("="*60)
    print(f"📈 重建完成")
    print(f"   新增样本：{migrated_count}")
    print(f"   总样本数：{len(registry)}")
    print("="*60)
    
    # 保存
    print()
    print("💾 保存样本登记表...")
    save_registry(registry)
    print(f"   已保存到：{SAMPLE_REGISTRY_PATH}")
    print()
    
    print("✅ 重建完成！")
    print()
    print("下一步:")
    print("   1. 使用 review_sample.py list --status imported_legacy 查看新导入的样本")
    print("   2. 使用 review_sample.py approve/reject 进行批量审核")
    print("   3. 使用 review_sample.py summary 查看统计")
    print()


if __name__ == '__main__':
    main()
