#!/usr/bin/env python3
"""
细化典型问题样本工具
为 21 个 2.5/3.0/3.5 typical_issue 样本补充详细字段
按问题类型分组处理：抛球问题 / 蓄力问题 / 击球点问题 / 随挥问题
"""

import json
from datetime import datetime

SAMPLE_REGISTRY_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/sample_registry.json'

# 问题标签映射到阶段
ISSUE_TO_PHASE = {
    # 抛球问题
    'toss_inconsistent': 'toss',
    'toss_height_low': 'toss',
    'toss_height_high': 'toss',
    'toss_position_front': 'toss',
    'toss_position_back': 'toss',
    'toss_position_left': 'toss',
    'toss_position_right': 'toss',
    
    # 蓄力问题
    'knee_bend_insufficient': 'loading',
    'rotation_insufficient': 'loading',
    'loading_insufficient': 'loading',
    'hip_rotation_insufficient': 'loading',
    
    # 击球点问题
    'contact_point_late': 'contact',
    'contact_point_early': 'contact',
    'contact_point_low': 'contact',
    'contact_point_high': 'contact',
    'contact_point_behind': 'contact',
    'contact_point_front': 'contact',
    
    # 随挥问题
    'follow_through_insufficient': 'follow_through',
    'follow_through_incomplete': 'follow_through',
    'body_not_forward': 'follow_through',
}

# 问题标签分组
TOSS_ISSUES = ['toss_inconsistent', 'toss_height_low', 'toss_height_high', 'toss_position_front', 'toss_position_back']
LOADING_ISSUES = ['knee_bend_insufficient', 'rotation_insufficient', 'loading_insufficient']
CONTACT_ISSUES = ['contact_point_late', 'contact_point_early', 'contact_point_low', 'contact_point_high']
FOLLOW_THROUGH_ISSUES = ['follow_through_insufficient', 'follow_through_incomplete']

def refine_issue_sample(sample):
    """细化典型问题样本"""
    
    ntrp = sample.get('ntrp_level', 'unknown')
    tags = sample.get('tags', [])
    
    # 找出所有问题标签
    issue_tags = [t for t in tags if any(issue in t for issue in ['insufficient', 'inconsistent', 'late', 'early', 'low', 'high', 'front', 'back', 'incomplete'])]
    
    # 确定主要问题（第一个问题标签）
    primary_issue = issue_tags[0] if issue_tags else None
    
    # 确定次要问题（第二个问题标签）
    secondary_issue = issue_tags[1] if len(issue_tags) > 1 else None
    
    # 确定问题阶段
    weaknesses = []
    for issue in issue_tags:
        phase = ISSUE_TO_PHASE.get(issue)
        if phase and phase not in weaknesses:
            weaknesses.append(phase)
    
    # 确定优势阶段（没有问题的阶段）
    all_phases = ['ready', 'toss', 'loading', 'contact', 'follow_through']
    strengths = [p for p in all_phases if p not in weaknesses]
    
    # 根据 NTRP 等级和问题数量确定质量等级
    if ntrp in ['2.5', '3.0']:
        # 低等级样本，问题较多，教学价值高
        quality_grade = 'A' if len(issue_tags) <= 2 else 'B'
        teaching_value = 'high'  # 典型问题，教学价值高
    elif ntrp == '3.5':
        # 中等级样本
        quality_grade = 'A' if len(issue_tags) == 1 else 'B'
        teaching_value = 'high' if len(issue_tags) <= 2 else 'medium'
    else:
        quality_grade = 'B'
        teaching_value = 'medium'
    
    # 确定问题类型分组
    problem_category = 'other'
    if any(issue in tags for issue in TOSS_ISSUES):
        problem_category = 'toss'
    elif any(issue in tags for issue in LOADING_ISSUES):
        problem_category = 'loading'
    elif any(issue in tags for issue in CONTACT_ISSUES):
        problem_category = 'contact'
    elif any(issue in tags for issue in FOLLOW_THROUGH_ISSUES):
        problem_category = 'follow_through'
    
    # 构建细化后的样本记录
    refined_sample = sample.copy()
    
    refined_sample['quality_grade'] = quality_grade
    refined_sample['teaching_value'] = teaching_value
    refined_sample['primary_issue'] = primary_issue
    refined_sample['secondary_issue'] = secondary_issue
    refined_sample['issue_tags'] = issue_tags
    refined_sample['action_phase_strengths'] = strengths if strengths else ['ready']
    refined_sample['action_phase_weaknesses'] = weaknesses
    refined_sample['problem_category'] = problem_category
    refined_sample['refined_at'] = datetime.now().isoformat()
    refined_sample['refined_by'] = 'system_auto_refine'
    
    # 确保 tags 已更新（添加 standard_motion 如果不是问题样本）
    if not issue_tags and 'standard_motion' not in tags:
        tags.append('standard_motion')
    refined_sample['tags'] = tags
    
    return refined_sample

def main():
    print("="*60)
    print("📋 细化典型问题样本工具")
    print("="*60)
    print()
    
    # 加载样本登记表
    with open(SAMPLE_REGISTRY_PATH, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    print(f"📋 当前样本总数：{len(registry)} 个")
    print()
    
    # 筛选典型问题样本
    issue_samples = [s for s in registry 
                    if s.get('ntrp_level') in ['2.5', '3.0', '3.5'] 
                    and s.get('sample_category') == 'typical_issue']
    
    print(f"📊 待细化典型问题样本：{len(issue_samples)} 个")
    print()
    
    # 按问题类型分组
    toss_issues = []
    loading_issues = []
    contact_issues = []
    follow_through_issues = []
    other_issues = []
    
    for sample in issue_samples:
        tags = sample.get('tags', [])
        
        has_toss_issue = any(t in tags for t in TOSS_ISSUES)
        has_loading_issue = any(t in tags for t in LOADING_ISSUES)
        has_contact_issue = any(t in tags for t in CONTACT_ISSUES)
        has_follow_through_issue = any(t in tags for t in FOLLOW_THROUGH_ISSUES)
        
        if has_toss_issue:
            toss_issues.append(sample)
        elif has_loading_issue:
            loading_issues.append(sample)
        elif has_contact_issue:
            contact_issues.append(sample)
        elif has_follow_through_issue:
            follow_through_issues.append(sample)
        else:
            other_issues.append(sample)
    
    groups = [
        ("🎾 抛球问题库", toss_issues, 'toss'),
        ("💪 蓄力问题库", loading_issues, 'loading'),
        ("🎯 击球点问题库", contact_issues, 'contact'),
        ("➡️ 随挥问题库", follow_through_issues, 'follow_through'),
        ("📦 其他问题库", other_issues, 'other'),
    ]
    
    # 细化样本
    print("🔍 开始按问题类型分组细化...")
    print()
    
    total_refined = 0
    for group_name, samples, category in groups:
        if not samples:
            continue
        
        print(f"\n{'='*60}")
        print(f"{group_name} ({len(samples)} 个)")
        print(f"{'='*60}")
        print()
        
        for i, sample in enumerate(samples, 1):
            sample_id = sample.get('sample_id', 'unknown')
            ntrp = sample.get('ntrp_level', 'unknown')
            
            # 如果已经细化过，跳过
            if 'quality_grade' in sample and 'primary_issue' in sample:
                print(f"   [{i}/{len(samples)}] {sample_id} - 已细化，跳过")
                continue
            
            # 细化样本
            refined_sample = refine_issue_sample(sample)
            
            # 更新 registry 中的样本
            for j in range(len(registry)):
                if registry[j].get('sample_id') == sample_id:
                    registry[j] = refined_sample
                    break
            
            total_refined += 1
            quality = refined_sample.get('quality_grade', 'B')
            teaching = refined_sample.get('teaching_value', 'medium')
            primary = refined_sample.get('primary_issue', 'none')
            weaknesses = refined_sample.get('action_phase_weaknesses', [])
            
            print(f"   [{i}/{len(samples)}] {sample_id}")
            print(f"      NTRP: {ntrp}")
            print(f"      Quality: {quality}")
            print(f"      Teaching Value: {teaching}")
            print(f"      Primary Issue: {primary}")
            print(f"      Weaknesses: {', '.join(weaknesses)}")
            print()
    
    # 保存细化后的样本登记表
    with open(SAMPLE_REGISTRY_PATH, 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    
    print("="*60)
    print("📊 细化完成统计")
    print("="*60)
    print()
    print(f"   细化样本数：{total_refined} 个")
    print(f"   总样本数：{len(registry)} 个")
    print()
    
    # 统计细化后的分布
    quality_count = {}
    teaching_count = {}
    category_count = {}
    
    for sample in registry:
        if sample.get('sample_category') == 'typical_issue' and sample.get('ntrp_level') in ['2.5', '3.0', '3.5']:
            if 'quality_grade' not in sample:
                continue
                
            quality = sample.get('quality_grade', 'unknown')
            teaching = sample.get('teaching_value', 'unknown')
            category = sample.get('problem_category', 'unknown')
            
            quality_count[quality] = quality_count.get(quality, 0) + 1
            teaching_count[teaching] = teaching_count.get(teaching, 0) + 1
            category_count[category] = category_count.get(category, 0) + 1
    
    print("📈 Quality Grade 分布:")
    for grade in ['A', 'B', 'C']:
        count = quality_count.get(grade, 0)
        print(f"   {grade}级：{count} 个")
    
    print()
    print("📈 Teaching Value 分布:")
    for value in ['high', 'medium', 'low']:
        count = teaching_count.get(value, 0)
        print(f"   {value}: {count} 个")
    
    print()
    print("📈 问题类型分布:")
    category_names = {
        'toss': '抛球问题',
        'loading': '蓄力问题',
        'contact': '击球点问题',
        'follow_through': '随挥问题',
        'other': '其他问题',
    }
    for cat, name in category_names.items():
        count = category_count.get(cat, 0)
        if count > 0:
            print(f"   {name}: {count} 个")
    
    print()
    print(f"💾 已保存到：{SAMPLE_REGISTRY_PATH}")
    print()
    print("="*60)
    print("✅ 典型问题样本细化完成！")
    print("="*60)
    print()

if __name__ == '__main__':
    main()
