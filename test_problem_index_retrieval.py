#!/usr/bin/env python3
"""
测试问题池索引检索功能
验证：
1. primary_issue 是否能命中对应主问题池
2. secondary_issue 是否能通过辅助索引召回
3. standard_demos 是否能被标准对照检索命中
4. phase_weakness 和 NTRP 索引是否工作正常
"""

import json

PROBLEM_INDEX_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/problem_index.json'
SAMPLE_REGISTRY_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/sample_registry.json'

def load_index():
    """加载问题池索引"""
    with open(PROBLEM_INDEX_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_registry():
    """加载样本登记表"""
    with open(SAMPLE_REGISTRY_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_primary_issue_retrieval(index, registry):
    """测试 1: primary_issue 是否能命中对应主问题池"""
    
    print("="*60)
    print("📍 测试 1: primary_issue 命中主问题池")
    print("="*60)
    print()
    
    # 测试用例
    test_cases = [
        ("toss_inconsistent", "toss_issues", "抛球问题库"),
        ("knee_bend_insufficient", "loading_issues", "蓄力问题库"),
        ("rotation_insufficient", "loading_issues", "蓄力问题库"),
        ("contact_point_late", "contact_issues", "击球点问题库"),
    ]
    
    all_passed = True
    
    for primary_issue, expected_pool, pool_name in test_cases:
        # 查找样本
        samples_with_issue = [s for s in registry if s.get('primary_issue') == primary_issue]
        
        # 检查是否在对应问题池中
        pool_sample_ids = index['problem_pools'][expected_pool]['sample_ids']
        
        matched = 0
        not_matched = []
        
        for sample in samples_with_issue:
            sample_id = sample.get('sample_id')
            if sample_id in pool_sample_ids:
                matched += 1
            else:
                not_matched.append(sample_id)
        
        total = len(samples_with_issue)
        
        if matched == total and total > 0:
            print(f"   ✅ {primary_issue}")
            print(f"      样本数：{total} 个")
            print(f"      命中池：{pool_name} ({expected_pool})")
            print(f"      命中率：{matched}/{total} = 100%")
        elif total == 0:
            print(f"   ⚠️  {primary_issue}")
            print(f"      样本数：0 个（无此问题的样本）")
        else:
            print(f"   ❌ {primary_issue}")
            print(f"      样本数：{total} 个")
            print(f"      命中：{matched}/{total}")
            print(f"      未命中：{not_matched}")
            all_passed = False
        
        print()
    
    if all_passed:
        print("✅ 测试 1 通过：所有 primary_issue 都能正确命中主问题池")
    else:
        print("❌ 测试 1 失败：存在 primary_issue 未命中问题池")
    
    print()
    return all_passed

def test_secondary_issue_retrieval(index, registry):
    """测试 2: secondary_issue 是否能通过辅助索引召回"""
    
    print("="*60)
    print("📍 测试 2: secondary_issue 辅助索引召回")
    print("="*60)
    print()
    
    # 测试用例
    test_cases = [
        "contact_point_late",
        "knee_bend_insufficient",
        "rotation_insufficient",
        "toss_inconsistent",
    ]
    
    all_passed = True
    
    for secondary_issue in test_cases:
        # 从辅助索引查找
        if secondary_issue in index['secondary_indexes']['by_secondary_issue']:
            index_data = index['secondary_indexes']['by_secondary_issue'][secondary_issue]
            index_count = index_data['sample_count']
            index_sample_ids = index_data['sample_ids']
        else:
            index_count = 0
            index_sample_ids = []
        
        # 从 registry 直接查找
        samples_with_secondary = [s for s in registry if s.get('secondary_issue') == secondary_issue]
        actual_count = len(samples_with_secondary)
        
        if index_count == actual_count:
            print(f"   ✅ {secondary_issue}")
            print(f"      索引样本数：{index_count} 个")
            print(f"      实际样本数：{actual_count} 个")
            print(f"      匹配：一致")
        else:
            print(f"   ❌ {secondary_issue}")
            print(f"      索引样本数：{index_count} 个")
            print(f"      实际样本数：{actual_count} 个")
            print(f"      匹配：不一致")
            all_passed = False
        
        print()
    
    if all_passed:
        print("✅ 测试 2 通过：所有 secondary_issue 辅助索引准确")
    else:
        print("❌ 测试 2 失败：存在 secondary_issue 索引不准确")
    
    print()
    return all_passed

def test_standard_demos_retrieval(index, registry):
    """测试 3: standard_demos 是否能被标准对照检索命中"""
    
    print("="*60)
    print("📍 测试 3: standard_demos 标准对照检索")
    print("="*60)
    print()
    
    # 从索引获取标准示范库
    standard_pool = index['problem_pools']['standard_demos']
    index_sample_ids = standard_pool['sample_ids']
    index_count = standard_pool['sample_count']
    
    # 从 registry 直接查找符合条件的样本
    standard_samples = [s for s in registry 
                       if s.get('sample_category') == 'excellent_demo'
                       and s.get('ntrp_level') in ['4.5', '5.0', '5.0+']
                       and s.get('quality_grade') == 'A']
    actual_count = len(standard_samples)
    actual_sample_ids = [s.get('sample_id') for s in standard_samples]
    
    # 比较
    index_set = set(index_sample_ids)
    actual_set = set(actual_sample_ids)
    
    missing_in_index = actual_set - index_set
    extra_in_index = index_set - actual_set
    
    print(f"   索引样本数：{index_count} 个")
    print(f"   实际样本数：{actual_count} 个")
    print()
    
    if index_count == actual_count and not missing_in_index and not extra_in_index:
        print("   ✅ standard_demos 索引准确")
        print(f"      样本数：{index_count} 个")
        print(f"      匹配：完全一致")
        print()
        print("✅ 测试 3 通过：standard_demos 索引准确")
        return True
    else:
        print("   ❌ standard_demos 索引存在差异")
        if missing_in_index:
            print(f"      索引缺失：{len(missing_in_index)} 个")
        if extra_in_index:
            print(f"      索引多余：{len(extra_in_index)} 个")
        print()
        print("❌ 测试 3 失败：standard_demos 索引不准确")
        return False

def test_phase_weakness_index(index, registry):
    """测试 4: phase_weakness 索引是否工作正常"""
    
    print("="*60)
    print("📍 测试 4: phase_weakness 阶段弱点索引")
    print("="*60)
    print()
    
    # 测试各阶段
    test_phases = ['toss', 'loading', 'contact', 'follow_through']
    
    all_passed = True
    
    for phase in test_phases:
        # 从索引获取
        if phase in index['secondary_indexes']['by_phase_weakness']:
            index_data = index['secondary_indexes']['by_phase_weakness'][phase]
            index_count = index_data['sample_count']
            index_sample_ids = set(index_data['sample_ids'])
        else:
            index_count = 0
            index_sample_ids = set()
        
        # 从 registry 直接查找
        samples_with_weakness = [s for s in registry 
                                if phase in s.get('action_phase_weaknesses', [])]
        actual_count = len(samples_with_weakness)
        actual_sample_ids = set(s.get('sample_id') for s in samples_with_weakness)
        
        if index_count == actual_count and index_sample_ids == actual_sample_ids:
            phase_names = {
                'toss': '抛球阶段',
                'loading': '蓄力阶段',
                'contact': '击球阶段',
                'follow_through': '随挥阶段',
            }
            print(f"   ✅ {phase_names.get(phase, phase)} ({phase})")
            print(f"      索引样本数：{index_count} 个")
            print(f"      实际样本数：{actual_count} 个")
            print(f"      匹配：一致")
        else:
            print(f"   ❌ {phase}")
            print(f"      索引样本数：{index_count} 个")
            print(f"      实际样本数：{actual_count} 个")
            print(f"      匹配：不一致")
            all_passed = False
        
        print()
    
    if all_passed:
        print("✅ 测试 4 通过：phase_weakness 索引准确")
    else:
        print("❌ 测试 4 失败：phase_weakness 索引不准确")
    
    print()
    return all_passed

def test_ntrp_level_index(index, registry):
    """测试 5: NTRP 等级索引是否工作正常"""
    
    print("="*60)
    print("📍 测试 5: NTRP 等级索引")
    print("="*60)
    print()
    
    # 测试各等级
    all_passed = True
    
    for ntrp, index_data in index['secondary_indexes']['by_ntrp_level'].items():
        index_count = index_data['sample_count']
        index_sample_ids = set(index_data['sample_ids'])
        
        # 从 registry 直接查找
        # 注意：unknown 等级包括没有 ntrp_level 字段的样本
        if ntrp == 'unknown':
            samples_with_ntrp = [s for s in registry 
                                if 'ntrp_level' not in s or s.get('ntrp_level') is None]
        else:
            samples_with_ntrp = [s for s in registry if s.get('ntrp_level') == ntrp]
        
        actual_count = len(samples_with_ntrp)
        actual_sample_ids = set(s.get('sample_id') for s in samples_with_ntrp)
        
        if index_count == actual_count and index_sample_ids == actual_sample_ids:
            print(f"   ✅ NTRP {ntrp}")
            print(f"      索引样本数：{index_count} 个")
            print(f"      实际样本数：{actual_count} 个")
            print(f"      匹配：一致")
        else:
            print(f"   ❌ NTRP {ntrp}")
            print(f"      索引样本数：{index_count} 个")
            print(f"      实际样本数：{actual_count} 个")
            print(f"      匹配：不一致")
            all_passed = False
        
        print()
    
    if all_passed:
        print("✅ 测试 5 通过：NTRP 等级索引准确")
    else:
        print("❌ 测试 5 失败：NTRP 等级索引不准确")
    
    print()
    return all_passed

def main():
    print("="*60)
    print("🧪 问题池索引检索功能测试")
    print("="*60)
    print()
    
    # 加载数据
    index = load_index()
    registry = load_registry()
    
    print(f"📋 样本总数：{len(registry)} 个")
    print(f"📚 索引版本：{index.get('version', 'unknown')}")
    print()
    
    # 运行测试
    results = []
    
    results.append(("primary_issue 命中主问题池", test_primary_issue_retrieval(index, registry)))
    results.append(("secondary_issue 辅助索引召回", test_secondary_issue_retrieval(index, registry)))
    results.append(("standard_demos 标准对照检索", test_standard_demos_retrieval(index, registry)))
    results.append(("phase_weakness 阶段弱点索引", test_phase_weakness_index(index, registry)))
    results.append(("NTRP 等级索引", test_ntrp_level_index(index, registry)))
    
    # 汇总结果
    print("="*60)
    print("📊 测试结果汇总")
    print("="*60)
    print()
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print()
    print(f"   总计：{passed} 个通过，{failed} 个失败")
    print()
    
    if failed == 0:
        print("="*60)
        print("🎉 所有测试通过！索引检索功能正常！")
        print("="*60)
        print()
        print("下一步:")
        print("   1. 接入知识库检索")
        print("   2. 接入黄金标准对比")
        print("   3. 接入报告生成")
        print()
    else:
        print("="*60)
        print("⚠️  存在测试失败，请检查索引结构！")
        print("="*60)
        print()

if __name__ == '__main__':
    main()
