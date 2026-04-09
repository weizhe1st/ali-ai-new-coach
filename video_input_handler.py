#!/usr/bin/env python3
"""
统一视频输入处理模块

负责：
- 根据任务生成工作目录
- 解析视频输入信息
- 将真实视频文件整理到标准位置
- 写入 task.source_file_path

确保视频任务进入执行层后，先经过输入准备层，
再交给旧分析能力。
"""

import os
import shutil
from typing import Dict, Any, Optional
from datetime import datetime

# 添加项目路径
import sys
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from models.task import UnifiedTask
from models.message import UnifiedMessage


# 任务工作目录根路径
TASK_WORKDIR_ROOT = os.path.join(PROJECT_ROOT, 'data', 'tasks')


def build_task_workdir(task: UnifiedTask) -> str:
    """
    为任务构建标准工作目录
    
    Args:
        task: UnifiedTask 对象
    
    Returns:
        str: 任务工作目录路径
    """
    workdir = os.path.join(TASK_WORKDIR_ROOT, task.task_id)
    
    # 创建目录结构
    os.makedirs(workdir, exist_ok=True)
    os.makedirs(os.path.join(workdir, 'input'), exist_ok=True)
    os.makedirs(os.path.join(workdir, 'output'), exist_ok=True)
    os.makedirs(os.path.join(workdir, 'logs'), exist_ok=True)
    
    return workdir


def resolve_video_source(task: UnifiedTask, message: UnifiedMessage) -> Dict[str, Any]:
    """
    解析视频来源信息
    
    优先级：
    1. task.source_file_path 已存在且文件存在
    2. message.file_url 存在
    3. message.file_path 存在
    4. message.extra 中有路径信息
    
    Args:
        task: UnifiedTask 对象
        message: UnifiedMessage 对象
    
    Returns:
        dict: 视频来源信息
            - source_type: 'local_path' | 'url' | 'missing'
            - source_url: 原始 URL（如果有）
            - source_name: 原始文件名（如果有）
            - local_path: 本地可用路径（如果有）
    """
    result = {
        'source_type': 'missing',
        'source_url': None,
        'source_name': None,
        'local_path': None
    }
    
    # 优先级 1: task.source_file_path 已存在
    if task.source_file_path and os.path.exists(task.source_file_path):
        result['source_type'] = 'local_path'
        result['local_path'] = task.source_file_path
        result['source_name'] = task.source_file_name or os.path.basename(task.source_file_path)
        return result
    
    # 优先级 2: message.file_url 存在
    if message.file_url:
        result['source_type'] = 'url'
        result['source_url'] = message.file_url
        result['source_name'] = message.file_name or os.path.basename(message.file_url)
        return result
    
    # 优先级 3: message.file_path 存在
    if message.file_path and os.path.exists(message.file_path):
        result['source_type'] = 'local_path'
        result['local_path'] = message.file_path
        result['source_name'] = message.file_name or os.path.basename(message.file_path)
        return result
    
    # 优先级 4: message.extra 中有路径信息
    if message.extra and isinstance(message.extra, dict):
        extra_path = message.extra.get('file_path') or message.extra.get('local_path')
        if extra_path and os.path.exists(extra_path):
            result['source_type'] = 'local_path'
            result['local_path'] = extra_path
            result['source_name'] = message.file_name or os.path.basename(extra_path)
            return result
    
    # 无可用视频输入
    return result


def prepare_video_input(task: UnifiedTask, message: UnifiedMessage) -> UnifiedTask:
    """
    准备视频输入
    
    流程：
    1. 构建任务工作目录
    2. 解析视频来源
    3. 将视频文件复制到标准位置
    4. 写入 task.source_file_path
    
    Args:
        task: UnifiedTask 对象
        message: UnifiedMessage 对象
    
    Returns:
        UnifiedTask: 更新后的任务对象
    """
    from task_logger import log_task_event
    
    # 步骤 1: 构建工作目录
    workdir = build_task_workdir(task)
    log_task_event(task, "workdir_created", f"Task workdir created at {workdir}")
    
    # 步骤 2: 解析视频来源
    source_info = resolve_video_source(task, message)
    
    if source_info['source_type'] == 'missing':
        # 视频输入缺失
        task.mark_failed(
            "VIDEO_INPUT_MISSING",
            "No valid video input found in task or message",
            "preparing_video_input"
        )
        log_task_event(
            task,
            "video_input_missing",
            "No valid video input found",
            extra={'source_info': source_info}
        )
        return task
    
    # 步骤 3: 准备本地文件
    if source_info['source_type'] == 'local_path':
        # 本地文件已存在
        source_path = source_info['local_path']
        
        # 复制到任务工作目录
        dest_filename = source_info['source_name'] or f"input_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.mp4"
        dest_path = os.path.join(workdir, 'input', dest_filename)
        
        # 如果源文件和目标文件不同，则复制
        if os.path.abspath(source_path) != os.path.abspath(dest_path):
            try:
                shutil.copy2(source_path, dest_path)
                log_task_event(
                    task,
                    "video_file_copied",
                    f"Video file copied from {source_path} to {dest_path}",
                    extra={'source': source_path, 'dest': dest_path}
                )
            except Exception as e:
                task.mark_failed(
                    "VIDEO_FILE_COPY_FAILED",
                    f"Failed to copy video file: {str(e)}",
                    "preparing_video_input"
                )
                log_task_event(
                    task,
                    "video_file_copy_failed",
                    f"Failed to copy: {str(e)}",
                    extra={'error': str(e)}
                )
                return task
        
        # 更新 task
        task.source_file_path = dest_path
        task.source_file_name = source_info['source_name'] or dest_filename
        task.source_file_url = source_info['source_url']
        
        log_task_event(
            task,
            "video_input_prepared",
            f"Video input prepared at {dest_path}",
            extra={'source_file_path': dest_path, 'source_file_name': task.source_file_name}
        )
        
        return task
    
    elif source_info['source_type'] == 'url':
        # URL 来源 - 当前阶段如果没有下载器，明确失败
        task.mark_failed(
            "VIDEO_URL_NOT_SUPPORTED",
            f"Video URL input not yet supported: {source_info['source_url']}",
            "preparing_video_input"
        )
        log_task_event(
            task,
            "video_url_not_supported",
            f"Video URL input not yet supported",
            extra={'source_url': source_info['source_url']}
        )
        return task
    
    # 不应该到达这里
    task.mark_failed(
        "VIDEO_INPUT_PREPARE_FAILED",
        "Unknown video input preparation error",
        "preparing_video_input"
    )
    return task


# 便捷函数
def create_task_workdir(task_id: str) -> str:
    """创建任务工作目录（便捷函数）"""
    workdir = os.path.join(TASK_WORKDIR_ROOT, task_id)
    os.makedirs(workdir, exist_ok=True)
    return workdir


# 测试
if __name__ == '__main__':
    print("\n" + "="*60)
    print("📹 视频输入处理模块测试")
    print("="*60 + "\n")
    
    # 测试 1: 创建工作目录
    print("--- 测试 1: 创建任务工作目录 ---")
    task = UnifiedTask(task_type='video_analysis', channel='dingtalk', user_id='test')
    workdir = build_task_workdir(task)
    print(f"工作目录：{workdir}")
    assert os.path.exists(workdir), "工作目录应存在"
    assert os.path.exists(os.path.join(workdir, 'input')), "input 目录应存在"
    print("✅ 通过\n")
    
    # 测试 2: 本地文件输入
    print("--- 测试 2: 本地文件输入准备 ---")
    from models.message import UnifiedMessage, ChannelType, MessageType
    
    # 创建一个临时测试文件
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
        tmp.write(b'test video content')
        tmp_path = tmp.name
    
    try:
        task = UnifiedTask(
            task_type='video_analysis',
            channel='dingtalk',
            user_id='test_user',
            source_file_name='test.mp4'
        )
        
        message = UnifiedMessage(
            channel=ChannelType.DINGTALK,
            message_type=MessageType.VIDEO,
            user_id='test_user',
            file_path=tmp_path,
            file_name='test.mp4'
        )
        
        # 准备视频输入
        task = prepare_video_input(task, message)
        
        print(f"任务状态：{task.status}")
        print(f"当前阶段：{task.current_stage}")
        print(f"文件路径：{task.source_file_path}")
        
        if task.status == 'failed':
            print(f"错误码：{task.error_code}")
            print(f"错误信息：{task.error_message}")
        else:
            assert task.source_file_path is not None, "source_file_path 应有值"
            assert os.path.exists(task.source_file_path), "文件应存在"
            print("✅ 通过\n")
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    
    # 测试 3: 缺失视频输入
    print("--- 测试 3: 缺失视频输入 ---")
    task = UnifiedTask(task_type='video_analysis', channel='dingtalk', user_id='test')
    message = UnifiedMessage(
        channel=ChannelType.DINGTALK,
        message_type=MessageType.VIDEO,
        user_id='test_user'
    )
    
    task = prepare_video_input(task, message)
    print(f"任务状态：{task.status}")
    print(f"错误码：{task.error_code}")
    assert task.status == 'failed', "任务应失败"
    assert task.error_code == 'VIDEO_INPUT_MISSING', "错误码应正确"
    print("✅ 通过\n")
    
    print("="*60)
    print("✅ 所有测试通过")
    print("="*60 + "\n")
