#!/usr/bin/env python3
"""
QQ 渠道适配器

负责将 QQ 原始消息转换为 UnifiedMessage 格式
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


def parse_qq_message(payload: Dict[str, Any]) -> UnifiedMessage:
    """
    解析 QQ 原始消息为统一消息对象
    
    Args:
        payload: QQ 原始消息 payload，预期结构：
        {
            "message_id": "消息 ID",
            "user_id": "用户 ID",
            "group_id": "群 ID（群聊时）",
            "message_type": "消息类型 (private/group)",
            "message": [
                {
                    "type": "text",
                    "data": {"text": "文本内容"}
                },
                {
                    "type": "image",
                    "data": {"file": "图片文件名", "url": "图片 URL"}
                },
                {
                    "type": "file",
                    "data": {"name": "文件名", "url": "文件 URL"}
                }
            ],
            "raw_message": "原始消息字符串",
            "time": 时间戳
        }
    
    Returns:
        UnifiedMessage: 统一消息对象
    """
    
    # 提取基础信息
    message_id = str(payload.get('message_id', ''))
    user_id = str(payload.get('user_id', ''))
    group_id = payload.get('group_id', None)
    conversation_id = str(group_id) if group_id else f"private_{user_id}"
    msg_time = payload.get('time', datetime.utcnow().timestamp())
    message_type_raw = payload.get('message_type', 'private')
    
    # 提取消息内容
    text_content = ''
    file_url = None
    file_name = None
    has_video = False
    has_image = False
    
    # 解析消息数组
    messages = payload.get('message', [])
    if isinstance(messages, list):
        for msg in messages:
            msg_type = msg.get('type', '')
            data = msg.get('data', {})
            
            if msg_type == 'text':
                text_content += data.get('text', '')
            
            elif msg_type == 'image':
                has_image = True
                file_url = data.get('url') or data.get('file')
                file_name = data.get('file', 'image.jpg')
            
            elif msg_type == 'video':
                has_video = True
                file_url = data.get('url') or data.get('file')
                file_name = data.get('file', 'video.mp4')
            
            elif msg_type == 'file':
                file_url = data.get('url') or data.get('file')
                file_name = data.get('name', 'file')
    
    # 也检查 raw_message
    if not text_content and not file_url:
        raw_message = payload.get('raw_message', '')
        if raw_message:
            text_content = raw_message
    
    # 判断统一消息类型
    if has_video:
        message_type = MessageType.VIDEO
    elif has_image:
        message_type = MessageType.IMAGE
    elif file_url:
        # 根据文件扩展名判断
        if file_name and file_name.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
            message_type = MessageType.VIDEO
        elif file_name and file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            message_type = MessageType.IMAGE
        else:
            message_type = MessageType.FILE
    elif text_content:
        message_type = MessageType.TEXT
    else:
        message_type = MessageType.UNKNOWN
    
    # 创建统一消息对象
    message = UnifiedMessage(
        channel=ChannelType.QQ,
        message_type=message_type,
        message_id=message_id,
        user_id=user_id,
        conversation_id=conversation_id,
        text=text_content,
        file_url=file_url,
        file_name=file_name,
        extra={
            'raw_payload': payload,
            'qq_msg_type': message_type_raw,
            'timestamp': datetime.fromtimestamp(msg_time).isoformat() if isinstance(msg_time, (int, float)) else str(msg_time)
        }
    )
    
    return message


def handle_qq_payload(payload: Dict[str, Any], router, reply_builder=None) -> Dict[str, Any]:
    """
    处理 QQ 原始消息 payload
    
    Args:
        payload: QQ 原始消息 payload
        router: MessageRouter 实例
        reply_builder: ReplyBuilder 实例（可选，默认创建新实例）
    
    Returns:
        dict: 统一返回结果（包含渠道输出格式）
    """
    
    # 解析为统一消息
    message = parse_qq_message(payload)
    
    # 通过路由器处理
    task = router.route_message(message)
    
    # 使用统一回复构建器
    if reply_builder is None:
        from reply_builder import ReplyBuilder
        reply_builder = ReplyBuilder()
    
    # 构建执行结果（TaskExecutor 格式）
    if task:
        execution_result = {
            'task_id': task.task_id,
            'task_type': task.task_type,
            'status': task.status,
            'channel': 'qq',
            'message_type': message.message_type.value,
            'result': task.result,
            'report': task.report,
            'error_code': task.error_code,
            'error_message': task.error_message,
            'current_stage': task.current_stage
        }
        
        # 通过 ReplyBuilder 构建统一回复
        reply = reply_builder.build_reply(execution_result)
        
        # 渲染为 QQ 渠道格式
        channel_output = reply_builder.render_reply_for_channel(reply, 'qq')
        
        return {
            'success': True,
            'channel': 'qq',
            'output': channel_output,
            'reply_object': reply,
            'task_id': task.task_id
        }
    else:
        # Router 返回 None 的错误情况
        error_result = {
            'task_id': None,
            'task_type': 'unknown',
            'status': 'failed',
            'channel': 'qq',
            'error_code': 'ROUTER_RETURNED_NONE',
            'error_message': 'Router returned None',
            'current_stage': 'routing'
        }
        
        reply = reply_builder.build_reply(error_result)
        channel_output = reply_builder.render_reply_for_channel(reply, 'qq')
        
        return {
            'success': False,
            'channel': 'qq',
            'output': channel_output,
            'reply_object': reply,
            'task_id': None
        }


# 测试
if __name__ == '__main__':
    print("\n" + "="*60)
    print("📱 QQ 适配器测试")
    print("="*60 + "\n")
    
    # 测试文本消息
    print("--- 测试 1: QQ 私聊文本消息 ---")
    text_payload = {
        'message_id': '12345',
        'user_id': '67890',
        'message_type': 'private',
        'message': [
            {'type': 'text', 'data': {'text': '你好，在吗？'}}
        ],
        'raw_message': '你好，在吗？',
        'time': 1712628000
    }
    
    message = parse_qq_message(text_payload)
    print(f"渠道：{message.channel.value}")
    print(f"类型：{message.message_type.value}")
    print(f"用户：{message.user_id}")
    print(f"文本：{message.text}")
    print(f"✅ 通过")
    
    # 测试群聊视频消息
    print("\n--- 测试 2: QQ 群聊视频消息 ---")
    video_payload = {
        'message_id': '12346',
        'user_id': '67890',
        'group_id': '111222',
        'message_type': 'group',
        'message': [
            {'type': 'video', 'data': {'file': 'video.mp4', 'url': 'https://example.com/video.mp4'}}
        ],
        'time': 1712628060
    }
    
    message = parse_qq_message(video_payload)
    print(f"渠道：{message.channel.value}")
    print(f"类型：{message.message_type.value}")
    print(f"会话：{message.conversation_id}")
    print(f"文件：{message.file_name}")
    print(f"✅ 通过")
    
    # 测试图片消息
    print("\n--- 测试 3: QQ 图片消息 ---")
    image_payload = {
        'message_id': '12347',
        'user_id': '67890',
        'message_type': 'private',
        'message': [
            {'type': 'image', 'data': {'file': 'image.jpg', 'url': 'https://example.com/image.jpg'}}
        ],
        'time': 1712628120
    }
    
    message = parse_qq_message(image_payload)
    print(f"渠道：{message.channel.value}")
    print(f"类型：{message.message_type.value}")
    print(f"✅ 通过")
    
    # 测试混合消息
    print("\n--- 测试 4: QQ 混合消息（文本 + 文件） ---")
    mixed_payload = {
        'message_id': '12348',
        'user_id': '67890',
        'message_type': 'private',
        'message': [
            {'type': 'text', 'data': {'text': '帮我看看这个文件'}},
            {'type': 'file', 'data': {'name': 'document.pdf', 'url': 'https://example.com/doc.pdf'}}
        ],
        'time': 1712628180
    }
    
    message = parse_qq_message(mixed_payload)
    print(f"渠道：{message.channel.value}")
    print(f"类型：{message.message_type.value}")
    print(f"文本：{message.text}")
    print(f"文件：{message.file_name}")
    print(f"✅ 通过")
    
    # 测试空消息
    print("\n--- 测试 5: 空消息 ---")
    empty_payload = {
        'message_id': '12349',
        'user_id': '67890',
        'message_type': 'private',
        'message': []
    }
    
    message = parse_qq_message(empty_payload)
    print(f"渠道：{message.channel.value}")
    print(f"类型：{message.message_type.value}")
    print(f"✅ 通过")
    
    print("\n" + "="*60)
    print("✅ 所有测试通过")
    print("="*60 + "\n")
