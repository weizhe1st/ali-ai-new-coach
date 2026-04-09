#!/usr/bin/env python3
"""
统一任务模型定义

用于标准化系统内部的任务流转
支持最小任务状态管理与日志记录
"""

from dataclasses import dataclass, field
from typing import Optional, Literal, Dict, Any
from datetime import datetime
import uuid


@dataclass
class UnifiedTask:
    """
    统一任务对象
    
    所有分析任务都使用这个统一结构，便于路由、跟踪和管理
    支持最小任务状态管理与日志记录
    """
    # 任务基础信息
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: Literal["chat", "video_analysis", "image_analysis", "query"] = "chat"
    status: Literal["created", "running", "success", "failed"] = "created"
    
    # 渠道信息
    channel: Literal["dingtalk", "qq", "feishu", "wechat", "unknown"] = "unknown"
    user_id: str = ""
    message_type: Literal["text", "video", "image", "file", "audio", "unknown"] = "unknown"
    
    # 源文件信息
    source_file_url: Optional[str] = None
    source_file_name: Optional[str] = None
    source_file_path: Optional[str] = None  # 本地文件路径
    
    # 消息内容
    text_content: Optional[str] = None
    
    # 执行状态跟踪
    current_stage: str = "created"  # 当前执行阶段
    error_code: Optional[str] = None  # 错误码
    
    # 分析结果
    result: Optional[Dict[str, Any]] = None
    report: Optional[str] = None
    error_message: Optional[str] = None
    
    # 时间戳
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    # 扩展字段
    extra: Optional[Dict[str, Any]] = None
    
    def mark_running(self, stage: str = "executing"):
        """标记任务开始执行"""
        self.status = "running"
        self.current_stage = stage
        self.started_at = datetime.utcnow().isoformat()
    
    def mark_success(self, stage: str = "completed", result: Dict[str, Any] = None, report: str = None):
        """标记任务成功"""
        self.status = "success"
        self.current_stage = stage
        self.result = result
        self.report = report
        self.completed_at = datetime.utcnow().isoformat()
    
    def mark_failed(self, error_code: str, error_message: str, stage: str = "failed"):
        """标记任务失败"""
        self.status = "failed"
        self.current_stage = stage
        self.error_code = error_code
        self.error_message = error_message
        self.completed_at = datetime.utcnow().isoformat()
    
    def is_video_analysis(self) -> bool:
        """是否为视频分析任务"""
        return self.task_type == "video_analysis"
    
    def is_chat(self) -> bool:
        """是否为聊天任务"""
        return self.task_type == "chat"
    
    def has_file(self) -> bool:
        """是否包含文件"""
        return bool(self.source_file_url or self.source_file_path)
    
    def is_running(self) -> bool:
        """检查任务是否正在执行"""
        return self.status == "running"
    
    def is_success(self) -> bool:
        """检查任务是否成功"""
        return self.status == "success"
    
    def is_failed(self) -> bool:
        """检查任务是否失败"""
        return self.status == "failed"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'task_type': self.task_type,
            'status': self.status,
            'current_stage': self.current_stage,
            'channel': self.channel,
            'user_id': self.user_id,
            'message_type': self.message_type,
            'source_file_url': self.source_file_url,
            'source_file_name': self.source_file_name,
            'source_file_path': self.source_file_path,
            'text_content': self.text_content,
            'result': self.result,
            'report': self.report,
            'error_code': self.error_code,
            'error_message': self.error_message,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UnifiedTask':
        """从字典创建"""
        return cls(**data)


# 类型别名
TaskDict = Dict[str, Any]
