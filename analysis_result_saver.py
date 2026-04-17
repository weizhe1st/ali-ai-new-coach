#!/usr/bin/env python3
"""
保存分析结果到 analysis_results.json
在 analyze_video_complete 函数结束时调用
"""

import os
import json
import time
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def save_analysis_result(task_id, video_path, ntrp_level, overall_score, confidence, 
                        normalized_result, cos_key=None, cos_url=None):
    """保存分析结果到 analysis_results.json"""
    try:
        analysis_results_path = os.path.join(PROJECT_ROOT, 'data', 'analysis_results.json')
        
        # 加载现有分析结果
        if os.path.exists(analysis_results_path):
            with open(analysis_results_path, 'r', encoding='utf-8') as f:
                analysis_results = json.load(f)
        else:
            analysis_results = []
        
        # 创建分析结果记录
        analysis_record = {
            'analysis_id': task_id or f"analysis_{int(time.time())}",
            'task_id': task_id,
            'video_file': os.path.basename(video_path) if video_path else 'unknown',
            'video_path': video_path,
            'analyzed_at': datetime.now().isoformat(),
            'ntrp_level': ntrp_level,
            'overall_score': overall_score,
            'confidence': confidence,
            'phase_analysis': normalized_result.get('phase_analysis', {}),
            'key_issues': normalized_result.get('key_issues', []),
            'training_plan': normalized_result.get('training_plan', []),
            'cos_key': cos_key,
            'cos_url': cos_url,
            'report_sent': False
        }
        
        # 添加到 analysis_results
        analysis_results.append(analysis_record)
        
        # 保存回文件
        with open(analysis_results_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, ensure_ascii=False, indent=2)
        
        print(f"  ✓ 分析结果已保存：{analysis_record['analysis_id']}")
        print(f"  ✓ NTRP: {ntrp_level}, 总分：{overall_score}")
        
        # 如果分数≥80，同时保存到 sample_registry.json（候选黄金样本）
        if overall_score >= 80:
            print(f"  🏆 分数≥80，同时登记为候选黄金样本...")
            save_to_sample_registry(analysis_record)
        
        return True
        
    except Exception as e:
        print(f"  ⚠️  分析结果保存失败：{e}")
        return False


def save_to_sample_registry(analysis_record):
    """保存高分样本到 sample_registry.json（候选黄金样本）"""
    try:
        sample_registry_path = os.path.join(PROJECT_ROOT, 'data', 'sample_registry.json')
        
        # 加载现有样本登记表
        if os.path.exists(sample_registry_path):
            with open(sample_registry_path, 'r', encoding='utf-8') as f:
                registry = json.load(f)
        else:
            registry = []
        
        # 创建样本记录
        sample_record = {
            'sample_id': analysis_record['analysis_id'],
            'source_type': 'auto_analyze',
            'action_type': 'video_analysis_serve',
            'source_file_name': analysis_record['video_file'],
            'source_file_path': analysis_record['video_path'],
            'cos_key': analysis_record['cos_key'],
            'cos_url': analysis_record['cos_url'],
            'candidate_for_golden': True,
            'golden_review_status': 'pending',
            'sample_category': 'excellent_demo',
            'ntrp_level': analysis_record['ntrp_level'],
            'overall_score': analysis_record['overall_score'],
            'quality_grade': 'A',
            'teaching_value': 'high',
            'tags': [],
            'task_id': analysis_record['task_id'],
            'archived_at': datetime.now().isoformat(),
            'analysis_summary': {
                'ntrp_level': analysis_record['ntrp_level'],
                'overall_score': analysis_record['overall_score'],
                'confidence': analysis_record.get('confidence', 0.75),
                'key_issues': analysis_record.get('key_issues', [])
            }
        }
        
        # 添加到 registry
        registry.append(sample_record)
        
        # 保存回文件
        with open(sample_registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)
        
        print(f"    ✓ 候选黄金样本已登记：{sample_record['sample_id']}")
        return True
        
    except Exception as e:
        print(f"    ⚠️  黄金样本登记失败：{e}")
        return False
