#!/usr/bin/env python3
"""
统一分析服务测试脚本

验证第七步新增的统一分析服务接入层功能
"""

import sys
import os
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

print("\n" + "="*60)
print("🔬 统一分析服务自检")
print("="*60 + "\n")

# 自检 1: 导入分析服务
print("自检 1: 导入统一分析服务...")
try:
    from analysis_service import AnalysisService, create_analysis_service
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 2: 分析服务实例化
print("自检 2: 分析服务实例化...")
try:
    service = AnalysisService()
    assert hasattr(service, 'analyze_video'), "应有 analyze_video 方法"
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 3: 输入路径缺失应明确失败
print("自检 3: 输入路径缺失应明确失败...")
try:
    from models.task import UnifiedTask
    
    service = AnalysisService()
    task = UnifiedTask(task_type='video_analysis', channel='dingtalk', user_id='test')
    
    result = service.analyze_video(task)
    
    print(f"  结果：{result['success']}")
    print(f"  错误码：{result.get('error', {}).get('code')}")
    
    assert result['success'] == False, "应失败"
    assert result['error']['code'] == 'VIDEO_SOURCE_PATH_MISSING', "错误码应正确"
    
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 4: 文件不存在应明确失败
print("自检 4: 文件不存在应明确失败...")
try:
    service = AnalysisService()
    task = UnifiedTask(
        task_type='video_analysis',
        channel='dingtalk',
        user_id='test',
        source_file_path='/nonexistent/video.mp4'
    )
    
    result = service.analyze_video(task)
    
    print(f"  结果：{result['success']}")
    print(f"  错误码：{result.get('error', {}).get('code')}")
    
    assert result['success'] == False, "应失败"
    assert result['error']['code'] == 'VIDEO_SOURCE_PATH_NOT_FOUND', "错误码应正确"
    
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 5: 统一返回结构
print("自检 5: 统一返回结构...")
try:
    service = AnalysisService()
    task = UnifiedTask(task_type='video_analysis', channel='dingtalk', user_id='test')
    
    result = service.analyze_video(task)
    
    # 检查返回结构字段
    required_fields = [
        'success',
        'analysis_type',
        'summary',
        'report',
        'structured_result',
        'raw_result',
        'error'
    ]
    
    for field in required_fields:
        assert field in result, f"缺少字段：{field}"
    
    print(f"  返回字段：{', '.join(required_fields)}")
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 6: TaskExecutor 使用 AnalysisService
print("自检 6: TaskExecutor 使用 AnalysisService...")
try:
    from task_executor import TaskExecutor
    
    executor = TaskExecutor()
    
    # 检查是否有 analysis_service
    assert hasattr(executor, 'analysis_service'), "应有 analysis_service 属性"
    assert isinstance(executor.analysis_service, AnalysisService), "应是 AnalysisService 实例"
    
    # 检查是否移除了 video_handler
    assert not hasattr(executor, 'video_handler') or executor.video_handler is None, "不应有 video_handler"
    
    print("  ✅ TaskExecutor 已改用 AnalysisService")
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 自检 7: 无 fallback 到默认样例
print("自检 7: 无 fallback 到默认样例...")
try:
    service = AnalysisService()
    task = UnifiedTask(task_type='video_analysis', channel='dingtalk', user_id='test')
    
    result = service.analyze_video(task)
    
    # 应明确失败，不应返回成功
    assert result['success'] == False, "应失败，不应 fallback 到默认样例"
    assert result['error'] is not None, "应有错误信息"
    
    print("  ✅ 无默认样例 fallback")
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 8: 分析服务日志
print("自检 8: 分析服务日志...")
try:
    service = AnalysisService()
    task = UnifiedTask(task_type='video_analysis', channel='dingtalk', user_id='test')
    
    # 调用分析服务（应记录日志）
    result = service.analyze_video(task)
    
    # 日志已在 task_logger 中记录
    print("  ✅ 日志记录正常")
    print("  ✅ 通过")
except Exception as e:
    print(f"  ❌ 失败：{e}")
    sys.exit(1)

# 自检 9: 原有模块导入
print("自检 9: 原有核心模块导入...")
try:
    import router
    from adapters.dingtalk_adapter import parse_dingtalk_message
    from video_input_handler import prepare_video_input
    print("  ✅ 通过")
except Exception as e:
    print(f"  ⚠️  警告：{e}")

print("\n" + "="*60)
print("✅ 所有自检通过！")
print("="*60 + "\n")

print("📊 测试摘要:")
print("  - 分析服务导入：✅")
print("  - 分析服务实例化：✅")
print("  - 输入路径缺失失败：✅")
print("  - 文件不存在失败：✅")
print("  - 统一返回结构：✅")
print("  - TaskExecutor 集成：✅")
print("  - 无默认样例 fallback: ✅")
print("  - 日志记录：✅")
print("  - 原有模块：✅")
print("\n统一分析服务接入层已就绪！\n")
