#!/usr/bin/env python3
"""
历史黄金样本导入工具

职责：
1. 扫描 COS 中的历史黄金样本目录
2. 过滤视频文件
3. 生成 sample_id 和 metadata
4. 写入 sample_registry.json
5. 标记 review_status=imported_legacy
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# 样本登记表路径
SAMPLE_REGISTRY_PATH = os.path.join(PROJECT_ROOT, 'data', 'sample_registry.json')


class LegacySampleImporter:
    """历史样本导入器"""
    
    def __init__(self):
        self.cos_client = None
        self.cos_bucket = None
        self._init_cos()
    
    def _init_cos(self):
        """初始化 COS 客户端"""
        try:
            from qcloud_cos import CosConfig
            from qcloud_cos import CosS3Client
            
            secret_id = os.environ.get('COS_SECRET_ID')
            secret_key = os.environ.get('COS_SECRET_KEY')
            bucket = os.environ.get('COS_BUCKET', 'tennis-ai-1411340868')
            region = os.environ.get('COS_REGION', 'ap-shanghai')
            
            if not secret_id or not secret_key:
                print("⚠️  COS 配置未设置")
                return False
            
            self.cos_config = CosConfig(
                Region=region,
                SecretId=secret_id,
                SecretKey=secret_key
            )
            self.cos_client = CosS3Client(self.cos_config)
            self.cos_bucket = bucket
            print("✅ COS 客户端已初始化")
            return True
            
        except Exception as e:
            print(f"⚠️  COS 初始化失败：{e}")
            return False
    
    def scan_cos_directory(self, prefix: str, max_keys: int = 100) -> List[dict]:
        """
        扫描 COS 目录
        
        Args:
            prefix: COS 前缀（目录）
            max_keys: 最大返回数量
        
        Returns:
            List[dict]: 对象列表
        """
        if not self.cos_client:
            print("❌ COS 客户端未初始化")
            return []
        
        try:
            response = self.cos_client.list_objects(
                Bucket=self.cos_bucket,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            objects = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    # 跳过目录本身
                    if obj['Key'].endswith('/'):
                        continue
                    
                    objects.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj.get('LastModified', '')
                    })
            
            return objects
            
        except Exception as e:
            print(f"❌ 扫描失败：{e}")
            return []
    
    def filter_video_files(self, objects: List[dict]) -> List[dict]:
        """
        过滤视频文件
        
        Args:
            objects: COS 对象列表
        
        Returns:
            List[dict]: 视频文件列表
        """
        video_extensions = ['.mp4', '.mov', '.mkv', '.avi']
        
        videos = []
        for obj in objects:
            key = obj['key']
            
            # 检查扩展名
            is_video = any(key.lower().endswith(ext) for ext in video_extensions)
            
            # 过滤非视频文件
            if not is_video:
                continue
            
            # 过滤临时文件
            if 'tmp' in key.lower() or 'temp' in key.lower():
                continue
            
            # 过滤缩略图
            if 'thumb' in key.lower() or 'preview' in key.lower():
                continue
            
            videos.append(obj)
        
        return videos
    
    def extract_metadata(self, cos_key: str) -> Dict[str, Any]:
        """
        从 COS Key 提取 metadata
        
        Args:
            cos_key: COS Key
        
        Returns:
            dict: 元数据
        """
        # 从路径推测动作类型
        action_type = 'unknown'
        if 'serve' in cos_key.lower() or '发球' in cos_key:
            action_type = 'serve'
        elif 'forehand' in cos_key.lower() or '正手' in cos_key:
            action_type = 'forehand'
        elif 'backhand' in cos_key.lower() or '反手' in cos_key:
            action_type = 'backhand'
        
        # 提取文件名
        filename = os.path.basename(cos_key)
        
        return {
            'action_type': action_type,
            'source_file_name': filename,
            'cos_key': cos_key
        }
    
    def generate_sample_id(self, index: int, prefix: str = 'legacy') -> str:
        """
        生成 sample_id
        
        Args:
            index: 序号
            prefix: 前缀
        
        Returns:
            str: sample_id
        """
        return f"{prefix}_{index:04d}"
    
    def import_samples(self, cos_prefix: str, max_samples: int = 100) -> Dict[str, Any]:
        """
        导入历史样本
        
        Args:
            cos_prefix: COS 前缀（目录）
            max_samples: 最大导入数量
        
        Returns:
            dict: 导入结果统计
        """
        print(f"\n{'='*60}")
        print(f"📥 开始导入历史样本")
        print(f"   COS 前缀：{cos_prefix}")
        print(f"   最大数量：{max_samples}")
        print(f"{'='*60}\n")
        
        if not self.cos_client:
            return {'success': False, 'error': 'COS client not initialized'}
        
        # 步骤 1: 扫描 COS 目录
        print("步骤 1: 扫描 COS 目录...")
        objects = self.scan_cos_directory(cos_prefix, max_samples)
        print(f"   找到 {len(objects)} 个对象")
        
        if not objects:
            return {'success': True, 'imported': 0, 'reason': 'no_objects_found'}
        
        # 步骤 2: 过滤视频文件
        print("\n步骤 2: 过滤视频文件...")
        videos = self.filter_video_files(objects)
        print(f"   找到 {len(videos)} 个视频文件")
        
        if not videos:
            return {'success': True, 'imported': 0, 'reason': 'no_videos_found'}
        
        # 步骤 3: 读取现有样本记录（用于去重）
        print("\n步骤 3: 检查现有样本记录...")
        existing_records = self._load_sample_registry()
        existing_keys = {r.get('cos_key') for r in existing_records}
        print(f"   现有记录：{len(existing_records)} 条")
        
        # 步骤 4: 导入样本
        print("\n步骤 4: 导入样本...")
        imported_count = 0
        skipped_count = 0
        
        for i, video in enumerate(videos, 1):
            cos_key = video['key']
            
            # 去重检查
            if cos_key in existing_keys:
                print(f"   [{i}/{len(videos)}] 跳过（已存在）: {cos_key}")
                skipped_count += 1
                continue
            
            # 提取 metadata
            metadata = self.extract_metadata(cos_key)
            
            # 生成 sample_id
            sample_id = self.generate_sample_id(len(existing_records) + imported_count + 1)
            
            # 创建样本记录
            sample_record = {
                'sample_id': sample_id,
                'source_type': 'legacy_cos_import',
                'action_type': metadata['action_type'],
                'sample_category': 'unknown',
                'cos_key': cos_key,
                'cos_url': self._get_cos_url(cos_key),
                'source_file_name': metadata['source_file_name'],
                'source_file_path': None,
                'task_id': None,
                'candidate_for_golden': False,
                'golden_review_status': 'imported_legacy',
                'analysis_summary': {},
                'score': None,
                'ntrp_level': None,
                'tags': [],
                'reviewer': None,
                'reviewed_at': None,
                'imported_at': datetime.now().isoformat(),
                'size': video['size'],
                'last_modified': video['last_modified']
            }
            
            # 保存到样本登记表
            self._append_sample_record(sample_record)
            
            print(f"   [{i}/{len(videos)}] ✅ 导入：{sample_id} - {metadata['source_file_name']}")
            imported_count += 1
        
        # 步骤 5: 输出统计
        print(f"\n{'='*60}")
        print("📊 导入完成")
        print(f"{'='*60}")
        print(f"   扫描总数：{len(objects)}")
        print(f"   有效视频：{len(videos)}")
        print(f"   成功导入：{imported_count}")
        print(f"   重复跳过：{skipped_count}")
        print(f"\n   样本登记表总数：{len(existing_records) + imported_count}")
        print(f"{'='*60}\n")
        
        return {
            'success': True,
            'scanned': len(objects),
            'videos': len(videos),
            'imported': imported_count,
            'skipped': skipped_count,
            'total_records': len(existing_records) + imported_count
        }
    
    def _load_sample_registry(self) -> List[dict]:
        """加载样本登记表"""
        if not os.path.exists(SAMPLE_REGISTRY_PATH):
            return []
        
        try:
            with open(SAMPLE_REGISTRY_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def _append_sample_record(self, sample_record: Dict[str, Any]):
        """追加样本记录"""
        records = self._load_sample_registry()
        records.append(sample_record)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(SAMPLE_REGISTRY_PATH), exist_ok=True)
        
        with open(SAMPLE_REGISTRY_PATH, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    
    def _get_cos_url(self, cos_key: str) -> str:
        """生成 COS 公开访问 URL"""
        if not self.cos_bucket or not self.cos_config:
            return ''
        
        region = getattr(self.cos_config, 'region', 'ap-shanghai')
        return f"https://{self.cos_bucket}.cos.{region}.myqcloud.com/{cos_key}"
    
    def get_import_summary(self) -> Dict[str, Any]:
        """获取导入统计摘要"""
        records = self._load_sample_registry()
        
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
        
        return {
            'total': len(records),
            'by_source': by_source,
            'by_action': by_action,
            'by_status': by_status
        }


# ═══════════════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════════════

def import_legacy_samples(cos_prefix: str = 'golden/', max_samples: int = 100) -> Dict[str, Any]:
    """
    便捷函数：导入历史样本
    
    Args:
        cos_prefix: COS 前缀
        max_samples: 最大导入数量
    
    Returns:
        dict: 导入结果
    """
    importer = LegacySampleImporter()
    return importer.import_samples(cos_prefix, max_samples)


def get_sample_summary() -> Dict[str, Any]:
    """便捷函数：获取样本统计摘要"""
    importer = LegacySampleImporter()
    return importer.get_import_summary()


# ═══════════════════════════════════════════════════════════════════
# 命令行工具
# ═══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='历史黄金样本导入工具')
    parser.add_argument('--prefix', type=str, default='golden/',
                       help='COS 前缀（目录），默认：golden/')
    parser.add_argument('--max', type=int, default=100,
                       help='最大导入数量，默认：100')
    parser.add_argument('--summary', action='store_true',
                       help='只显示统计摘要，不导入')
    
    args = parser.parse_args()
    
    print("="*60)
    print("📦 历史黄金样本导入工具")
    print("="*60)
    
    importer = LegacySampleImporter()
    
    if args.summary:
        # 只显示统计摘要
        summary = importer.get_import_summary()
        
        print(f"\n📊 样本统计摘要")
        print(f"{'='*60}")
        print(f"   总样本数：{summary.get('total', 0)}")
        print(f"\n   按来源分类:")
        for source, count in summary.get('by_source', {}).items():
            print(f"     {source}: {count}")
        print(f"\n   按动作类型分类:")
        for action, count in summary.get('by_action', {}).items():
            print(f"     {action}: {count}")
        print(f"\n   按审核状态分类:")
        for status, count in summary.get('by_status', {}).items():
            print(f"     {status}: {count}")
        print(f"{'='*60}\n")
        
    else:
        # 执行导入
        result = importer.import_samples(args.prefix, args.max)
        
        if result.get('success'):
            print("✅ 导入成功")
        else:
            print(f"❌ 导入失败：{result.get('error', 'unknown')}")
