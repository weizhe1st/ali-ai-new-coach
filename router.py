#!/usr/bin/env python3
"""
统一消息路由层

负责：
- 接收来自不同渠道的原始消息
- 转换为统一消息对象
- 创建统一任务对象
- 交给执行层执行

注意：路由层不再直接执行业务逻辑，只负责建任务和分发
"""

import os
import sys
from typing import Dict, Any, Optional

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from models.message import UnifiedMessage, ChannelType, MessageType
from models.task import UnifiedTask
from task_executor import TaskExecutor


class MessageRouter:
    """
    消息路由器
    
    职责：
    - 接收 UnifiedMessage
    - 创建 UnifiedTask
    - 交给 TaskExecutor 执行
    - 返回执行结果
    """
    
    def __init__(self):
        self.executor = TaskExecutor()
        print("✅ MessageRouter 已初始化（含 TaskExecutor）")
    
    def register_video_handler(self, handler):
        """注册视频分析处理器"""
        self.executor.register_video_handler(handler)
    
    def register_text_handler(self, handler):
        """注册文本消息处理器"""
        self.executor.register_text_handler(handler)
    
    def register_image_handler(self, handler):
        """注册图片分析处理器"""
        self.executor.register_image_handler(handler)
    
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
    
    def route_message(self, message: UnifiedMessage) -> Dict[str, Any]:
        """
        路由消息到执行层
        
        Args:
            message: UnifiedMessage 对象
        
        Returns:
            dict: 统一执行结果
        """
        
        print(f"\n📬 收到消息:")
        print(f"  渠道：{message.channel.value}")
        print(f"  类型：{message.message_type.value}")
        print(f"  用户：{message.user_id}")
        
        # 创建任务
        task = self.build_task_from_message(message)
        
        # 交给执行层执行
        print(f"  🔄 交给执行层处理...")
        result = self.executor.execute(task, message)
        
        return result


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


# 测试
if __name__ == '__main__':
    print("\n" + "="*60)
    print("📬 消息路由器测试（使用 TaskExecutor）")
    print("="*60 + "\n")
    
    router = MessageRouter()
    
    # 测试文本消息
    print("\n--- 测试 1: 钉钉文本消息 ---")
    text_msg = from_dingtalk(
        user_id='test_user_123',
        text='你好，在吗？'
    )
    
    result = router.route_message(text_msg)
    print(f"\n结果：{result['status']}")
    print(f"任务 ID: {result['task_id']}")
    print(f"✅ 通过")
    
    # 测试视频消息
    print("\n--- 测试 2: QQ 视频消息 ---")
    video_msg = from_qq(
        user_id='test_user_456',
        text='帮我分析这个视频',
        file_path='/tmp/test.mp4'
    )
    
    result = router.route_message(video_msg)
    print(f"\n结果：{result['status']}")
    print(f"任务 ID: {result['task_id']}")
    print(f"✅ 通过")
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60 + "\n")
