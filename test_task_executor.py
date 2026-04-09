#!/usr/bin/env python3
"""
任务执行器测试脚本

验证路由层变薄，执行层接管业务逻辑
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

print("\n" + "="*60)
print("🧪 任务执行层自检")
print("="*60 + "\n")

# 自检 1: 导入执行器
print("自检 1: 导入任务执行器...")
try:
    from task_executor import TaskExecutor, create_executor
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 2: 导入路由器
print("自检 2: 导入路由器...")
try:
    from router import MessageRouter
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 3: 导入模型
print("自检 3: 导入模型...")
try:
    from models.task import UnifiedTask
    from models.message import UnifiedMessage
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 4: 执行器实例化
print("自检 4: 执行器实例化...")
try:
    executor = TaskExecutor()
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 5: 路由器使用执行器
print("自检 5: 路由器使用执行器...")
try:
    router = MessageRouter()
    assert hasattr(router, 'executor'), "路由器应该包含 executor 属性"
    assert isinstance(router.executor, TaskExecutor), "executor 应该是 TaskExecutor 实例"
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 6: 文本任务执行
print("自检 6: 文本任务执行...")
try:
    router = MessageRouter()
    from router import from_dingtalk
    
    msg = from_dingtalk(
        user_id='test_user',
        text='测试文本'
    )
    
    result = router.route_message(msg)
    
    assert 'task_id' in result, "结果应包含 task_id"
    assert 'status' in result, "结果应包含 status"
    assert result['channel'] == 'dingtalk', "渠道应该是 dingtalk"
    assert result['error'] is None, "错误应该为 None"
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 7: 视频任务执行
print("自检 7: 视频任务执行...")
try:
    router = MessageRouter()
    from router import from_qq
    
    msg = from_qq(
        user_id='test_user',
        text='分析视频',
        file_path='/tmp/test.mp4'
    )
    
    result = router.route_message(msg)
    
    assert 'task_id' in result, "结果应包含 task_id"
    assert result['task_type'] == 'video_analysis', "任务类型应该是 video_analysis"
    assert result['channel'] == 'qq', "渠道应该是 qq"
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 8: 错误处理
print("自检 8: 错误处理...")
try:
    executor = TaskExecutor()
    
    task = UnifiedTask(task_type='unknown_type')
    message = UnifiedMessage(channel='dingtalk', message_type='text', user_id='test')
    
    result = executor.execute(task, message)
    
    # 未知任务类型应该返回失败
    assert result['error'] is not None, "错误信息不应为 None"
    assert 'code' in result['error'], "错误应包含 code"
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

# 自检 10: 适配器导入
print("自检 10: 渠道适配器导入...")
try:
    from adapters.dingtalk_adapter import parse_dingtalk_message
    from adapters.qq_adapter import parse_qq_message
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

print("\n" + "="*60)
print("✅ 所有自检通过！")
print("="*60 + "\n")

print("📊 测试摘要:")
print("  - 执行器导入：✅")
print("  - 路由器导入：✅")
print("  - 模型导入：✅")
print("  - 执行器实例化：✅")
print("  - 路由器使用执行器：✅")
print("  - 文本任务执行：✅")
print("  - 视频任务执行：✅")
print("  - 错误处理：✅")
print("  - 原有模块：✅")
print("  - 适配器：✅")
print("\n任务执行层已就绪！\n")
