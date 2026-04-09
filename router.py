#!/usr/bin/env python3
"""
统一消息路由层

负责：
- 接收来自不同渠道的原始消息
- 转换为统一消息对象
- 判断消息类型
- 创建任务对象
- 分发到对应处理链
"""

import os
import sys
import uuid
from datetime import datetime
from typing import Optional, Callable

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from models.message import (
    UnifiedMessage,
    AnalysisTask,
    ChannelType,
    MessageType,
    TaskType,
    TaskStatus
)


class MessageRouter:
    """
    消息路由器
    
    统一入口，负责将不同渠道的消息标准化并路由到对应处理链
    """
    
    def __init__(self):
        self.video_analysis_handler: Optional[Callable] = None
        self.text_handler: Optional[Callable] = None
        self.image_handler: Optional[Callable] = None
        
        print("✅ MessageRouter 已初始化")
    
    def register_video_handler(self, handler: Callable):
        """注册视频分析处理器"""
        self.video_analysis_handler = handler
        print("  ✓ 视频分析处理器已注册")
    
    def register_text_handler(self, handler: Callable):
        """注册文本消息处理器"""
        self.text_handler = handler
        print("  ✓ 文本消息处理器已注册")
    
    def register_image_handler(self, handler: Callable):
        """注册图片分析处理器"""
        self.image_handler = handler
        print("  ✓ 图片分析处理器已注册")
    
    def create_message(
        self,
        channel: str,
        message_type: str,
        user_id: str,
        text: str = "",
        file_url: str = None,
        file_path: str = None,
        **kwargs
    ) -> UnifiedMessage:
        """
        创建统一消息对象
        
        Args:
            channel: 渠道名称 (dingtalk/qq/feishu)
            message_type: 消息类型 (text/video/image/file)
            user_id: 用户 ID
            text: 文本内容
            file_url: 文件 URL
            file_path: 本地文件路径
            **kwargs: 其他参数
        
        Returns:
            UnifiedMessage: 统一消息对象
        """
        
        # 转换渠道类型
        channel_map = {
            'dingtalk': ChannelType.DINGTALK,
            'qq': ChannelType.QQ,
            'feishu': ChannelType.FEISHU,
            'wechat': ChannelType.WECHAT,
        }
        channel_enum = channel_map.get(channel.lower(), ChannelType.UNKNOWN)
        
        # 转换消息类型
        type_map = {
            'text': MessageType.TEXT,
            'video': MessageType.VIDEO,
            'image': MessageType.IMAGE,
            'file': MessageType.FILE,
            'audio': MessageType.AUDIO,
        }
        type_enum = type_map.get(message_type.lower(), MessageType.UNKNOWN)
        
        # 创建消息对象
        message = UnifiedMessage(
            channel=channel_enum,
            message_type=type_enum,
            message_id=kwargs.get('message_id', str(uuid.uuid4())),
            user_id=user_id,
            user_name=kwargs.get('user_name'),
            conversation_id=kwargs.get('conversation_id'),
            text=text,
            file_url=file_url,
            file_name=kwargs.get('file_name'),
            file_path=file_path,
            extra=kwargs.get('extra'),
        )
        
        return message
    
    def create_task(
        self,
        message: UnifiedMessage,
        task_type: str = "video_analysis"
    ) -> AnalysisTask:
        """
        创建分析任务
        
        Args:
            message: 统一消息对象
            task_type: 任务类型 (video_analysis/image_analysis/chat)
        
        Returns:
            AnalysisTask: 分析任务对象
        """
        
        # 转换任务类型
        type_map = {
            'video_analysis': TaskType.VIDEO_ANALYSIS,
            'image_analysis': TaskType.IMAGE_ANALYSIS,
            'chat': TaskType.CHAT,
            'query': TaskType.QUERY,
        }
        task_type_enum = type_map.get(task_type.lower(), TaskType.UNKNOWN)
        
        # 创建任务
        task = AnalysisTask(
            task_id=str(uuid.uuid4()),
            task_type=task_type_enum,
            message=message,
            video_path=message.file_path,
            user_id=message.user_id,
        )
        
        return task
    
    def route(self, message: UnifiedMessage) -> Optional[AnalysisTask]:
        """
        路由消息到对应处理器
        
        Args:
            message: 统一消息对象
        
        Returns:
            AnalysisTask: 分析任务对象（如果已创建）
        """
        
        print(f"\n📬 收到消息:")
        print(f"  渠道：{message.channel.value}")
        print(f"  类型：{message.message_type.value}")
        print(f"  用户：{message.user_id}")
        
        # 根据消息类型路由
        if message.is_video():
            return self._route_video(message)
        elif message.is_text():
            return self._route_text(message)
        elif message.message_type == MessageType.IMAGE:
            return self._route_image(message)
        else:
            print(f"  ⚠️ 未知消息类型：{message.message_type}")
            return None
    
    def _route_video(self, message: UnifiedMessage) -> Optional[AnalysisTask]:
        """路由视频消息"""
        
        print(f"  🎬 视频消息 -> 视频分析链")
        
        if not self.video_analysis_handler:
            print(f"  ❌ 视频分析处理器未注册")
            return None
        
        # 创建任务
        task = self.create_task(message, 'video_analysis')
        task.start()
        
        # 调用处理器
        try:
            result = self.video_analysis_handler(task)
            print(f"  ✅ 视频分析完成")
            return result
        except Exception as e:
            task.fail(str(e))
            print(f"  ❌ 视频分析失败：{e}")
            return task
    
    def _route_text(self, message: UnifiedMessage) -> Optional[AnalysisTask]:
        """路由文本消息"""
        
        print(f"  💬 文本消息 -> 聊天链")
        
        if not self.text_handler:
            print(f"  ℹ️  文本处理器未注册，跳过")
            return None
        
        # 创建任务
        task = self.create_task(message, 'chat')
        task.start()
        
        try:
            result = self.text_handler(task)
            print(f"  ✅ 文本处理完成")
            return result
        except Exception as e:
            task.fail(str(e))
            print(f"  ❌ 文本处理失败：{e}")
            return task
    
    def _route_image(self, message: UnifiedMessage) -> Optional[AnalysisTask]:
        """路由图片消息"""
        
        print(f"  🖼️  图片消息 -> 图片分析链")
        
        if not self.image_handler:
            print(f"  ℹ️  图片处理器未注册，跳过")
            return None
        
        # 创建任务
        task = self.create_task(message, 'image_analysis')
        task.start()
        
        try:
            result = self.image_handler(task)
            print(f"  ✅ 图片分析完成")
            return result
        except Exception as e:
            task.fail(str(e))
            print(f"  ❌ 图片分析失败：{e}")
            return task


# 便捷函数
def from_dingtalk(
    user_id: str,
    text: str = "",
    file_url: str = None,
    **kwargs
) -> UnifiedMessage:
    """
    从钉钉消息创建统一消息对象
    
    Args:
        user_id: 钉钉用户 ID
        text: 消息文本
        file_url: 文件/视频 URL
        **kwargs: 其他参数
    
    Returns:
        UnifiedMessage
    """
    router = MessageRouter()
    return router.create_message(
        channel='dingtalk',
        message_type='video' if file_url else 'text',
        user_id=user_id,
        text=text,
        file_url=file_url,
        **kwargs
    )


def from_qq(
    user_id: str,
    text: str = "",
    file_url: str = None,
    **kwargs
) -> UnifiedMessage:
    """
    从 QQ 消息创建统一消息对象
    """
    router = MessageRouter()
    return router.create_message(
        channel='qq',
        message_type='video' if file_url else 'text',
        user_id=user_id,
        text=text,
        file_url=file_url,
        **kwargs
    )


# 测试
if __name__ == '__main__':
    print("\n" + "="*60)
    print("📬 消息路由器测试")
    print("="*60 + "\n")
    
    # 创建路由器
    router = MessageRouter()
    
    # 注册处理器（模拟）
    def mock_video_handler(task):
        print(f"    [Mock] 视频分析处理中...")
        task.complete(report="模拟分析报告", ntrp_level="3.5", confidence=0.8)
        return task
    
    router.register_video_handler(mock_video_handler)
    
    # 测试视频消息
    print("\n--- 测试 1: 钉钉视频消息 ---")
    video_msg = from_dingtalk(
        user_id='test_user_123',
        text='帮我分析一下这个发球',
        file_url='https://example.com/video.mp4',
        file_path='/tmp/video.mp4'
    )
    
    task = router.route(video_msg)
    if task:
        print(f"\n任务状态：{task.status.value}")
        print(f"报告：{task.report[:50]}...")
    
    # 测试文本消息
    print("\n--- 测试 2: QQ 文本消息 ---")
    text_msg = router.create_message(
        channel='qq',
        message_type='text',
        user_id='qq_user_456',
        text='你好'
    )
    
    task = router.route(text_msg)
    if task:
        print(f"\n任务状态：{task.status.value}")
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60 + "\n")
