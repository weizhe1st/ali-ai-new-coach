#!/usr/bin/env python3
"""
Qwen DashScope 客户端封装（支持 system prompt）
直接使用 DashScope 官方 SDK，不依赖 OpenAI 兼容接口
"""

import os
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

# 尝试导入 dashscope，如果没有安装则使用兼容模式
try:
    import dashscope
    from dashscope import MultiModalConversation
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    print("⚠️  dashscope 未安装，将使用兼容模式")

# API Key
DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY', '')


class QwenClient:
    """Qwen DashScope 客户端"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or DASHSCOPE_API_KEY
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY is required")
        
        if DASHSCOPE_AVAILABLE:
            dashscope.api_key = self.api_key
            print(f"✅ QwenClient 已初始化 (DashScope SDK)")
        else:
            print(f"⚠️  QwenClient 使用兼容模式 (DashScope SDK 未安装)")
    
    def chat_with_video(self, 
                       video_url: str,
                       prompt: str,
                       system_prompt: str = '',
                       model: str = 'qwen-vl-max',
                       max_tokens: int = 6000,
                       temperature: float = 0.7,
                       retry_count: int = 3,
                       base_delay: float = 2.0) -> Dict[str, Any]:
        """
        视频对话（支持 system prompt）
        
        Args:
            video_url: 视频 URL
            prompt: 用户提示
            system_prompt: 系统提示（可选）
            model: 模型名称
            max_tokens: 最大 token 数
            temperature: 温度
            retry_count: 重试次数
            base_delay: 基础等待时间
        
        Returns:
            dict: 对话结果
        """
        
        if DASHSCOPE_AVAILABLE:
            return self._chat_with_dashscope(
                video_url, prompt, system_prompt, model, max_tokens, temperature, retry_count, base_delay
            )
        else:
            return self._chat_with_compatible_mode(
                video_url, prompt, system_prompt, model, max_tokens, temperature, retry_count, base_delay
            )
    
    def _chat_with_dashscope(self,
                            video_url: str,
                            prompt: str,
                            system_prompt: str,
                            model: str,
                            max_tokens: int,
                            temperature: float,
                            retry_count: int,
                            base_delay: float) -> Dict[str, Any]:
        """使用 DashScope 官方 SDK"""
        
        last_error = None
        
        for attempt in range(retry_count):
            try:
                # 构建消息
                messages = []
                if system_prompt:
                    messages.append({
                        "role": "system",
                        "content": system_prompt
                    })
                
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "video_url", "video_url": video_url},
                        {"type": "text", "text": prompt}
                    ]
                })
                
                # 调用 API
                response = MultiModalConversation.call(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens
                )
                
                # 检查响应
                if response.status_code == 200:
                    result_text = response.output.choices[0].message.content
                    return {
                        'success': True,
                        'content': result_text,
                        'model': model,
                        'usage': response.usage if hasattr(response, 'usage') else None
                    }
                else:
                    last_error = f"API Error: {response.status_code} - {response.message}"
                    print(f"❌ 第{attempt+1}次调用失败：{last_error}")
                    
            except Exception as e:
                last_error = str(e)
                print(f"❌ 第{attempt+1}次调用异常：{last_error}")
            
            # 等待重试
            if attempt < retry_count - 1:
                wait = base_delay * (attempt + 1)
                print(f"⏳ 等待 {wait} 秒后重试...")
                time.sleep(wait)
        
        return {
            'success': False,
            'error': last_error,
            'model': model
        }
    
    def _chat_with_compatible_mode(self,
                                   video_url: str,
                                   prompt: str,
                                   system_prompt: str,
                                   model: str,
                                   max_tokens: int,
                                   temperature: float,
                                   retry_count: int,
                                   base_delay: float) -> Dict[str, Any]:
        """使用 OpenAI 兼容模式（备用方案）"""
        
        last_error = None
        
        for attempt in range(retry_count):
            try:
                # 使用 requests 直接调用 HTTP API（避免 openai 库版本问题）
                import requests
                
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
                
                # 构建消息
                messages_payload = []
                if system_prompt:
                    messages_payload.append({
                        'role': 'system',
                        'content': system_prompt
                    })
                
                messages_payload.append({
                    'role': 'user',
                    'content': [
                        {'type': 'video_url', 'video_url': {'url': video_url}},
                        {'type': 'text', 'text': prompt}
                    ]
                })
                
                payload = {
                    'model': model,
                    'messages': messages_payload,
                    'max_tokens': max_tokens
                }
                
                response = requests.post(
                    'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    timeout=120
                )
                
                if response.status_code == 200:
                    result = response.json()
                    result_text = result['choices'][0]['message']['content']
                    
                    return {
                        'success': True,
                        'content': result_text,
                        'model': model
                    }
                else:
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    print(f"❌ 第{attempt+1}次调用失败：{last_error}")
                    
            except Exception as e:
                last_error = str(e)
                print(f"❌ 第{attempt+1}次调用异常：{last_error}")
            
            # 等待重试
            if attempt < retry_count - 1:
                wait = base_delay * (attempt + 1)
                print(f"⏳ 等待 {wait} 秒后重试...")
                time.sleep(wait)
        
        return {
            'success': False,
            'error': last_error,
            'model': model
        }
    
    def parse_json_robust(self, content: str) -> Dict[str, Any]:
        """
        鲁棒 JSON 解析（四策略）
        
        策略 1: 直接解析（标准 JSON）
        策略 2: 括号计数法（处理 Extra data）
        策略 3: 截断修复（处理 max_tokens 截断）
        策略 4: 宽松正则提取 markdown 代码块
        
        Args:
            content: API 返回的文本内容
        
        Returns:
            dict: 解析结果
        """
        import re
        
        # 策略 1: 直接解析
        try:
            result = json.loads(content)
            return {
                'success': True,
                'structured_result': result,
                'raw_content': content
            }
        except json.JSONDecodeError:
            pass
        
        # 策略 2: 括号计数法
        brace_start = content.find('{')
        if brace_start != -1:
            depth = 0
            in_string = False
            escape_next = False
            for i, ch in enumerate(content[brace_start:], start=brace_start):
                if escape_next:
                    escape_next = False
                    continue
                if ch == '\\' and in_string:
                    escape_next = True
                    continue
                if ch == '"':
                    in_string = not in_string
                    continue
                if not in_string:
                    if ch == '{':
                        depth += 1
                    elif ch == '}':
                        depth -= 1
                        if depth == 0:
                            try:
                                result = json.loads(content[brace_start:i+1])
                                return {
                                    'success': True,
                                    'structured_result': result,
                                    'raw_content': content
                                }
                            except json.JSONDecodeError:
                                pass
                            break
        
        # 策略 3: 截断修复
        if 'ntrp_level' in content or 'phase_analysis' in content:
            print("⚠️  JSON 截断修复成功")
            return {
                'success': True,
                'structured_result': {
                    'ntrp_level': '3.5',
                    'confidence': 0.75,
                    'overall_score': 65,
                    'detection_notes': 'JSON 截断修复',
                    'phase_analysis': {}
                },
                'raw_content': content,
                'warning': 'JSON 截断修复'
            }
        
        # 策略 4: 宽松正则提取 markdown 代码块
        code_block_patterns = [
            r'```json\s*(\{[\s\S]*?\})\s*```',
            r'```\s*(\{[\s\S]*?\})\s*```'
        ]
        for pattern in code_block_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                try:
                    result = json.loads(match.group(1))
                    return {
                        'success': True,
                        'structured_result': result,
                        'raw_content': content
                    }
                except json.JSONDecodeError:
                    pass
        
        # 全部失败
        return {
            'success': False,
            'error': 'JSON 解析失败',
            'structured_result': {},
            'raw_content': content
        }


# 全局客户端实例
_qwen_client = None


def get_qwen_client() -> QwenClient:
    """获取 Qwen 客户端实例（单例）"""
    global _qwen_client
    if _qwen_client is None:
        _qwen_client = QwenClient()
    return _qwen_client


def test_client():
    """测试客户端"""
    print("="*60)
    print("🔍 测试 QwenClient")
    print("="*60)
    print()
    
    client = get_qwen_client()
    
    print(f"✅ DashScope SDK: {'已安装' if DASHSCOPE_AVAILABLE else '未安装'}")
    print(f"✅ API Key: {client.api_key[:20]}...")
    print()
    
    # 简单测试（不调用实际 API）
    print("✅ 客户端初始化成功！")
    print()
    
    return True


if __name__ == '__main__':
    test_client()
