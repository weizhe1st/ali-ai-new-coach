#!/usr/bin/env python3
"""
黄金标准对比接入（最小对比逻辑）
功能：
1. 根据 ntrp_level 选标准示范样本
2. 根据 primary_issue 和 action_phase_weaknesses 做阶段差异对照
3. 输出结构化差异结果给报告层
"""

import json
from typing import Dict, List, Optional

PROBLEM_INDEX_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/problem_index.json'
SAMPLE_REGISTRY_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/sample_registry.json'

# 黄金标准阶段要求（简化版）
GOLDEN_STANDARDS = {
    'ready': {
        'name': '准备阶段',
        'requirements': [
            '双脚与肩同宽',
            '身体重心稳定',
            '拍头自然下垂',
            '目光注视前方'
        ],
        'key_points': ['stance', 'balance', 'focus']
    },
    'toss': {
        'name': '抛球阶段',
        'requirements': [
            '抛球手臂伸直',
            '抛球高度稳定',
            '抛球位置在身体正前方',
            '抛球动作流畅'
        ],
        'key_points': ['arm_extension', 'height_consistency', 'position', 'fluidity']
    },
    'loading': {
        'name': '蓄力阶段',
        'requirements': [
            '膝盖充分弯曲',
            '髋部充分旋转',
            '肩部充分转动',
            '重心后移'
        ],
        'key_points': ['knee_bend', 'hip_rotation', 'shoulder_rotation', 'weight_transfer']
    },
    'contact': {
        'name': '击球阶段',
        'requirements': [
            '击球点准确',
            '拍面控制良好',
            '手臂充分伸展',
            '身体向上发力'
        ],
        'key_points': ['contact_point', 'racket_face', 'arm_extension', 'upward_power']
    },
    'follow_through': {
        'name': '随挥阶段',
        'requirements': [
            '随挥动作完整',
            '随挥方向正确',
            '身体向前移动',
            '重心完全转移'
        ],
        'key_points': ['follow_through_complete', 'direction', 'forward_movement', 'weight_transfer']
    }
}

# 问题到阶段的影响映射
ISSUE_PHASE_IMPACT = {
    'toss_inconsistent': {
        'affected_phases': ['toss', 'contact'],
        'impact': '抛球不稳定导致击球点不准确'
    },
    'knee_bend_insufficient': {
        'affected_phases': ['loading', 'contact'],
        'impact': '膝盖蓄力不足导致发力不充分'
    },
    'rotation_insufficient': {
        'affected_phases': ['loading', 'contact'],
        'impact': '转体不充分导致力量传递不足'
    },
    'contact_point_late': {
        'affected_phases': ['contact', 'follow_through'],
        'impact': '击球点偏晚导致发力时机错误'
    },
}


class GoldenStandardComparator:
    """黄金标准对比器"""
    
    def __init__(self, index_path: str = PROBLEM_INDEX_PATH, 
                 registry_path: str = SAMPLE_REGISTRY_PATH):
        # 加载索引
        with open(index_path, 'r', encoding='utf-8') as f:
            self.index = json.load(f)
        
        # 加载样本登记表
        with open(registry_path, 'r', encoding='utf-8') as f:
            self.registry = json.load(f)
        
        # 构建 sample_id 到 sample 的映射
        self.sample_map = {s.get('sample_id'): s for s in self.registry}
        
        # 提取标准示范样本
        self.standard_samples = [
            s for s in self.registry 
            if s.get('sample_category') == 'excellent_demo'
            and s.get('ntrp_level') in ['4.5', '5.0', '5.0+']
            and s.get('quality_grade') == 'A'
        ]
    
    def select_golden_standard(self, ntrp_level: str, limit: int = 3) -> Dict:
        """
        根据 NTRP 等级选择黄金标准样本
        
        Args:
            ntrp_level: 用户 NTRP 等级
            limit: 返回样本数量限制
        
        Returns:
            黄金标准样本选择结果
        """
        result = {
            'success': False,
            'user_ntrp_level': ntrp_level,
            'selected_samples': [],
            'sample_count': 0,
            'message': ''
        }
        
        # 从标准示范库中选择
        standard_pool = self.index['problem_pools'].get('standard_demos', {})
        standard_ids = standard_pool.get('sample_ids', [])
        
        if not standard_ids:
            result['message'] = '标准示范库为空'
            return result
        
        # 优先选择 NTRP 等级相近的标准样本
        # 策略：选择相同或略高等级的标准样本作为参考
        target_ntrps = [ntrp_level]
        
        # 尝试获取略高等级的样本
        ntrp_order = ['2.5', '3.0', '3.5', '4.0', '4.5', '5.0', '5.0+']
        try:
            current_idx = ntrp_order.index(ntrp_level)
            if current_idx < len(ntrp_order) - 1:
                target_ntrps.append(ntrp_order[current_idx + 1])
        except ValueError:
            pass
        
        # 选择样本
        selected = []
        for sample_id in standard_ids:
            if sample_id in self.sample_map:
                sample = self.sample_map[sample_id]
                sample_ntrp = sample.get('ntrp_level', '')
                
                if sample_ntrp in target_ntrps:
                    selected.append(sample)
                    if len(selected) >= limit:
                        break
        
        # 如果没找到，就随机选几个
        if not selected:
            selected = [
                self.sample_map[sid] 
                for sid in standard_ids[:limit] 
                if sid in self.sample_map
            ]
        
        result['success'] = len(selected) > 0
        result['selected_samples'] = selected
        result['sample_count'] = len(selected)
        result['message'] = f'已选择 {len(selected)} 个黄金标准样本'
        
        return result
    
    def compare_phase(self, user_sample: Dict, golden_sample: Dict, phase: str) -> Dict:
        """
        对比用户样本与黄金标准在某个阶段的差异
        
        Args:
            user_sample: 用户样本
            golden_sample: 黄金标准样本
            phase: 阶段名称
        
        Returns:
            阶段差异对比结果
        """
        result = {
            'phase': phase,
            'phase_name': GOLDEN_STANDARDS.get(phase, {}).get('name', phase),
            'golden_requirements': GOLDEN_STANDARDS.get(phase, {}).get('requirements', []),
            'user_performance': 'unknown',
            'has_issue': False,
            'issues': [],
            'suggestions': []
        }
        
        # 获取用户样本的问题标签
        user_weaknesses = user_sample.get('action_phase_weaknesses', [])
        user_primary_issue = user_sample.get('primary_issue')
        user_secondary_issue = user_sample.get('secondary_issue')
        
        # 判断该阶段是否有问题
        if phase in user_weaknesses:
            result['has_issue'] = True
            result['user_performance'] = '需要改进'
            
            # 找出具体问题
            if user_primary_issue:
                result['issues'].append(f'主要问题：{user_primary_issue}')
            if user_secondary_issue:
                result['issues'].append(f'次要问题：{user_secondary_issue}')
            
            # 生成建议
            if phase == 'toss' and user_primary_issue == 'toss_inconsistent':
                result['suggestions'].append('练习抛球稳定性，确保抛球高度一致')
                result['suggestions'].append('抛球手臂应充分伸直')
            elif phase == 'loading' and user_primary_issue in ['knee_bend_insufficient', 'rotation_insufficient']:
                result['suggestions'].append('加强膝盖蓄力训练')
                result['suggestions'].append('确保转体充分')
            elif phase == 'contact' and user_secondary_issue == 'contact_point_late':
                result['suggestions'].append('调整击球时机')
                result['suggestions'].append('确保击球点在身体前方')
        else:
            result['user_performance'] = '良好'
            result['suggestions'].append('保持当前动作')
        
        return result
    
    def compare_comprehensive(self, user_sample_id: str, 
                             golden_sample_ids: Optional[List[str]] = None,
                             ntrp_level: Optional[str] = None) -> Dict:
        """
        综合对比用户样本与黄金标准
        
        Args:
            user_sample_id: 用户样本 ID
            golden_sample_ids: 黄金标准样本 ID 列表（可选）
            ntrp_level: 用户 NTRP 等级（用于自动选择黄金标准）
        
        Returns:
            综合对比结果
        """
        result = {
            'success': False,
            'user_sample_id': user_sample_id,
            'user_sample': None,
            'golden_samples': [],
            'phase_comparisons': [],
            'overall_gap': '',
            'priority_improvements': [],
            'message': ''
        }
        
        # 获取用户样本
        if user_sample_id not in self.sample_map:
            result['message'] = f'未找到用户样本：{user_sample_id}'
            return result
        
        user_sample = self.sample_map[user_sample_id]
        result['user_sample'] = user_sample
        
        # 选择黄金标准
        if golden_sample_ids:
            golden_samples = [
                self.sample_map[sid] 
                for sid in golden_sample_ids 
                if sid in self.sample_map
            ]
        elif ntrp_level:
            selection_result = self.select_golden_standard(ntrp_level, limit=2)
            golden_samples = selection_result.get('selected_samples', [])
        else:
            # 默认选择前 2 个标准样本
            golden_samples = self.standard_samples[:2]
        
        result['golden_samples'] = golden_samples
        
        # 获取用户样本的问题阶段
        user_weaknesses = user_sample.get('action_phase_weaknesses', [])
        user_primary_issue = user_sample.get('primary_issue')
        
        # 逐阶段对比
        phases_to_compare = user_weaknesses if user_weaknesses else ['toss', 'loading', 'contact', 'follow_through']
        
        for phase in phases_to_compare:
            if golden_samples:
                comparison = self.compare_phase(user_sample, golden_samples[0], phase)
                result['phase_comparisons'].append(comparison)
        
        # 生成总体差距描述
        if user_primary_issue:
            impact = ISSUE_PHASE_IMPACT.get(user_primary_issue, {})
            result['overall_gap'] = impact.get('impact', f'存在 {user_primary_issue} 问题')
        else:
            result['overall_gap'] = '动作基本规范'
        
        # 生成优先改进建议
        if user_primary_issue:
            result['priority_improvements'].append(f'优先解决：{user_primary_issue}')
        
        if user_weaknesses:
            for weakness in user_weaknesses[:2]:
                phase_name = GOLDEN_STANDARDS.get(weakness, {}).get('name', weakness)
                result['priority_improvements'].append(f'改进 {phase_name} 阶段')
        
        result['success'] = True
        result['message'] = f'对比完成，共分析 {len(result["phase_comparisons"])} 个阶段'
        
        return result


def main():
    print("="*60)
    print("📊 黄金标准对比接入测试（最小对比逻辑）")
    print("="*60)
    print()
    
    # 创建对比器
    comparator = GoldenStandardComparator()
    
    print(f"📋 样本总数：{len(comparator.registry)}")
    print(f"⭐ 标准示范样本：{len(comparator.standard_samples)} 个")
    print()
    
    # 测试用例
    test_cases = [
        {
            'name': '测试 1: 选择黄金标准样本（NTRP 3.0）',
            'type': 'select',
            'params': {'ntrp_level': '3.0', 'limit': 3},
        },
        {
            'name': '测试 2: 阶段差异对比',
            'type': 'phase_compare',
            'params': {
                'user_sample_id': 'batch001_video001',
                'golden_sample_id': None,
                'phase': 'toss'
            },
        },
        {
            'name': '测试 3: 综合对比（有问题的样本）',
            'type': 'comprehensive',
            'params': {
                'user_sample_id': 'batch001_video001',
                'ntrp_level': '2.5'
            },
        },
        {
            'name': '测试 4: 综合对比（蓄力问题）',
            'type': 'comprehensive',
            'params': {
                'user_sample_id': 'batch001_video004',
                'ntrp_level': '3.0'
            },
        },
    ]
    
    for test_case in test_cases:
        print("="*60)
        print(f"🧪 {test_case['name']}")
        print("="*60)
        print()
        
        if test_case['type'] == 'select':
            result = comparator.select_golden_standard(**test_case['params'])
            
            print(f"   选择成功：{'✅ 是' if result['success'] else '❌ 否'}")
            print(f"   消息：{result['message']}")
            print(f"   用户 NTRP: {result['user_ntrp_level']}")
            print(f"   选择样本数：{result['sample_count']} 个")
            print()
            
            if result['selected_samples']:
                print(f"   黄金标准样本:")
                for i, sample in enumerate(result['selected_samples'][:3], 1):
                    ntrp = sample.get('ntrp_level', 'N/A')
                    sample_id = sample.get('sample_id', 'N/A')
                    print(f"      {i}. {sample_id} (NTRP {ntrp})")
            print()
        
        elif test_case['type'] == 'phase_compare':
            user_id = test_case['params']['user_sample_id']
            phase = test_case['params']['phase']
            
            if user_id not in comparator.sample_map:
                print(f"   ❌ 未找到样本：{user_id}")
                continue
            
            user_sample = comparator.sample_map[user_id]
            golden_sample = comparator.standard_samples[0] if comparator.standard_samples else None
            
            if not golden_sample:
                print(f"   ❌ 无标准示范样本")
                continue
            
            result = comparator.compare_phase(user_sample, golden_sample, phase)
            
            print(f"   阶段：{result['phase_name']} ({result['phase']})")
            print(f"   用户表现：{result['user_performance']}")
            print(f"   存在问题：{'是' if result['has_issue'] else '否'}")
            print()
            
            if result['issues']:
                print(f"   具体问题:")
                for issue in result['issues']:
                    print(f"      - {issue}")
                print()
            
            if result['suggestions']:
                print(f"   改进建议:")
                for suggestion in result['suggestions']:
                    print(f"      - {suggestion}")
                print()
        
        elif test_case['type'] == 'comprehensive':
            result = comparator.compare_comprehensive(**test_case['params'])
            
            print(f"   对比成功：{'✅ 是' if result['success'] else '❌ 否'}")
            print(f"   消息：{result['message']}")
            print()
            
            if result['user_sample']:
                user = result['user_sample']
                print(f"   用户样本:")
                print(f"      ID: {user.get('sample_id', 'N/A')}")
                print(f"      NTRP: {user.get('ntrp_level', 'N/A')}")
                print(f"      主要问题：{user.get('primary_issue', 'N/A') or '无'}")
                print(f"      次要问题：{user.get('secondary_issue', 'N/A') or '无'}")
                print(f"      问题阶段：{', '.join(user.get('action_phase_weaknesses', [])) or '无'}")
                print()
            
            if result['golden_samples']:
                print(f"   黄金标准样本 ({len(result['golden_samples'])} 个):")
                for i, golden in enumerate(result['golden_samples'][:2], 1):
                    print(f"      {i}. {golden.get('sample_id', 'N/A')} (NTRP {golden.get('ntrp_level', 'N/A')})")
                print()
            
            if result['phase_comparisons']:
                print(f"   阶段对比 ({len(result['phase_comparisons'])} 个阶段):")
                for comp in result['phase_comparisons']:
                    status = '⚠️  需改进' if comp['has_issue'] else '✅ 良好'
                    print(f"      {comp['phase_name']}: {status}")
                print()
            
            if result['overall_gap']:
                print(f"   总体差距：{result['overall_gap']}")
                print()
            
            if result['priority_improvements']:
                print(f"   优先改进:")
                for improvement in result['priority_improvements']:
                    print(f"      - {improvement}")
                print()
    
    print("="*60)
    print("✅ 黄金标准对比接入测试完成！")
    print("="*60)
    print()
    print("下一步:")
    print("   1. 接入报告生成（问题检索 + 标准对比 → 报告）")
    print()


if __name__ == '__main__':
    main()
