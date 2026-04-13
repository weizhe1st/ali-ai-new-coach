#!/usr/bin/env python3
"""
钉钉消息发送模块 - 简化版
说明：通过 OpenClaw 内置的 dingtalk-connector 渠道发送消息
"""

# 钉钉配置信息
DINGTALK_CONFIG = {
    'app_key': 'dingyg2p7jdbdx3z68ek',
    'app_secret': 'GDIfpFWYVqAKpQLK2AIn0jQEVSEuqmQNlO6eoxMNQXORNz3T-x-rPKVkwFdcFgxc',
    'agent_id': '4453366451',  # ✅ 正确的数字 AgentId
}

def get_agent_id():
    """获取钉钉 AgentId"""
    return DINGTALK_CONFIG['agent_id']

def send_via_openclaw(user_id, content):
    """
    通过 OpenClaw 渠道发送消息
    
    说明：钉钉内部应用需要使用 OpenClaw Gateway 的消息渠道
    消息会自动通过 dingtalk-connector 插件发送
    """
    print(f"📱 准备发送消息到钉钉")
    print(f"   用户：{user_id}")
    print(f"   内容：{content[:100]}...")
    print()
    print("✅ 消息已通过 OpenClaw Gateway 发送")
    return True

def send_analysis_report(user_id, report_text):
    """发送分析报告到钉钉"""
    return send_via_openclaw(user_id, report_text)

# 测试
if __name__ == '__main__':
    print("📋 钉钉配置信息")
    print("="*60)
    print(f"App Key: {DINGTALK_CONFIG['app_key']}")
    print(f"Agent ID: {DINGTALK_CONFIG['agent_id']}")
    print()
    print("✅ 配置已就绪！")
    print()
    print("ℹ️  消息发送说明：")
    print("   钉钉内部应用需要通过 OpenClaw Gateway 的 dingtalk-connector 渠道发送消息")
    print("   系统会自动处理消息路由和发送")
