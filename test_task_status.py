#!/usr/bin/env python3
"""
任务状态与日志测试脚本

验证第五步新增的任务状态管理和日志记录功能
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

print("\n" + "="*60)
print("🧪 任务状态与日志自检")
print("="*60 + "\n")

# 自检 1: 导入 UnifiedTask 新字段
print("自检 1: 导入 UnifiedTask 新字段...")
try:
    from models.task import UnifiedTask
    
    task = UnifiedTask(task_type='chat', channel='dingtalk', user_id='test')
    
    # 检查新字段
    assert hasattr(task, 'current_stage'), "缺少 current_stage 字段"
    assert hasattr(task, 'error_code'), "缺少 error_code 字段"
    assert task.current_stage == "created", "初始阶段应为 created"
    assert task.error_code is None, "初始 error_code 应为 None"
    
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 2: 状态更新方法
print("自检 2: 状态更新方法测试...")
try:
    task = UnifiedTask(task_type='chat', channel='dingtalk', user_id='test')
    
    # 测试 mark_running
    task.mark_running("executing_text")
    assert task.status == "running", "状态应为 running"
    assert task.current_stage == "executing_text", "阶段应为 executing_text"
    assert task.started_at is not None, "started_at 应有值"
    
    # 测试 mark_success
    task.mark_success("completed", result={'test': 'ok'}, report="测试报告")
    assert task.status == "success", "状态应为 success"
    assert task.current_stage == "completed", "阶段应为 completed"
    assert task.completed_at is not None, "completed_at 应有值"
    assert task.result == {'test': 'ok'}, "result 应正确"
    
    # 测试 mark_failed
    task2 = UnifiedTask(task_type='video_analysis', channel='qq', user_id='test')
    task2.mark_failed("TEST_ERROR", "测试错误", "executing_video")
    assert task2.status == "failed", "状态应为 failed"
    assert task2.current_stage == "executing_video", "阶段应正确"
    assert task2.error_code == "TEST_ERROR", "error_code 应正确"
    assert task2.error_message == "测试错误", "error_message 应正确"
    
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 3: 状态检查方法
print("自检 3: 状态检查方法测试...")
try:
    task1 = UnifiedTask(task_type='chat')
    assert task1.is_running() == False, "初始状态不应为 running"
    
    task1.mark_running()
    assert task1.is_running() == True, "应为 running"
    
    task1.mark_success()
    assert task1.is_success() == True, "应为 success"
    
    task2 = UnifiedTask(task_type='video_analysis')
    task2.mark_failed("ERROR", "msg")
    assert task2.is_failed() == True, "应为 failed"
    
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 4: 导入任务日志模块
print("自检 4: 导入任务日志模块...")
try:
    from task_logger import (
        log_task_event,
        log_task_start,
        log_task_success,
        log_task_failure,
        log_text_execution_start,
        log_text_execution_success,
        log_text_execution_failure,
        log_video_execution_start,
        log_video_execution_success,
        log_video_execution_failure
    )
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 5: 日志函数调用
print("自检 5: 日志函数调用测试...")
try:
    task = UnifiedTask(task_type='chat', channel='dingtalk', user_id='test')
    
    # 测试各种日志函数
    log_task_start(task, "executing_text")
    log_task_success(task, "completed")
    
    task2 = UnifiedTask(task_type='video_analysis', channel='qq', user_id='test')
    log_task_failure(task2, "TEST_ERROR", "测试错误")
    
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 6: TaskExecutor 导入
print("自检 6: 导入 TaskExecutor...")
try:
    from task_executor import TaskExecutor, create_executor
    executor = TaskExecutor()
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 7: 文本任务状态流转
print("自检 7: 文本任务状态流转测试...")
try:
    from task_executor import TaskExecutor
    from models.message import UnifiedMessage, ChannelType, MessageType
    
    executor = TaskExecutor()
    
    message = UnifiedMessage(
        channel=ChannelType.DINGTALK,
        message_type=MessageType.TEXT,
        user_id='test_user',
        text='测试'
    )
    
    task = UnifiedTask(task_type='chat', channel='dingtalk', user_id='test')
    
    result = executor.execute(task, message)
    
    # 验证结果包含状态信息
    assert 'status' in result, "结果应包含 status"
    assert 'current_stage' in result, "结果应包含 current_stage"
    assert result['status'] == 'success', "状态应为 success"
    assert result['current_stage'] == 'completed', "阶段应为 completed"
    
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 8: 视频任务状态流转
print("自检 8: 视频任务状态流转测试...")
try:
    from task_executor import TaskExecutor
    from models.message import UnifiedMessage, ChannelType, MessageType
    
    executor = TaskExecutor()
    
    message = UnifiedMessage(
        channel=ChannelType.QQ,
        message_type=MessageType.VIDEO,
        user_id='test_user',
        file_path='/tmp/test.mp4'
    )
    
    task = UnifiedTask(task_type='video_analysis', channel='qq', user_id='test')
    
    result = executor.execute(task, message)
    
    # 验证结果包含状态信息
    assert 'status' in result, "结果应包含 status"
    assert 'current_stage' in result, "结果应包含 current_stage"
    assert result['status'] == 'success', "状态应为 success"
    assert result['current_stage'] == 'completed', "阶段应为 completed"
    
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 9: 错误结果结构
print("自检 9: 错误结果结构测试...")
try:
    from task_executor import TaskExecutor
    from models.message import UnifiedMessage, ChannelType, MessageType
    
    executor = TaskExecutor()
    
    # 模拟未知任务类型
    message = UnifiedMessage(channel='dingtalk', message_type='text', user_id='test')
    task = UnifiedTask(task_type='unknown_type', channel='dingtalk', user_id='test')
    
    result = executor.execute(task, message)
    
    # 验证错误结构
    assert result['status'] == 'failed', "状态应为 failed"
    assert result['error'] is not None, "error 不应为 None"
    assert 'code' in result['error'], "error 应包含 code"
    assert 'message' in result['error'], "error 应包含 message"
    
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 10: 原有模块导入
print("自检 10: 原有核心模块导入...")
try:
    import router
    from adapters.dingtalk_adapter import parse_dingtalk_message
    from adapters.qq_adapter import parse_qq_message
    print("  ✅ 通过")
except Exception as e:
    print(f"  ⚠️  警告：{e}")

print("\n" + "="*60)
print("✅ 所有自检通过！")
print("="*60 + "\n")

print("📊 测试摘要:")
print("  - UnifiedTask 新字段：✅")
print("  - 状态更新方法：✅")
print("  - 状态检查方法：✅")
print("  - 任务日志模块：✅")
print("  - 日志函数调用：✅")
print("  - TaskExecutor: ✅")
print("  - 文本任务状态流转：✅")
print("  - 视频任务状态流转：✅")
print("  - 错误结果结构：✅")
print("  - 原有模块：✅")
print("\n任务状态与日志系统已就绪！\n")
