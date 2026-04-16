#!/usr/bin/env python3
"""
细化 unknown 分类的样本
根据 NTRP 等级和文件名自动推断分类
"""

import json
from datetime import datetime

SAMPLE_REGISTRY_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/sample_registry.json'

def classify_and_refine_sample(sample):
    """自动分类并细化样本"""
    
    ntrp = sample.get('ntrp_level', 'unknown')
    filename = sample.get('source_file_name', '')
    source_type = sample.get('source_type', 'unknown')
    
    # 1. 确定分类
    if ntrp in ['5.0', '5.0+']:
        category = 'excellent_demo'
    elif ntrp in ['4.5']:
        # 4.5 级可能是 excellent_demo 或 typical_issue
        # 根据文件名判断（batch004 是高水平样本）
        if 'batch004' in filename or 'batch_eval' in filename:
            category = 'excellent_demo'
        else:
            category = 'typical_issue'
    elif ntrp in ['4.0']:
        # 4.0 级通常是 typical_issue
        category = 'typical_issue'
    elif ntrp in ['3.0', '3.5']:
        category = 'typical_issue'
    elif ntrp in ['2.5']:
        category = 'typical_issue'
    elif ntrp == 'unknown':
        # NTRP 未知的样本，暂时标记为 boundary_case
        category = 'boundary_case'
    else:
        category = 'unknown'
    
    # 2. 细化样本
    refined_sample = sample.copy()
    refined_sample['sample_category'] = category
    
    # 3. 根据分类细化
    if category == 'excellent_demo':
        # 优秀示范样本细化
        if ntrp in ['5.0', '5.0+']:
            refined_sample['quality_grade'] = 'A'
            refined_sample['teaching_value'] = 'high'
        elif ntrp == '4.5':
            refined_sample['quality_grade'] = 'B'
            refined_sample['teaching_value'] = 'medium'
        else:
            refined_sample['quality_grade'] = 'B'
            refined_sample['teaching_value'] = 'medium'
        
        refined_sample['action_phase_strengths'] = ['ready', 'toss', 'loading', 'contact', 'follow_through']
        refined_sample['action_phase_weaknesses'] = []
        refined_sample['tags'] = ['standard_motion']
        
    elif category == 'typical_issue':
        # 典型问题样本细化
        if ntrp in ['2.5', '3.0']:
            refined_sample['quality_grade'] = 'A'
            refined_sample['teaching_value'] = 'high'
        elif ntrp == '3.5':
            refined_sample['quality_grade'] = 'A'
            refined_sample['teaching_value'] = 'high'
        elif ntrp in ['4.0', '4.5']:
            refined_sample['quality_grade'] = 'B'
            refined_sample['teaching_value'] = 'medium'
        else:
            refined_sample['quality_grade'] = 'B'
            refined_sample['teaching_value'] = 'medium'
        
        refined_sample['action_phase_strengths'] = ['ready']
        refined_sample['action_phase_weaknesses'] = ['toss', 'loading', 'contact', 'follow_through']
        refined_sample['problem_category'] = 'other'
        refined_sample['issue_tags'] = []
        refined_sample['primary_issue'] = None
        refined_sample['secondary_issue'] = None
        refined_sample['tags'] = []
        
    elif category == 'boundary_case':
        # 边界样本
        refined_sample['quality_grade'] = 'B'
        refined_sample['teaching_value'] = 'medium'
        refined_sample['action_phase_strengths'] = ['ready']
        refined_sample['action_phase_weaknesses'] = []
        refined_sample['tags'] = []
    
    # 添加细化时间
    refined_sample['refined_at'] = datetime.now().isoformat()
    refined_sample['refined_by'] = 'system_auto_classify'
    
    return refined_sample

def main():
    print("="*70)
    print("📋 细化 unknown 分类样本")
    print("="*70)
    print()
    
    # 加载样本登记表
    with open(SAMPLE_REGISTRY_PATH, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    print(f"📋 当前样本总数：{len(registry)}")
    print()
    
    # 筛选 unknown 分类的样本
    unknown_samples = [s for s in registry if s.get('sample_category') == 'unknown']
    
    print(f"🔍 unknown 分类样本：{len(unknown_samples)}个")
    print()
    
    if not unknown_samples:
        print("✅ 所有样本已分类！")
        return
    
    # 按来源类型统计
    from collections import Counter
    source_count = Counter(s.get('source_type', 'unknown') for s in unknown_samples)
    print("按来源类型：")
    for src, count in sorted(source_count.items(), key=lambda x: -x[1]):
        print(f"   {src}: {count}个")
    print()
    
    # 按 NTRP 统计
    ntrp_count = Counter(s.get('ntrp_level', 'unknown') for s in unknown_samples)
    print("按 NTRP：")
    for ntrp in sorted(ntrp_count.keys()):
        count = ntrp_count.get(ntrp, 0)
        print(f"   {ntrp}: {count}个")
    print()
    
    # 细化样本
    print("="*70)
    print("🔄 开始分类并细化...")
    print("="*70)
    print()
    
    refined_count = 0
    category_count = Counter()
    
    for i, sample in enumerate(unknown_samples, 1):
        sample_id = sample.get('sample_id', 'unknown')
        ntrp = sample.get('ntrp_level', 'unknown')
        filename = sample.get('source_file_name', '')
        
        # 细化样本
        refined_sample = classify_and_refine_sample(sample)
        new_category = refined_sample['sample_category']
        
        # 更新 registry 中的样本
        for j in range(len(registry)):
            if registry[j].get('sample_id') == sample_id:
                registry[j] = refined_sample
                break
        
        refined_count += 1
        category_count[new_category] += 1
        
        print(f"   [{i}/{len(unknown_samples)}] {filename}")
        print(f"      sample_id: {sample_id}")
        print(f"      NTRP: {ntrp}")
        print(f"      分类：{new_category}")
        if new_category == 'excellent_demo':
            print(f"      Quality: {refined_sample.get('quality_grade')}")
            print(f"      Teaching: {refined_sample.get('teaching_value')}")
        elif new_category == 'typical_issue':
            print(f"      Quality: {refined_sample.get('quality_grade')}")
            print(f"      Teaching: {refined_sample.get('teaching_value')}")
        print()
    
    # 保存细化后的样本登记表
    print("="*70)
    print("💾 保存样本登记表...")
    print("="*70)
    
    with open(SAMPLE_REGISTRY_PATH, 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ 已保存")
    print()
    
    # 统计结果
    print("="*70)
    print("📊 细化完成统计")
    print("="*70)
    print()
    print(f"   细化样本数：{refined_count}个")
    print()
    print("   新增分类分布:")
    for cat, count in sorted(category_count.items(), key=lambda x: -x[1]):
        print(f"      {cat}: {count}个")
    print()
    
    # 总体统计
    excellent_count = len([s for s in registry if s.get('sample_category') == 'excellent_demo'])
    issue_count = len([s for s in registry if s.get('sample_category') == 'typical_issue'])
    boundary_count = len([s for s in registry if s.get('sample_category') == 'boundary_case'])
    unknown_count = len([s for s in registry if s.get('sample_category') == 'unknown'])
    
    print("   总体分类分布:")
    print(f"      excellent_demo: {excellent_count}个")
    print(f"      typical_issue: {issue_count}个")
    print(f"      boundary_case: {boundary_count}个")
    print(f"      unknown: {unknown_count}个")
    print()
    
    # 细化状态
    refined_total = len([s for s in registry if s.get('quality_grade')])
    unrefined_total = len([s for s in registry if not s.get('quality_grade')])
    
    print(f"   细化状态:")
    print(f"      ✅ 已细化：{refined_total}个 ({refined_total/len(registry)*100:.1f}%)")
    print(f"      ❌ 未细化：{unrefined_total}个 ({unrefined_total/len(registry)*100:.1f}%)")
    print()
    
    print("="*70)
    print("✅ unknown 分类样本细化完成！")
    print("="*70)
    print()

if __name__ == '__main__':
    main()
