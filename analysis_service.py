#!/usr/bin/env python3
"""
统一分析服务接入层

负责：
- 接收标准任务输入（task.source_file_path）
- 调用旧分析能力
- 规范化返回结构

让执行层不再直接耦合旧分析脚本，
后续替换模型、替换实现时只需修改本层。
"""

import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from models.task import UnifiedTask
from task_logger import log_task_event


class AnalysisService:
    """
    统一分析服务
    
    职责：
    - 接收标准任务输入
    - 调用旧分析能力
    - 规范化返回结构
    """
    
    def __init__(self):
        self.analysis_entry = "legacy_adapter"  # 默认使用 legacy adapter
        print(f"✅ AnalysisService 已初始化 (entry={self.analysis_entry})")
    
    def analyze_video(self, task: UnifiedTask) -> Dict[str, Any]:
        """
        统一视频分析接口
        
        Args:
            task: UnifiedTask 对象（应已包含 source_file_path）
        
        Returns:
            dict: 统一分析结果
        """
        
        # 校验输入
        if not task.source_file_path:
            return self._build_error_result(
                "VIDEO_SOURCE_PATH_MISSING",
                "task.source_file_path is not set"
            )
        
        if not os.path.exists(task.source_file_path):
            return self._build_error_result(
                "VIDEO_SOURCE_PATH_NOT_FOUND",
                f"Video file not found at {task.source_file_path}"
            )
        
        # 调用旧分析能力
        try:
            result = self._call_legacy_analysis(task)
            return self._normalize_result(result, task)
        except Exception as e:
            return self._build_error_result(
                "VIDEO_ANALYSIS_FAILED",
                f"Legacy analysis failed: {str(e)}"
            )
    
    def _call_legacy_analysis(self, task: UnifiedTask) -> Dict[str, Any]:
        """
        调用旧分析能力
        
        通过 legacy adapter 调用现有分析能力
        当前支持：
        - complete_analysis_service (主要)
        - qwen_vl_analysis (临时备用)
        
        Args:
            task: UnifiedTask 对象
        
        Returns:
            dict: 旧分析模块返回结果
        """
        
        # 优先使用 complete_analysis_service（主要旧分析能力）
        try:
            print(f"🔍 尝试调用 complete_analysis_service...")
            from complete_analysis_service import analyze_video_complete
            
            result = analyze_video_complete(
                video_path=task.source_file_path,
                user_id=task.user_id,
                task_id=task.task_id
            )
            
            if result and result.get('success'):
                print(f"✅ 使用 complete_analysis_service 成功")
                return {
                    'success': True,
                    'analysis': result.get('analysis', {}),
                    'entry': 'complete_analysis_service',
                    'mp_metrics': result.get('mp_metrics'),
                    'knowledge_results': result.get('knowledge_results')
                }
            else:
                print(f"⚠️  complete_analysis_service 返回失败，尝试备用方案")
                
        except ImportError as e:
            print(f"⚠️  complete_analysis_service 不可用：{e}")
        except Exception as e:
            print(f"⚠️  complete_analysis_service 调用失败：{e}")
        
        # 备用方案：使用临时 Qwen-VL 实现
        # TODO: 后续应移除此临时实现，统一使用 legacy adapter
        print(f"⚠️  使用临时 Qwen-VL 实现（应尽快替换为 legacy adapter）")
        return self._analyze_with_qwen_vl_temp(task)
    
    def _analyze_with_qwen_vl_temp(self, task: UnifiedTask) -> Dict[str, Any]:
        """
        使用 Qwen-VL 进行视频分析（临时实现）
        
        ⚠️  这是临时备用方案，应尽快替换为 legacy adapter
        
        Args:
            task: UnifiedTask 对象
        
        Returns:
            dict: 分析结果
        """
        
        # 从环境变量读取 API Key（不允许硬编码）
        dashscope_api_key = os.environ.get('DASHSCOPE_API_KEY')
        if not dashscope_api_key:
            raise ValueError(
                "DASHSCOPE_API_KEY environment variable is required. "
                "Please set it before running analysis."
            )
        
        import base64
        import requests
        
        API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        MODEL_NAME = "qwen-vl-max"
        
        # 读取视频文件
        with open(task.source_file_path, 'rb') as f:
            video_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        # 系统提示词
        system_prompt = """你是一个专业的网球发球分析系统。

【分析要求】
1. 使用"三步分析法"：逐帧观察 → 标准对照 → 输出 JSON
2. 对照 169 条教练知识（杨超 71 条、灵犀 41 条、Yellow 57 条）
3. 输出通俗易懂的分析报告

【输出格式】
必须是合法 JSON：
{
  "ntrp_level": "3.0|3.5|4.0|4.5|5.0",
  "confidence": 0.0-1.0,
  "overall_score": 0-100,
  "key_issues": [{"phase": "...", "severity": "critical|major|minor", "description": "..."}],
  "highlights": ["..."],
  "training_priorities": ["..."],
  "detailed_analysis": {"ready": "...", "toss": "...", "loading": "...", "contact": "...", "follow": "..."},
  "coach_references": {"杨超": [...], "灵犀": [...], "Yellow": [...]}
}
"""
        
        # 调用 API
        headers = {
            "Authorization": f"Bearer {dashscope_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "video_url", "video_url": {"url": f"data:video/mp4;base64,{video_base64}"}},
                        {"type": "text", "text": "请分析这个网球发球视频，输出 JSON 格式结果。"}
                    ]
                }
            ],
            "max_tokens": 3000
        }
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # 解析 JSON
        import json
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            analysis = json.loads(content[json_start:json_end])
        else:
            analysis = {"raw_analysis": content}
        
        return {
            'success': True,
            'analysis': analysis,
            'entry': 'qwen_vl_temp'
        }
    
    def _normalize_result(self, result: Dict[str, Any], task: UnifiedTask) -> Dict[str, Any]:
        """
        规范化分析结果
        
        Args:
            result: 旧分析模块返回结果
            task: UnifiedTask 对象
        
        Returns:
            dict: 统一标准结果
        """
        
        if not result.get('success'):
            return result
        
        analysis = result.get('analysis', {})
        
        # 构建统一返回结构
        return {
            'success': True,
            'analysis_type': 'video',
            'entry': result.get('entry', 'unknown'),
            'summary': self._generate_summary(analysis),
            'report': self._generate_report(analysis),
            'structured_result': {
                'ntrp_level': analysis.get('ntrp_level', 'N/A'),
                'confidence': analysis.get('confidence', 0),
                'overall_score': analysis.get('overall_score', 0),
                'key_issues': analysis.get('key_issues', []),
                'highlights': analysis.get('highlights', []),
                'training_priorities': analysis.get('training_priorities', [])
            },
            'detailed_analysis': analysis.get('detailed_analysis', {}),
            'coach_references': analysis.get('coach_references', {}),
            'raw_result': analysis,
            'error': None,
            'video_file': task.source_file_path,
            'video_name': task.source_file_name
        }
    
    def _generate_summary(self, analysis: Dict[str, Any]) -> str:
        """生成分析摘要"""
        ntrp_level = analysis.get('ntrp_level', 'N/A')
        confidence = analysis.get('confidence', 0) * 100
        score = analysis.get('overall_score', 0)
        
        return f"NTRP {ntrp_level}级（置信度{confidence:.0f}%），综合评分{score}/100"
    
    def _generate_report(self, analysis: Dict[str, Any]) -> str:
        """生成分析报告"""
        ntrp_level = analysis.get('ntrp_level', 'N/A')
        score = analysis.get('overall_score', 0)
        
        lines = []
        lines.append(f"🎾 网球发球分析报告")
        lines.append(f"")
        lines.append(f"📊 综合评估")
        lines.append(f"  NTRP 等级：{ntrp_level}")
        lines.append(f"  综合评分：{score}/100")
        lines.append(f"")
        
        # 亮点
        highlights = analysis.get('highlights', [])
        if highlights:
            lines.append(f"✅ 亮点")
            for h in highlights:
                lines.append(f"  ✓ {h}")
            lines.append(f"")
        
        # 问题
        key_issues = analysis.get('key_issues', [])
        if key_issues:
            lines.append(f"⚠️ 关键问题")
            severity_map = {'critical': '🔴', 'major': '🟠', 'minor': '🟡'}
            for issue in key_issues:
                emoji = severity_map.get(issue.get('severity', 'minor'), '⚪')
                phase = issue.get('phase', '')
                desc = issue.get('description', '')
                lines.append(f"  {emoji} [{phase}] {desc}")
            lines.append(f"")
        
        # 训练建议
        priorities = analysis.get('training_priorities', [])
        if priorities:
            lines.append(f"🎯 训练优先级")
            for i, p in enumerate(priorities[:3], 1):
                lines.append(f"  {i}. {p}")
        
        return '\n'.join(lines)
    
    def _build_error_result(self, error_code: str, error_message: str) -> Dict[str, Any]:
        """
        构建错误结果
        
        Args:
            error_code: 错误码
            error_message: 错误信息
        
        Returns:
            dict: 统一错误结果
        """
        return {
            'success': False,
            'analysis_type': 'video',
            'entry': self.analysis_entry,
            'summary': '',
            'report': None,
            'structured_result': None,
            'detailed_analysis': None,
            'coach_references': None,
            'raw_result': None,
            'error': {
                'code': error_code,
                'message': error_message
            },
            'video_file': None,
            'video_name': None
        }


# 便捷函数
def create_analysis_service() -> AnalysisService:
    """创建分析服务实例"""
    return AnalysisService()


# 测试
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🔬 统一分析服务测试")
    print("="*60 + "\n")
    
    service = AnalysisService()
    
    # 测试 1: 输入路径缺失
    print("--- 测试 1: 输入路径缺失 ---")
    task = UnifiedTask(task_type='video_analysis', channel='dingtalk', user_id='test')
    result = service.analyze_video(task)
    
    print(f"结果：{result['success']}")
    print(f"错误码：{result.get('error', {}).get('code')}")
    assert result['success'] == False, "应失败"
    assert result['error']['code'] == 'VIDEO_SOURCE_PATH_MISSING', "错误码应正确"
    print("✅ 通过\n")
    
    # 测试 2: 文件不存在
    print("--- 测试 2: 文件不存在 ---")
    task = UnifiedTask(
        task_type='video_analysis',
        channel='dingtalk',
        user_id='test',
        source_file_path='/nonexistent/video.mp4'
    )
    result = service.analyze_video(task)
    
    print(f"结果：{result['success']}")
    print(f"错误码：{result.get('error', {}).get('code')}")
    assert result['success'] == False, "应失败"
    assert result['error']['code'] == 'VIDEO_SOURCE_PATH_NOT_FOUND', "错误码应正确"
    print("✅ 通过\n")
    
    print("="*60)
    print("✅ 基础测试通过")
    print("="*60 + "\n")
    print("注意：完整视频分析测试需要配置 DASHSCOPE_API_KEY 环境变量")
    print("并准备真实视频文件。\n")
    print("⚠️  临时 Qwen-VL 实现仅供备用，应优先使用 complete_analysis_service\n")
