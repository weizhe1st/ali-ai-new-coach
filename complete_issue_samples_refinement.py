#!/usr/bin/env python3
"""
补充细化 8 个典型问题样本工具
按照教练知识点规则，为剩余未细化的样本补充字段
"""

import json
from datetime import datetime

SAMPLE_REGISTRY_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/sample_registry.json'

# 问题标签映射到阶段
ISSUE_TO_PHASE = {
    'toss_inconsistent': 'toss',
    'toss_height_low': 'toss',
    'toss_height_high': 'toss',
    'toss_position_front': 'toss',
    'toss_position_back': 'toss',
    'knee_bend_insufficient': 'loading',
    'rotation_insufficient': 'loading',
    'loading_insufficient': 'loading',
    'contact_point_late': 'contact',
    'contact_point_early': 'contact',
    'contact_point_low': 'contact',
    'contact_point_high': 'contact',
    'follow_through_insufficient': 'follow_through',
}

def refine_sample(sample):
    """按照教练知识点规则细化样本"""
    
    ntrp = sample.get('ntrp_level', 'unknown')
    tags = sample.get('tags', [])
    
    # 找出所有问题标签
    issue_tags = [t for t in tags if any(x in t for x in ['insufficient', 'inconsistent', 'late', 'early', 'low', 'high', 'front', 'back'])]
    
    # 根据教练知识点规则判断 primary_issue
    # 优先级：抛球问题 > 蓄力问题 > 击球点问题 > 随挥问题
    primary_issue = None
    secondary_issue = None
    
    # 优先判断抛球问题（上游根因）
    toss_issues = [t for t in issue_tags if 'toss' in t]
    if toss_issues:
        primary_issue = toss_issues[0]
        remaining = [t for t in issue_tags if t != primary_issue]
        secondary_issue = remaining[0] if remaining else None
    
    # 其次判断蓄力问题（次级根因）
    elif any('knee_bend' in t or 'rotation' in t for t in issue_tags):
        loading_issues = [t for t in issue_tags if 'knee_bend' in t or 'rotation' in t]
        primary_issue = loading_issues[0]
        remaining = [t for t in issue_tags if t != primary_issue]
        secondary_issue = remaining[0] if remaining else None
    
    # 最后判断击球点问题（通常是结果性问题）
    elif any('contact' in t for t in issue_tags):
        contact_issues = [t for t in issue_tags if 'contact' in t]
        primary_issue = contact_issues[0]
        remaining = [t for t in issue_tags if t != primary_issue]
        secondary_issue = remaining[0] if remaining else None
    
    # 确定问题阶段（根据教练知识点映射）
    weaknesses = []
    for issue in issue_tags:
        phase = ISSUE_TO_PHASE.get(issue)
        if phase and phase not in weaknesses:
            weaknesses.append(phase)
    
    # 确定优势阶段
    all_phases = ['ready', 'toss', 'loading', 'contact', 'follow_through']
    strengths = [p for p in all_phases if p not in weaknesses]
    if not strengths:
        strengths = ['ready']  # 至少准备阶段是好的
    
    # 根据教练知识点规则确定 quality_grade 和 teaching_value
    if ntrp in ['2.5', '3.0']:
        # 低等级样本，问题典型，教学价值高
        quality_grade = 'A' if len(issue_tags) <= 2 else 'B'
        teaching_value = 'high'
    elif ntrp == '3.5':
        # 中等级样本
        quality_grade = 'A' if len(issue_tags) == 1 else 'B'
        teaching_value = 'high' if len(issue_tags) <= 2 else 'medium'
    else:
        quality_grade = 'B'
        teaching_value = 'medium'
    
    # 构建细化后的样本记录
    refined_sample = sample.copy()
    
    refined_sample['quality_grade'] = quality_grade
    refined_sample['teaching_value'] = teaching_value
    refined_sample['primary_issue'] = primary_issue
    refined_sample['secondary_issue'] = secondary_issue
    refined_sample['issue_tags'] = issue_tags
    refined_sample['action_phase_strengths'] = strengths
    refined_sample['action_phase_weaknesses'] = weaknesses
    refined_sample['refined_at'] = datetime.now().isoformat()
    refined_sample['refined_by'] = 'system_auto_refine_coach_rules'
    
    return refined_sample

def main():
    print("="*60)
    print("📦 补充细化 8 个典型问题样本")
    print("="*60)
    print()
    
    # 加载样本登记表
    with open(SAMPLE_REGISTRY_PATH, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    print(f"📋 当前样本总数：{len(registry)} 个")
    print()
    
    # 筛选未细化的典型问题样本
    unrefined_samples = [s for s in registry 
                        if s.get('sample_category') == 'typical_issue' 
                        and s.get('ntrp_level') in ['2.5', '3.0', '3.5']
                        and 'primary_issue' not in s]
    
    print(f"📊 待细化样本数：{len(unrefined_samples)} 个")
    print()
    
    if not unrefined_samples:
        print("✅ 所有样本已细化完成！")
        return
    
    # 细化样本
    print("🔍 开始按教练知识点规则细化...")
    print()
    
    for i, sample in enumerate(unrefined_samples, 1):
        sample_id = sample.get('sample_id', 'unknown')
        ntrp = sample.get('ntrp_level', 'unknown')
        tags = sample.get('tags', [])
        
        # 细化样本
        refined_sample = refine_sample(sample)
        
        # 更新 registry 中的样本
        for j in range(len(registry)):
            if registry[j].get('sample_id') == sample_id:
                registry[j] = refined_sample
                break
        
        quality = refined_sample.get('quality_grade', 'B')
        teaching = refined_sample.get('teaching_value', 'medium')
        primary = refined_sample.get('primary_issue', 'none')
        secondary = refined_sample.get('secondary_issue', 'none')
        weaknesses = refined_sample.get('action_phase_weaknesses', [])
        
        print(f"   [{i}/{len(unrefined_samples)}] {sample_id}")
        print(f"      NTRP: {ntrp}")
        print(f"      Quality: {quality}")
        print(f"      Teaching Value: {teaching}")
        print(f"      Primary Issue: {primary}")
        print(f"      Secondary Issue: {secondary}")
        print(f"      Weaknesses: {', '.join(weaknesses)}")
        print()
    
    # 保存细化后的样本登记表
    with open(SAMPLE_REGISTRY_PATH, 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    
    print("="*60)
    print("📊 细化完成统计")
    print("="*60)
    print()
    print(f"   本次细化：{len(unrefined_samples)} 个")
    print(f"   总样本数：{len(registry)} 个")
    print()
    
    # 统计细化后的分布
    all_issue_samples = [s for s in registry 
                        if s.get('sample_category') == 'typical_issue' 
                        and s.get('ntrp_level') in ['2.5', '3.0', '3.5']]
    
    quality_count = {}
    teaching_count = {}
    primary_issue_count = {}
    
    for sample in all_issue_samples:
        if 'quality_grade' not in sample:
            continue
        
        quality = sample.get('quality_grade', 'unknown')
        teaching = sample.get('teaching_value', 'unknown')
        primary = sample.get('primary_issue', 'unknown')
        
        quality_count[quality] = quality_count.get(quality, 0) + 1
        teaching_count[teaching] = teaching_count.get(teaching, 0) + 1
        primary_issue_count[primary] = primary_issue_count.get(primary, 0) + 1
    
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
    print("📈 Primary Issue 分布:")
    for issue, count in sorted(primary_issue_count.items(), key=lambda x: -x[1])[:10]:
        print(f"   {issue:35s}: {count:2d} 个")
    
    print()
    print(f"💾 已保存到：{SAMPLE_REGISTRY_PATH}")
    print()
    print("="*60)
    print("✅ 典型问题样本库补全完成！")
    print("="*60)
    print()
    print("下一步:")
    print("   1. 建立 5 个问题池索引")
    print("   2. 抛球问题库")
    print("   3. 蓄力问题库")
    print("   4. 击球点问题库")
    print("   5. 随挥问题库")
    print("   6. 标准动作示范库")
    print()

if __name__ == '__main__':
    main()
