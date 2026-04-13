#!/usr/bin/env python3
"""
统一回复构建层测试

验证：
1. reply_builder.py 可正常 import
2. 文本任务可生成统一回复对象
3. 视频任务可生成统一回复对象
4. 失败任务可生成统一失败回复
5. 统一回复对象可被渲染为纯文本
6. 钉钉适配器已接入统一回复层
7. QQ 适配器已接入统一回复层
"""

import os
import sys

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)


def test_reply_builder_import():
    """测试 1: reply_builder.py 可正常 import"""
    print("[TEST] reply_builder import...")
    try:
        from reply_builder import ReplyBuilder, create_reply_builder
        builder = create_reply_builder()
        print("[PASS] reply builder import works")
        return True
    except Exception as e:
        print(f"[FAIL] reply builder import failed: {e}")
        return False


def test_text_task_reply():
    """测试 2: 文本任务可生成统一回复对象"""
    print("[TEST] text task reply building...")
    try:
        from reply_builder import ReplyBuilder
        
        builder = ReplyBuilder()
        text_result = {
            'task_id': 'test_text_001',
            'task_type': 'chat',
            'status': 'success',
            'channel': 'dingtalk',
            'result': {'message': 'text task executed'},
            'report': '收到文本消息：你好'
        }
        
        reply = builder.build_reply(text_result)
        
        assert reply['success'] == True, "应成功"
        assert reply['reply_type'] == 'text', "回复类型应为 text"
        assert reply['title'] == '💬 文本任务已处理', "标题应正确"
        assert reply['task_id'] == 'test_text_001', "任务 ID 应正确"
        
        # 测试渲染为纯文本
        text_output = builder.render_reply_as_text(reply)
        assert '文本任务已处理' in text_output, "应包含标题"
        assert '收到文本消息' in text_output, "应包含报告内容"
        
        print("[PASS] text task reply building works")
        return True
    except Exception as e:
        print(f"[FAIL] text task reply building failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_video_task_reply():
    """测试 3: 视频任务可生成统一回复对象"""
    print("[TEST] video task reply building...")
    try:
        from reply_builder import ReplyBuilder
        
        builder = ReplyBuilder()
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
        
        assert reply['success'] == True, "应成功"
        assert reply['reply_type'] == 'analysis_report', "回复类型应为 analysis_report"
        assert reply['title'] == '🎾 发球分析已完成', "标题应正确"
        assert reply['task_id'] == 'test_video_001', "任务 ID 应正确"
        
        # 测试渲染为纯文本
        text_output = builder.render_reply_as_text(reply)
        assert '发球分析已完成' in text_output, "应包含标题"
        assert '3.5' in text_output, "应包含 NTRP 等级"
        assert '72' in text_output, "应包含综合评分"
        
        print("[PASS] video task reply building works")
        return True
    except Exception as e:
        print(f"[FAIL] video task reply building failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_failure_reply():
    """测试 4: 失败任务可生成统一失败回复"""
    print("[TEST] failure reply building...")
    try:
        from reply_builder import ReplyBuilder
        
        builder = ReplyBuilder()
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
        
        assert reply['success'] == False, "应失败"
        assert reply['reply_type'] == 'error', "回复类型应为 error"
        assert reply['title'] == '❌ 任务执行失败', "标题应正确"
        assert reply['task_id'] == 'test_error_001', "任务 ID 应正确"
        
        # 测试渲染为纯文本
        text_output = builder.render_reply_as_text(reply)
        assert '任务执行失败' in text_output, "应包含标题"
        assert 'VIDEO_INPUT_MISSING' in text_output, "应包含错误码"
        assert '视频文件未找到' in text_output, "应包含错误信息"
        
        print("[PASS] failure reply building works")
        return True
    except Exception as e:
        print(f"[FAIL] failure reply building failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_plain_text_renderer():
    """测试 5: 统一回复对象可被渲染为纯文本"""
    print("[TEST] plain text renderer...")
    try:
        from reply_builder import ReplyBuilder
        
        builder = ReplyBuilder()
        reply = {
            'success': True,
            'reply_type': 'text',
            'title': '测试标题',
            'message': '测试消息',
            'details': ['详情 1', '详情 2'],
            'task_id': 'test_001'
        }
        
        text_output = builder.render_reply_as_text(reply)
        
        assert '测试标题' in text_output, "应包含标题"
        assert '测试消息' in text_output, "应包含消息"
        assert '详情 1' in text_output, "应包含详情 1"
        assert '详情 2' in text_output, "应包含详情 2"
        assert 'test_001' in text_output, "应包含任务 ID"
        
        print("[PASS] plain text renderer works")
        return True
    except Exception as e:
        print(f"[FAIL] plain text renderer failed: {e}")
        return False


def test_dingtalk_adapter_integration():
    """测试 6: 钉钉适配器已接入统一回复层"""
    print("[TEST] dingtalk adapter uses reply builder...")
    try:
        # 检查适配器代码是否包含 reply_builder 调用
        import os
        adapter_path = os.path.join(PROJECT_ROOT, 'adapters', 'dingtalk_adapter.py')
        with open(adapter_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'reply_builder' in content, "适配器应包含 reply_builder"
        assert 'build_reply' in content, "适配器应调用 build_reply"
        assert 'render_reply_for_channel' in content, "适配器应调用 render_reply_for_channel"
        
        print("[PASS] dingtalk adapter uses reply builder")
        return True
    except Exception as e:
        print(f"[FAIL] dingtalk adapter uses reply builder failed: {e}")
        return False


def test_qq_adapter_integration():
    """测试 7: QQ 适配器已接入统一回复层"""
    print("[TEST] qq adapter uses reply builder...")
    try:
        # 检查适配器代码是否包含 reply_builder 调用
        import os
        adapter_path = os.path.join(PROJECT_ROOT, 'adapters', 'qq_adapter.py')
        with open(adapter_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'reply_builder' in content, "适配器应包含 reply_builder"
        assert 'build_reply' in content, "适配器应调用 build_reply"
        assert 'render_reply_for_channel' in content, "适配器应调用 render_reply_for_channel"
        
        print("[PASS] qq adapter uses reply builder")
        return True
    except Exception as e:
        print(f"[FAIL] qq adapter uses reply builder failed: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🔨 统一回复构建层测试")
    print("="*60 + "\n")
    
    tests = [
        test_reply_builder_import,
        test_text_task_reply,
        test_video_task_reply,
        test_failure_reply,
        test_plain_text_renderer,
        test_dingtalk_adapter_integration,
        test_qq_adapter_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
        print()
    
    print("="*60)
    print(f"测试结果：{passed} 通过，{failed} 失败")
    print("="*60 + "\n")
    
    if failed == 0:
        print("✅ 所有测试通过！")
        return 0
    else:
        print(f"❌ {failed} 个测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
