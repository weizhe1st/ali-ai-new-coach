#!/usr/bin/env python3
"""
统一视频输入处理模块（修复版）

负责：
- 根据任务生成工作目录
- 解析视频输入信息
- URL 视频下载到本地标准路径
- 将真实视频文件整理到标准位置
- 写入 task.source_file_path

确保视频任务进入执行层后，先经过输入准备层，
再交给分析服务。
"""

import os
import shutil
import requests
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

# 添加项目路径
import sys
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from models.task import UnifiedTask
from models.message import UnifiedMessage
from config import get_path_config


@dataclass
class PreparedVideo:
    """视频输入准备结果"""
    source_type: str  # 'local_file' | 'file_url' | 'cos_url' | 'http_url'
    original_value: str  # 原始 URL 或路径
    local_path: str  # 本地文件路径
    file_size_bytes: int  # 文件大小
    mime_type: Optional[str] = None  # MIME 类型
    download_success: bool = True  # 下载是否成功
    error_message: Optional[str] = None  # 错误信息（如果有）


# 任务工作目录根路径（从配置层读取）
_path_config = get_path_config()
TASK_WORKDIR_ROOT = _path_config.task_data_dir

# 视频下载配置
VIDEO_DOWNLOAD_TIMEOUT = (10, 120)  # (连接超时，读取超时)
VIDEO_DOWNLOAD_CHUNK_SIZE = 8192  # 流式下载块大小
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 最大视频大小 100MB


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


def download_video_from_url(url: str, dest_path: str) -> PreparedVideo:
    """
    从 URL 下载视频到本地
    
    Args:
        url: 视频 URL
        dest_path: 目标本地路径
    
    Returns:
        PreparedVideo: 下载结果
    """
    from task_logger import log_task_event
    
    try:
        # 流式下载
        response = requests.get(url, stream=True, timeout=VIDEO_DOWNLOAD_TIMEOUT)
        response.raise_for_status()
        
        # 获取文件大小（如果有）
        total_size = int(response.headers.get('content-length', 0))
        
        # 下载并写入文件
        downloaded_size = 0
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=VIDEO_DOWNLOAD_CHUNK_SIZE):
                if chunk:  # 过滤 keep-alive chunks
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    
                    # 检查是否超过最大大小
                    if downloaded_size > MAX_VIDEO_SIZE:
                        # 删除未完成的文件
                        if os.path.exists(dest_path):
                            os.unlink(dest_path)
                        return PreparedVideo(
                            source_type='http_url',
                            original_value=url,
                            local_path=dest_path,
                            file_size_bytes=0,
                            download_success=False,
                            error_message=f'Video size exceeds limit ({downloaded_size} > {MAX_VIDEO_SIZE})'
                        )
        
        # 校验下载结果
        if downloaded_size == 0:
            return PreparedVideo(
                source_type='http_url',
                original_value=url,
                local_path=dest_path,
                file_size_bytes=0,
                download_success=False,
                error_message='Downloaded file is empty'
            )
        
        # 获取 MIME 类型
        mime_type = response.headers.get('content-type', 'video/mp4')
        
        return PreparedVideo(
            source_type='http_url',
            original_value=url,
            local_path=dest_path,
            file_size_bytes=downloaded_size,
            mime_type=mime_type,
            download_success=True
        )
        
    except requests.exceptions.Timeout as e:
        error_msg = f'Download timeout: {str(e)}'
        return PreparedVideo(
            source_type='http_url',
            original_value=url,
            local_path=dest_path,
            file_size_bytes=0,
            download_success=False,
            error_message=error_msg
        )
    
    except requests.exceptions.RequestException as e:
        error_msg = f'Download failed: {str(e)}'
        return PreparedVideo(
            source_type='http_url',
            original_value=url,
            local_path=dest_path,
            file_size_bytes=0,
            download_success=False,
            error_message=error_msg
        )
    
    except Exception as e:
        error_msg = f'Unexpected error: {str(e)}'
        return PreparedVideo(
            source_type='http_url',
            original_value=url,
            local_path=dest_path,
            file_size_bytes=0,
            download_success=False,
            error_message=error_msg
        )


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
    准备视频输入（修复版：支持 URL 下载）
    
    流程：
    1. 构建任务工作目录
    2. 解析视频来源
    3. URL 视频下载到标准位置 / 本地文件复制到标准位置
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
            "input_prepare"
        )
        log_task_event(
            task,
            "video_input_missing",
            "No valid video input found",
            extra={'source_info': source_info}
        )
        return task
    
    # 步骤 3: 准备本地文件
    dest_filename = source_info['source_name'] or f"source_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    dest_path = os.path.join(workdir, 'input', dest_filename)
    
    if source_info['source_type'] == 'local_path':
        # 本地文件已存在
        source_path = source_info['local_path']
        
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
                    "input_prepare"
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
        task.source_file_url = source_info.get('source_url')
        
        log_task_event(
            task,
            "video_input_prepared",
            f"Video input prepared at {dest_path}",
            extra={
                'source_file_path': dest_path,
                'source_file_name': task.source_file_name,
                'source_type': 'local_path'
            }
        )
        
        return task
    
    elif source_info['source_type'] == 'url':
        # URL 来源 - 下载到本地
        url = source_info['source_url']
        
        log_task_event(
            task,
            "video_download_starting",
            f"Starting video download from {url}",
            extra={'source_url': url, 'dest_path': dest_path}
        )
        
        # 下载视频
        download_result = download_video_from_url(url, dest_path)
        
        if not download_result.download_success:
            # 下载失败
            task.mark_failed(
                "VIDEO_DOWNLOAD_FAILED",
                download_result.error_message,
                "download"
            )
            log_task_event(
                task,
                "video_download_failed",
                download_result.error_message,
                extra={
                    'source_url': url,
                    'error': download_result.error_message
                }
            )
            return task
        
        # 下载成功
        task.source_file_path = download_result.local_path
        task.source_file_name = source_info['source_name'] or dest_filename
        task.source_file_url = url
        
        log_task_event(
            task,
            "video_download_success",
            f"Video downloaded successfully to {download_result.local_path}",
            extra={
                'source_url': url,
                'local_path': download_result.local_path,
                'file_size_bytes': download_result.file_size_bytes,
                'mime_type': download_result.mime_type
            }
        )
        
        return task
    
    # 不应该到达这里
    task.mark_failed(
        "VIDEO_INPUT_PREPARE_FAILED",
        "Unknown video input preparation error",
        "input_prepare"
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
    print("📹 视频输入处理模块测试（修复版）")
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
