#!/usr/bin/env python3
"""
细化标准示范样本工具
为 21 个 4.5/5.0+ excellent_demo 样本补充详细字段
"""

import json
from datetime import datetime

SAMPLE_REGISTRY_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/sample_registry.json'

def refine_excellent_sample(sample):
    """细化标准示范样本"""
    
    ntrp = sample.get('ntrp_level', 'unknown')
    tags = sample.get('tags', [])
    
    # 根据 NTRP 等级和标签自动推断细化字段
    if ntrp in ['5.0', '5.0+']:
        quality_grade = 'A'  # 5.0 级默认为 A 级
        teaching_value = 'high'
    elif ntrp == '4.5':
        quality_grade = 'A' if len(tags) >= 4 else 'B'
        teaching_value = 'high' if len(tags) >= 4 else 'medium'
    else:
        quality_grade = 'B'
        teaching_value = 'medium'
    
    # 分析各阶段表现
    strengths = []
    weaknesses = []
    
    # 准备阶段
    if 'ready_good' in tags:
        strengths.append('ready')
    else:
        weaknesses.append('ready')
    
    # 抛球阶段
    if 'toss_consistent' in tags:
        strengths.append('toss')
    elif 'toss_inconsistent' in tags:
        weaknesses.append('toss')
    
    # 蓄力阶段
    if 'rotation_good' in tags:
        strengths.append('loading')
    elif 'rotation_insufficient' in tags:
        weaknesses.append('loading')
    
    if 'knee_bend_insufficient' not in tags and 'rotation_good' in tags:
        if 'loading' not in strengths:
            strengths.append('loading')
    
    # 击球阶段
    if 'power_good' in tags:
        strengths.append('contact')
    elif 'contact_point_late' in tags:
        weaknesses.append('contact')
    
    # 随挥阶段
    if 'follow_through_complete' in tags:
        strengths.append('follow_through')
    elif 'follow_through_insufficient' in tags:
        weaknesses.append('follow_through')
    
    # 确定主要问题和次要问题（标准示范样本通常无明显问题）
    primary_issue = None
    secondary_issue = None
    
    # 如果有少量问题标签，记录下来
    issue_tags = [t for t in tags if 'insufficient' in t or 'inconsistent' in t or 'late' in t or 'low' in t]
    if issue_tags:
        primary_issue = issue_tags[0] if issue_tags else None
        secondary_issue = issue_tags[1] if len(issue_tags) > 1 else None
    
    # 如果没有问题标签，标记为标准动作
    if not issue_tags:
        if 'standard_motion' not in tags:
            tags.append('standard_motion')
    
    # 构建细化后的样本记录
    refined_sample = sample.copy()
    
    refined_sample['quality_grade'] = quality_grade
    refined_sample['teaching_value'] = teaching_value
    refined_sample['primary_issue'] = primary_issue
    refined_sample['secondary_issue'] = secondary_issue
    refined_sample['action_phase_strengths'] = strengths if strengths else ['ready', 'toss', 'loading', 'contact', 'follow_through']
    refined_sample['action_phase_weaknesses'] = weaknesses
    refined_sample['refined_at'] = datetime.now().isoformat()
    refined_sample['refined_by'] = 'system_auto_refine'
    
    # 确保 tags 已更新
    refined_sample['tags'] = tags
    
    return refined_sample

def main():
    print("="*60)
    print("⭐ 细化标准示范样本工具")
    print("="*60)
    print()
    
    # 加载样本登记表
    with open(SAMPLE_REGISTRY_PATH, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    print(f"📋 当前样本总数：{len(registry)} 个")
    print()
    
    # 筛选标准示范样本
    excellent_samples = [s for s in registry 
                        if s.get('ntrp_level') in ['4.5', '5.0', '5.0+'] 
                        and s.get('sample_category') == 'excellent_demo']
    
    print(f"📊 待细化标准示范样本：{len(excellent_samples)} 个")
    print()
    
    # 细化样本
    print("🔍 开始细化...")
    print()
    
    refined_count = 0
    for i, sample in enumerate(excellent_samples, 1):
        sample_id = sample.get('sample_id', 'unknown')
        ntrp = sample.get('ntrp_level', 'unknown')
        
        # 如果已经细化过，跳过
        if 'quality_grade' in sample and 'teaching_value' in sample:
            print(f"   [{i}/{len(excellent_samples)}] {sample_id} - 已细化，跳过")
            continue
        
        # 细化样本
        refined_sample = refine_excellent_sample(sample)
        
        # 更新 registry 中的样本
        for j in range(len(registry)):
            if registry[j].get('sample_id') == sample_id:
                registry[j] = refined_sample
                break
        
        refined_count += 1
        quality = refined_sample.get('quality_grade', 'B')
        teaching = refined_sample.get('teaching_value', 'medium')
        strengths = refined_sample.get('action_phase_strengths', [])
        
        print(f"   [{i}/{len(excellent_samples)}] {sample_id}")
        print(f"      NTRP: {ntrp}")
        print(f"      Quality: {quality}")
        print(f"      Teaching Value: {teaching}")
        print(f"      Strengths: {', '.join(strengths[:3])}")
        print()
    
    # 保存细化后的样本登记表
    with open(SAMPLE_REGISTRY_PATH, 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    
    print("="*60)
    print("📊 细化完成统计")
    print("="*60)
    print()
    print(f"   细化样本数：{refined_count} 个")
    print(f"   总样本数：{len(registry)} 个")
    print()
    
    # 统计细化后的分布
    quality_count = {}
    teaching_count = {}
    
    for sample in registry:
        if sample.get('sample_category') == 'excellent_demo' and sample.get('ntrp_level') in ['4.5', '5.0', '5.0+']:
            quality = sample.get('quality_grade', 'unknown')
            teaching = sample.get('teaching_value', 'unknown')
            
            quality_count[quality] = quality_count.get(quality, 0) + 1
            teaching_count[teaching] = teaching_count.get(teaching, 0) + 1
    
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
    print(f"💾 已保存到：{SAMPLE_REGISTRY_PATH}")
    print()
    print("="*60)
    print("✅ 标准示范样本细化完成！")
    print("="*60)
    print()

if __name__ == '__main__':
    main()
