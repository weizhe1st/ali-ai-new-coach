#!/usr/bin/env python3
"""
统一消息路由层

负责：
- 接收来自不同渠道的原始消息
- 转换为统一消息对象
- 创建统一任务对象
- 判断消息类型并路由到对应处理器
- 视频任务接入现有分析能力
- 文本任务最小占位处理
"""

import os
import sys
from datetime import datetime
from typing import Optional, Callable, Dict, Any

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from models.message import UnifiedMessage, ChannelType, MessageType
from models.task import UnifiedTask


class MessageRouter:
    """
    消息路由器
    
    统一入口，负责将不同渠道的消息标准化并路由到对应处理链
    """
    
    def __init__(self):
        self.video_handler: Optional[Callable] = None
        self.text_handler: Optional[Callable] = None
        self.image_handler: Optional[Callable] = None
        
        print("✅ MessageRouter 已初始化")
    
    def register_video_handler(self, handler: Callable):
        """注册视频分析处理器"""
        self.video_handler = handler
        print("  ✓ 视频分析处理器已注册")
    
    def register_text_handler(self, handler: Callable):
        """注册文本消息处理器"""
        self.text_handler = handler
        print("  ✓ 文本消息处理器已注册")
    
    def register_image_handler(self, handler: Callable):
        """注册图片分析处理器"""
        self.image_handler = handler
        print("  ✓ 图片分析处理器已注册")
    
    def build_task_from_message(self, message: UnifiedMessage) -> UnifiedTask:
        """
        从统一消息创建统一任务
        
        Args:
            message: UnifiedMessage 对象
        
        Returns:
            UnifiedTask: 统一任务对象
        """
        task = UnifiedTask(
            task_type=self._guess_task_type(message),
            channel=message.channel.value,
            user_id=message.user_id,
            message_type=message.message_type.value,
            source_file_url=message.file_url,
            source_file_name=message.file_name,
            source_file_path=message.file_path,
            text_content=message.text if message.is_text() else None,
            extra={'message_id': message.message_id} if message.message_id else None
        )
        
        return task
    
    def _guess_task_type(self, message: UnifiedMessage) -> str:
        """根据消息类型猜测任务类型"""
        if message.is_video():
            return "video_analysis"
        elif message.message_type == MessageType.IMAGE:
            return "image_analysis"
        elif message.is_text():
            return "chat"
        else:
            return "chat"
    
    def route_message(self, message: UnifiedMessage) -> Optional[UnifiedTask]:
        """
        路由消息到对应处理器
        
        Args:
            message: UnifiedMessage 对象
        
        Returns:
            UnifiedTask: 任务对象（处理完成后）
        """
        
        print(f"\n📬 收到消息:")
        print(f"  渠道：{message.channel.value}")
        print(f"  类型：{message.message_type.value}")
        print(f"  用户：{message.user_id}")
        
        # 创建任务
        task = self.build_task_from_message(message)
        
        # 根据消息类型路由
        if message.is_video():
            return self.handle_video_message(message, task)
        elif message.is_text():
            return self.handle_text_message(message, task)
        elif message.message_type == MessageType.IMAGE:
            return self.handle_image_message(message, task)
        else:
            print(f"  ⚠️ 未知消息类型：{message.message_type}")
            task.fail("Unknown message type")
            return task
    
    def handle_video_message(self, message: UnifiedMessage, task: UnifiedTask) -> UnifiedTask:
        """
        处理视频消息
        
        接入现有分析能力（simple_integration.py 或 complete_analysis_service.py）
        
        Args:
            message: UnifiedMessage 对象
            task: UnifiedTask 对象
        
        Returns:
            UnifiedTask: 处理后的任务对象
        """
        
        print(f"  🎬 视频消息 -> 视频分析链")
        task.start()
        
        # 检查是否注册了处理器
        if not self.video_handler:
            print(f"  ⚠️  视频分析处理器未注册，使用默认处理")
            # 最小占位处理
            task.success(
                result={'ntrp_level': 'N/A', 'confidence': 0},
                report="视频分析功能已就绪，请配置分析处理器"
            )
            return task
        
        # 调用现有分析能力
        try:
            print(f"  📹 调用现有视频分析能力...")
            
            # 调用处理器（传入任务对象）
            result = self.video_handler(task)
            
            # 如果处理器返回了任务，使用返回的任务
            if isinstance(result, UnifiedTask):
                task = result
            
            print(f"  ✅ 视频分析完成")
            return task
            
        except Exception as e:
            task.fail(f"视频分析失败：{str(e)}")
            print(f"  ❌ 视频分析失败：{e}")
            return task
    
    def handle_text_message(self, message: UnifiedMessage, task: UnifiedTask) -> UnifiedTask:
        """
        处理文本消息
        
        最小占位实现
        
        Args:
            message: UnifiedMessage 对象
            task: UnifiedTask 对象
        
        Returns:
            UnifiedTask: 处理后的任务对象
        """
        
        print(f"  💬 文本消息 -> 聊天链")
        task.start()
        
        # 检查是否注册了处理器
        if not self.text_handler:
            print(f"  ℹ️  文本处理器未注册，返回占位结果")
            # 最小占位处理
            task.success(
                result={'message': 'text routing placeholder'},
                report="收到文本消息：" + (message.text[:50] if message.text else "")
            )
            return task
        
        # 调用处理器
        try:
            result = self.text_handler(task)
            if isinstance(result, UnifiedTask):
                task = result
            print(f"  ✅ 文本处理完成")
            return task
        except Exception as e:
            task.fail(f"文本处理失败：{str(e)}")
            print(f"  ❌ 文本处理失败：{e}")
            return task
    
    def handle_image_message(self, message: UnifiedMessage, task: UnifiedTask) -> UnifiedTask:
        """
        处理图片消息
        
        最小占位实现
        
        Args:
            message: UnifiedMessage 对象
            task: UnifiedTask 对象
        
        Returns:
            UnifiedTask: 处理后的任务对象
        """
        
        print(f"  🖼️  图片消息 -> 图片分析链")
        task.start()
        
        if not self.image_handler:
            print(f"  ℹ️  图片处理器未注册，返回占位结果")
            task.success(
                result={'message': 'image analysis placeholder'},
                report="图片分析功能待实现"
            )
            return task
        
        try:
            result = self.image_handler(task)
            if isinstance(result, UnifiedTask):
                task = result
            print(f"  ✅ 图片分析完成")
            return task
        except Exception as e:
            task.fail(f"图片分析失败：{str(e)}")
            print(f"  ❌ 图片分析失败：{e}")
            return task


# 便捷函数
def from_dingtalk(
    user_id: str,
    text: str = "",
    file_url: str = None,
    file_path: str = None,
    message_id: str = None,
    **kwargs
) -> UnifiedMessage:
    """从钉钉消息创建统一消息对象"""
    from models.message import ChannelType, MessageType
    
    # 如果有文件，优先识别为视频消息
    if file_url or file_path:
        msg_type = MessageType.VIDEO
    elif text:
        msg_type = MessageType.TEXT
    else:
        msg_type = MessageType.UNKNOWN
    
    return UnifiedMessage(
        channel=ChannelType.DINGTALK,
        message_type=msg_type,
        message_id=message_id,
        user_id=user_id,
        text=text,
        file_url=file_url,
        file_path=file_path,
        **kwargs
    )


def from_qq(
    user_id: str,
    text: str = "",
    file_url: str = None,
    file_path: str = None,
    message_id: str = None,
    **kwargs
) -> UnifiedMessage:
    """从 QQ 消息创建统一消息对象"""
    from models.message import ChannelType, MessageType
    
    # 如果有文件，优先识别为视频消息
    if file_url or file_path:
        msg_type = MessageType.VIDEO
    elif text:
        msg_type = MessageType.TEXT
    else:
        msg_type = MessageType.UNKNOWN
    
    return UnifiedMessage(
        channel=ChannelType.QQ,
        message_type=msg_type,
        message_id=message_id,
        user_id=user_id,
        text=text,
        file_url=file_url,
        file_path=file_path,
        **kwargs
    )


# 示例：视频分析处理器（接入现有能力）
def example_video_handler(task: UnifiedTask) -> UnifiedTask:
    """
    示例视频分析处理器
    
    实际使用时应调用 complete_analysis_service.py 或 simple_integration.py 中的分析能力
    """
    
    if not task.source_file_path:
        task.fail("未提供视频文件路径")
        return task
    
    print(f"    [示例处理器] 分析视频：{task.source_file_path}")
    
    # TODO: 这里应该调用现有的分析能力
    # 例如：from complete_analysis_service import analyze_video_complete
    # result = analyze_video_complete(task.source_file_path, task.user_id)
    
    # 临时占位
    task.success(
        result={
            'ntrp_level': '3.5',
            'confidence': 0.8,
            'overall_score': 70
        },
        report="示例分析报告：视频分析功能已就绪"
    )
    return task


# 示例：文本处理器
def example_text_handler(task: UnifiedTask) -> UnifiedTask:
    """示例文本处理器"""
    print(f"    [示例处理器] 处理文本：{task.text_content}")
    task.success(
        result={'message': '收到'},
        report=f"收到消息：{task.text_content}"
    )
    return task


# 测试
if __name__ == '__main__':
    print("\n" + "="*60)
    print("📬 消息路由器测试")
    print("="*60 + "\n")
    
    # 创建路由器
    router = MessageRouter()
    
    # 注册处理器
    router.register_video_handler(example_video_handler)
    router.register_text_handler(example_text_handler)
    
    # 测试视频消息
    print("\n--- 测试 1: 钉钉视频消息 ---")
    video_msg = from_dingtalk(
        user_id='test_user_123',
        text='帮我分析一下这个发球',
        file_path='/tmp/test_video.mp4'
    )
    
    task = router.route_message(video_msg)
    if task:
        print(f"\n任务状态：{task.status}")
        print(f"报告：{task.report[:50]}...")
    
    # 测试文本消息
    print("\n--- 测试 2: QQ 文本消息 ---")
    text_msg = from_qq(
        user_id='qq_user_456',
        text='你好，在吗？'
    )
    
    task = router.route_message(text_msg)
    if task:
        print(f"\n任务状态：{task.status}")
        print(f"报告：{task.report[:50]}...")
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60 + "\n")
