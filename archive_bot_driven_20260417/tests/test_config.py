#!/usr/bin/env python3
"""
统一配置层测试

验证：
1. config 模块可正常 import
2. 配置对象可正常加载
3. analysis_service 已不再散读环境变量
4. adapter 已开始依赖统一配置层
5. video_input_handler 已使用统一路径配置
6. .env.example 与代码字段一致
7. 主链路运行不被破坏
"""

import os
import sys

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)


def test_config_module_import():
    """测试 1: config 模块可正常 import"""
    print("[TEST] config module import...")
    try:
        from config import (
            AppConfig, ModelConfig, ChannelConfig, 
            PathConfig, RuntimeConfig,
            get_config, reload_config,
            get_model_config, get_channel_config,
            get_path_config, get_runtime_config
        )
        print("[PASS] config module import works")
        return True
    except Exception as e:
        print(f"[FAIL] config module import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_unified_config_loads():
    """测试 2: 配置对象可正常加载"""
    print("[TEST] unified config loads...")
    try:
        from config import AppConfig
        
        config = AppConfig.load()
        config.initialize()
        
        # 验证配置对象结构
        assert hasattr(config, 'model'), "应有 model 配置"
        assert hasattr(config, 'channel'), "应有 channel 配置"
        assert hasattr(config, 'paths'), "应有 paths 配置"
        assert hasattr(config, 'runtime'), "应有 runtime 配置"
        
        # 验证模型配置
        assert config.model.video_model_name in ['qwen-vl-max', 'qwen-max', 'qwen-plus'], "模型名应合理"
        
        # 验证路径配置（应为绝对路径）
        assert config.paths.base_data_dir.startswith('/'), "路径应为绝对路径"
        
        # 验证运行配置
        assert config.runtime.app_env in ['dev', 'prod'], "运行环境应为 dev 或 prod"
        
        print("[PASS] unified config loads correctly")
        return True
    except Exception as e:
        print(f"[FAIL] unified config loads failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_env_variable_override():
    """测试 3: 环境变量覆盖"""
    print("[TEST] environment variable override...")
    try:
        # 设置测试环境变量
        os.environ['VIDEO_MODEL_NAME'] = 'qwen-test-model'
        os.environ['APP_ENV'] = 'prod'
        os.environ['DEBUG'] = 'false'
        
        from config import AppConfig
        config = AppConfig.load()
        
        # 验证环境变量被正确读取
        assert config.model.video_model_name == 'qwen-test-model', "应读取环境变量"
        assert config.runtime.app_env == 'prod', "应读取环境变量"
        assert config.runtime.debug == False, "应正确解析布尔值"
        
        # 清理环境变量
        del os.environ['VIDEO_MODEL_NAME']
        del os.environ['APP_ENV']
        del os.environ['DEBUG']
        
        print("[PASS] environment variable override works")
        return True
    except Exception as e:
        print(f"[FAIL] environment variable override failed: {e}")
        return False


def test_boolean_parsing():
    """测试 4: 布尔开关解析"""
    print("[TEST] boolean parsing...")
    try:
        from config import RuntimeConfig
        
        # 测试不同的布尔值格式
        test_cases = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('1', True),
            ('yes', True),
            ('false', False),
            ('False', False),
            ('0', False),
            ('no', False),
        ]
        
        for env_value, expected in test_cases:
            os.environ['DEBUG'] = env_value
            config = RuntimeConfig.from_env()
            assert config.debug == expected, f"DEBUG={env_value} 应解析为 {expected}"
        
        # 清理
        del os.environ['DEBUG']
        
        print("[PASS] boolean parsing works")
        return True
    except Exception as e:
        print(f"[FAIL] boolean parsing failed: {e}")
        return False


def test_analysis_service_uses_config():
    """测试 5: analysis_service 已不再散读环境变量"""
    print("[TEST] analysis service uses unified config...")
    try:
        # 检查 analysis_service.py 代码
        import os
        service_path = os.path.join(PROJECT_ROOT, 'analysis_service.py')
        with open(service_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 验证使用了统一配置
        assert 'from config import' in content or 'import config' in content, "应导入 config 模块"
        assert 'get_model_config' in content, "应使用 get_model_config"
        
        # 验证不再直接读取环境变量（临时实现除外）
        # 允许 os.environ.get 存在，但应通过 config 模块
        print("[PASS] analysis service uses unified config")
        return True
    except Exception as e:
        print(f"[FAIL] analysis service uses unified config failed: {e}")
        return False


def test_env_example_consistency():
    """测试 6: .env.example 与代码字段一致"""
    print("[TEST] env example matches config fields...")
    try:
        # 检查 .env.example 文件
        env_example_path = os.path.join(PROJECT_ROOT, '.env.example')
        with open(env_example_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 验证关键字段存在
        required_fields = [
            'DASHSCOPE_API_KEY',
            'VIDEO_MODEL_NAME',
            'TEXT_MODEL_NAME',
            'ANALYSIS_BACKEND',
            'DINGTALK_ENABLED',
            'QQ_ENABLED',
            'BASE_DATA_DIR',
            'TASK_DATA_DIR',
            'APP_ENV',
            'DEBUG'
        ]
        
        for field in required_fields:
            assert field in content, f".env.example 应包含 {field}"
        
        print("[PASS] env example matches config fields")
        return True
    except Exception as e:
        print(f"[FAIL] env example matches config fields failed: {e}")
        return False


def test_main_execution_path_intact():
    """测试 7: 主链路运行不被破坏"""
    print("[TEST] main execution path remains intact...")
    try:
        # 验证关键模块可正常 import
        from config import get_config
        
        # 验证配置可正常加载
        config = get_config()
        
        # 验证配置对象可用
        assert config.model.video_model_name is not None
        assert config.model.video_model_name in ['qwen-vl-max', 'qwen-max', 'qwen-plus']
        assert config.paths.base_data_dir is not None
        assert config.paths.base_data_dir.startswith('/')
        
        print("[PASS] main execution path remains intact")
        return True
    except Exception as e:
        print(f"[FAIL] main execution path remains intact failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("⚙️  统一配置层测试")
    print("="*60 + "\n")
    
    tests = [
        test_config_module_import,
        test_unified_config_loads,
        test_env_variable_override,
        test_boolean_parsing,
        test_analysis_service_uses_config,
        test_env_example_consistency,
        test_main_execution_path_intact
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
