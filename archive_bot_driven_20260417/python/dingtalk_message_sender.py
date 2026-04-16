#!/usr/bin/env python3
"""
钉钉消息发送模块
用于发送网球 AI 分析报告到钉钉用户
"""

import requests
import time
import json

# 钉钉配置
DINGTALK_CONFIG = {
    'app_key': 'dingyg2p7jdbdx3z68ek',
    'app_secret': 'GDIfpFWYVqAKpQLK2AIn0jQEVSEuqmQNlO6eoxMNQXORNz3T-x-rPKVkwFdcFgxc',
    'agent_id': '4453366451',  # ✅ 已更新为正确的数字 AgentId
}

# Access Token 缓存
_access_token_cache = {
    'token': None,
    'expires_at': 0
}


def get_access_token():
    """获取钉钉 Access Token（带缓存）"""
    current_time = time.time()
    
    # 检查缓存
    if _access_token_cache['token'] and current_time < _access_token_cache['expires_at']:
        return _access_token_cache['token']
    
    # 获取新 Token
    url = 'https://oapi.dingtalk.com/gettoken'
    params = {
        'appkey': DINGTALK_CONFIG['app_key'],
        'appsecret': DINGTALK_CONFIG['app_secret']
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        result = response.json()
        
        if result.get('errcode') == 0:
            token = result.get('access_token')
            expires_in = result.get('expires_in', 7200)
            
            # 缓存 Token（提前 5 分钟过期）
            _access_token_cache['token'] = token
            _access_token_cache['expires_at'] = current_time + expires_in - 300
            
            return token
        else:
            print(f"❌ 获取 Access Token 失败：{result}")
            return None
            
    except Exception as e:
        print(f"❌ 请求失败：{e}")
        return None


def send_text_message(user_id, content):
    """发送文本消息到钉钉用户"""
    
    token = get_access_token()
    if not token:
        return False
    
    # 使用正确的 API
    url = 'https://oapi.dingtalk.com/topapi/message/sendtocommonconversation'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    # 尝试不同的 API 格式
    payload = {
        'userid': user_id,
        'agent_id': DINGTALK_CONFIG['agent_id'],
        'msgtype': 'text',
        'msgparam': {
            'content': content
        }
    }
    
    # 第一次尝试
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        result = response.json()
        
        # 如果 API 不合法，尝试备用 API
        if result.get('errcode') == 22 or '不合法ApiName' in str(result.get('sub_msg', '')):
            print("⚠️  尝试备用 API...")
            return _send_via_im_chat(user_id, content)
        
        if result.get('errcode') == 0:
            print(f"✅ 消息发送成功：{user_id}")
            return True
        else:
            print(f"❌ 消息发送失败：{result}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败：{e}")
        return _send_via_im_chat(user_id, content)
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        result = response.json()
        
        if result.get('errcode') == 0:
            print(f"✅ 消息发送成功：{user_id}")
            return True
        else:
            print(f"❌ 消息发送失败：{result}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败：{e}")
        return False


def send_markdown_message(user_id, title, content):
    """发送 Markdown 消息到钉钉用户"""
    
    token = get_access_token()
    if not token:
        return False
    
    url = 'https://oapi.dingtalk.com/topapi/message/sendtocommonconversation'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    # Markdown 格式
    markdown_text = f"## {title}\n\n{content}"
    
    payload = {
        'userid': user_id,
        'agent_id': DINGTALK_CONFIG['agent_id'],
        'msgtype': 'markdown',
        'msgparam': {
            'title': title,
            'text': markdown_text
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        result = response.json()
        
        if result.get('errcode') == 0:
            print(f"✅ Markdown 消息发送成功：{user_id}")
            return True
        else:
            print(f"❌ Markdown 消息发送失败：{result}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败：{e}")
        return False


def _send_via_im_chat(user_id, content):
    """使用 IM 聊天 API 发送消息（备用方案）"""
    token = get_access_token()
    if not token:
        return False
    
    url = 'https://oapi.dingtalk.com/v1.0/robot/otoMessages/send'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    payload = {
        'userIds': [user_id],
        'agentId': DINGTALK_CONFIG['agent_id'],
        'msgKey': 'sampleText',
        'msgParam': {
            'content': content
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        result = response.json()
        
        if result.get('success'):
            print(f"✅ 消息发送成功（IM API）: {user_id}")
            return True
        else:
            print(f"❌ IM API 发送失败：{result}")
            return False
    except Exception as e:
        print(f"❌ IM API 请求失败：{e}")
        return False


def send_analysis_report(user_id, report_text):
    """发送分析报告到钉钉用户"""
    return send_text_message(user_id, report_text)


# 测试
if __name__ == '__main__':
    print("🧪 测试钉钉消息发送...")
    
    # 测试 Token
    token = get_access_token()
    if token:
        print(f"✅ Access Token 获取成功：{token[:20]}...")
        print(f"✅ agent_id: {DINGTALK_CONFIG['agent_id']}")
        print()
        print("✅ 钉钉消息模块配置完成！")
    else:
        print("❌ 无法获取 Access Token")
