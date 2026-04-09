#!/usr/bin/env python3
"""
轻量任务日志模块

提供最小可用的结构化日志记录能力
当前为简单实现，后续可升级为正式日志系统
"""

import sys
from datetime import datetime
from typing import Optional, Dict, Any

# 导入任务模型
try:
    from models.task import UnifiedTask
except ImportError:
    # 如果在根目录运行
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from models.task import UnifiedTask


def log_task_event(
    task: UnifiedTask,
    event: str,
    detail: str = "",
    extra: Optional[Dict[str, Any]] = None
):
    """
    记录任务事件日志
    
    Args:
        task: UnifiedTask 对象
        event: 事件名称（如 "task_started", "video_execution_succeeded"）
        detail: 事件详细描述
        extra: 额外信息字典
    """
    
    timestamp = datetime.utcnow().isoformat()
    
    # 构建日志条目
    log_entry = {
        'timestamp': timestamp,
        'task_id': task.task_id,
        'task_type': task.task_type,
        'status': task.status,
        'current_stage': task.current_stage,
        'channel': task.channel,
        'message_type': task.message_type,
        'user_id': task.user_id,
        'event': event,
        'detail': detail,
    }
    
    # 添加额外信息
    if extra:
        log_entry.update(extra)
    
    # 输出日志（当前为简单打印，后续可改为 logging 模块或写入文件）
    _print_log(log_entry)


def _print_log(log_entry: Dict[str, Any]):
    """打印日志（简单实现）"""
    
    timestamp = log_entry.get('timestamp', '?')
    task_id = log_entry.get('task_id', '?')[:8]
    event = log_entry.get('event', '?')
    detail = log_entry.get('detail', '')
    
    # 格式化输出
    log_line = f"[{timestamp}] Task[{task_id}] {event}"
    if detail:
        log_line += f" - {detail}"
    
    print(log_line)
    
    # 也输出到 stderr 便于分离
    print(log_line, file=sys.stderr)


def log_task_start(task: UnifiedTask, stage: str = "executing"):
    """记录任务开始执行"""
    log_task_event(
        task,
        event="task_started",
        detail=f"Task started at stage: {stage}",
        extra={'stage': stage}
    )


def log_task_success(task: UnifiedTask, stage: str = "completed"):
    """记录任务成功完成"""
    log_task_event(
        task,
        event="task_succeeded",
        detail=f"Task completed successfully at stage: {stage}",
        extra={'stage': stage}
    )


def log_task_failure(task: UnifiedTask, error_code: str, error_message: str, stage: str = "failed"):
    """记录任务失败"""
    log_task_event(
        task,
        event="task_failed",
        detail=f"Task failed at stage: {stage} - {error_code}: {error_message}",
        extra={
            'stage': stage,
            'error_code': error_code,
            'error_message': error_message
        }
    )


# 文本任务专用日志
def log_text_execution_start(task: UnifiedTask):
    """记录文本执行开始"""
    log_task_event(
        task,
        event="text_execution_started",
        detail="Starting text task execution",
        extra={'stage': 'executing_text'}
    )


def log_text_execution_success(task: UnifiedTask):
    """记录文本执行成功"""
    log_task_event(
        task,
        event="text_execution_succeeded",
        detail="Text task completed successfully",
        extra={'stage': 'completed'}
    )


def log_text_execution_failure(task: UnifiedTask, error_code: str, error_message: str):
    """记录文本执行失败"""
    log_task_event(
        task,
        event="text_execution_failed",
        detail=f"Text task failed: {error_code} - {error_message}",
        extra={
            'stage': 'executing_text',
            'error_code': error_code,
            'error_message': error_message
        }
    )


# 视频任务专用日志
def log_video_execution_start(task: UnifiedTask):
    """记录视频执行开始"""
    log_task_event(
        task,
        event="video_execution_started",
        detail="Starting video analysis task execution",
        extra={
            'stage': 'executing_video',
            'source_file': task.source_file_name or task.source_file_url
        }
    )


def log_video_execution_success(task: UnifiedTask):
    """记录视频执行成功"""
    log_task_event(
        task,
        event="video_execution_succeeded",
        detail="Video analysis completed successfully",
        extra={'stage': 'completed'}
    )


def log_video_execution_failure(task: UnifiedTask, error_code: str, error_message: str):
    """记录视频执行失败"""
    log_task_event(
        task,
        event="video_execution_failed",
        detail=f"Video analysis failed: {error_code} - {error_message}",
        extra={
            'stage': 'executing_video',
            'error_code': error_code,
            'error_message': error_message
        }
    )


# 测试
if __name__ == '__main__':
    print("\n" + "="*60)
    print("📝 任务日志模块测试")
    print("="*60 + "\n")
    
    # 创建测试任务
    task = UnifiedTask(
        task_type='video_analysis',
        channel='dingtalk',
        user_id='test_user',
        source_file_name='test.mp4'
    )
    
    print("--- 测试 1: 任务开始日志 ---")
    log_task_start(task, 'executing_video')
    print("✅ 通过\n")
    
    print("--- 测试 2: 视频执行成功日志 ---")
    log_video_execution_success(task)
    print("✅ 通过\n")
    
    print("--- 测试 3: 任务失败日志 ---")
    task2 = UnifiedTask(task_type='chat', channel='qq', user_id='test')
    log_task_failure(task2, 'TEST_ERROR', '测试错误信息')
    print("✅ 通过\n")
    
    print("="*60)
    print("✅ 所有测试通过")
    print("="*60 + "\n")
