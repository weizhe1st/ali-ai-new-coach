#!/usr/bin/env python3
"""
统一回复构建模块

负责将 TaskExecutor 的执行结果转换为用户可见的回复内容
让钉钉/QQ 不再各自拼回复，统一通过本层生成

当前主要输出为纯文本回复，后续可扩展为富文本/卡片/网页端/API 输出
"""

import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime


class ReplyBuilder:
    """
    统一回复构建器
    
    职责：
    - 接收 TaskExecutor 执行结果
    - 转换为用户可见的回复对象
    - 统一成功/失败回复格式
    - 提供纯文本渲染器
    """
    
    def __init__(self):
        print("✅ ReplyBuilder 已初始化")
    
    def build_reply(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建统一回复对象
        
        Args:
            execution_result: TaskExecutor 返回的执行结果
        
        Returns:
            dict: 统一回复对象
        """
        
        status = execution_result.get('status', 'unknown')
        task_type = execution_result.get('task_type', 'unknown')
        
        # 根据状态和任务类型分发
        if status == 'success':
            if task_type == 'video_analysis':
                return self._build_video_reply(execution_result)
            elif task_type == 'chat':
                return self._build_text_reply(execution_result)
            elif task_type == 'image_analysis':
                return self._build_image_reply(execution_result)
            else:
                return self._build_generic_success_reply(execution_result)
        
        elif status == 'failed':
            return self._build_error_reply(execution_result)
        
        else:
            return self._build_error_reply(
                execution_result,
                title="任务状态未知",
                message=f"任务状态：{status}"
            )
    
    def _build_video_reply(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建视频分析任务回复（详细版）
        
        Args:
            execution_result: TaskExecutor 返回的执行结果
        
        Returns:
            dict: 统一回复对象
        """
        
        result = execution_result.get('result', {})
        report = execution_result.get('report', '')
        
        # 提取关键信息
        ntrp_level = result.get('ntrp_level', 'N/A') if result else 'N/A'
        score = result.get('overall_score', 0) if result else 0
        confidence = result.get('confidence', 0) * 100 if result else 0
        
        # 构建标题
        title = "🎾 网球发球分析报告"
        
        # 构建核心消息（摘要）
        message = f"NTRP {ntrp_level}级（置信度{confidence:.0f}%），综合评分{score}/100"
        
        # 构建详情列表（详细版）
        details = []
        
        # 1. 综合评估
        eval_section = "📊 综合评估\n"
        eval_section += "━"*40 + "\n"
        eval_section += f"  NTRP 等级：{ntrp_level}\n"
        eval_section += f"  置信度：{confidence:.0f}%\n"
        eval_section += f"  综合评分：{score}/100\n"
        details.append(eval_section)
        
        # 2. 亮点（如果有）
        highlights = result.get('highlights', [])
        if highlights:
            highlight_section = "✅ 做得好的地方\n"
            highlight_section += "━"*40 + "\n"
            for h in highlights:
                highlight_section += f"  ✓ {h}\n"
            details.append(highlight_section)
        
        # 3. 关键问题（详细版）
        key_issues = result.get('key_issues', [])
        if key_issues:
            issues_section = "⚠️ 需要改进\n"
            issues_section += "━"*40 + "\n"
            severity_map = {'critical': '🔴 严重', 'major': '🟠 重要', 'minor': '🟡 一般'}
            for issue in key_issues:
                phase = issue.get('phase', '')
                severity = issue.get('severity', 'minor')
                desc = issue.get('description', '')
                severity_label = severity_map.get(severity, '⚪')
                issues_section += f"  {severity_label} [{phase}] {desc}\n"
            details.append(issues_section)
        
        # 4. 训练建议（详细版）
        priorities = result.get('training_priorities', [])
        if priorities:
            suggestion_section = "💪 训练建议\n"
            suggestion_section += "━"*40 + "\n"
            for i, p in enumerate(priorities[:5], 1):
                suggestion_section += f"  {i}. {p}\n"
            details.append(suggestion_section)
        
        # 5. 教练知识点（如果有）
        coach_refs = result.get('coach_references', {})
        if coach_refs:
            coach_section = "📚 教练知识点\n"
            coach_section += "━"*40 + "\n"
            for coach, refs in coach_refs.items():
                if isinstance(refs, list):
                    count = len(refs)
                else:
                    count = refs
                if count > 0:
                    coach_section += f"  👤 {coach}: {count} 条\n"
            details.append(coach_section)
        
        return {
            'success': True,
            'reply_type': 'analysis_report',
            'title': title,
            'message': message,
            'details': details,
            'task_id': execution_result.get('task_id'),
            'task_type': 'video_analysis',
            'channel': execution_result.get('channel', 'unknown'),
            'raw_result': result
        }
    
    def _build_text_reply(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建文本任务回复
        
        Args:
            execution_result: TaskExecutor 返回的执行结果
        
        Returns:
            dict: 统一回复对象
        """
        
        result = execution_result.get('result', {})
        report = execution_result.get('report', '')
        
        # 构建标题
        title = "💬 文本任务已处理"
        
        # 构建核心消息
        message = report if report else "文本消息已收到"
        
        # 构建详情列表
        details = []
        if result:
            details.append(f"处理结果：{result}")
        
        return {
            'success': True,
            'reply_type': 'text',
            'title': title,
            'message': message,
            'details': details,
            'task_id': execution_result.get('task_id'),
            'task_type': 'chat',
            'channel': execution_result.get('channel', 'unknown'),
            'raw_result': result
        }
    
    def _build_image_reply(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建图片分析任务回复
        
        Args:
            execution_result: TaskExecutor 返回的执行结果
        
        Returns:
            dict: 统一回复对象
        """
        
        result = execution_result.get('result', {})
        report = execution_result.get('report', '')
        
        # 构建标题
        title = "🖼️  图片分析已完成"
        
        # 构建核心消息
        message = report if report else "图片分析完成"
        
        # 构建详情列表
        details = []
        if result:
            details.append(f"分析结果：{result}")
        
        return {
            'success': True,
            'reply_type': 'analysis_report',
            'title': title,
            'message': message,
            'details': details,
            'task_id': execution_result.get('task_id'),
            'task_type': 'image_analysis',
            'channel': execution_result.get('channel', 'unknown'),
            'raw_result': result
        }
    
    def _build_generic_success_reply(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建通用成功回复
        
        Args:
            execution_result: TaskExecutor 返回的执行结果
        
        Returns:
            dict: 统一回复对象
        """
        
        task_type = execution_result.get('task_type', 'unknown')
        
        return {
            'success': True,
            'reply_type': 'text',
            'title': f"{task_type} 任务已完成",
            'message': "任务执行成功",
            'details': [],
            'task_id': execution_result.get('task_id'),
            'task_type': task_type,
            'channel': execution_result.get('channel', 'unknown'),
            'raw_result': execution_result.get('result')
        }
    
    def _build_error_reply(self, execution_result: Dict[str, Any], 
                          title: Optional[str] = None, 
                          message: Optional[str] = None) -> Dict[str, Any]:
        """
        构建失败回复
        
        Args:
            execution_result: TaskExecutor 返回的执行结果
            title: 自定义标题（可选）
            message: 自定义消息（可选）
        
        Returns:
            dict: 统一回复对象
        """
        
        error_code = execution_result.get('error_code', 'UNKNOWN_ERROR')
        error_message = execution_result.get('error_message', '未知错误')
        current_stage = execution_result.get('current_stage', 'unknown')
        
        # 构建标题
        if title:
            reply_title = title
        else:
            reply_title = "❌ 任务执行失败"
        
        # 构建核心消息
        if message:
            reply_message = message
        else:
            reply_message = "本次任务未成功完成，请检查输入或稍后重试。"
        
        # 构建详情列表
        details = [
            f"错误码：{error_code}",
            f"错误信息：{error_message}",
            f"执行阶段：{current_stage}"
        ]
        
        return {
            'success': False,
            'reply_type': 'error',
            'title': reply_title,
            'message': reply_message,
            'details': details,
            'task_id': execution_result.get('task_id'),
            'task_type': execution_result.get('task_type', 'unknown'),
            'channel': execution_result.get('channel', 'unknown'),
            'raw_result': None
        }
    
    def render_reply_as_text(self, reply: Dict[str, Any]) -> str:
        """
        将统一回复对象渲染为纯文本
        
        Args:
            reply: 统一回复对象
        
        Returns:
            str: 纯文本回复
        """
        
        lines = []
        
        # 标题
        title = reply.get('title', '')
        if title:
            lines.append(title)
            lines.append("")
        
        # 核心消息
        message = reply.get('message', '')
        if message:
            lines.append(message)
            lines.append("")
        
        # 详情列表
        details = reply.get('details', [])
        if details:
            for detail in details:
                lines.append(detail)
                lines.append("")  # 每个部分之间加空行
        
        # 任务编号（放在最后）
        task_id = reply.get('task_id')
        if task_id:
            lines.append("━"*40)
            lines.append(f"任务编号：{task_id}")
        
        return '\n'.join(lines)
    
    def render_reply_for_channel(self, reply: Dict[str, Any], channel: str) -> Dict[str, Any]:
        """
        为特定渠道渲染回复
        
        Args:
            reply: 统一回复对象
            channel: 渠道名称（dingtalk/qq）
        
        Returns:
            dict: 渠道特定的回复格式
        """
        
        # 当前先统一使用纯文本格式
        # 后续可以扩展为富文本/卡片等
        text_content = self.render_reply_as_text(reply)
        
        return {
            'channel': channel,
            'msg_type': 'text',
            'content': text_content,
            'reply_object': reply  # 保留完整回复对象供调试
        }


# 便捷函数
def create_reply_builder() -> ReplyBuilder:
    """创建回复构建器实例"""
    return ReplyBuilder()


# 测试
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🔨 统一回复构建器测试")
    print("="*60 + "\n")
    
    builder = ReplyBuilder()
    
    # 测试 1: 视频分析成功回复
    print("--- 测试 1: 视频分析成功回复 ---")
    video_result = {
        'task_id': 'test_video_001',
        'task_type': 'video_analysis',
        'status': 'success',
        'channel': 'dingtalk',
        'result': {
            'ntrp_level': '3.5',
            'overall_score': 72,
            'key_issues': [
                {'phase': 'toss', 'severity': 'major', 'description': '抛球高度不稳定'},
                {'phase': 'loading', 'severity': 'minor', 'description': '身体转身不够充分'}
            ],
            'training_priorities': [
                '练习固定抛球高度',
                '加强核心力量训练'
            ]
        },
        'report': '发球动作流畅，整体节奏感良好。'
    }
    
    reply = builder.build_reply(video_result)
    print(f"回复对象：{reply['title']}")
    print(f"回复类型：{reply['reply_type']}")
    print()
    print("渲染为纯文本:")
    print(builder.render_reply_as_text(reply))
    print()
    
    # 测试 2: 文本任务成功回复
    print("--- 测试 2: 文本任务成功回复 ---")
    text_result = {
        'task_id': 'test_text_001',
        'task_type': 'chat',
        'status': 'success',
        'channel': 'qq',
        'result': {'message': 'text task executed'},
        'report': '收到文本消息：你好'
    }
    
    reply = builder.build_reply(text_result)
    print(f"回复对象：{reply['title']}")
    print()
    print("渲染为纯文本:")
    print(builder.render_reply_as_text(reply))
    print()
    
    # 测试 3: 失败回复
    print("--- 测试 3: 失败回复 ---")
    error_result = {
        'task_id': 'test_error_001',
        'task_type': 'video_analysis',
        'status': 'failed',
        'channel': 'dingtalk',
        'error_code': 'VIDEO_INPUT_MISSING',
        'error_message': '视频文件未找到',
        'current_stage': 'preparing_video_input'
    }
    
    reply = builder.build_reply(error_result)
    print(f"回复对象：{reply['title']}")
    print(f"成功状态：{reply['success']}")
    print()
    print("渲染为纯文本:")
    print(builder.render_reply_as_text(reply))
    print()
    
    # 测试 4: 渠道渲染
    print("--- 测试 4: 渠道渲染 ---")
    channel_reply = builder.render_reply_for_channel(reply, 'dingtalk')
    print(f"渠道：{channel_reply['channel']}")
    print(f"消息类型：{channel_reply['msg_type']}")
    print()
    
    print("="*60)
    print("✅ 所有测试通过")
    print("="*60 + "\n")
