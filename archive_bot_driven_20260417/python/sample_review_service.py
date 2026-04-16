#!/usr/bin/env python3
"""
样本审核服务层

职责：
1. 读取 sample_registry
2. 修改样本记录
3. 写回 sample_registry
4. 做基本校验
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# 项目路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SAMPLE_REGISTRY_PATH = os.path.join(PROJECT_ROOT, 'data', 'sample_registry.json')


class SampleReviewService:
    """样本审核服务"""
    
    # 合法的审核状态
    VALID_REVIEW_STATUS = ['pending', 'imported_legacy', 'approved', 'rejected']
    
    # 合法的样本分类
    VALID_CATEGORIES = ['unknown', 'excellent_demo', 'typical_issue', 'boundary_case']
    
    def __init__(self, registry_path: str = SAMPLE_REGISTRY_PATH):
        self.registry_path = registry_path
    
    def load_registry(self) -> List[dict]:
        """加载样本登记表"""
        if not os.path.exists(self.registry_path):
            return []
        
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  加载样本登记表失败：{e}")
            return []
    
    def save_registry(self, records: List[dict]):
        """保存样本登记表"""
        # 确保目录存在
        os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
        
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    
    def get_sample(self, sample_id: str) -> Optional[dict]:
        """
        获取单个样本
        
        Args:
            sample_id: 样本 ID
        
        Returns:
            dict: 样本记录，不存在返回 None
        """
        records = self.load_registry()
        
        for record in records:
            if record.get('sample_id') == sample_id:
                return record
        
        return None
    
    def sample_exists(self, sample_id: str) -> bool:
        """检查样本是否存在"""
        return self.get_sample(sample_id) is not None
    
    def list_samples(self, status: str = None, action_type: str = None,
                    category: str = None, ntrp: str = None,
                    limit: int = 0) -> List[dict]:
        """
        列出样本（支持过滤）
        
        Args:
            status: 审核状态过滤
            action_type: 动作类型过滤
            category: 样本分类过滤
            ntrp: NTRP 等级过滤
            limit: 数量限制（0 表示不限制）
        
        Returns:
            List[dict]: 样本列表
        """
        records = self.load_registry()
        
        # 过滤
        if status:
            records = [r for r in records if r.get('golden_review_status') == status]
        
        if action_type:
            records = [r for r in records if r.get('action_type') == action_type]
        
        if category:
            records = [r for r in records if r.get('sample_category') == category]
        
        if ntrp:
            # 支持多种 NTRP 字段位置
            records = [r for r in records if 
                      r.get('ntrp_level') == ntrp or 
                      r.get('analysis_summary', {}).get('ntrp_level') == ntrp]
        
        # 限制数量
        if limit > 0:
            records = records[:limit]
        
        return records
    
    def approve_sample(self, sample_id: str, reviewer: str, note: str = '') -> Dict[str, Any]:
        """
        审核通过样本
        
        Args:
            sample_id: 样本 ID
            reviewer: 审核人
            note: 审核备注
        
        Returns:
            dict: 操作结果
        """
        # 校验
        if not sample_id:
            return {'success': False, 'error': 'sample_id 不能为空'}
        
        if not reviewer:
            return {'success': False, 'error': 'reviewer 不能为空'}
        
        records = self.load_registry()
        
        # 查找样本
        found = False
        for i, record in enumerate(records):
            if record.get('sample_id') == sample_id:
                # 更新审核状态
                records[i]['golden_review_status'] = 'approved'
                records[i]['golden_review_note'] = note
                records[i]['reviewer'] = reviewer
                records[i]['reviewed_at'] = datetime.now().isoformat()
                found = True
                break
        
        if not found:
            return {'success': False, 'error': f'样本不存在：{sample_id}'}
        
        # 保存
        self.save_registry(records)
        
        return {
            'success': True,
            'sample_id': sample_id,
            'review_status': 'approved',
            'reviewer': reviewer,
            'reviewed_at': records[0].get('reviewed_at'),
            'note': note
        }
    
    def reject_sample(self, sample_id: str, reviewer: str, note: str = '') -> Dict[str, Any]:
        """
        审核拒绝样本
        
        Args:
            sample_id: 样本 ID
            reviewer: 审核人
            note: 审核备注
        
        Returns:
            dict: 操作结果
        """
        # 校验
        if not sample_id:
            return {'success': False, 'error': 'sample_id 不能为空'}
        
        if not reviewer:
            return {'success': False, 'error': 'reviewer 不能为空'}
        
        records = self.load_registry()
        
        # 查找样本
        found = False
        for i, record in enumerate(records):
            if record.get('sample_id') == sample_id:
                # 更新审核状态
                records[i]['golden_review_status'] = 'rejected'
                records[i]['golden_review_note'] = note
                records[i]['reviewer'] = reviewer
                records[i]['reviewed_at'] = datetime.now().isoformat()
                found = True
                break
        
        if not found:
            return {'success': False, 'error': f'样本不存在：{sample_id}'}
        
        # 保存
        self.save_registry(records)
        
        return {
            'success': True,
            'sample_id': sample_id,
            'review_status': 'rejected',
            'reviewer': reviewer,
            'reviewed_at': records[0].get('reviewed_at'),
            'note': note
        }
    
    def set_category(self, sample_id: str, category: str) -> Dict[str, Any]:
        """
        设置样本分类
        
        Args:
            sample_id: 样本 ID
            category: 分类
        
        Returns:
            dict: 操作结果
        """
        # 校验
        if not sample_id:
            return {'success': False, 'error': 'sample_id 不能为空'}
        
        if category not in self.VALID_CATEGORIES:
            return {
                'success': False,
                'error': f'无效的分类：{category}',
                'valid_categories': self.VALID_CATEGORIES
            }
        
        records = self.load_registry()
        
        # 查找样本
        found = False
        for i, record in enumerate(records):
            if record.get('sample_id') == sample_id:
                records[i]['sample_category'] = category
                found = True
                break
        
        if not found:
            return {'success': False, 'error': f'样本不存在：{sample_id}'}
        
        # 保存
        self.save_registry(records)
        
        return {
            'success': True,
            'sample_id': sample_id,
            'sample_category': category
        }
    
    def set_ntrp(self, sample_id: str, ntrp_level: str) -> Dict[str, Any]:
        """
        设置 NTRP 等级
        
        Args:
            sample_id: 样本 ID
            ntrp_level: NTRP 等级
        
        Returns:
            dict: 操作结果
        """
        # 校验
        if not sample_id:
            return {'success': False, 'error': 'sample_id 不能为空'}
        
        # 简单的 NTRP 等级校验
        valid_levels = ['2.0', '2.5', '3.0', '3.5', '4.0', '4.5', '5.0']
        if ntrp_level and ntrp_level not in valid_levels:
            return {
                'success': False,
                'error': f'无效的 NTRP 等级：{ntrp_level}',
                'valid_levels': valid_levels
            }
        
        records = self.load_registry()
        
        # 查找样本
        found = False
        for i, record in enumerate(records):
            if record.get('sample_id') == sample_id:
                if ntrp_level:
                    records[i]['ntrp_level'] = ntrp_level
                else:
                    records[i]['ntrp_level'] = None
                found = True
                break
        
        if not found:
            return {'success': False, 'error': f'样本不存在：{sample_id}'}
        
        # 保存
        self.save_registry(records)
        
        return {
            'success': True,
            'sample_id': sample_id,
            'ntrp_level': ntrp_level if ntrp_level else None
        }
    
    def add_tags(self, sample_id: str, tags: List[str]) -> Dict[str, Any]:
        """
        添加标签
        
        Args:
            sample_id: 样本 ID
            tags: 标签列表
        
        Returns:
            dict: 操作结果
        """
        # 校验
        if not sample_id:
            return {'success': False, 'error': 'sample_id 不能为空'}
        
        if not tags:
            return {'success': False, 'error': 'tags 不能为空'}
        
        records = self.load_registry()
        
        # 查找样本
        found = False
        for i, record in enumerate(records):
            if record.get('sample_id') == sample_id:
                # 获取现有标签
                existing_tags = record.get('tags', [])
                if not existing_tags:
                    existing_tags = []
                
                # 添加新标签（去重）
                for tag in tags:
                    tag = tag.strip()
                    if tag and tag not in existing_tags:
                        existing_tags.append(tag)
                
                records[i]['tags'] = existing_tags
                found = True
                break
        
        if not found:
            return {'success': False, 'error': f'样本不存在：{sample_id}'}
        
        # 保存
        self.save_registry(records)
        
        return {
            'success': True,
            'sample_id': sample_id,
            'tags': records[0].get('tags', [])
        }
    
    def remove_tags(self, sample_id: str, tags: List[str]) -> Dict[str, Any]:
        """
        移除标签
        
        Args:
            sample_id: 样本 ID
            tags: 标签列表
        
        Returns:
            dict: 操作结果
        """
        # 校验
        if not sample_id:
            return {'success': False, 'error': 'sample_id 不能为空'}
        
        records = self.load_registry()
        
        # 查找样本
        found = False
        for i, record in enumerate(records):
            if record.get('sample_id') == sample_id:
                # 获取现有标签
                existing_tags = record.get('tags', [])
                if not existing_tags:
                    existing_tags = []
                
                # 移除指定标签
                records[i]['tags'] = [t for t in existing_tags if t not in tags]
                found = True
                break
        
        if not found:
            return {'success': False, 'error': f'样本不存在：{sample_id}'}
        
        # 保存
        self.save_registry(records)
        
        return {
            'success': True,
            'sample_id': sample_id,
            'tags': records[0].get('tags', [])
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """获取样本统计摘要"""
        records = self.load_registry()
        
        # 按来源分类
        by_source = {}
        for record in records:
            source_type = record.get('source_type', 'unknown')
            by_source[source_type] = by_source.get(source_type, 0) + 1
        
        # 按动作类型分类
        by_action = {}
        for record in records:
            action = record.get('action_type', 'unknown')
            by_action[action] = by_action.get(action, 0) + 1
        
        # 按审核状态分类
        by_status = {}
        for record in records:
            status = record.get('golden_review_status', 'unknown')
            by_status[status] = by_status.get(status, 0) + 1
        
        # 按分类统计
        by_category = {}
        for record in records:
            category = record.get('sample_category', 'unknown')
            by_category[category] = by_category.get(category, 0) + 1
        
        return {
            'total': len(records),
            'by_source': by_source,
            'by_action': by_action,
            'by_status': by_status,
            'by_category': by_category
        }


# ═══════════════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════════════

def create_review_service() -> SampleReviewService:
    """创建样本审核服务实例"""
    return SampleReviewService()
