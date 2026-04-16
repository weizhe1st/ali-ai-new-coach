#!/usr/bin/env python3
"""
重新扫描历史任务并补登记到 sample_registry

用途：
- 扫描 data/tasks/ 目录下的所有历史任务
- 提取已分析成功的任务
- 补登记到 sample_registry.json
- 标记为 imported_legacy 状态
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# 项目路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(PROJECT_ROOT, 'data', 'tasks')
SAMPLE_REGISTRY_PATH = os.path.join(PROJECT_ROOT, 'data', 'sample_registry.json')


def load_sample_registry():
    """加载样本登记表"""
    if os.path.exists(SAMPLE_REGISTRY_PATH):
        try:
            with open(SAMPLE_REGISTRY_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_sample_registry(records):
    """保存样本登记表"""
    os.makedirs(os.path.dirname(SAMPLE_REGISTRY_PATH), exist_ok=True)
    with open(SAMPLE_REGISTRY_PATH, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def scan_task_directories():
    """扫描所有任务目录"""
    if not os.path.exists(TASKS_DIR):
        print(f"❌ 任务目录不存在：{TASKS_DIR}")
        return []
    
    tasks = []
    for task_id in os.listdir(TASKS_DIR):
        task_path = os.path.join(TASKS_DIR, task_id)
        if os.path.isdir(task_path):
            tasks.append({
                'task_id': task_id,
                'task_path': task_path
            })
    
    return tasks


def extract_task_info(task_path):
    """从任务目录提取信息"""
    task_info = {
        'task_id': os.path.basename(task_path),
        'source_file_name': None,
        'source_file_path': None,
        'cos_key': None,
        'cos_url': None,
        'analysis_result': None,
        'report': None,
        'created_at': None
    }
    
    # 查找源文件信息
    source_info_path = os.path.join(task_path, 'source_info.json')
    if os.path.exists(source_info_path):
        try:
            with open(source_info_path, 'r', encoding='utf-8') as f:
                source_info = json.load(f)
                task_info['source_file_name'] = source_info.get('source_file_name')
                task_info['source_file_path'] = source_info.get('source_file_path')
        except:
            pass
    
    # 查找分析结果
    result_path = os.path.join(task_path, 'result.json')
    if os.path.exists(result_path):
        try:
            with open(result_path, 'r', encoding='utf-8') as f:
                result = json.load(f)
                task_info['analysis_result'] = result
                if result.get('success'):
                    task_info['cos_key'] = result.get('cos_key')
                    task_info['cos_url'] = result.get('cos_url')
        except:
            pass
    
    # 查找报告
    report_files = list(Path(task_path).glob('report_*.txt'))
    if report_files:
        try:
            with open(report_files[0], 'r', encoding='utf-8') as f:
                task_info['report'] = f.read()[:500]  # 只取前 500 字符
        except:
            pass
    
    # 查找创建时间
    task_info['created_at'] = datetime.fromtimestamp(
        os.path.getmtime(task_path)
    ).isoformat()
    
    return task_info


def generate_sample_id(task_id):
    """生成样本 ID"""
    # 从 task_id 提取日期
    date_str = datetime.now().strftime('%Y%m%d')
    short_id = task_id[-6:] if len(task_id) >= 6 else task_id
    return f"legacy_{date_str}_{short_id}"


def migrate_task_to_sample(task_info):
    """将任务信息转换为样本记录"""
    analysis = task_info.get('analysis_result', {})
    
    # 提取 NTRP 和评分
    ntrp_level = 'unknown'
    overall_score = None
    
    if analysis:
        structured = analysis.get('structured_result', {})
        ntrp_level = structured.get('ntrp_level', 'unknown')
        overall_score = structured.get('overall_score')
    
    sample_record = {
        'sample_id': generate_sample_id(task_info['task_id']),
        'source_type': 'legacy_task_import',
        'action_type': task_info.get('action_type', 'video_analysis_serve'),
        'source_file_name': task_info.get('source_file_name', 'unknown'),
        'source_file_path': task_info.get('source_file_path'),
        'cos_key': task_info.get('cos_key'),
        'cos_url': task_info.get('cos_url'),
        'candidate_for_golden': False,
        'golden_review_status': 'imported_legacy',
        'analysis_summary': {
            'ntrp_level': ntrp_level,
            'overall_score': overall_score,
        } if overall_score else {},
        'imported_at': datetime.now().isoformat(),
        'golden_review_note': '从历史任务目录导入，待确认分类和审核状态'
    }
    
    return sample_record


def main():
    print("="*60)
    print("📦 历史任务补登记工具")
    print("="*60)
    print()
    
    # 加载现有样本登记表
    print("📋 加载现有样本登记表...")
    registry = load_sample_registry()
    existing_task_ids = {r.get('task_id') for r in registry if r.get('task_id')}
    print(f"   现有样本数：{len(registry)}")
    print(f"   已有任务 ID 数：{len(existing_task_ids)}")
    print()
    
    # 扫描任务目录
    print("🔍 扫描任务目录...")
    tasks = scan_task_directories()
    print(f"   找到任务目录数：{len(tasks)}")
    print()
    
    # 提取任务信息
    print("📊 提取任务信息...")
    migrated_count = 0
    skipped_count = 0
    
    for task in tasks:
        task_id = task['task_id']
        
        # 跳过已存在的样本
        if task_id in existing_task_ids:
            skipped_count += 1
            continue
        
        # 提取任务信息
        task_info = extract_task_info(task['task_path'])
        
        # 检查是否分析成功
        analysis = task_info.get('analysis_result') or {}
        if not analysis.get('success'):
            print(f"   ⚠️  跳过（分析失败或未分析）: {task_id}")
            skipped_count += 1
            continue
        
        # 转换为样本记录
        sample_record = migrate_task_to_sample(task_info)
        
        # 添加到登记表
        registry.append(sample_record)
        migrated_count += 1
        print(f"   ✅ 已登记：{sample_record['sample_id']} ({task_id})")
    
    print()
    print("="*60)
    print(f"📈 迁移完成")
    print(f"   新增样本：{migrated_count}")
    print(f"   跳过：{skipped_count}")
    print(f"   总样本数：{len(registry)}")
    print("="*60)
    
    # 保存
    print()
    print("💾 保存样本登记表...")
    save_sample_registry(registry)
    print(f"   已保存到：{SAMPLE_REGISTRY_PATH}")
    print()
    
    print("✅ 补登记完成！")
    print()
    print("下一步:")
    print("   1. 使用 review_sample.py list --status imported_legacy 查看新导入的样本")
    print("   2. 使用 review_sample.py approve/reject 进行批量审核")
    print()


if __name__ == '__main__':
    main()
