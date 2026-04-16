#!/usr/bin/env python3
"""
更新报告生成逻辑
添加：等级区间 + 置信度 + 更稳妥的话术
"""

import os

REPORT_FILE = 'ai-coach/report_generation_integration.py'

print("="*70)
print("📝 更新报告生成逻辑")
print("="*70)
print()

# 读取文件
with open(REPORT_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 添加置信度计算函数
print("1️⃣  添加置信度计算函数...")

confidence_func = '''
    def _calculate_confidence(self, user_sample: dict) -> dict:
        """
        计算评估置信度
        
        Returns:
            dict: {level: '高/中/低', reasons: [...]}
        """
        ntrp = user_sample.get('ntrp_level', 'unknown')
        category = user_sample.get('sample_category', 'unknown')
        quality_grade = user_sample.get('quality_grade', 'unknown')
        
        reasons = []
        
        # 高置信度条件
        if ntrp in ['5.0', '5.0+'] and category == 'excellent_demo' and quality_grade == 'A':
            return {'level': '高', 'reasons': ['顶级水平样本', 'A 级质量', '动作标准']}
        
        if ntrp in ['2.5', '3.0', '3.5'] and category == 'typical_issue' and quality_grade == 'A':
            return {'level': '高', 'reasons': ['典型问题清晰', 'A 级质量', '问题明确']}
        
        # 中置信度条件
        if ntrp in ['4.0', '4.5']:
            reasons.append('中等级别样本')
        
        if quality_grade == 'B':
            reasons.append('B 级质量')
        
        if category == 'boundary_case':
            reasons.append('边界案例')
        
        if ntrp == 'unknown':
            reasons.append('NTRP 未知')
        
        # 低置信度条件
        if len(reasons) >= 3:
            return {'level': '低', 'reasons': reasons}
        
        if reasons:
            return {'level': '中', 'reasons': reasons}
        
        return {'level': '中', 'reasons': ['标准样本']}
    
    def _get_ntrp_range(self, ntrp: str) -> str:
        """
        将单点 NTRP 转换为区间
        
        Args:
            ntrp: 单点 NTRP 等级（如 "3.0"）
        
        Returns:
            str: NTRP 区间（如 "3.0-3.5"）
        """
        if ntrp == 'unknown':
            return '待评估'
        
        # 定义区间映射
        range_map = {
            '2.5': '2.5-3.0',
            '3.0': '3.0-3.5',
            '3.5': '3.5-4.0',
            '4.0': '4.0-4.5',
            '4.5': '4.5-5.0',
            '5.0': '5.0+',
            '5.0+': '5.0+'
        }
        
        return range_map.get(ntrp, ntrp)

'''

# 找到 ISSUE_TO_KNOWLEDGE 字典的结尾，插入置信度函数
insert_marker = "ISSUE_TO_KNOWLEDGE = {"
if insert_marker in content:
    # 在 ISSUE_TO_KNOWLEDGE 之前插入
    content = content.replace(
        "ISSUE_TO_KNOWLEDGE = {",
        f"    def _calculate_confidence(self, user_sample: dict) -> dict:\n        \"\"\"\n        计算评估置信度\n        \n        Returns:\n            dict: {{level: '高/中/低', reasons: [...]}}\n        \"\"\"\n        ntrp = user_sample.get('ntrp_level', 'unknown')\n        category = user_sample.get('sample_category', 'unknown')\n        quality_grade = user_sample.get('quality_grade', 'unknown')\n        \n        reasons = []\n        \n        # 高置信度条件\n        if ntrp in ['5.0', '5.0+'] and category == 'excellent_demo' and quality_grade == 'A':\n            return {{'level': '高', 'reasons': ['顶级水平样本', 'A 级质量', '动作标准']}}\n        \n        if ntrp in ['2.5', '3.0', '3.5'] and category == 'typical_issue' and quality_grade == 'A':\n            return {{'level': '高', 'reasons': ['典型问题清晰', 'A 级质量', '问题明确']}}\n        \n        # 中置信度条件\n        if ntrp in ['4.0', '4.5']:\n            reasons.append('中等级别样本')\n        \n        if quality_grade == 'B':\n            reasons.append('B 级质量')\n        \n        if category == 'boundary_case':\n            reasons.append('边界案例')\n        \n        if ntrp == 'unknown':\n            reasons.append('NTRP 未知')\n        \n        # 低置信度条件\n        if len(reasons) >= 3:\n            return {{'level': '低', 'reasons': reasons}}\n        \n        if reasons:\n            return {{'level': '中', 'reasons': reasons}}\n        \n        return {{'level': '中', 'reasons': ['标准样本']}}\n    \n    def _get_ntrp_range(self, ntrp: str) -> str:\n        \"\"\"\n        将单点 NTRP 转换为区间\n        \n        Args:\n            ntrp: 单点 NTRP 等级（如 \"3.0\"）\n        \n        Returns:\n            str: NTRP 区间（如 \"3.0-3.5\"）\n        \"\"\"\n        if ntrp == 'unknown':\n            return '待评估'\n        \n        # 定义区间映射\n        range_map = {{\n            '2.5': '2.5-3.0',\n            '3.0': '3.0-3.5',\n            '3.5': '3.5-4.0',\n            '4.0': '4.0-4.5',\n            '4.5': '4.5-5.0',\n            '5.0': '5.0+',\n            '5.0+': '5.0+'\n        }}\n        \n        return range_map.get(ntrp, ntrp)\n\n\nISSUE_TO_KNOWLEDGE = {{"
    )
    print("   ✅ 已添加置信度计算函数")
else:
    print("   ⚠️  未找到插入位置")

print()

# 2. 更新总结生成逻辑（使用区间 + 置信度）
print("2️⃣  更新总结生成逻辑...")

old_summary_pattern = '''        # 生成总结（带校准的小流量模式）
        ntrp = user_sample.get('ntrp_level', '未知')
        if primary_issue:
            impact = ISSUE_TO_KNOWLEDGE.get(primary_issue, {}).get('priority', 'medium')
            # 加入教练风格的总结
            coach_tone = ISSUE_TO_KNOWLEDGE.get(primary_issue, {}).get('coach_tips', [])
            if coach_tone:
                coach_tip = coach_tone[0]  # 取第一条教练提示
                # 使用区间评估，避免过硬结论
                report['summary'] = (
                    f'发球分析：{coach_tip} 主要问题为 {primary_issue}，'
                    f'优先级 {impact}。NTRP 等级约 {ntrp} 级（参考值），'
                    f'建议优先改进 {len(phase_weaknesses)} 个阶段，'
                    f'参考 {len(golden_samples)} 个标准示范样本进行练习。'
                )
            else:
                report['summary'] = (
                    f'发球分析：主要问题为 {primary_issue}，'
                    f'优先级 {impact}。NTRP 等级约 {ntrp} 级（参考值），'
                    f'建议优先改进 {len(phase_weaknesses)} 个阶段，'
                    f'参考 {len(golden_samples)} 个标准示范样本进行练习。'
                )'''

new_summary_pattern = '''        # 生成总结（小流量模式：区间 + 置信度）
        ntrp = user_sample.get('ntrp_level', 'unknown')
        ntrp_range = self._get_ntrp_range(ntrp)
        confidence = self._calculate_confidence(user_sample)
        
        # 根据置信度调整话术
        if confidence['level'] == '高':
            confidence_text = '评估置信度：高'
            range_text = f'NTRP 水平 {ntrp_range}级'
        elif confidence['level'] == '中':
            confidence_text = f'评估置信度：中（{",".join(confidence["reasons"][:2])}）'
            range_text = f'NTRP 水平约 {ntrp_range}级（参考区间）'
        else:
            confidence_text = f'评估置信度：低（{",".join(confidence["reasons"][:2])}），建议人工复核'
            range_text = f'NTRP 水平可能在 {ntrp_range}级范围'
        
        if primary_issue:
            impact = ISSUE_TO_KNOWLEDGE.get(primary_issue, {}).get('priority', 'medium')
            # 加入教练风格的总结
            coach_tone = ISSUE_TO_KNOWLEDGE.get(primary_issue, {}).get('coach_tips', [])
            if coach_tone:
                coach_tip = coach_tone[0]  # 取第一条教练提示
                report['summary'] = (
                    f'发球分析：{coach_tip} 主要问题为 {primary_issue}，'
                    f'优先级 {impact}。{range_text}，{confidence_text}。'
                    f'建议优先改进 {len(phase_weaknesses)} 个阶段，'
                    f'参考 {len(golden_samples)} 个标准示范样本进行练习。'
                )
            else:
                report['summary'] = (
                    f'发球分析：主要问题为 {primary_issue}，'
                    f'优先级 {impact}。{range_text}，{confidence_text}。'
                    f'建议优先改进 {len(phase_weaknesses)} 个阶段，'
                    f'参考 {len(golden_samples)} 个标准示范样本进行练习。'
                )'''

if old_summary_pattern in content:
    content = content.replace(old_summary_pattern, new_summary_pattern)
    print("   ✅ 已更新总结生成逻辑")
else:
    print("   ⚠️  未找到总结生成逻辑")

print()

# 3. 更新用户报告输出（添加置信度显示）
print("3️⃣  更新用户报告输出...")

old_report_output = '''        lines.append(f"📊 {report['summary']}")'''

new_report_output = '''        # 添加评估信息
        ntrp = user_sample.get('ntrp_level', 'unknown')
        confidence = self._calculate_confidence(user_sample)
        ntrp_range = self._get_ntrp_range(ntrp)
        
        lines.append("📊 评估信息:")
        lines.append(f"   等级区间：{ntrp_range}级")
        lines.append(f"   置信度：{confidence['level']}")
        if confidence['reasons']:
            lines.append(f"   依据：{', '.join(confidence['reasons'])}")
        lines.append("")
        lines.append(f"📝 {report['summary']}")'''

if old_report_output in content:
    content = content.replace(old_report_output, new_report_output)
    print("   ✅ 已更新用户报告输出")
else:
    print("   ⚠️  未找到报告输出位置")

print()

# 保存文件
with open(REPORT_FILE, 'w', encoding='utf-8') as f:
    f.write(content)

print("="*70)
print("✅ 报告生成逻辑更新完成！")
print("="*70)
print()
print("新增功能:")
print("   1. NTRP 区间输出（如 3.0-3.5 级）")
print("   2. 置信度标注（高/中/低）")
print("   3. 置信度依据说明")
print("   4. 更稳妥的话术（约/可能/参考区间）")
print()
