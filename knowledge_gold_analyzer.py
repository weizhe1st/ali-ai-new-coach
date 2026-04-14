#!/usr/bin/env python3
"""
知识库检索与黄金标准对比分析模块

功能：
1. 根据 NTRP 等级和阶段检索教练知识库
2. 将用户动作与黄金标准对比
3. 生成针对性的改进建议
"""

import os
import sys
import json
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime

# 数据库路径
DB_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/db/app.db'


# ═══════════════════════════════════════════════════════════════════
# 知识库检索
# ═══════════════════════════════════════════════════════════════════

class KnowledgeRetriever:
    """教练知识库检索器"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """获取数据库连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def query_by_phase(self, phase: str, ntrp_level: str = None, limit: int = 10) -> List[dict]:
        """
        根据阶段查询知识库
        
        Args:
            phase: 阶段名称 (ready/toss/loading/contact/follow)
            ntrp_level: NTRP 等级（可选，用于过滤）
            limit: 返回数量限制
        
        Returns:
            List[dict]: 知识库条目列表
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        # 查询该阶段相关的知识
        cursor.execute('''
            SELECT coach_id, knowledge_type, title, knowledge_summary, 
                   key_elements, common_errors, correction_method,
                   issue_tags, phase, quality_grade
            FROM coach_knowledge
            WHERE phase LIKE ?
            ORDER BY 
                CASE quality_grade 
                    WHEN 'A' THEN 1 
                    WHEN 'B' THEN 2 
                    WHEN 'C' THEN 3 
                    ELSE 4 
                END,
                confidence DESC
            LIMIT ?
        ''', (f'%{phase}%', limit))
        
        rows = cursor.fetchall()
        results = []
        
        for row in rows:
            item = {
                'coach_id': row['coach_id'],
                'knowledge_type': row['knowledge_type'],
                'title': row['title'],
                'summary': row['knowledge_summary'],
                'key_elements': json.loads(row['key_elements']) if row['key_elements'] else [],
                'common_errors': json.loads(row['common_errors']) if row['common_errors'] else [],
                'correction_method': row['correction_method'],
                'issue_tags': json.loads(row['issue_tags']) if row['issue_tags'] else [],
                'phase': json.loads(row['phase']) if row['phase'] else [],
                'quality_grade': row['quality_grade']
            }
            
            # 如果指定了 NTRP 等级，过滤相关知识
            if ntrp_level:
                # 根据等级过滤（可以根据 coach_id 或 knowledge_type 过滤）
                # 这里简单返回所有，实际可以根据需要添加过滤逻辑
                pass
            
            results.append(item)
        
        return results
    
    def query_by_issue(self, issue_tags: List[str], ntrp_level: str = None, limit: int = 5) -> List[dict]:
        """
        根据问题标签查询知识库
        
        Args:
            issue_tags: 问题标签列表
            ntrp_level: NTRP 等级
            limit: 返回数量限制
        
        Returns:
            List[dict]: 知识库条目列表
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        results = []
        
        for tag in issue_tags:
            cursor.execute('''
                SELECT coach_id, knowledge_type, title, knowledge_summary,
                       common_errors, correction_method, issue_tags, phase
                FROM coach_knowledge
                WHERE issue_tags LIKE ?
                ORDER BY confidence DESC
                LIMIT ?
            ''', (f'%{tag}%', limit // len(issue_tags) if issue_tags else limit))
            
            rows = cursor.fetchall()
            for row in rows:
                item = {
                    'coach_id': row['coach_id'],
                    'knowledge_type': row['knowledge_type'],
                    'title': row['title'],
                    'summary': row['knowledge_summary'],
                    'common_errors': json.loads(row['common_errors']) if row['common_errors'] else [],
                    'correction_method': row['correction_method'],
                    'issue_tags': json.loads(row['issue_tags']) if row['issue_tags'] else [],
                    'phase': json.loads(row['phase']) if row['phase'] else []
                }
                
                # 去重
                if not any(r['title'] == item['title'] for r in results):
                    results.append(item)
        
        return results[:limit]
    
    def get_knowledge_for_analysis(self, phase_analysis: dict, ntrp_level: str) -> dict:
        """
        根据分析结果获取相关知识库内容
        
        Args:
            phase_analysis: 各阶段分析结果
            ntrp_level: NTRP 等级
        
        Returns:
            dict: 按阶段组织的知识库引用
        """
        knowledge_context = {}
        
        for phase_name, phase_data in phase_analysis.items():
            issues = phase_data.get('issues', [])
            score = phase_data.get('score', 0)
            
            # 只针对需要改进的阶段（分数低于 70）检索知识
            if score >= 70:
                continue
            
            # 检索该阶段的知识
            phase_knowledge = self.query_by_phase(phase_name, ntrp_level, limit=3)
            
            # 如果有具体问题标签，额外检索
            if issues:
                issue_knowledge = self.query_by_issue(issues, ntrp_level, limit=2)
                # 合并并去重
                existing_titles = {k['title'] for k in phase_knowledge}
                for item in issue_knowledge:
                    if item['title'] not in existing_titles:
                        phase_knowledge.append(item)
            
            if phase_knowledge:
                knowledge_context[phase_name] = {
                    'phase': phase_name,
                    'user_score': score,
                    'knowledge': phase_knowledge[:5]  # 最多返回 5 条
                }
        
        return {'knowledge': list(knowledge_context.values())}


# ═══════════════════════════════════════════════════════════════════
# 黄金标准对比
# ═══════════════════════════════════════════════════════════════════

class GoldStandardComparator:
    """黄金标准对比分析器"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
    
    def get_gold_standard(self, level: str) -> Optional[dict]:
        """
        获取指定等级的黄金标准
        
        Args:
            level: NTRP 等级
        
        Returns:
            dict: 黄金标准数据，不存在返回 None
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT level, description, standards_json, sample_count
            FROM level_gold_standards
            WHERE level = ?
        ''', (level,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            'level': row['level'],
            'description': row['description'],
            'standards': json.loads(row['standards_json']),
            'sample_count': row['sample_count']
        }
    
    def get_all_levels(self) -> List[str]:
        """获取所有可用的 NTRP 等级"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT level FROM level_gold_standards ORDER BY level')
        rows = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in rows]
    
    def compare_phase(self, phase_name: str, user_data: dict, standard_data: dict) -> dict:
        """
        对比单个阶段的用户表现与黄金标准
        
        Args:
            phase_name: 阶段名称
            user_data: 用户该阶段的表现数据
            standard_data: 黄金标准该阶段的要求
        
        Returns:
            dict: 对比结果
        """
        user_score = user_data.get('score', 0)
        user_observations = user_data.get('observations', [])
        user_issues = user_data.get('issues', [])
        
        comparison = {
            'phase': phase_name,
            'user_score': user_score,
            'standard_requirements': standard_data,
            'user_performance': user_observations,
            'gaps': [],
            'met_requirements': [],
            'priority': 'low'
        }
        
        # 根据分数判断整体状态
        if user_score >= 80:
            comparison['met_requirements'].append(f"{phase_name} 表现优秀，达到或超过标准")
            comparison['priority'] = 'low'
        elif user_score >= 60:
            comparison['gaps'].append(f"{phase_name} 基本达标，但有改进空间")
            comparison['priority'] = 'medium'
        elif user_score >= 40:
            comparison['gaps'].append(f"{phase_name} 需要重点改进")
            comparison['priority'] = 'high'
        else:
            comparison['gaps'].append(f"{phase_name} 严重不足，需优先改进")
            comparison['priority'] = 'critical'
        
        # 对比具体问题
        for issue in user_issues:
            if isinstance(issue, dict):
                issue_desc = issue.get('issue', str(issue))
            else:
                issue_desc = str(issue)
            
            comparison['gaps'].append(issue_desc)
        
        # 检查是否满足黄金标准的关键要求
        # （这里可以根据具体指标做更精细的对比）
        for key_req, req_value in standard_data.items():
            # 简单对比逻辑，实际可以根据具体指标优化
            if user_score < 60:
                comparison['gaps'].append(f"{key_req}: 未达到标准 ({req_value})")
        
        return comparison
    
    def compare_with_gold_standard(self, analysis_result: dict, target_level: str = None) -> dict:
        """
        将分析结果与黄金标准对比
        
        Args:
            analysis_result: Qwen-VL 分析结果
            target_level: 目标等级（可选，默认使用分析结果中的等级）
        
        Returns:
            dict: 完整对比结果
        """
        # 确定对比的目标等级
        if not target_level:
            target_level = analysis_result.get('ntrp_level', '3.0')
        
        # 获取黄金标准
        gold_standard = self.get_gold_standard(target_level)
        
        if not gold_standard:
            return {
                'error': f'NTRP {target_level} 的黄金标准不存在',
                'available_levels': self.get_all_levels()
            }
        
        comparison = {
            'target_level': target_level,
            'target_description': gold_standard['description'],
            'standards': gold_standard['standards'],
            'phase_comparisons': [],
            'overall_gap_score': 0,
            'priority_phases': []
        }
        
        phase_analysis = analysis_result.get('phase_analysis', {})
        standards = gold_standard.get('standards', {})
        
        total_score = 0
        phase_count = 0
        
        for phase_name, phase_data in phase_analysis.items():
            if phase_name not in standards:
                continue
            
            standard = standards[phase_name]
            phase_comparison = self.compare_phase(phase_name, phase_data, standard)
            
            comparison['phase_comparisons'].append(phase_comparison)
            total_score += phase_data.get('score', 0)
            phase_count += 1
            
            # 记录高优先级的阶段
            if phase_comparison['priority'] in ['critical', 'high']:
                comparison['priority_phases'].append({
                    'phase': phase_name,
                    'priority': phase_comparison['priority'],
                    'score': phase_data.get('score', 0)
                })
        
        # 计算整体差距分数（0-100，越小差距越大）
        if phase_count > 0:
            comparison['overall_gap_score'] = total_score / phase_count
        
        # 按优先级排序
        comparison['priority_phases'].sort(
            key=lambda x: (0 if x['priority'] == 'critical' else 1 if x['priority'] == 'high' else 2, x['score'])
        )
        
        return comparison


# ═══════════════════════════════════════════════════════════════════
# 整合分析
# ═══════════════════════════════════════════════════════════════════

class KnowledgeGoldAnalyzer:
    """知识库与黄金标准整合分析器"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.knowledge_retriever = KnowledgeRetriever(db_path)
        self.gold_comparator = GoldStandardComparator(db_path)
    
    def analyze(self, analysis_result: dict) -> dict:
        """
        完整的知识库检索与黄金标准对比分析
        
        Args:
            analysis_result: Qwen-VL 视觉分析结果
        
        Returns:
            dict: 完整分析结果（包含知识库引用和黄金标准对比）
        """
        ntrp_level = analysis_result.get('ntrp_level', '3.0')
        phase_analysis = analysis_result.get('phase_analysis', {})
        
        # 1. 知识库检索
        knowledge_context = self.knowledge_retriever.get_knowledge_for_analysis(
            phase_analysis, ntrp_level
        )
        
        # 2. 黄金标准对比
        gold_comparison = self.gold_comparator.compare_with_gold_standard(
            analysis_result, ntrp_level
        )
        
        # 3. 整合结果
        enhanced_result = analysis_result.copy()
        enhanced_result['knowledge_references'] = knowledge_context
        enhanced_result['gold_standard_comparison'] = gold_comparison
        
        # 4. 生成改进优先级建议
        enhanced_result['improvement_priorities'] = self._generate_priorities(
            phase_analysis, gold_comparison, knowledge_context
        )
        
        return enhanced_result
    
    def _generate_priorities(self, phase_analysis: dict, gold_comparison: dict, 
                            knowledge_context: dict) -> dict:
        """生成改进优先级建议"""
        
        priorities = {
            'critical': [],  # 必须优先改进
            'high': [],      # 重点改进
            'medium': [],    # 可以改进
            'low': []        # 保持即可
        }
        
        # 根据黄金标准对比结果确定优先级
        for phase_comp in gold_comparison.get('phase_comparisons', []):
            phase = phase_comp.get('phase')
            priority = phase_comp.get('priority', 'medium')
            score = phase_comp.get('user_score', 0)
            gaps = phase_comp.get('gaps', [])
            
            # 查找相关知识
            knowledge_items = []
            for kc in knowledge_context.get('knowledge', []):
                if kc.get('phase') == phase:
                    knowledge_items = kc.get('knowledge', [])[:2]
                    break
            
            priority_item = {
                'phase': phase,
                'score': score,
                'gaps': gaps[:3],
                'knowledge': knowledge_items
            }
            
            if priority == 'critical':
                priorities['critical'].append(priority_item)
            elif priority == 'high':
                priorities['high'].append(priority_item)
            elif priority == 'medium':
                priorities['medium'].append(priority_item)
            else:
                priorities['low'].append(priority_item)
        
        return priorities
    
    def generate_report(self, enhanced_result: dict) -> str:
        """生成完整分析报告"""
        
        lines = []
        lines.append("="*60)
        lines.append("🎾 网球发球技术分析报告")
        lines.append("="*60)
        lines.append("")
        
        # 基本信息
        analysis = enhanced_result
        lines.append(f"📊 技术等级：NTRP {analysis.get('ntrp_level', '未知')}")
        lines.append(f"📈 整体评分：{analysis.get('overall_score', 0)}/100")
        lines.append(f"🎯 置信度：{analysis.get('confidence', 0)*100:.0f}%")
        lines.append("")
        
        # 黄金标准对比
        gold_comp = analysis.get('gold_standard_comparison', {})
        if gold_comp and 'target_description' in gold_comp:
            lines.append("🏆 黄金标准对比")
            lines.append("-"*60)
            lines.append(f"目标等级：{gold_comp['target_description']}")
            lines.append(f"整体匹配度：{gold_comp.get('overall_gap_score', 0):.1f}/100")
            lines.append("")
            
            if gold_comp.get('priority_phases'):
                lines.append("🔴 优先改进阶段:")
                for item in gold_comp['priority_phases'][:3]:
                    lines.append(f"  • {item['phase'].upper()}: {item['score']}/100 ({item['priority']})")
                lines.append("")
        
        # 各阶段详细分析
        lines.append("📋 各阶段技术分析")
        lines.append("-"*60)
        
        phase_analysis = analysis.get('phase_analysis', {})
        for phase, data in phase_analysis.items():
            score = data.get('score', 0)
            status = "✅" if score >= 70 else "⚠️" if score >= 50 else "❌"
            lines.append(f"{status} {phase.upper()}: {score}/100")
            
            observations = data.get('observations', [])
            if observations:
                for obs in observations[:3]:
                    lines.append(f"   • {obs}")
        lines.append("")
        
        # 优点
        lines.append("✅ 优点")
        lines.append("-"*60)
        for strength in analysis.get('key_strengths', [])[:3]:
            lines.append(f"  • {strength}")
        lines.append("")
        
        # 需要改进的问题
        lines.append("⚠️ 需要改进的问题")
        lines.append("-"*60)
        
        key_issues = analysis.get('key_issues', [])
        for issue in key_issues[:5]:
            if isinstance(issue, dict):
                severity = issue.get('severity', 'medium')
                icon = "🔴" if severity == 'high' else "🟡" if severity == 'medium' else "🟢"
                lines.append(f"{icon} {issue.get('issue', '')}")
                if issue.get('coach_advice'):
                    lines.append(f"   建议：{issue['coach_advice']}")
            else:
                lines.append(f"  • {issue}")
        lines.append("")
        
        # 知识库参考
        knowledge_refs = analysis.get('knowledge_references', {}).get('knowledge', [])
        if knowledge_refs:
            lines.append("📚 教练知识库参考")
            lines.append("-"*60)
            
            for ref in knowledge_refs[:3]:
                phase = ref.get('phase', '')
                knowledge_items = ref.get('knowledge', [])
                
                if knowledge_items:
                    lines.append(f"{phase.upper()}:")
                    for item in knowledge_items[:2]:
                        if isinstance(item, dict):
                            title = item.get('title', '')
                            summary = item.get('summary', '')
                            lines.append(f"  • {title}")
                            lines.append(f"    {summary[:80]}...")
            lines.append("")
        
        # 训练计划
        lines.append("💡 训练计划")
        lines.append("-"*60)
        
        priorities = analysis.get('improvement_priorities', {})
        priority_order = ['critical', 'high', 'medium', 'low']
        
        step = 1
        for priority in priority_order:
            items = priorities.get(priority, [])
            for item in items[:2]:
                phase = item.get('phase', '').upper()
                gaps = item.get('gaps', [])
                
                lines.append(f"  {step}. 改进{phase}:")
                for gap in gaps[:2]:
                    lines.append(f"     - {gap}")
                step += 1
                
                if step > 10:
                    break
            
            if step > 10:
                break
        
        lines.append("")
        lines.append("="*60)
        
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════════════

def analyze_with_knowledge_and_gold(analysis_result: dict) -> dict:
    """
    便捷函数：对分析结果进行知识库检索和黄金标准对比
    
    Args:
        analysis_result: Qwen-VL 分析结果
    
    Returns:
        dict: 增强后的分析结果
    """
    analyzer = KnowledgeGoldAnalyzer()
    return analyzer.analyze(analysis_result)


def generate_complete_report(enhanced_result: dict) -> str:
    """
    便捷函数：生成完整分析报告
    
    Args:
        enhanced_result: 增强后的分析结果
    
    Returns:
        str: 格式化报告文本
    """
    analyzer = KnowledgeGoldAnalyzer()
    return analyzer.generate_report(enhanced_result)


# ═══════════════════════════════════════════════════════════════════
# 测试
# ═══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    # 测试数据
    test_analysis = {
        'ntrp_level': '3.0',
        'confidence': 0.75,
        'overall_score': 55,
        'phase_analysis': {
            'ready': {'score': 60, 'observations': ['站位约 45 度'], 'issues': []},
            'toss': {'score': 50, 'observations': ['抛球高度不稳定'], 'issues': ['toss_inconsistent']},
            'loading': {'score': 45, 'observations': ['膝盖弯曲不足'], 'issues': ['knee_bend_insufficient']},
            'contact': {'score': 55, 'observations': ['击球点准确'], 'issues': ['pronation_missing']},
            'follow': {'score': 60, 'observations': ['随挥完整'], 'issues': []}
        },
        'key_strengths': ['握拍正确', '击球点准确'],
        'key_issues': [
            {'issue': '膝盖蓄力不足', 'severity': 'high', 'phase': 'loading', 'coach_advice': '深蹲练习'},
            {'issue': '缺少旋内', 'severity': 'medium', 'phase': 'contact', 'coach_advice': '旋内练习'}
        ]
    }
    
    print("测试知识库检索与黄金标准对比...")
    print("="*60)
    
    analyzer = KnowledgeGoldAnalyzer()
    result = analyzer.analyze(test_analysis)
    
    print("\n✅ 分析完成")
    print(f"   知识库引用：{len(result.get('knowledge_references', {}).get('knowledge', []))} 条")
    
    gold_comp = result.get('gold_standard_comparison', {})
    if gold_comp:
        print(f"   黄金标准：NTRP {gold_comp.get('target_level', 'N/A')}")
        print(f"   对比阶段：{len(gold_comp.get('phase_comparisons', []))} 个")
    
    print("\n" + "="*60)
    print("完整报告:")
    print("="*60)
    
    report = analyzer.generate_report(result)
    print(report)
