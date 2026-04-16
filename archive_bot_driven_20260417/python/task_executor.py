#!/usr/bin/env python3
"""
统一任务执行服务层

负责真正执行任务，调用旧分析能力
路由层只负责建任务和分发，执行层负责真正干活

已接入最小任务状态管理与日志记录
"""

import os
import sys
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from models.task import UnifiedTask
from models.message import UnifiedMessage
from task_logger import (
    log_task_start,
    log_task_success,
    log_task_failure,
    log_task_event,
    log_text_execution_start,
    log_text_execution_success,
    log_text_execution_failure,
    log_video_execution_start,
    log_video_execution_success,
    log_video_execution_failure
)
from video_input_handler import prepare_video_input
from analysis_service import AnalysisService
from cos_uploader import COSUploader


class TaskExecutor:
    """
    统一任务执行器
    
    职责：
    - 接收 UnifiedTask
    - 根据 task_type 执行对应逻辑
    - 调用统一分析服务
    - 统一错误处理
    - 统一结果包装
    - 任务状态跟踪
    - 任务日志记录
    """
    
    def __init__(self):
        self.analysis_service = AnalysisService()
        self.text_handler: Optional[Callable] = None
        self.image_handler: Optional[Callable] = None
        
        print("✅ TaskExecutor 已初始化（含 AnalysisService、状态跟踪和日志）")
    
    def register_text_handler(self, handler: Callable):
        """注册文本消息处理器"""
        self.text_handler = handler
        print("  ✓ 文本消息处理器已注册")
    
    def register_image_handler(self, handler: Callable):
        """注册图片分析处理器"""
        self.image_handler = handler
        print("  ✓ 图片分析处理器已注册")
    
    def execute(self, task: UnifiedTask, message: UnifiedMessage) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            task: UnifiedTask 对象
            message: UnifiedMessage 对象
        
        Returns:
            dict: 统一执行结果
        """
        
        print(f"\n⚙️  执行任务:")
        print(f"  任务 ID: {task.task_id}")
        print(f"  类型：{task.task_type}")
        print(f"  渠道：{task.channel}")
        
        # 根据任务类型执行
        if task.task_type == "video_analysis":
            return self._execute_video(task, message)
        elif task.task_type == "chat":
            return self._execute_text(task, message)
        elif task.task_type == "image_analysis":
            return self._execute_image(task, message)
        else:
            # 未知任务类型
            task.mark_failed("UNKNOWN_TASK_TYPE", f"Unknown task type: {task.task_type}")
            log_task_failure(task, "UNKNOWN_TASK_TYPE", f"Unknown task type: {task.task_type}")
            return self._build_error_result(task, "UNKNOWN_TASK_TYPE", f"Unknown task type: {task.task_type}", message)
    
    def _execute_video(self, task: UnifiedTask, message: UnifiedMessage) -> Dict[str, Any]:
        """
        执行视频分析任务
        
        流程：
        1. 准备视频输入（解析来源、复制到工作目录）
        2. 校验 source_file_path
        3. 调用统一分析服务
        
        Args:
            task: UnifiedTask 对象
            message: UnifiedMessage 对象
        
        Returns:
            dict: 统一执行结果
        """
        
        print(f"  🎬 执行视频分析...")
        
        # 步骤 1: 准备视频输入
        print(f"  📥 准备视频输入...")
        task = prepare_video_input(task, message)
        
        # 检查视频输入准备是否成功
        if task.status == 'failed':
            print(f"  ❌ 视频输入准备失败：{task.error_code}")
            # 错误已在 prepare_video_input 中记录
            return self._build_error_result(task, task.error_code, task.error_message, message)
        
        # 步骤 2: 校验 source_file_path（强制校验本地文件已准备完成）
        if not task.source_file_path:
            task.mark_failed(
                "VIDEO_PATH_MISSING",
                "source_file_path is not set after video input preparation",
                "input_prepare"
            )
            log_task_event(
                task,
                "video_path_missing",
                "source_file_path is not set after input preparation",
                extra={
                    'error_stage': 'input_prepare',
                    'error_code': 'VIDEO_PATH_MISSING'
                }
            )
            return self._build_error_result(task, "VIDEO_PATH_MISSING", "source_file_path is not set", message)
        
        if not os.path.exists(task.source_file_path):
            task.mark_failed(
                "VIDEO_FILE_NOT_FOUND",
                f"Video file not found at {task.source_file_path}",
                "input_prepare"
            )
            log_task_event(
                task,
                "video_file_not_found",
                f"File not found at {task.source_file_path}",
                extra={
                    'error_stage': 'input_prepare',
                    'error_code': 'VIDEO_FILE_NOT_FOUND',
                    'local_video_path': task.source_file_path
                }
            )
            return self._build_error_result(task, "VIDEO_FILE_NOT_FOUND", f"Video file not found", message)
        
        # 记录结构化日志
        log_task_event(
            task,
            "video_input_validated",
            f"Video input validated at {task.source_file_path}",
            extra={
                'source_type': 'local_file',
                'local_video_path': task.source_file_path,
                'video_size_bytes': os.path.getsize(task.source_file_path) if os.path.exists(task.source_file_path) else 0
            }
        )
        
        print(f"  ✅ 视频输入已准备：{task.source_file_path}")
        
        # 步骤 3: 标记开始执行
        task.mark_running("executing_video")
        log_video_execution_start(task)
        
        # 步骤 4: 调用统一分析服务（不允许把 URL 直接传给分析服务）
        try:
            print(f"  📹 调用统一分析服务...")
            
            # 强制校验：必须传本地文件路径
            if not task.source_file_path or not os.path.exists(task.source_file_path):
                raise ValueError(f"Analysis service requires local file path, got: {task.source_file_path}")
            
            # 调用分析服务
            analysis_result = self.analysis_service.analyze_video(task)
            
            # 检查分析结果
            if not analysis_result.get('success'):
                error_code = analysis_result.get('error', {}).get('code', 'VIDEO_ANALYSIS_FAILED')
                error_message = analysis_result.get('error', {}).get('message', 'Unknown analysis error')
                task.mark_failed(error_code, error_message, "analysis")
                log_video_execution_failure(
                    task,
                    error_code,
                    error_message,
                    extra={
                        'error_stage': 'analysis',
                        'error_code': error_code,
                        'local_video_path': task.source_file_path
                    }
                )
                return self._build_error_result(task, error_code, error_message)
            
            # 标记成功
            task.mark_success(
                "completed",
                result=analysis_result.get('structured_result'),
                report=analysis_result.get('report')
            )
            log_video_execution_success(task)
            
            print(f"  ✅ 视频分析完成")
            
            # 步骤 5: 样本归档（分析成功后自动上传 COS + 标记候选黄金样本）
            try:
                print(f"  📦 准备样本归档...")
                from sample_archive_service import SampleArchiveService
                
                archive_service = SampleArchiveService()
                archive_result = archive_service.archive_after_analysis(task, analysis_result)
                
                if archive_result.get('archived'):
                    task.extra = task.extra or {}
                    task.extra['cos_key'] = archive_result.get('cos_key')
                    task.extra['cos_url'] = archive_result.get('cos_url')
                    task.extra['candidate_for_golden'] = archive_result.get('candidate_for_golden', False)
                    
                    print(f"  ✅ 样本已归档到 COS")
                    if archive_result.get('candidate_for_golden'):
                        print(f"  🌟 已标记为候选黄金样本")
                else:
                    print(f"  ⚠️  样本归档跳过：{archive_result.get('reason', 'unknown')}")
                    
            except Exception as e:
                print(f"  ⚠️  样本归档失败（不影响主流程）: {e}")
            
            return self._build_success_result(task, message, analysis_result)
            
        except Exception as e:
            print(f"  ❌ 视频分析失败：{e}")
            task.mark_failed("VIDEO_EXECUTION_ERROR", str(e), "executing_video")
            log_video_execution_failure(task, "VIDEO_EXECUTION_ERROR", str(e))
            return self._build_error_result(task, "VIDEO_EXECUTION_ERROR", str(e))
    
    def _execute_text(self, task: UnifiedTask, message: UnifiedMessage) -> Dict[str, Any]:
        """
        执行文本消息任务
        
        Args:
            task: UnifiedTask 对象
            message: UnifiedMessage 对象
        
        Returns:
            dict: 统一执行结果
        """
        
        print(f"  💬 执行文本处理...")
        
        # 标记开始执行
        task.mark_running("executing_text")
        log_text_execution_start(task)
        
        # 检查是否注册了处理器
        if not self.text_handler:
            print(f"  ℹ️  文本处理器未注册，返回占位结果")
            task.mark_success(
                "completed",
                result={
                    'message': 'text task executed',
                    'text': message.text[:100] if message.text else ''
                },
                report=f"收到文本消息：{message.text[:50] if message.text else ''}"
            )
            log_text_execution_success(task)
            return self._build_success_result(task, message)
        
        # 调用处理器
        try:
            result = self.text_handler(task)
            if isinstance(result, UnifiedTask):
                task = result
            task.mark_success("completed")
            log_text_execution_success(task)
            print(f"  ✅ 文本处理完成")
            return self._build_success_result(task, message)
            
        except Exception as e:
            print(f"  ❌ 文本处理失败：{e}")
            task.mark_failed("TEXT_EXECUTION_ERROR", str(e), "executing_text")
            log_text_execution_failure(task, "TEXT_EXECUTION_ERROR", str(e))
            return self._build_error_result(task, "TEXT_EXECUTION_ERROR", str(e))
    
    def _execute_image(self, task: UnifiedTask, message: UnifiedMessage) -> Dict[str, Any]:
        """
        执行图片分析任务
        
        Args:
            task: UnifiedTask 对象
            message: UnifiedMessage 对象
        
        Returns:
            dict: 统一执行结果
        """
        
        print(f"  🖼️  执行图片分析...")
        
        # 标记开始执行
        task.mark_running("executing_image")
        log_task_event(task, "image_execution_started", "Starting image analysis")
        
        if not self.image_handler:
            print(f"  ℹ️  图片处理器未注册，返回占位结果")
            task.mark_success(
                "completed",
                result={'message': 'image analysis placeholder'},
                report="图片分析功能待实现"
            )
            log_task_event(task, "image_execution_succeeded", "Image analysis completed (placeholder)")
            return self._build_success_result(task, message)
        
        try:
            result = self.image_handler(task)
            if isinstance(result, UnifiedTask):
                task = result
            task.mark_success("completed")
            log_task_event(task, "image_execution_succeeded", "Image analysis completed")
            print(f"  ✅ 图片分析完成")
            return self._build_success_result(task, message)
            
        except Exception as e:
            print(f"  ❌ 图片分析失败：{e}")
            task.mark_failed("IMAGE_EXECUTION_ERROR", str(e), "executing_image")
            log_task_event(task, "image_execution_failed", f"Image analysis failed: {str(e)}")
            return self._build_error_result(task, "IMAGE_EXECUTION_ERROR", str(e))
    
    def _build_success_result(self, task: UnifiedTask, message: UnifiedMessage, analysis_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        构建成功结果
        
        Args:
            task: UnifiedTask 对象
            message: UnifiedMessage 对象
            analysis_result: 分析结果（可选）
        
        Returns:
            dict: 统一成功结果
        """
        result = {
            'task_id': task.task_id,
            'task_type': task.task_type,
            'status': task.status,
            'current_stage': task.current_stage,
            'channel': task.channel,
            'message_type': message.message_type.value,
            'result': task.result,
            'report': task.report,
            'error': None,
            'started_at': task.started_at,
            'completed_at': task.completed_at
        }
        
        # 如果提供了分析结果，添加详细信息
        if analysis_result:
            result['analysis_entry'] = analysis_result.get('entry', 'unknown')
            result['video_file'] = analysis_result.get('video_file')
            result['video_name'] = analysis_result.get('video_name')
            result['detailed_analysis'] = analysis_result.get('detailed_analysis')
            result['coach_references'] = analysis_result.get('coach_references')
        
        return result
    
    def _build_error_result(self, task: UnifiedTask, error_code: str, error_message: str, message: UnifiedMessage = None) -> Dict[str, Any]:
        """
        构建错误结果
        
        Args:
            task: UnifiedTask 对象
            error_code: 错误码
            error_message: 错误信息
            message: UnifiedMessage 对象（可选）
        
        Returns:
            dict: 统一错误结果
        """
        message_type = 'unknown'
        if message:
            if hasattr(message, 'message_type'):
                if hasattr(message.message_type, 'value'):
                    message_type = message.message_type.value
                else:
                    message_type = str(message.message_type)
        
        return {
            'task_id': task.task_id,
            'task_type': task.task_type,
            'status': task.status,
            'current_stage': task.current_stage,
            'channel': task.channel,
            'message_type': message_type,
            'result': None,
            'report': None,
            'error': {
                'code': error_code,
                'message': error_message
            },
            'started_at': task.started_at,
            'completed_at': task.completed_at
        }
    
    def _upload_to_cos(self, task: UnifiedTask, analysis_result: Dict[str, Any]) -> Optional[str]:
        """
        上传视频和报告到 COS
        
        Args:
            task: UnifiedTask 对象
            analysis_result: 分析结果
        
        Returns:
            str: COS Key（上传成功）或 None（失败）
        """
        
        # 检查是否有视频文件路径
        video_path = task.source_file_path
        if not video_path or not os.path.exists(video_path):
            print(f"  ⚠️  视频文件不存在，跳过 COS 上传")
            return None
        
        # 创建 COS 上传器
        uploader = COSUploader()
        
        # 上传视频
        video_name = task.source_file_name or os.path.basename(video_path)
        cos_key = uploader.upload_video(
            local_path=video_path,
            task_id=task.task_id,
            video_name=video_name,
            is_golden=False  # 当前不是黄金样本
        )
        
        # 如果有报告，也上传报告
        report = analysis_result.get('report')
        if report and cos_key:
            # 保存报告到临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(report)
                report_path = f.name
            
            try:
                uploader.upload_report(
                    report_path=report_path,
                    task_id=task.task_id,
                    report_name='report.txt'
                )
            finally:
                # 清理临时文件
                os.unlink(report_path)
        
        return cos_key


# 便捷函数
def create_executor() -> TaskExecutor:
    """创建任务执行器实例"""
    return TaskExecutor()


# 测试
if __name__ == '__main__':
    print("\n" + "="*60)
    print("⚙️  任务执行器测试（含状态跟踪和日志）")
    print("="*60 + "\n")
    
    executor = TaskExecutor()
    
    # 测试文本任务
    print("--- 测试 1: 文本任务执行 ---")
    from models.message import UnifiedMessage, ChannelType, MessageType
    from models.task import UnifiedTask
    
    message = UnifiedMessage(
        channel=ChannelType.DINGTALK,
        message_type=MessageType.TEXT,
        user_id='test_user',
        text='你好，在吗？'
    )
    
    task = UnifiedTask(
        task_type='chat',
        channel='dingtalk',
        user_id='test_user'
    )
    
    result = executor.execute(task, message)
    print(f"\n结果状态：{result['status']}")
    print(f"当前阶段：{result['current_stage']}")
    print(f"任务 ID: {result['task_id']}")
    print(f"✅ 通过")
    
    # 测试视频任务
    print("\n--- 测试 2: 视频任务执行 ---")
    message = UnifiedMessage(
        channel=ChannelType.DINGTALK,
        message_type=MessageType.VIDEO,
        user_id='test_user',
        file_path='/tmp/test.mp4'
    )
    
    task = UnifiedTask(
        task_type='video_analysis',
        channel='dingtalk',
        user_id='test_user',
        source_file_path='/tmp/test.mp4'
    )
    
    result = executor.execute(task, message)
    print(f"\n结果状态：{result['status']}")
    print(f"当前阶段：{result['current_stage']}")
    print(f"任务 ID: {result['task_id']}")
    print(f"✅ 通过")
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60 + "\n")
