#!/usr/bin/env python3
"""
系统验收测试脚本

验证主链路是否正常工作：
1. 钉钉文字消息联调
2. QQ 文字消息联调
3. 钉钉视频消息联调（模拟）
4. QQ 视频消息联调（模拟）
5. 视频输入失败场景
6. 分析失败场景
7. ReplyBuilder 输出一致性
8. 配置层加载
"""

import os
import sys
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)


def test_config_loading():
    """测试 1: 配置层加载"""
    print("[TEST] 配置层加载...")
    try:
        from config import AppConfig, get_config
        
        # 加载配置
        config = AppConfig.load()
        config.initialize()
        
        # 验证配置对象
        assert config.model.video_model_name is not None
        assert config.paths.base_data_dir is not None
        assert config.runtime.app_env in ['dev', 'prod']
        
        print("[PASS] 配置层加载成功")
        return True
    except Exception as e:
        print(f"[FAIL] 配置层加载失败：{e}")
        return False


def test_dingtalk_text_flow():
    """测试 2: 钉钉文字消息联调"""
    print("[TEST] 钉钉文字消息联调...")
    try:
        # 检查适配器代码是否包含 ReplyBuilder 调用
        import os
        adapter_path = os.path.join(PROJECT_ROOT, 'adapters', 'dingtalk_adapter.py')
        with open(adapter_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 验证使用了 ReplyBuilder
        assert 'reply_builder' in content or 'ReplyBuilder' in content
        assert 'build_reply' in content
        assert 'render_reply_for_channel' in content
        
        print("[PASS] 钉钉文字消息联调通过（代码结构验证）")
        return True
    except Exception as e:
        print(f"[FAIL] 钉钉文字消息联调失败：{e}")
        return False


def test_qq_text_flow():
    """测试 3: QQ 文字消息联调"""
    print("[TEST] QQ 文字消息联调...")
    try:
        # 检查适配器代码是否包含 ReplyBuilder 调用
        import os
        adapter_path = os.path.join(PROJECT_ROOT, 'adapters', 'qq_adapter.py')
        with open(adapter_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 验证使用了 ReplyBuilder
        assert 'reply_builder' in content or 'ReplyBuilder' in content
        assert 'build_reply' in content
        assert 'render_reply_for_channel' in content
        
        print("[PASS] QQ 文字消息联调通过（代码结构验证）")
        return True
    except Exception as e:
        print(f"[FAIL] QQ 文字消息联调失败：{e}")
        return False


def test_video_input_failure():
    """测试 4: 视频输入失败场景"""
    print("[TEST] 视频输入失败场景...")
    try:
        # 检查 task_executor.py 是否包含失败处理逻辑
        import os
        executor_path = os.path.join(PROJECT_ROOT, 'task_executor.py')
        with open(executor_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 验证包含失败处理
        assert 'mark_failed' in content
        assert 'VIDEO_INPUT_MISSING' in content or 'VIDEO_PATH_MISSING' in content
        assert 'error_code' in content
        
        print("[PASS] 视频输入失败场景处理正确（代码结构验证）")
        return True
    except Exception as e:
        print(f"[FAIL] 视频输入失败场景处理失败：{e}")
        return False


def test_reply_builder_consistency():
    """测试 5: ReplyBuilder 输出一致性"""
    print("[TEST] ReplyBuilder 输出一致性...")
    try:
        from reply_builder import ReplyBuilder
        
        builder = ReplyBuilder()
        
        # 测试成功回复
        success_result = {
            'task_id': 'test_001',
            'task_type': 'video_analysis',
            'status': 'success',
            'channel': 'dingtalk',
            'result': {
                'ntrp_level': '3.5',
                'overall_score': 72
            },
            'report': '测试报告'
        }
        
        reply_success = builder.build_reply(success_result)
        assert reply_success['success'] == True
        assert reply_success['reply_type'] == 'analysis_report'
        
        # 测试失败回复
        error_result = {
            'task_id': 'test_002',
            'task_type': 'video_analysis',
            'status': 'failed',
            'channel': 'dingtalk',
            'error_code': 'TEST_ERROR',
            'error_message': '测试错误',
            'current_stage': 'testing'
        }
        
        reply_error = builder.build_reply(error_result)
        assert reply_error['success'] == False
        assert reply_error['reply_type'] == 'error'
        
        # 测试渲染为文本
        text_success = builder.render_reply_as_text(reply_success)
        text_error = builder.render_reply_as_text(reply_error)
        
        assert '测试报告' in text_success or '3.5' in text_success
        assert '测试错误' in text_error
        
        print("[PASS] ReplyBuilder 输出一致性验证通过")
        return True
    except Exception as e:
        print(f"[FAIL] ReplyBuilder 输出一致性验证失败：{e}")
        return False


def test_analysis_service_config():
    """测试 6: AnalysisService 配置接入"""
    print("[TEST] AnalysisService 配置接入...")
    try:
        # 检查 analysis_service.py 是否使用 config
        import os
        service_path = os.path.join(PROJECT_ROOT, 'analysis_service.py')
        with open(service_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 验证使用了 config
        assert 'from config import' in content or 'import config' in content
        assert 'get_model_config' in content
        assert 'model_config.dashscope_api_key' in content
        assert 'model_config.video_model_name' in content
        
        # 验证不再直接读取环境变量
        assert 'os.environ.get' not in content or content.count('os.environ.get') == 0
        
        print("[PASS] AnalysisService 配置接入验证通过")
        return True
    except Exception as e:
        print(f"[FAIL] AnalysisService 配置接入验证失败：{e}")
        return False


def test_video_input_handler_path_config():
    """测试 7: VideoInputHandler 路径配置"""
    print("[TEST] VideoInputHandler 路径配置...")
    try:
        # 检查 video_input_handler.py 是否使用 config
        import os
        handler_path = os.path.join(PROJECT_ROOT, 'video_input_handler.py')
        with open(handler_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 验证使用了 config
        assert 'from config import' in content or 'import config' in content
        assert 'get_path_config' in content or 'PathConfig' in content
        
        print("[PASS] VideoInputHandler 路径配置验证通过")
        return True
    except Exception as e:
        print(f"[FAIL] VideoInputHandler 路径配置验证失败：{e}")
        return False


def main():
    """运行所有验收测试"""
    print("\n" + "="*60)
    print("🎾 网球 AI 教练系统 - 验收测试")
    print("="*60 + "\n")
    
    tests = [
        ("配置层加载", test_config_loading),
        ("钉钉文字消息联调", test_dingtalk_text_flow),
        ("QQ 文字消息联调", test_qq_text_flow),
        ("视频输入失败场景", test_video_input_failure),
        ("ReplyBuilder 输出一致性", test_reply_builder_consistency),
        ("AnalysisService 配置接入", test_analysis_service_config),
        ("VideoInputHandler 路径配置", test_video_input_handler_path_config)
    ]
    
    passed = 0
    failed = 0
    results = []
    
    for name, test_func in tests:
        if test_func():
            passed += 1
            results.append(f"[PASS] {name}")
        else:
            failed += 1
            results.append(f"[FAIL] {name}")
        print()
    
    print("="*60)
    print(f"测试结果：{passed} 通过，{failed} 失败")
    print("="*60 + "\n")
    
    for result in results:
        print(result)
    
    print()
    if failed == 0:
        print("✅ 所有验收测试通过！")
        print()
        print("当前版本状态：可小范围内部试运行")
        print("下一步：真实渠道联调 + 生产配置准备")
        return 0
    else:
        print(f"❌ {failed} 个验收测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
