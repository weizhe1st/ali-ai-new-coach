#!/usr/bin/env python3
"""
统一消息模型定义

用于标准化来自不同渠道（钉钉、QQ、飞书等）的消息输入
"""

from dataclasses import dataclass, field
try:
    from typing import Optional, Literal, Dict, Any, Union
except ImportError:
    # Python 3.6.8 不支持 Literal，使用 typing_extensions
    from typing import Optional, Dict, Any, Union
    from typing_extensions import Literal
from datetime import datetime
from enum import Enum


class ChannelType(str, Enum):
    """渠道类型"""
    DINGTALK = "dingtalk"
    QQ = "qq"
    FEISHU = "feishu"
    WECHAT = "wechat"
    UNKNOWN = "unknown"


class MessageType(str, Enum):
    """消息类型"""
    TEXT = "text"
    VIDEO = "video"
    IMAGE = "image"
    FILE = "file"
    AUDIO = "audio"
    UNKNOWN = "unknown"


class TaskType(str, Enum):
    """任务类型"""
    VIDEO_ANALYSIS = "video_analysis"
    IMAGE_ANALYSIS = "image_analysis"
    CHAT = "chat"
    QUERY = "query"
    UNKNOWN = "unknown"


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class UnifiedMessage:
    """
    统一消息对象
    
    所有渠道的消息都先转换为这个格式，再进入系统内部处理
    """
    # 基础信息
    channel: ChannelType = ChannelType.UNKNOWN
    message_type: MessageType = MessageType.UNKNOWN
    message_id: Optional[str] = None
    
    # 用户信息
    user_id: str = ""
    user_name: Optional[str] = None
    conversation_id: Optional[str] = None  # 会话 ID（群聊/私聊）
    
    # 消息内容
    text: str = ""
    file_url: Optional[str] = None  # 文件/视频 URL
    file_name: Optional[str] = None
    file_path: Optional[str] = None  # 本地文件路径（下载后）
    
    # 元数据
    timestamp: datetime = field(default_factory=datetime.now)
    extra: Optional[Dict[str, Any]] = None  # 渠道特定信息
    
    # 解析后的信息（可选）
    video_duration: Optional[float] = None  # 视频时长（秒）
    video_size: Optional[int] = None  # 文件大小（字节）
    
    def is_video(self) -> bool:
        """是否为视频消息"""
        return self.message_type == MessageType.VIDEO
    
    def is_text(self) -> bool:
        """是否为文本消息"""
        return self.message_type == MessageType.TEXT
    
    def has_file(self) -> bool:
        """是否包含文件"""
        return bool(self.file_url or self.file_path)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'channel': self.channel.value,
            'message_type': self.message_type.value,
            'message_id': self.message_id,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'conversation_id': self.conversation_id,
            'text': self.text,
            'file_url': self.file_url,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'timestamp': self.timestamp.isoformat(),
            'video_duration': self.video_duration,
            'video_size': self.video_size,
        }


@dataclass
class AnalysisTask:
    """
    分析任务对象
    
    由路由层创建，传递给分析层执行
    """
    # 任务基础信息
    task_id: str = ""
    task_type: TaskType = TaskType.UNKNOWN
    status: TaskStatus = TaskStatus.PENDING
    
    # 关联消息
    message: Optional[UnifiedMessage] = None
    
    # 分析参数
    video_path: Optional[str] = None
    user_id: str = ""
    
    # 分析结果
    ntrp_level: Optional[str] = None
    confidence: Optional[float] = None
    overall_score: Optional[int] = None
    report: Optional[str] = None
    
    # 错误信息
    error: Optional[str] = None
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def start(self):
        """标记任务开始"""
        self.status = TaskStatus.PROCESSING
        self.started_at = datetime.now()
    
    def complete(self, report: str, **kwargs):
        """标记任务完成"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.report = report
        
        # 可选参数
        if 'ntrp_level' in kwargs:
            self.ntrp_level = kwargs['ntrp_level']
        if 'confidence' in kwargs:
            self.confidence = kwargs['confidence']
        if 'overall_score' in kwargs:
            self.overall_score = kwargs['overall_score']
    
    def fail(self, error: str):
        """标记任务失败"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'task_type': self.task_type.value,
            'status': self.status.value,
            'user_id': self.user_id,
            'video_path': self.video_path,
            'ntrp_level': self.ntrp_level,
            'confidence': self.confidence,
            'overall_score': self.overall_score,
            'report': self.report,
            'error': self.error,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


# 类型别名
MessageOrDict = Union[UnifiedMessage, Dict[str, Any]]
TaskOrDict = Union[AnalysisTask, Dict[str, Any]]
