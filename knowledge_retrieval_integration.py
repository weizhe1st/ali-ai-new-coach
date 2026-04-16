#!/usr/bin/env python3
"""
知识库检索接入（最小接入逻辑）
功能：
1. primary_issue 命中主问题池
2. secondary_issue 命中辅助索引
3. phase_weakness 补充阶段知识点
4. ntrp_level 过滤参考样本
"""

import json
from typing import Dict, List, Optional

PROBLEM_INDEX_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/problem_index.json'
SAMPLE_REGISTRY_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/sample_registry.json'

# 问题到知识点的映射（简化版）
ISSUE_TO_KNOWLEDGE = {
    # 抛球问题
    'toss_inconsistent': {
        'phase': 'toss',
        'knowledge_keys': ['抛球稳定性', '抛球高度控制', '抛球位置'],
        'priority': 'high',
        'downstream_effects': ['contact_point_late', 'contact_point_low']
    },
    'toss_height_low': {
        'phase': 'toss',
        'knowledge_keys': ['抛球高度', '抛球时机'],
        'priority': 'medium'
    },
    'toss_position_front': {
        'phase': 'toss',
        'knowledge_keys': ['抛球位置', '抛球前置问题'],
        'priority': 'medium'
    },
    
    # 蓄力问题
    'knee_bend_insufficient': {
        'phase': 'loading',
        'knowledge_keys': ['膝盖蓄力', '下肢发力', '屈膝角度'],
        'priority': 'high',
        'downstream_effects': ['power_loss']
    },
    'rotation_insufficient': {
        'phase': 'loading',
        'knowledge_keys': ['转体充分性', '髋部旋转', '肩部旋转'],
        'priority': 'high',
        'downstream_effects': ['power_loss', 'contact_point_late']
    },
    
    # 击球点问题
    'contact_point_late': {
        'phase': 'contact',
        'knowledge_keys': ['击球时机', '击球点位置'],
        'priority': 'medium',
        'is_downstream': True  # 通常是结果性问题
    },
    'contact_point_low': {
        'phase': 'contact',
        'knowledge_keys': ['击球点高度', '击球点前置'],
        'priority': 'medium',
        'is_downstream': True
    },
    
    # 随挥问题
    'follow_through_insufficient': {
        'phase': 'follow_through',
        'knowledge_keys': ['随挥完整性', '随挥方向'],
        'priority': 'low'
    },
}

class KnowledgeRetriever:
    """知识库检索器"""
    
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
    
    def retrieve_by_primary_issue(self, primary_issue: str) -> Dict:
        """
        根据 primary_issue 检索主问题池
        
        Args:
            primary_issue: 主要问题标签
        
        Returns:
            检索结果字典
        """
        result = {
            'success': False,
            'primary_issue': primary_issue,
            'matched_pool': None,
            'sample_ids': [],
            'sample_count': 0,
            'knowledge_keys': [],
            'phase': None,
            'priority': None,
            'message': ''
        }
        
        # 获取知识点配置中的 phase
        if primary_issue not in ISSUE_TO_KNOWLEDGE:
            result['message'] = f"未知的问题标签：{primary_issue}"
            return result
        
        knowledge = ISSUE_TO_KNOWLEDGE[primary_issue]
        expected_phase = knowledge.get('phase')
        
        result['knowledge_keys'] = knowledge.get('knowledge_keys', [])
        result['priority'] = knowledge.get('priority', 'medium')
        result['phase'] = expected_phase
        
        # 根据 phase 查找对应的问题池
        for pool_key, pool_data in self.index['problem_pools'].items():
            if pool_key == 'standard_demos':
                continue  # 跳过标准示范库
            
            if pool_data.get('phase') == expected_phase:
                result['success'] = True
                result['matched_pool'] = pool_key
                result['sample_ids'] = pool_data['sample_ids']
                result['sample_count'] = pool_data['sample_count']
                result['message'] = f"命中主问题池：{pool_data['name']}"
                break
        
        if not result['success']:
            result['message'] = f"未找到对应主问题池：{primary_issue}"
        
        return result
    
    def retrieve_by_secondary_issue(self, secondary_issue: str) -> Dict:
        """
        根据 secondary_issue 检索辅助索引
        
        Args:
            secondary_issue: 次要问题标签
        
        Returns:
            检索结果字典
        """
        result = {
            'success': False,
            'secondary_issue': secondary_issue,
            'sample_ids': [],
            'sample_count': 0,
            'message': ''
        }
        
        # 从辅助索引查找
        if secondary_issue in self.index['secondary_indexes']['by_secondary_issue']:
            index_data = self.index['secondary_indexes']['by_secondary_issue'][secondary_issue]
            result['success'] = True
            result['sample_ids'] = index_data['sample_ids']
            result['sample_count'] = index_data['sample_count']
            result['message'] = f"命中辅助索引：secondary_issue={secondary_issue}"
        else:
            result['message'] = f"未在辅助索引中找到：{secondary_issue}"
        
        return result
    
    def retrieve_by_phase_weakness(self, phase: str) -> Dict:
        """
        根据 phase_weakness 检索辅助索引
        
        Args:
            phase: 阶段名称 (toss/loading/contact/follow_through)
        
        Returns:
            检索结果字典
        """
        result = {
            'success': False,
            'phase': phase,
            'sample_ids': [],
            'sample_count': 0,
            'phase_name': '',
            'message': ''
        }
        
        # 从辅助索引查找
        if phase in self.index['secondary_indexes']['by_phase_weakness']:
            index_data = self.index['secondary_indexes']['by_phase_weakness'][phase]
            result['success'] = True
            result['sample_ids'] = index_data['sample_ids']
            result['sample_count'] = index_data['sample_count']
            result['phase_name'] = index_data.get('phase_name', phase)
            result['message'] = f"命中阶段弱点索引：{result['phase_name']}"
        else:
            result['message'] = f"未在阶段弱点索引中找到：{phase}"
        
        return result
    
    def retrieve_by_ntrp_level(self, ntrp_level: str, limit: int = 10) -> Dict:
        """
        根据 NTRP 等级过滤参考样本
        
        Args:
            ntrp_level: NTRP 等级
            limit: 返回样本数量限制
        
        Returns:
            检索结果字典
        """
        result = {
            'success': False,
            'ntrp_level': ntrp_level,
            'sample_ids': [],
            'sample_count': 0,
            'limit': limit,
            'message': ''
        }
        
        # 从辅助索引查找
        if ntrp_level in self.index['secondary_indexes']['by_ntrp_level']:
            index_data = self.index['secondary_indexes']['by_ntrp_level'][ntrp_level]
            result['success'] = True
            result['sample_ids'] = index_data['sample_ids'][:limit]
            result['sample_count'] = min(len(index_data['sample_ids']), limit)
            result['message'] = f"命中 NTRP 等级索引：{ntrp_level}"
        else:
            result['message'] = f"未在 NTRP 等级索引中找到：{ntrp_level}"
        
        return result
    
    def get_sample_details(self, sample_ids: List[str]) -> List[Dict]:
        """
        获取样本详细信息
        
        Args:
            sample_ids: 样本 ID 列表
        
        Returns:
            样本详细信息列表
        """
        details = []
        for sample_id in sample_ids:
            if sample_id in self.sample_map:
                details.append(self.sample_map[sample_id])
        return details
    
    def retrieve_comprehensive(self, primary_issue: Optional[str] = None,
                              secondary_issue: Optional[str] = None,
                              phase: Optional[str] = None,
                              ntrp_level: Optional[str] = None,
                              ntrp_limit: int = 10) -> Dict:
        """
        综合检索（支持多条件组合）
        
        Args:
            primary_issue: 主要问题
            secondary_issue: 次要问题
            phase: 阶段
            ntrp_level: NTRP 等级
            ntrp_limit: NTRP 样本数量限制
        
        Returns:
            综合检索结果
        """
        result = {
            'success': False,
            'primary_issue_result': None,
            'secondary_issue_result': None,
            'phase_result': None,
            'ntrp_result': None,
            'combined_sample_ids': [],
            'combined_sample_count': 0,
            'knowledge_keys': [],
            'message': ''
        }
        
        # 1. primary_issue 命中主问题池
        if primary_issue:
            result['primary_issue_result'] = self.retrieve_by_primary_issue(primary_issue)
        
        # 2. secondary_issue 命中辅助索引
        if secondary_issue:
            result['secondary_issue_result'] = self.retrieve_by_secondary_issue(secondary_issue)
        
        # 3. phase_weakness 补充阶段知识点
        if phase:
            result['phase_result'] = self.retrieve_by_phase_weakness(phase)
        
        # 4. ntrp_level 过滤参考样本
        if ntrp_level:
            result['ntrp_result'] = self.retrieve_by_ntrp_level(ntrp_level, limit=ntrp_limit)
        
        # 合并样本 ID（去重）
        all_sample_ids = set()
        has_result = False
        
        if result['primary_issue_result'] and result['primary_issue_result']['success']:
            all_sample_ids.update(result['primary_issue_result']['sample_ids'])
            has_result = True
        
        if result['secondary_issue_result'] and result['secondary_issue_result']['success']:
            all_sample_ids.update(result['secondary_issue_result']['sample_ids'])
            has_result = True
        
        if result['phase_result'] and result['phase_result']['success']:
            all_sample_ids.update(result['phase_result']['sample_ids'])
            has_result = True
        
        # NTRP 检索不决定成功与否，只是过滤
        if result['ntrp_result'] and result['ntrp_result']['success']:
            has_result = True
        
        result['combined_sample_ids'] = list(all_sample_ids)
        result['combined_sample_count'] = len(all_sample_ids)
        result['success'] = has_result
        
        # 收集知识点
        if primary_issue and primary_issue in ISSUE_TO_KNOWLEDGE:
            result['knowledge_keys'] = ISSUE_TO_KNOWLEDGE[primary_issue].get('knowledge_keys', [])
        
        if result['success']:
            result['message'] = f"检索成功，共找到 {result['combined_sample_count']} 个样本"
        else:
            result['message'] = "未找到匹配的样本"
        
        return result


def main():
    print("="*60)
    print("📚 知识库检索接入测试（最小接入逻辑）")
    print("="*60)
    print()
    
    # 创建检索器
    retriever = KnowledgeRetriever()
    
    print("📋 样本总数:", len(retriever.registry))
    print()
    
    # 测试用例
    test_cases = [
        {
            'name': '测试 1: primary_issue 检索',
            'params': {'primary_issue': 'toss_inconsistent'},
        },
        {
            'name': '测试 2: secondary_issue 检索',
            'params': {'secondary_issue': 'contact_point_late'},
        },
        {
            'name': '测试 3: phase_weakness 检索',
            'params': {'phase': 'loading'},
        },
        {
            'name': '测试 4: NTRP 等级检索',
            'params': {'ntrp_level': '3.0', 'ntrp_limit': 5},
        },
        {
            'name': '测试 5: 综合检索',
            'params': {
                'primary_issue': 'knee_bend_insufficient',
                'secondary_issue': 'contact_point_late',
                'phase': 'loading',
                'ntrp_level': '3.0',
                'ntrp_limit': 5
            },
        },
    ]
    
    for test_case in test_cases:
        print("="*60)
        print(f"🧪 {test_case['name']}")
        print("="*60)
        print()
        
        result = retriever.retrieve_comprehensive(**test_case['params'])
        
        print(f"   检索成功：{'✅ 是' if result['success'] else '❌ 否'}")
        print(f"   消息：{result['message']}")
        print()
        
        if result['primary_issue_result']:
            r = result['primary_issue_result']
            print(f"   primary_issue:")
            print(f"      命中池：{r.get('matched_pool', 'N/A')}")
            print(f"      样本数：{r.get('sample_count', 0)} 个")
            print(f"      阶段：{r.get('phase', 'N/A')}")
            print(f"      知识点：{', '.join(r.get('knowledge_keys', []))}")
            print()
        
        if result['secondary_issue_result']:
            r = result['secondary_issue_result']
            print(f"   secondary_issue:")
            print(f"      样本数：{r.get('sample_count', 0)} 个")
            print()
        
        if result['phase_result']:
            r = result['phase_result']
            print(f"   phase_weakness:")
            print(f"      阶段：{r.get('phase_name', 'N/A')}")
            print(f"      样本数：{r.get('sample_count', 0)} 个")
            print()
        
        if result['ntrp_result']:
            r = result['ntrp_result']
            print(f"   ntrp_level:")
            print(f"      等级：{r.get('ntrp_level', 'N/A')}")
            print(f"      样本数：{r.get('sample_count', 0)} 个")
            print()
        
        print(f"   合并样本数：{result.get('combined_sample_count', 0)} 个")
        print()
    
    print("="*60)
    print("✅ 知识库检索接入测试完成！")
    print("="*60)
    print()
    print("下一步:")
    print("   1. 接入黄金标准对比")
    print("   2. 接入报告生成")
    print()


if __name__ == '__main__':
    main()
