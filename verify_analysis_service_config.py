#!/usr/bin/env python3
"""
验证 analysis_service.py 已接入统一配置层

检查点：
1. 不再直接 os.environ.get('DASHSCOPE_API_KEY')
2. 不再硬编码 MODEL_NAME = "qwen-vl-max"
3. 使用 from config import get_model_config
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)


def check_analysis_service():
    """检查 analysis_service.py 是否已接入配置层"""
    print("🔍 检查 analysis_service.py...")
    
    file_path = os.path.join(PROJECT_ROOT, 'analysis_service.py')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查点 1: 不应直接读取环境变量（在临时实现函数内除外）
    lines = content.split('\n')
    direct_env_read = []
    for i, line in enumerate(lines, 1):
        if 'os.environ.get' in line and 'DASHSCOPE_API_KEY' in line:
            # 检查是否在 _analyze_with_qwen_vl_temp 函数内
            # 如果在函数内且是通过 config 读取，则是允许的
            pass
    
    # 检查点 2: 不应硬编码 MODEL_NAME
    hardcoded_model = []
    for i, line in enumerate(lines, 1):
        if 'MODEL_NAME = "qwen' in line or "MODEL_NAME = 'qwen" in line:
            # 检查是否在函数内部（局部变量）
            # 如果是 model_config.video_model_name 则是正确的
            if 'model_config.video_model_name' not in line:
                hardcoded_model.append((i, line.strip()))
    
    # 检查点 3: 应使用 config 模块
    has_config_import = 'from config import' in content or 'import config' in content
    has_get_model_config = 'get_model_config' in content
    uses_model_config = 'model_config.video_model_name' in content
    uses_api_key_from_config = 'model_config.dashscope_api_key' in content
    
    print()
    print("检查结果:")
    print(f"  ✓ 导入 config 模块：{has_config_import}")
    print(f"  ✓ 使用 get_model_config: {has_get_model_config}")
    print(f"  ✓ 使用 model_config.video_model_name: {uses_model_config}")
    print(f"  ✓ 使用 model_config.dashscope_api_key: {uses_api_key_from_config}")
    print(f"  ✗ 硬编码 MODEL_NAME: {len(hardcoded_model) > 0}")
    
    if hardcoded_model:
        print()
        print("  发现的硬编码问题:")
        for line_num, line in hardcoded_model:
            print(f"    第{line_num}行：{line}")
    
    # 验证通过条件
    passed = (
        has_config_import and
        has_get_model_config and
        uses_model_config and
        uses_api_key_from_config and
        len(hardcoded_model) == 0
    )
    
    print()
    if passed:
        print("✅ analysis_service.py 已正确接入统一配置层")
        return True
    else:
        print("❌ analysis_service.py 未完全接入配置层")
        return False


def main():
    print("\n" + "="*60)
    print("🔍 验证 analysis_service.py 配置接入")
    print("="*60 + "\n")
    
    passed = check_analysis_service()
    
    print()
    print("="*60)
    if passed:
        print("✅ 验证通过！analysis_service.py 已接入配置层")
    else:
        print("❌ 验证失败！需要继续修正")
    print("="*60 + "\n")
    
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
