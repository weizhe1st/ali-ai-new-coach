#!/usr/bin/env python3
"""
样本归档服务

职责：
1. 分析成功后自动上传 COS
2. 标记候选黄金样本
3. 记录样本元数据
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# 数据库路径
DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'db', 'app.db')
SAMPLE_REGISTRY_PATH = os.path.join(PROJECT_ROOT, 'data', 'sample_registry.json')


class SampleArchiveService:
    """样本归档服务"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.cos_client = None
        self.cos_config = None
        self._init_cos()
    
    def _init_cos(self):
        """初始化 COS 客户端"""
        try:
            from qcloud_cos import CosConfig
            from qcloud_cos import CosS3Client
            
            # 从环境变量获取配置
            secret_id = os.environ.get('COS_SECRET_ID')
            secret_key = os.environ.get('COS_SECRET_KEY')
            bucket = os.environ.get('COS_BUCKET', 'tennis-ai-1411340868')
            region = os.environ.get('COS_REGION', 'ap-shanghai')
            
            if not secret_id or not secret_key:
                print("⚠️  COS 配置未设置，跳过 COS 上传功能")
                return
            
            self.cos_config = CosConfig(
                Region=region,
                SecretId=secret_id,
                SecretKey=secret_key
            )
            self.cos_client = CosS3Client(self.cos_config)
            self.cos_bucket = bucket
            print("✅ COS 客户端已初始化")
            
        except ImportError:
            print("⚠️  cos-python-sdk-v5 未安装，跳过 COS 上传功能")
        except Exception as e:
            print(f"⚠️  COS 初始化失败：{e}")
    
    def archive_after_analysis(self, task: Any, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析成功后归档样本
        
        Args:
            task: UnifiedTask 对象
            analysis_result: 分析结果
        
        Returns:
            dict: 归档结果
        """
        print("\n📦 开始样本归档...")
        
        # 检查分析是否成功
        if not analysis_result.get('success'):
            print("⚠️  分析失败，跳过归档")
            return {'archived': False, 'reason': 'analysis_failed'}
        
        # 检查视频文件是否存在
        video_path = getattr(task, 'source_file_path', None)
        if not video_path or not os.path.exists(video_path):
            print("⚠️  视频文件不存在，跳过归档")
            return {'archived': False, 'reason': 'video_not_found'}
        
        # 提取必要信息
        task_id = getattr(task, 'task_id', 'unknown')
        action_type = getattr(task, 'task_type', 'video_analysis')
        user_id = getattr(task, 'user_id', 'unknown')
        
        # 生成 COS Key
        cos_key = self._generate_cos_key(action_type, task_id, video_path)
        
        # 上传到 COS
        upload_result = self._upload_to_cos(video_path, cos_key)
        
        if not upload_result.get('success'):
            print(f"⚠️  COS 上传失败：{upload_result.get('error')}")
            return {'archived': False, 'reason': 'cos_upload_failed', **upload_result}
        
        # 判断是否候选黄金样本
        is_candidate = self._should_mark_as_candidate(analysis_result, task)
        
        # 如果符合候选条件，上传到 candidate_golden 目录
        candidate_cos_key = None
        if is_candidate:
            candidate_cos_key = self._generate_candidate_cos_key(action_type, task_id, video_path)
            candidate_result = self._upload_to_cos(video_path, candidate_cos_key)
            
            if candidate_result.get('success'):
                print(f"✅ 已标记为候选黄金样本")
            else:
                print(f"⚠️  候选样本上传失败：{candidate_result.get('error')}")
        
        # 记录样本元数据
        sample_record = {
            'task_id': task_id,
            'user_id': user_id,
            'action_type': action_type,
            'source_file_name': os.path.basename(video_path),
            'source_file_path': video_path,
            'cos_key': cos_key,
            'cos_url': self._get_cos_url(cos_key),
            'candidate_cos_key': candidate_cos_key,
            'candidate_for_golden': is_candidate,
            'golden_review_status': 'pending' if is_candidate else 'not_candidate',
            'analysis_summary': {
                'ntrp_level': analysis_result.get('structured_result', {}).get('ntrp_level', 'unknown'),
                'overall_score': analysis_result.get('structured_result', {}).get('overall_score', 0),
                'key_issues': analysis_result.get('structured_result', {}).get('key_issues', [])
            },
            'archived_at': datetime.now().isoformat(),
            'golden_review_note': '分析成功，动作完整，建议人工复核' if is_candidate else ''
        }
        
        # 保存到样本登记表
        self._save_sample_record(sample_record)
        
        print(f"✅ 样本归档完成")
        print(f"   COS Key: {cos_key}")
        print(f"   候选标记：{'是' if is_candidate else '否'}")
        
        return {
            'archived': True,
            'cos_key': cos_key,
            'cos_url': sample_record['cos_url'],
            'candidate_for_golden': is_candidate,
            'candidate_cos_key': candidate_cos_key,
            'sample_record': sample_record
        }
    
    def _generate_cos_key(self, action_type: str, task_id: str, video_path: str) -> str:
        """生成 COS Key（归档目录）"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = os.path.basename(video_path)
        
        # 简化动作类型
        action_short = 'serve' if 'serve' in action_type.lower() else 'other'
        
        return f"analyzed/{action_short}/{date_str}/{task_id}_{filename}"
    
    def _generate_candidate_cos_key(self, action_type: str, task_id: str, video_path: str) -> str:
        """生成 COS Key（候选黄金样本目录）"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = os.path.basename(video_path)
        
        action_short = 'serve' if 'serve' in action_type.lower() else 'other'
        
        return f"candidate_golden/{action_short}/{date_str}/{task_id}_{filename}"
    
    def _upload_to_cos(self, local_path: str, cos_key: str) -> Dict[str, Any]:
        """上传文件到 COS"""
        if not self.cos_client:
            return {'success': False, 'error': 'COS client not initialized'}
        
        try:
            with open(local_path, 'rb') as f:
                self.cos_client.put_object(
                    Bucket=self.cos_bucket,
                    Body=f,
                    Key=cos_key
                )
            
            print(f"✅ 上传成功：{cos_key}")
            return {'success': True, 'cos_key': cos_key}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_cos_url(self, cos_key: str) -> str:
        """生成 COS 公开访问 URL"""
        if not self.cos_bucket or not self.cos_config:
            return ''
        
        region = getattr(self.cos_config, 'region', 'ap-shanghai')
        return f"https://{self.cos_bucket}.cos.{region}.myqcloud.com/{cos_key}"
    
    def _should_mark_as_candidate(self, analysis_result: Dict[str, Any], task: Any) -> bool:
        """
        判断是否应该标记为候选黄金样本
        
        当前阶段的简单规则：
        1. 分析成功
        2. 动作类型为发球
        3. 整体评分 >= 50
        4. 视频非默认样例
        """
        # 检查分析是否成功
        if not analysis_result.get('success'):
            return False
        
        # 检查动作类型
        action_type = getattr(task, 'task_type', '')
        if 'serve' not in action_type.lower():
            return False
        
        # 检查整体评分
        structured = analysis_result.get('structured_result', {})
        overall_score = structured.get('overall_score', 0)
        
        if overall_score < 50:
            return False
        
        # 检查是否为默认样例（简单判断）
        source_path = getattr(task, 'source_file_path', '')
        if 'default' in source_path.lower() or 'sample' in source_path.lower():
            return False
        
        # 检查视频文件是否真实存在
        if not source_path or not os.path.exists(source_path):
            return False
        
        return True
    
    def _save_sample_record(self, sample_record: Dict[str, Any]):
        """保存样本记录到登记表"""
        # 确保目录存在
        os.makedirs(os.path.dirname(SAMPLE_REGISTRY_PATH), exist_ok=True)
        
        # 读取现有记录
        records = []
        if os.path.exists(SAMPLE_REGISTRY_PATH):
            try:
                with open(SAMPLE_REGISTRY_PATH, 'r', encoding='utf-8') as f:
                    records = json.load(f)
            except:
                records = []
        
        # 添加新记录
        records.append(sample_record)
        
        # 保存
        with open(SAMPLE_REGISTRY_PATH, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 样本记录已保存：{SAMPLE_REGISTRY_PATH}")
    
    def get_sample_registry(self) -> list:
        """获取样本登记表"""
        if not os.path.exists(SAMPLE_REGISTRY_PATH):
            return []
        
        try:
            with open(SAMPLE_REGISTRY_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def update_golden_review_status(self, task_id: str, status: str, note: str = ''):
        """
        更新黄金样本审核状态
        
        Args:
            task_id: 任务 ID
            status: 状态 (pending/approved/rejected)
            note: 审核备注
        """
        records = self.get_sample_registry()
        
        updated = False
        for record in records:
            if record.get('task_id') == task_id:
                record['golden_review_status'] = status
                record['golden_review_note'] = note
                record['reviewed_at'] = datetime.now().isoformat()
                updated = True
                break
        
        if updated:
            with open(SAMPLE_REGISTRY_PATH, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            print(f"✅ 审核状态已更新：{task_id} -> {status}")
        else:
            print(f"⚠️  未找到样本记录：{task_id}")


# ═══════════════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════════════

def create_archive_service() -> SampleArchiveService:
    """创建样本归档服务实例"""
    return SampleArchiveService()


# ═══════════════════════════════════════════════════════════════════
# 测试
# ═══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("="*60)
    print("📦 样本归档服务测试")
    print("="*60)
    
    # 创建服务实例
    service = SampleArchiveService()
    
    # 查看现有样本记录
    records = service.get_sample_registry()
    print(f"\n现有样本记录：{len(records)} 条")
    
    if records:
        print("\n最近 5 条记录:")
        for record in records[-5:]:
            print(f"  - {record.get('task_id')}: {record.get('source_file_name')}")
            print(f"    候选：{record.get('candidate_for_golden')}")
            print(f"    状态：{record.get('golden_review_status')}")
    
    print("\n" + "="*60)
