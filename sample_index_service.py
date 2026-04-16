#!/usr/bin/env python3
"""
样本统一索引服务
提供统一的样本检索和访问接口，底层对接分散存储的 COS 目录
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional

SAMPLE_REGISTRY_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/sample_registry.json'


class SampleIndexService:
    """样本统一索引服务"""
    
    def __init__(self, registry_path: str = SAMPLE_REGISTRY_PATH):
        self.registry_path = registry_path
        self.registry = self._load_registry()
        self._build_index()
    
    def _load_registry(self) -> List[Dict]:
        """加载样本登记表"""
        if not os.path.exists(self.registry_path):
            return []
        
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _build_index(self):
        """构建索引"""
        # 按 sample_id 索引
        self.id_to_sample = {s.get('sample_id'): s for s in self.registry}
        
        # 按 NTRP 等级索引
        self.ntrp_index = {}
        for sample in self.registry:
            ntrp = sample.get('ntrp_level', 'unknown')
            if ntrp not in self.ntrp_index:
                self.ntrp_index[ntrp] = []
            self.ntrp_index[ntrp].append(sample.get('sample_id'))
        
        # 按分类索引
        self.category_index = {}
        for sample in self.registry:
            category = sample.get('sample_category', 'unknown')
            if category not in self.category_index:
                self.category_index[category] = []
            self.category_index[category].append(sample.get('sample_id'))
        
        # 按问题类型索引
        self.issue_index = {}
        for sample in self.registry:
            primary_issue = sample.get('primary_issue')
            if primary_issue:
                if primary_issue not in self.issue_index:
                    self.issue_index[primary_issue] = []
                self.issue_index[primary_issue].append(sample.get('sample_id'))
        
        # 按 COS 目录索引
        self.cos_dir_index = {}
        for sample in self.registry:
            cos_key = sample.get('cos_key')
            if cos_key:
                dir_path = '/'.join(cos_key.split('/')[:2])
                if dir_path not in self.cos_dir_index:
                    self.cos_dir_index[dir_path] = []
                self.cos_dir_index[dir_path].append(sample.get('sample_id'))
    
    def get_sample(self, sample_id: str) -> Optional[Dict]:
        """根据 sample_id 获取样本"""
        return self.id_to_sample.get(sample_id)
    
    def search_samples(self, 
                      ntrp_level: Optional[str] = None,
                      category: Optional[str] = None,
                      primary_issue: Optional[str] = None,
                      has_cos_url: Optional[bool] = None) -> List[Dict]:
        """
        搜索样本（统一检索接口）
        
        Args:
            ntrp_level: NTRP 等级过滤
            category: 分类过滤
            primary_issue: 主要问题过滤
            has_cos_url: 是否有 COS URL
        
        Returns:
            样本列表
        """
        results = self.registry
        
        # NTRP 等级过滤
        if ntrp_level:
            results = [s for s in results if s.get('ntrp_level') == ntrp_level]
        
        # 分类过滤
        if category:
            results = [s for s in results if s.get('sample_category') == category]
        
        # 主要问题过滤
        if primary_issue:
            results = [s for s in results if s.get('primary_issue') == primary_issue]
        
        # COS URL 过滤
        if has_cos_url is not None:
            if has_cos_url:
                results = [s for s in results if s.get('cos_url')]
            else:
                results = [s for s in results if not s.get('cos_url')]
        
        return results
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        stats = {
            'total_samples': len(self.registry),
            'by_ntrp': {},
            'by_category': {},
            'by_issue': {},
            'by_cos_dir': {},
            'cos_upload_status': {
                'uploaded': len([s for s in self.registry if s.get('cos_url')]),
                'not_uploaded': len([s for s in self.registry if not s.get('cos_url')])
            }
        }
        
        # 按 NTRP 统计
        for ntrp, sample_ids in self.ntrp_index.items():
            stats['by_ntrp'][ntrp] = len(sample_ids)
        
        # 按分类统计
        for category, sample_ids in self.category_index.items():
            stats['by_category'][category] = len(sample_ids)
        
        # 按问题统计
        for issue, sample_ids in self.issue_index.items():
            stats['by_issue'][issue] = len(sample_ids)
        
        # 按 COS 目录统计
        for dir_path, sample_ids in self.cos_dir_index.items():
            stats['by_cos_dir'][dir_path] = len(sample_ids)
        
        return stats
    
    def get_sample_display_info(self, sample_id: str) -> Dict:
        """获取样本展示信息（含视频访问方式）"""
        sample = self.get_sample(sample_id)
        if not sample:
            return {'error': f'样本不存在：{sample_id}'}
        
        # 构建展示信息
        display_info = {
            'sample_id': sample.get('sample_id'),
            'ntrp_level': sample.get('ntrp_level'),
            'category': sample.get('sample_category'),
            'primary_issue': sample.get('primary_issue'),
            'secondary_issue': sample.get('secondary_issue'),
            'video_info': self._get_video_access_info(sample),
            'status': self._get_sample_status(sample),
        }
        
        return display_info
    
    def _get_video_access_info(self, sample: Dict) -> Dict:
        """获取视频访问信息"""
        cos_url = sample.get('cos_url')
        cos_key = sample.get('cos_key')
        
        if cos_url:
            return {
                'status': 'available',
                'access_type': 'direct',
                'url': cos_url,
                'message': '可直接访问视频链接'
            }
        elif cos_key:
            return {
                'status': 'pending',
                'access_type': 'cos_key_only',
                'cos_key': cos_key,
                'message': '视频已上传到 COS，但 URL 未生成'
            }
        else:
            return {
                'status': 'not_uploaded',
                'access_type': 'local_only',
                'local_path': sample.get('source_file_path'),
                'message': '请联系教练获取视频'
            }
    
    def _get_sample_status(self, sample: Dict) -> str:
        """获取样本状态"""
        if sample.get('cos_url'):
            return '✅ 已上传'
        elif sample.get('cos_key'):
            return '⏳ 上传中'
        else:
            return '⏳ 待上传'
    
    def export_index_summary(self) -> str:
        """导出索引摘要"""
        stats = self.get_statistics()
        
        lines = []
        lines.append("="*60)
        lines.append("📊 样本统一索引摘要")
        lines.append("="*60)
        lines.append("")
        lines.append(f"总样本数：{stats['total_samples']} 个")
        lines.append("")
        
        lines.append("按 NTRP 等级分布:")
        for ntrp, count in sorted(stats['by_ntrp'].items()):
            lines.append(f"   {ntrp}: {count} 个")
        lines.append("")
        
        lines.append("按分类分布:")
        for category, count in sorted(stats['by_category'].items()):
            lines.append(f"   {category}: {count} 个")
        lines.append("")
        
        lines.append("按问题类型分布:")
        for issue, count in sorted(stats['by_issue'].items(), key=lambda x: -x[1])[:10]:
            lines.append(f"   {issue}: {count} 个")
        lines.append("")
        
        lines.append("COS 目录分布:")
        for dir_path, count in sorted(stats['by_cos_dir'].items()):
            lines.append(f"   {dir_path}: {count} 个")
        lines.append("")
        
        lines.append("上传状态:")
        lines.append(f"   已上传：{stats['cos_upload_status']['uploaded']} 个")
        lines.append(f"   待上传：{stats['cos_upload_status']['not_uploaded']} 个")
        lines.append("")
        
        return "\n".join(lines)


def main():
    """测试统一索引服务"""
    print("="*60)
    print("📚 样本统一索引服务测试")
    print("="*60)
    print()
    
    # 创建索引服务
    index_service = SampleIndexService()
    
    # 打印索引摘要
    print(index_service.export_index_summary())
    
    # 测试搜索
    print("="*60)
    print("🔍 搜索测试")
    print("="*60)
    print()
    
    # 搜索 5.0 级样本
    samples_5_0 = index_service.search_samples(ntrp_level='5.0')
    print(f"5.0 级样本：{len(samples_5_0)} 个")
    
    # 搜索优秀示范
    excellent = index_service.search_samples(category='excellent_demo')
    print(f"优秀示范样本：{len(excellent)} 个")
    
    # 搜索已上传 COS 的样本
    uploaded = index_service.search_samples(has_cos_url=True)
    print(f"已上传 COS: {len(uploaded)} 个")
    
    print()
    print("="*60)
    print("✅ 测试完成")
    print("="*60)


if __name__ == '__main__':
    main()
