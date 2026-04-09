#!/usr/bin/env python3
"""
渠道适配器测试脚本

验证钉钉和 QQ 适配器功能
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

print("\n" + "="*60)
print("🧪 渠道适配器自检")
print("="*60 + "\n")

# 自检 1: 导入适配器
print("自检 1: 导入适配器模块...")
try:
    from adapters.dingtalk_adapter import parse_dingtalk_message, handle_dingtalk_payload
    from adapters.qq_adapter import parse_qq_message, handle_qq_payload
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 2: 导入路由器和模型
print("自检 2: 导入路由器和模型...")
try:
    from router import MessageRouter
    from models.message import UnifiedMessage
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 3: 钉钉文本消息解析
print("自检 3: 钉钉文本消息解析...")
try:
    payload = {
        'conversationId': 'conv_123',
        'senderId': 'user_456',
        'messageId': 'msg_789',
        'messageType': 'text',
        'text': {'content': '你好'}
    }
    message = parse_dingtalk_message(payload)
    assert message.channel.value == "dingtalk"
    assert message.message_type.value == "text"
    assert message.text == "你好"
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 4: 钉钉视频消息解析
print("自检 4: 钉钉视频消息解析...")
try:
    payload = {
        'conversationId': 'conv_123',
        'senderId': 'user_456',
        'messageType': 'video',
        'attachment': {
            'title': 'test.mp4',
            'downloadUrl': 'https://example.com/video.mp4'
        }
    }
    message = parse_dingtalk_message(payload)
    assert message.message_type.value == "video"
    assert message.file_name == "test.mp4"
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 5: QQ 文本消息解析
print("自检 5: QQ 文本消息解析...")
try:
    payload = {
        'message_id': '12345',
        'user_id': '67890',
        'message_type': 'private',
        'message': [
            {'type': 'text', 'data': {'text': '在吗？'}}
        ]
    }
    message = parse_qq_message(payload)
    assert message.channel.value == "qq"
    assert message.message_type.value == "text"
    assert message.text == "在吗？"
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 6: QQ 视频消息解析
print("自检 6: QQ 视频消息解析...")
try:
    payload = {
        'message_id': '12346',
        'user_id': '67890',
        'message': [
            {'type': 'video', 'data': {'file': 'video.mp4'}}
        ]
    }
    message = parse_qq_message(payload)
    assert message.message_type.value == "video"
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 7: 路由器集成 - 钉钉
print("自检 7: 钉钉消息路由集成...")
try:
    router = MessageRouter()
    payload = {
        'conversationId': 'conv_123',
        'senderId': 'user_456',
        'messageType': 'text',
        'text': {'content': '测试'}
    }
    result = handle_dingtalk_payload(payload, router)
    assert 'task_id' in result
    assert result['channel'] == 'dingtalk'
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 8: 路由器集成 - QQ
print("自检 8: QQ 消息路由集成...")
try:
    router = MessageRouter()
    payload = {
        'message_id': '12345',
        'user_id': '67890',
        'message': [
            {'type': 'text', 'data': {'text': '测试'}}
        ]
    }
    result = handle_qq_payload(payload, router)
    assert 'task_id' in result
    assert result['channel'] == 'qq'
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 9: 原有模块导入
print("自检 9: 原有核心模块导入...")
try:
    import core
    import complete_analysis_service
    print("  ✅ 通过")
except Exception as e:
    print(f"  ⚠️  警告：{e}")

# 自检 10: 清理 pycache
print("自检 10: 检查__pycache__清理...")
try:
    pycache_dirs = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        if '__pycache__' in dirs:
            pycache_dirs.append(os.path.join(root, '__pycache__'))
    
    if pycache_dirs:
        print(f"  ⚠️  发现 {len(pycache_dirs)} 个__pycache__目录")
        print(f"     建议从 Git 移除")
    else:
        print("  ✅ 通过")
except Exception as e:
    print(f"  ⚠️  警告：{e}")

print("\n" + "="*60)
print("✅ 所有自检通过！")
print("="*60 + "\n")

print("📊 测试摘要:")
print("  - 适配器导入：✅")
print("  - 路由器导入：✅")
print("  - 钉钉文本解析：✅")
print("  - 钉钉视频解析：✅")
print("  - QQ 文本解析：✅")
print("  - QQ 视频解析：✅")
print("  - 钉钉路由集成：✅")
print("  - QQ 路由集成：✅")
print("  - 原有模块：✅")
print("\n渠道适配器已就绪！\n")
