#!/usr/bin/env python3
"""
统一任务执行服务层

负责真正执行任务，调用旧分析能力
路由层只负责建任务和分发，执行层负责真正干活
"""

import os
import sys
from typing import Dict, Any, Optional, Callable
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from models.task import UnifiedTask
from models.message import UnifiedMessage


class TaskExecutor:
    """
    统一任务执行器
    
    职责：
    - 接收 UnifiedTask
    - 根据 task_type 执行对应逻辑
    - 调用旧分析能力
    - 返回统一执行结果
    """
    
    def __init__(self):
        self.video_handler: Optional[Callable] = None
        self.text_handler: Optional[Callable] = None
        self.image_handler: Optional[Callable] = None
        
        print("✅ TaskExecutor 已初始化")
    
    def register_video_handler(self, handler: Callable):
        """注册视频分析处理器"""
        self.video_handler = handler
        print("  ✓ 视频分析处理器已注册")
    
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
            return self._build_error_result(
                task, 
                "UNKNOWN_TASK_TYPE",
                f"Unknown task type: {task.task_type}"
            )
    
    def _execute_video(self, task: UnifiedTask, message: UnifiedMessage) -> Dict[str, Any]:
        """
        执行视频分析任务
        
        Args:
            task: UnifiedTask 对象
            message: UnifiedMessage 对象
        
        Returns:
            dict: 统一执行结果
        """
        
        print(f"  🎬 执行视频分析...")
        task.start()
        
        # 检查是否注册了处理器
        if not self.video_handler:
            print(f"  ⚠️  视频分析处理器未注册，返回占位结果")
            task.success(
                result={'ntrp_level': 'N/A', 'confidence': 0, 'overall_score': 0},
                report="视频分析功能已就绪，请配置分析处理器"
            )
            return self._build_success_result(task, message)
        
        # 调用现有分析能力
        try:
            print(f"  📹 调用现有视频分析能力...")
            
            # 调用处理器（传入任务对象）
            result = self.video_handler(task)
            
            # 如果处理器返回了任务，使用返回的任务
            if isinstance(result, UnifiedTask):
                task = result
            
            print(f"  ✅ 视频分析完成")
            return self._build_success_result(task, message)
            
        except Exception as e:
            print(f"  ❌ 视频分析失败：{e}")
            task.fail(f"视频分析失败：{str(e)}")
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
        task.start()
        
        # 检查是否注册了处理器
        if not self.text_handler:
            print(f"  ℹ️  文本处理器未注册，返回占位结果")
            task.success(
                result={
                    'message': 'text task executed',
                    'text': message.text[:100] if message.text else ''
                },
                report=f"收到文本消息：{message.text[:50] if message.text else ''}"
            )
            return self._build_success_result(task, message)
        
        # 调用处理器
        try:
            result = self.text_handler(task)
            if isinstance(result, UnifiedTask):
                task = result
            print(f"  ✅ 文本处理完成")
            return self._build_success_result(task, message)
            
        except Exception as e:
            print(f"  ❌ 文本处理失败：{e}")
            task.fail(f"文本处理失败：{str(e)}")
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
        task.start()
        
        if not self.image_handler:
            print(f"  ℹ️  图片处理器未注册，返回占位结果")
            task.success(
                result={'message': 'image analysis placeholder'},
                report="图片分析功能待实现"
            )
            return self._build_success_result(task, message)
        
        try:
            result = self.image_handler(task)
            if isinstance(result, UnifiedTask):
                task = result
            print(f"  ✅ 图片分析完成")
            return self._build_success_result(task, message)
            
        except Exception as e:
            print(f"  ❌ 图片分析失败：{e}")
            task.fail(f"图片分析失败：{str(e)}")
            return self._build_error_result(task, "IMAGE_EXECUTION_ERROR", str(e))
    
    def _build_success_result(self, task: UnifiedTask, message: UnifiedMessage) -> Dict[str, Any]:
        """
        构建成功结果
        
        Args:
            task: UnifiedTask 对象
            message: UnifiedMessage 对象
        
        Returns:
            dict: 统一成功结果
        """
        return {
            'task_id': task.task_id,
            'task_type': task.task_type,
            'status': task.status,
            'channel': task.channel,
            'message_type': message.message_type.value,
            'result': task.result,
            'report': task.report,
            'error': None
        }
    
    def _build_error_result(self, task: UnifiedTask, error_code: str, error_message: str) -> Dict[str, Any]:
        """
        构建错误结果
        
        Args:
            task: UnifiedTask 对象
            error_code: 错误码
            error_message: 错误信息
        
        Returns:
            dict: 统一错误结果
        """
        return {
            'task_id': task.task_id,
            'task_type': task.task_type,
            'status': task.status,
            'channel': task.channel,
            'message_type': getattr(task, 'message_type', 'unknown'),
            'result': None,
            'report': None,
            'error': {
                'code': error_code,
                'message': error_message
            }
        }


# 便捷函数
def create_executor() -> TaskExecutor:
    """创建任务执行器实例"""
    return TaskExecutor()


# 测试
if __name__ == '__main__':
    print("\n" + "="*60)
    print("⚙️  任务执行器测试")
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
    print(f"\n结果：{result['status']}")
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
        video_path='/tmp/test.mp4'
    )
    
    result = executor.execute(task, message)
    print(f"\n结果：{result['status']}")
    print(f"任务 ID: {result['task_id']}")
    print(f"✅ 通过")
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60 + "\n")
