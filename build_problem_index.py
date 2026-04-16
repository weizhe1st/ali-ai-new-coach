#!/usr/bin/env python3
"""
建立 5 个问题池索引 + 3 个辅助索引
按照"主问题池 + 辅助索引"的双层结构
"""

import json
from datetime import datetime
from collections import defaultdict

SAMPLE_REGISTRY_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/sample_registry.json'
PROBLEM_INDEX_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/problem_index.json'

# 主问题池定义
PROBLEM_POOLS_CONFIG = {
    "toss_issues": {
        "name": "抛球问题库",
        "phase": "toss",
        "primary_issue_keys": [
            "toss_inconsistent",
            "toss_height_low",
            "toss_height_high",
            "toss_position_front",
            "toss_position_back",
            "toss_position_left",
            "toss_position_right"
        ]
    },
    "loading_issues": {
        "name": "蓄力问题库",
        "phase": "loading",
        "primary_issue_keys": [
            "knee_bend_insufficient",
            "rotation_insufficient",
            "loading_insufficient",
            "hip_rotation_insufficient"
        ]
    },
    "contact_issues": {
        "name": "击球点问题库",
        "phase": "contact",
        "primary_issue_keys": [
            "contact_point_late",
            "contact_point_early",
            "contact_point_low",
            "contact_point_high",
            "contact_point_behind",
            "contact_point_front"
        ]
    },
    "follow_through_issues": {
        "name": "随挥问题库",
        "phase": "follow_through",
        "primary_issue_keys": [
            "follow_through_insufficient",
            "follow_through_incomplete",
            "body_not_forward"
        ]
    },
    "standard_demos": {
        "name": "标准动作示范库",
        "phase": "all",
        "criteria": {
            "sample_category": "excellent_demo",
            "ntrp_level": ["4.5", "5.0", "5.0+"],
            "quality_grade": ["A"]
        }
    }
}

def build_problem_pools(registry):
    """建立主问题池"""
    
    pools = {}
    
    for pool_key, config in PROBLEM_POOLS_CONFIG.items():
        pool = {
            "name": config["name"],
            "phase": config["phase"],
            "sample_ids": [],
            "sample_count": 0
        }
        
        if pool_key == "standard_demos":
            # 标准示范库按条件筛选
            criteria = config["criteria"]
            for sample in registry:
                if (sample.get('sample_category') == criteria['sample_category'] and
                    sample.get('ntrp_level') in criteria['ntrp_level'] and
                    sample.get('quality_grade') in criteria['quality_grade']):
                    pool["sample_ids"].append(sample.get('sample_id'))
        else:
            # 问题库按 primary_issue 筛选
            primary_issue_keys = config["primary_issue_keys"]
            for sample in registry:
                primary_issue = sample.get('primary_issue')
                if primary_issue and primary_issue in primary_issue_keys:
                    # 一个样本只能进入一个主池（按 primary_issue 判断）
                    pool["sample_ids"].append(sample.get('sample_id'))
        
        pool["sample_count"] = len(pool["sample_ids"])
        pools[pool_key] = pool
    
    return pools

def build_secondary_indexes(registry):
    """建立辅助索引"""
    
    indexes = {
        "by_secondary_issue": {},
        "by_phase_weakness": {},
        "by_ntrp_level": {}
    }
    
    # by_secondary_issue: 按次要问题分组
    secondary_issue_index = defaultdict(list)
    for sample in registry:
        secondary_issue = sample.get('secondary_issue')
        if secondary_issue:
            sample_id = sample.get('sample_id')
            secondary_issue_index[secondary_issue].append(sample_id)
    
    for issue, sample_ids in sorted(secondary_issue_index.items()):
        indexes["by_secondary_issue"][issue] = {
            "issue": issue,
            "sample_ids": sample_ids,
            "sample_count": len(sample_ids)
        }
    
    # by_phase_weakness: 按问题阶段分组
    phase_weakness_index = defaultdict(list)
    for sample in registry:
        weaknesses = sample.get('action_phase_weaknesses', [])
        for phase in weaknesses:
            sample_id = sample.get('sample_id')
            phase_weakness_index[phase].append(sample_id)
    
    for phase, sample_ids in sorted(phase_weakness_index.items()):
        phase_names = {
            'toss': '抛球阶段',
            'loading': '蓄力阶段',
            'contact': '击球阶段',
            'follow_through': '随挥阶段',
            'ready': '准备阶段'
        }
        indexes["by_phase_weakness"][phase] = {
            "phase": phase,
            "phase_name": phase_names.get(phase, phase),
            "sample_ids": list(set(sample_ids)),  # 去重
            "sample_count": len(set(sample_ids))
        }
    
    # by_ntrp_level: 按 NTRP 等级分组
    ntrp_index = defaultdict(list)
    for sample in registry:
        ntrp = sample.get('ntrp_level', 'unknown')
        sample_id = sample.get('sample_id')
        ntrp_index[ntrp].append(sample_id)
    
    for ntrp, sample_ids in sorted(ntrp_index.items()):
        indexes["by_ntrp_level"][ntrp] = {
            "ntrp_level": ntrp,
            "sample_ids": sample_ids,
            "sample_count": len(sample_ids)
        }
    
    return indexes

def main():
    print("="*60)
    print("📚 建立问题池索引（主池 + 辅助索引）")
    print("="*60)
    print()
    
    # 加载样本登记表
    with open(SAMPLE_REGISTRY_PATH, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    print(f"📋 当前样本总数：{len(registry)} 个")
    print()
    
    # 建立主问题池
    print("🔍 建立 5 个主问题池...")
    print()
    
    problem_pools = build_problem_pools(registry)
    
    for pool_key, pool in problem_pools.items():
        config = PROBLEM_POOLS_CONFIG[pool_key]
        print(f"   {pool['name']} ({pool_key})")
        print(f"      阶段：{pool['phase']}")
        print(f"      样本数：{pool['sample_count']} 个")
        if pool_key != "standard_demos":
            print(f"      主要问题：{', '.join(config['primary_issue_keys'][:3])}...")
        print()
    
    # 建立辅助索引
    print("🔍 建立 3 个辅助索引...")
    print()
    
    secondary_indexes = build_secondary_indexes(registry)
    
    # by_secondary_issue
    print(f"   by_secondary_issue ({len(secondary_indexes['by_secondary_issue'])} 个次要问题)")
    for issue, data in list(secondary_indexes['by_secondary_issue'].items())[:5]:
        print(f"      {issue}: {data['sample_count']} 个")
    print()
    
    # by_phase_weakness
    print(f"   by_phase_weakness ({len(secondary_indexes['by_phase_weakness'])} 个阶段)")
    for phase, data in secondary_indexes['by_phase_weakness'].items():
        print(f"      {data['phase_name']}: {data['sample_count']} 个")
    print()
    
    # by_ntrp_level
    print(f"   by_ntrp_level ({len(secondary_indexes['by_ntrp_level'])} 个等级)")
    for ntrp, data in sorted(secondary_indexes['by_ntrp_level'].items()):
        print(f"      NTRP {ntrp}: {data['sample_count']} 个")
    print()
    
    # 构建完整索引结构
    problem_index = {
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "created_by": "system_auto_index",
        "total_samples": len(registry),
        "problem_pools": problem_pools,
        "secondary_indexes": secondary_indexes
    }
    
    # 保存索引
    with open(PROBLEM_INDEX_PATH, 'w', encoding='utf-8') as f:
        json.dump(problem_index, f, ensure_ascii=False, indent=2)
    
    print("="*60)
    print("📊 索引建立完成统计")
    print("="*60)
    print()
    print(f"   主问题池：5 个")
    print(f"   辅助索引：3 个")
    print(f"   总样本数：{len(registry)} 个")
    print()
    
    # 统计主池分布
    print("📈 主问题池样本分布:")
    for pool_key, pool in problem_pools.items():
        print(f"   {pool['name']:20s}: {pool['sample_count']:3d} 个")
    print()
    
    # 验证样本不重复（一个样本只能有一个主池）
    all_sample_ids = []
    for pool_key, pool in problem_pools.items():
        if pool_key != "standard_demos":  # 标准示范库可以和其他池重叠
            all_sample_ids.extend(pool["sample_ids"])
    
    unique_count = len(set(all_sample_ids))
    total_count = len(all_sample_ids)
    
    if unique_count == total_count:
        print("✅ 验证通过：问题池样本无重复（一个样本一个主池）")
    else:
        print(f"⚠️  验证警告：发现 {total_count - unique_count} 个重复样本")
    
    print()
    print(f"💾 已保存到：{PROBLEM_INDEX_PATH}")
    print()
    print("="*60)
    print("✅ 问题池索引建立完成！")
    print("="*60)
    print()
    print("下一步:")
    print("   1. 查看完整索引结构")
    print("   2. 使用索引进行知识库检索")
    print("   3. 使用索引进行黄金标准对比")
    print("   4. 使用索引生成训练建议")
    print()

if __name__ == '__main__':
    main()
