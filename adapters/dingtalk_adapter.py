#!/usr/bin/env python3
"""
钉钉渠道适配器

负责将钉钉原始消息转换为 UnifiedMessage 格式
不处理业务逻辑，只负责消息解析和格式转换
"""

import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from models.message import UnifiedMessage, ChannelType, MessageType


def parse_dingtalk_message(payload: Dict[str, Any]) -> UnifiedMessage:
    """
    解析钉钉原始消息为统一消息对象
    
    Args:
        payload: 钉钉原始消息 payload，预期结构：
        {
            "conversationId": "会话 ID",
            "senderId": "发送者 ID",
            "senderNick": "发送者昵称",
            "messageId": "消息 ID",
            "messageType": "消息类型 (text/image/video/file)",
            "text": {"content": "文本内容"},
            "richText": {"content": "富文本内容"},
            "attachment": {
                "title": "文件标题",
                "downloadUrl": "下载 URL"
            },
            "createdAt": "时间戳"
        }
    
    Returns:
        UnifiedMessage: 统一消息对象
    """
    
    # 提取基础信息
    conversation_id = payload.get('conversationId', '')
    user_id = payload.get('senderId', '')
    user_name = payload.get('senderNick', '')
    message_id = payload.get('messageId', '')
    msg_type = payload.get('messageType', 'unknown').lower()
    timestamp = payload.get('createdAt', datetime.utcnow().isoformat())
    
    # 提取消息内容
    text_content = ''
    file_url = None
    file_name = None
    
    # 解析文本消息
    if msg_type == 'text':
        text_obj = payload.get('text', {})
        text_content = text_obj.get('content', '') if isinstance(text_obj, dict) else str(text_obj)
    
    # 解析富文本消息
    elif msg_type == 'richText':
        rich_text = payload.get('richText', {})
        text_content = rich_text.get('content', '') if isinstance(rich_text, dict) else str(rich_text)
    
    # 解析图片消息
    elif msg_type == 'image':
        attachment = payload.get('attachment', {})
        if isinstance(attachment, dict):
            file_url = attachment.get('downloadUrl') or attachment.get('url')
            file_name = attachment.get('title', 'image.jpg')
    
    # 解析视频/文件消息
    elif msg_type in ['video', 'file']:
        attachment = payload.get('attachment', {})
        if isinstance(attachment, dict):
            file_url = attachment.get('downloadUrl') or attachment.get('url')
            file_name = attachment.get('title', 'file')
    
    # 判断统一消息类型
    if file_url:
        # 根据文件扩展名判断具体类型
        if file_name.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
            message_type = MessageType.VIDEO
        elif file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            message_type = MessageType.IMAGE
        else:
            message_type = MessageType.FILE
    elif text_content:
        message_type = MessageType.TEXT
    else:
        message_type = MessageType.UNKNOWN
    
    # 创建统一消息对象
    message = UnifiedMessage(
        channel=ChannelType.DINGTALK,
        message_type=message_type,
        message_id=message_id,
        user_id=user_id,
        user_name=user_name,
        conversation_id=conversation_id,
        text=text_content,
        file_url=file_url,
        file_name=file_name,
        extra={
            'raw_payload': payload,
            'dingtalk_msg_type': msg_type,
            'timestamp': timestamp
        }
    )
    
    return message


def handle_dingtalk_payload(payload: Dict[str, Any], router) -> Dict[str, Any]:
    """
    处理钉钉原始消息 payload
    
    Args:
        payload: 钉钉原始消息 payload
        router: MessageRouter 实例
    
    Returns:
        dict: 统一返回结果
    """
    
    # 解析为统一消息
    message = parse_dingtalk_message(payload)
    
    # 通过路由器处理
    task = router.route_message(message)
    
    # 返回统一结果
    if task:
        return {
            'task_id': task.task_id,
            'task_type': task.task_type,
            'status': task.status,
            'channel': 'dingtalk',
            'message_type': message.message_type.value,
            'result': task.result,
            'report': task.report,
            'error_message': task.error_message
        }
    else:
        return {
            'task_id': None,
            'task_type': 'unknown',
            'status': 'failed',
            'channel': 'dingtalk',
            'error_message': 'Router returned None'
        }


# 测试
if __name__ == '__main__':
    print("\n" + "="*60)
    print("📱 钉钉适配器测试")
    print("="*60 + "\n")
    
    # 测试文本消息
    print("--- 测试 1: 钉钉文本消息 ---")
    text_payload = {
        'conversationId': 'conv_123',
        'senderId': 'user_456',
        'senderNick': '测试用户',
        'messageId': 'msg_789',
        'messageType': 'text',
        'text': {'content': '你好，帮我分析一下这个视频'},
        'createdAt': '2026-04-09T10:00:00Z'
    }
    
    message = parse_dingtalk_message(text_payload)
    print(f"渠道：{message.channel.value}")
    print(f"类型：{message.message_type.value}")
    print(f"用户：{message.user_id}")
    print(f"文本：{message.text}")
    print(f"✅ 通过")
    
    # 测试视频消息
    print("\n--- 测试 2: 钉钉视频消息 ---")
    video_payload = {
        'conversationId': 'conv_123',
        'senderId': 'user_456',
        'senderNick': '测试用户',
        'messageId': 'msg_790',
        'messageType': 'video',
        'attachment': {
            'title': '发球视频.mp4',
            'downloadUrl': 'https://example.com/video.mp4'
        },
        'createdAt': '2026-04-09T10:01:00Z'
    }
    
    message = parse_dingtalk_message(video_payload)
    print(f"渠道：{message.channel.value}")
    print(f"类型：{message.message_type.value}")
    print(f"文件：{message.file_name}")
    print(f"URL: {message.file_url}")
    print(f"✅ 通过")
    
    # 测试文件消息
    print("\n--- 测试 3: 钉钉文件消息 ---")
    file_payload = {
        'conversationId': 'conv_123',
        'senderId': 'user_456',
        'messageId': 'msg_791',
        'messageType': 'file',
        'attachment': {
            'title': '文档.pdf',
            'downloadUrl': 'https://example.com/doc.pdf'
        }
    }
    
    message = parse_dingtalk_message(file_payload)
    print(f"渠道：{message.channel.value}")
    print(f"类型：{message.message_type.value}")
    print(f"✅ 通过")
    
    # 测试未知消息类型
    print("\n--- 测试 4: 未知消息类型 ---")
    unknown_payload = {
        'conversationId': 'conv_123',
        'senderId': 'user_456',
        'messageId': 'msg_792',
        'messageType': 'unknown_type'
    }
    
    message = parse_dingtalk_message(unknown_payload)
    print(f"渠道：{message.channel.value}")
    print(f"类型：{message.message_type.value}")
    print(f"✅ 通过")
    
    print("\n" + "="*60)
    print("✅ 所有测试通过")
    print("="*60 + "\n")
