#!/usr/bin/env python3
"""
腾讯云 COS 上传模块

使用官方 SDK：cos-python-sdk-v5
"""

import os
import sys
from typing import Optional
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from config import get_cos_config


class COSUploader:
    """
    COS 上传器（使用官方 SDK）
    """
    
    def __init__(self):
        self.config = get_cos_config()
        self.client = None
        
        if self.config.enabled:
            self._init_client()
    
    def _init_client(self):
        """初始化 COS 客户端（使用官方 SDK）"""
        try:
            from qcloud_cos import CosConfig
            from qcloud_cos import CosS3Client
            
            # 配置
            config = CosConfig(
                Region=self.config.region,
                SecretId=self.config.secret_id,
                SecretKey=self.config.secret_key
            )
            
            self.client = CosS3Client(config)
            print(f"✅ COS 客户端初始化成功 (Bucket: {self.config.bucket})")
        except ImportError as e:
            print(f"⚠️  未安装 cos-python-sdk-v5: {e}")
            print("   使用简单上传模式")
            self.client = None
        except Exception as e:
            print(f"⚠️  COS 客户端初始化失败：{e}")
            self.client = None
    
    def upload_file(self, local_path: str, cos_key: str) -> bool:
        """
        上传文件到 COS
        
        Args:
            local_path: 本地文件路径
            cos_key: COS Key（存储路径）
        
        Returns:
            bool: 上传成功返回 True
        """
        
        if not os.path.exists(local_path):
            print(f"❌ 文件不存在：{local_path}")
            return False
        
        try:
            if self.client:
                # 使用官方 SDK 上传
                with open(local_path, 'rb') as f:
                    self.client.put_object(
                        Bucket=self.config.bucket,
                        Body=f,
                        Key=cos_key,
                        ACL='public-read'  # 设置公开读权限
                    )
                print(f"✅ 上传成功（SDK）: {cos_key}")
            else:
                # 简单上传模式
                return self._simple_upload(local_path, cos_key)
            
            return True
            
        except Exception as e:
            print(f"❌ 上传失败：{e}")
            return False
    
    def _simple_upload(self, local_path: str, cos_key: str) -> bool:
        """简单上传模式（使用 requests）"""
        import requests
        
        url = f"https://{self.config.bucket}.cos.{self.config.region}.myqcloud.com/{cos_key}"
        
        with open(local_path, 'rb') as f:
            file_data = f.read()
        
        try:
            response = requests.put(url, data=file_data, timeout=120)
            
            if response.status_code in [200, 204]:
                print(f"✅ 上传成功（简单模式）: {cos_key}")
                return True
            else:
                print(f"❌ 上传失败：{response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 上传异常：{e}")
            return False
    
    def upload_video(self, local_path: str, task_id: str, 
                    video_name: str, is_golden: bool = False) -> Optional[str]:
        """
        上传视频到 COS
        
        Args:
            local_path: 本地视频文件路径
            task_id: 任务 ID
            video_name: 视频文件名
            is_golden: 是否为黄金样本
        
        Returns:
            str: COS Key（上传成功）或 None（失败）
        """
        
        if not self.config.enabled:
            print("ℹ️  COS 上传已禁用")
            return None
        
        # 构建 COS Key
        prefix = self.config.golden_prefix if is_golden else self.config.analyzed_prefix
        month_prefix = self.config.current_month_prefix
        cos_key = f"{prefix}{month_prefix}/{task_id}/{video_name}"
        
        # 上传
        if self.upload_file(local_path, cos_key):
            return cos_key
        else:
            return None
    
    def upload_report(self, report_path: str, task_id: str, 
                     report_name: str = "report.txt") -> Optional[str]:
        """
        上传分析报告到 COS
        
        Args:
            report_path: 本地报告文件路径
            task_id: 任务 ID
            report_name: 报告文件名
        
        Returns:
            str: COS Key（上传成功）或 None（失败）
        """
        
        if not self.config.enabled:
            return None
        
        # 构建 COS Key
        month_prefix = self.config.current_month_prefix
        cos_key = f"{self.config.analyzed_prefix}{month_prefix}/{task_id}/{report_name}"
        
        # 上传
        if self.upload_file(report_path, cos_key):
            return cos_key
        else:
            return None
    
    def get_public_url(self, cos_key: str) -> str:
        """
        获取公开访问 URL
        
        Args:
            cos_key: COS Key
        
        Returns:
            str: 公开访问 URL
        """
        return f"https://{self.config.bucket}.cos.{self.config.region}.myqcloud.com/{cos_key}"
    
    def get_presigned_url(self, cos_key: str, expires: int = 3600) -> str:
        """
        获取预签名 URL
        
        Args:
            cos_key: COS Key
            expires: 过期时间（秒）
        
        Returns:
            str: 预签名 URL
        """
        
        if self.client:
            return self.client.get_presigned_download_url(
                Bucket=self.config.bucket,
                Key=cos_key,
                Expire=expires
            )
        else:
            return self.get_public_url(cos_key)


# 便捷函数
def upload_video_to_cos(local_path: str, task_id: str, 
                       video_name: str, is_golden: bool = False) -> Optional[str]:
    """上传视频到 COS"""
    uploader = COSUploader()
    return uploader.upload_video(local_path, task_id, video_name, is_golden)


def upload_report_to_cos(report_path: str, task_id: str, 
                        report_name: str = "report.txt") -> Optional[str]:
    """上传报告到 COS"""
    uploader = COSUploader()
    return uploader.upload_report(report_path, task_id, report_name)


# 测试
if __name__ == '__main__':
    print("\n" + "="*60)
    print("📦 COS 上传模块测试（官方 SDK）")
    print("="*60 + "\n")
    
    # 加载配置
    config = get_cos_config()
    
    print("📋 COS 配置")
    print("="*60)
    print(f"启用：{config.enabled}")
    print(f"Bucket: {config.bucket}")
    print(f"Region: {config.region}")
    print(f"SecretId: {config.secret_id[:15]}...")
    print(f"前缀：raw/{config.current_month_prefix}")
    print()
    
    if config.enabled:
        print("✅ COS 配置完成，可以开始上传")
        
        # 测试客户端初始化
        uploader = COSUploader()
        if uploader.client:
            print("✅ 官方 SDK 已就绪")
        else:
            print("⚠️  使用简单上传模式")
    else:
        print("⚠️  COS 上传已禁用")
    
    print()
    print("="*60)
