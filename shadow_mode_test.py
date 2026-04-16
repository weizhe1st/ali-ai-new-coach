#!/usr/bin/env python3
"""
影子模式测试脚本
用于小流量验证新三层分析流程
"""

import json
from datetime import datetime
from report_generation_integration import ReportGenerator

def run_shadow_mode_test(sample_id: str, ntrp_level: str, video_type: str) -> dict:
    """
    运行影子模式测试
    
    Args:
        sample_id: 样本 ID
        ntrp_level: NTRP 等级
        video_type: 视频类型（抛球问题/蓄力问题/高水平示范/边界样本）
    
    Returns:
        测试结果字典
    """
    generator = ReportGenerator()
    
    # 生成影子模式报告
    report = generator.generate_report(sample_id, ntrp_level, shadow_mode=True)
    
    # 人工评估字段
    evaluation = {
        'task_id': sample_id,
        'report_version': report['report_version'],
        'shadow_mode': report['shadow_mode'],
        'video_type': video_type,
        'primary_issue_accurate': None,  # 人工填写
        'secondary_issue_reasonable': None,  # 人工填写
        'phase_difference_reasonable': None,  # 人工填写
        'training_advice_executable': None,  # 人工填写
        'looks_like_human_coach': None,  # 1-5 分
        'notes': '',
        'generated_at': datetime.now().isoformat()
    }
    
    # 自动评估字段
    auto_checks = {
        'has_primary_issue': report['primary_issue'] is not None,
        'has_secondary_issue': report['secondary_issue'] is not None,
        'has_matched_pool': report['matched_problem_pool'] is not None,
        'has_standard_samples': len(report['matched_standard_samples']) > 0,
        'has_phase_comparison': len(report['phase_comparison']) > 0,
        'has_priority_gaps': len(report['priority_gaps']) > 0,
        'has_training_advice': len(report['training_advice']) > 0,
        'has_summary': bool(report['summary']),
        'no_empty_fields': all([
            report['summary'],
            report['phase_comparison'],
            report['training_advice']
        ])
    }
    
    return {
        'report': report,
        'evaluation': evaluation,
        'auto_checks': auto_checks
    }


def main():
    print("="*60)
    print("🧪 影子模式测试（小流量验证）")
    print("="*60)
    print()
    
    # 测试样本（4 类）
    test_samples = [
        {
            'name': '测试 1: 典型抛球问题样本',
            'sample_id': 'batch001_video001',
            'ntrp_level': '2.5',
            'video_type': '抛球问题',
        },
        {
            'name': '测试 2: 典型蓄力问题样本',
            'sample_id': 'batch001_video004',
            'ntrp_level': '3.0',
            'video_type': '蓄力问题',
        },
        {
            'name': '测试 3: 高水平示范样本',
            'sample_id': 'batch003_video003',
            'ntrp_level': '4.5',
            'video_type': '高水平示范',
        },
        {
            'name': '测试 4: 边界样本',
            'sample_id': 'sample_20260415_abc123',
            'ntrp_level': '3.5',
            'video_type': '边界样本',
        },
    ]
    
    results = []
    
    for test_case in test_samples:
        print("="*60)
        print(f"🧪 {test_case['name']}")
        print("="*60)
        print()
        
        result = run_shadow_mode_test(
            test_case['sample_id'],
            test_case['ntrp_level'],
            test_case['video_type']
        )
        
        report = result['report']
        auto_checks = result['auto_checks']
        
        # 打印报告摘要
        print(f"📋 报告摘要:")
        print(f"   报告版本：{report['report_version']}")
        print(f"   影子模式：{report['shadow_mode']}")
        print(f"   Summary: {report['summary'][:80]}...")
        print()
        
        # 打印关键结果
        print(f"🔍 关键结果:")
        print(f"   Primary Issue: {report['primary_issue']}")
        print(f"   Secondary Issue: {report['secondary_issue']}")
        print(f"   Matched Pool: {report['matched_problem_pool']}")
        print(f"   Standard Samples: {len(report['matched_standard_samples'])} 个")
        print(f"   Priority Gaps: {len(report['priority_gaps'])} 个")
        print(f"   Training Advice: {len(report['training_advice'])} 条")
        print()
        
        # 自动检查结果
        print(f"✅ 自动检查:")
        passed = 0
        total = len(auto_checks)
        for check_name, passed_check in auto_checks.items():
            status = '✅' if passed_check else '⚠️'
            print(f"   {status} {check_name}: {passed_check}")
            if passed_check:
                passed += 1
        
        print()
        print(f"   通过率：{passed}/{total} ({passed/total*100:.0f}%)")
        print()
        
        # 打印人工评估模板
        evaluation = result['evaluation']
        print(f"📝 人工评估模板:")
        print(f"   primary_issue 是否准确：[是/否]")
        print(f"   secondary_issue 是否合理：[是/否]")
        print(f"   阶段差异是否合理：[是/否]")
        print(f"   训练建议是否可执行：[是/否]")
        print(f"   整体像不像真人教练：[1-5 分]")
        print(f"   备注：[填写备注]")
        print()
        
        results.append({
            'test_case': test_case,
            'result': result
        })
    
    # 汇总结果
    print("="*60)
    print("📊 影子模式测试汇总")
    print("="*60)
    print()
    
    total_passed = 0
    total_checks = 0
    
    for r in results:
        auto_checks = r['result']['auto_checks']
        passed = sum(1 for v in auto_checks.values() if v)
        total = len(auto_checks)
        total_passed += passed
        total_checks += total
        
        print(f"   {r['test_case']['name']}: {passed}/{total} ({passed/total*100:.0f}%)")
    
    print()
    overall_rate = total_passed / total_checks * 100 if total_checks > 0 else 0
    print(f"   总体通过率：{total_passed}/{total_checks} ({overall_rate:.0f}%)")
    print()
    
    if overall_rate >= 80:
        print("✅ 影子模式测试通过！可以进入小流量正式启用阶段")
    else:
        print("⚠️  影子模式测试未通过，建议先优化后再试")
    
    print()
    
    # 保存测试结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = f'reports/shadow_mode_test_{timestamp}.json'
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"💾 测试结果已保存到：{output_path}")
    print()
    
    print("="*60)
    print("下一步:")
    print("   1. 人工评估每个测试结果")
    print("   2. 填写评估表")
    print("   3. 达到通过标准后启用小流量")
    print("="*60)


if __name__ == '__main__':
    main()
