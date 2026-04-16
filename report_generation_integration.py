#!/usr/bin/env python3
"""
报告生成接入（最小报告结构）
功能：
1. 问题检索结果
2. 黄金标准对比结果
3. 优先改进项
4. 训练建议
5. 总结输出

输出结构：
{
 "summary": "...",
 "primary_issue": "...",
 "secondary_issue": "...",
 "matched_problem_pool": "...",
 "matched_standard_samples": ["..."],
 "phase_comparison": {
 "toss": "...",
 "loading": "...",
 "contact": "...",
 "follow": "..."
 },
 "priority_gaps": ["...", "..."],
 "training_advice": ["...", "...", "..."]
}
"""

import json
from typing import Dict, List, Optional
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════
# 辅助函数（小流量模式：区间 + 置信度）
# ═══════════════════════════════════════════════════════════════════

def get_ntrp_range(ntrp: str) -> str:
    """将单点 NTRP 转换为区间"""
    if ntrp == 'unknown' or not ntrp:
        return '待评估'
    
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


def get_confidence_info(sample: dict) -> dict:
    """获取置信度信息"""
    ntrp = sample.get('ntrp_level', 'unknown')
    category = sample.get('sample_category', 'unknown')
    quality_grade = sample.get('quality_grade', 'unknown')
    
    # 高置信度
    if ntrp in ['5.0', '5.0+'] and category == 'excellent_demo' and quality_grade == 'A':
        return {'level': '高', 'reasons': ['顶级水平样本', 'A 级质量']}
    
    if ntrp in ['2.5', '3.0', '3.5'] and category == 'typical_issue' and quality_grade == 'A':
        return {'level': '高', 'reasons': ['典型问题清晰', 'A 级质量']}
    
    # 中/低置信度
    reasons = []
    if ntrp in ['4.0', '4.5']:
        reasons.append('中等级别')
    if quality_grade == 'B':
        reasons.append('B 级质量')
    if category == 'boundary_case':
        reasons.append('边界案例')
    if ntrp == 'unknown' or not ntrp:
        reasons.append('NTRP 未知')
    
    if len(reasons) >= 2:
        return {'level': '低', 'reasons': reasons}
    
    if reasons:
        return {'level': '中', 'reasons': reasons}
    
    return {'level': '中', 'reasons': ['标准样本']}



PROBLEM_INDEX_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/problem_index.json'
SAMPLE_REGISTRY_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/sample_registry.json'
REPORTS_DIR = '/home/admin/.openclaw/workspace/ai-coach/reports'

# 问题到知识点的映射（真人教练风格）
ISSUE_TO_KNOWLEDGE = {
    "toss_inconsistent": {
        "phase": "toss",
        "knowledge_keys": [
            "抛球稳定性",
            "抛球高度控制",
            "抛球位置"
        ],
        "priority": "high",
        "coach_tips": [
            "抛球是发球的灵魂！球抛不稳，后面动作再好也白搭。",
            "手臂伸直，把球稳稳地送上去，不是扔上去。",
            "抛球位置要在身体正前方，偏了就会追着球打。"
        ],
        "training_advice": [
            "练习抛球稳定性：站在发球线，连续抛球 10 次，目标是每次高度都一致",
            "抛球手臂应充分伸直，想象把球轻轻放到天花板上的感觉",
            "抛球位置练习：在身体正前方放一个标记物，抛球时让球经过标记物上方"
        ]
    },
    "rotation_insufficient": {
        "phase": "loading",
        "knowledge_keys": [
            "转体充分性",
            "髋部旋转",
            "肩部旋转"
        ],
        "priority": "high",
        "coach_tips": [
            "转体不够，力量就少一半！侧身，把肩膀转过去，让对手看到你的后背。",
            "髋部先转，肩膀跟着转，最后手臂甩出去，这才是完整的动力链。",
            "很多人转体只转肩膀，髋部不动，那是假转体！"
        ],
        "training_advice": [
            "确保转体充分：发球前侧身站立，髋部和肩膀都要转动，让对手看到你的后背",
            "练习转体动作：不拿球拍，徒手做转体动作，感受髋部带动肩膀的感觉",
            "对着镜子练习：检查转体幅度，目标是能看到自己的后背"
        ]
    },
    "contact_point_late": {
        "phase": "contact",
        "knowledge_keys": [
            "击球时机",
            "击球点位置"
        ],
        "priority": "medium",
        "coach_tips": [
            "击球点晚了，球就会下网或者出界。要提前预判，主动迎球。",
            "击球点要在身体前方，不是在头顶，更不是在身后。",
            "抛球和挥拍要协调，球到了，拍子也要到，这才是时机。"
        ],
        "training_advice": [
            "调整击球时机：抛球后心里默数\"1-2-3\"，在第 3 拍击球，建立节奏感",
            "练习抛球与挥拍的协调性：先慢后快，确保球和拍子同时到达击球点",
            "使用标记物练习：在身体前方放一个标记物，击球时让球拍经过标记物"
        ]
    },
    "grip_incorrect": {
        "phase": "ready",
        "knowledge_keys": [
            "大陆式握拍",
            "握拍力度",
            "手腕灵活性"
        ],
        "priority": "high",
        "coach_tips": [
            "握拍是基础中的基础！用大陆式握拍，这是发球的标准握法。",
            "握拍力度要适中，太紧手腕转不动，太松控制不住。",
            "想象握锤子的力度，既能稳定控制，又不影响手腕转动。"
        ],
        "training_advice": [
            "检查握拍：食指根部关节对准拍柄右侧面，虎口形成 V 字形",
            "握拍力度练习：握拍后转动手腕，应该能灵活转动但不会松动",
            "转换练习：从正手握拍快速转换到大陆式握拍，建立肌肉记忆"
        ]
    },
    "stance_unstable": {
        "phase": "ready",
        "knowledge_keys": [
            "站位宽度",
            "身体角度",
            "重心位置"
        ],
        "priority": "medium",
        "coach_tips": [
            "站位是发球的根基！双脚与肩同宽，身体侧对球网约 45 度。",
            "重心稍前倾在脚掌，形成稳定的击球基础。",
            "站位太宽转不动，太窄站不稳，找到合适的宽度。"
        ],
        "training_advice": [
            "检查站位：双脚与肩同宽，身体侧对球网，重心前倾",
            "站位练习：在地面画线标记脚的位置，每次站到相同位置",
            "平衡练习：单脚站立 10 秒，增强平衡能力"
        ]
    },
    "swing_path_incomplete": {
        "phase": "loading",
        "knowledge_keys": [
            "C 形轨迹",
            "奖杯姿势",
            "挥拍节奏"
        ],
        "priority": "high",
        "coach_tips": [
            "挥拍轨迹呈 C 字形，从后下方到前上方，形成完整的弧线。",
            "奖杯姿势是挥拍的转折点，蓄力到释放的关键节点。",
            "挥拍要有节奏：慢 - 快 - 慢，后摆慢，向前快，随挥自然减速。"
        ],
        "training_advice": [
            "影子挥拍：不带球进行完整挥拍练习，每天 20-30 次",
            "慢动作练习：用慢动作感受 C 形轨迹，逐步加速到正常速度",
            "录像检查：录制自己的挥拍，检查是否呈 C 字形"
        ]
    },
    "pronation_late": {
        "phase": "contact",
        "knowledge_keys": [
            "旋内时机",
            "前臂旋转",
            "拍面控制"
        ],
        "priority": "high",
        "coach_tips": [
            "旋内是发球力量的关键技术！击球瞬间前臂向内旋转。",
            "旋内时机要准：太早没力量，太晚没控制，就在击球瞬间。",
            "想象用拍面刷球的感觉，从垂直地面转到向前。"
        ],
        "training_advice": [
            "无球旋内练习：徒手做旋内动作，感受前臂旋转",
            "抛球后旋内：抛球后只做旋内动作，不击球",
            "慢动作整合：慢动作发球，在击球瞬间刻意旋内"
        ]
    },
    "leg_drive_weak": {
        "phase": "loading",
        "knowledge_keys": [
            "腿部蹬地",
            "力量传递",
            "向上跳起"
        ],
        "priority": "high",
        "coach_tips": [
            "5.0 发球的核心：腿部蹬地的力量传递！",
            "蹬地应在抛球达到最高点前开始，在击球时达到最大伸展。",
            "从脚到手的完整动力链，腿部、躯干、肩部、手臂协调发力。"
        ],
        "training_advice": [
            "无球蹬地练习：徒手做蹬地动作，感受腿部发力",
            "抛球后蹬地：抛球后只做蹬地动作，不击球",
            "深蹲跳训练：每天 3 组，每组 15 次，增强腿部爆发力"
        ]
    }
}


PROBLEM_INDEX_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/problem_index.json'
SAMPLE_REGISTRY_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/sample_registry.json'
REPORTS_DIR = '/home/admin/.openclaw/workspace/ai-coach/reports'

# 问题到知识点的映射（真人教练风格）
ISSUE_TO_KNOWLEDGE = {
    "toss_inconsistent": {
        "phase": "toss",
        "knowledge_keys": [
            "抛球稳定性",
            "抛球高度控制",
            "抛球位置"
        ],
        "priority": "high",
        "coach_tips": [
            "抛球是发球的灵魂！球抛不稳，后面动作再好也白搭。",
            "手臂伸直，把球稳稳地送上去，不是扔上去。",
            "抛球位置要在身体正前方，偏了就会追着球打。"
        ],
        "training_advice": [
            "练习抛球稳定性：站在发球线，连续抛球 10 次，目标是每次高度都一致",
            "抛球手臂应充分伸直，想象把球轻轻放到天花板上的感觉",
            "抛球位置练习：在身体正前方放一个标记物，抛球时让球经过标记物上方"
        ]
    },
    "rotation_insufficient": {
        "phase": "loading",
        "knowledge_keys": [
            "转体充分性",
            "髋部旋转",
            "肩部旋转"
        ],
        "priority": "high",
        "coach_tips": [
            "转体不够，力量就少一半！侧身，把肩膀转过去，让对手看到你的后背。",
            "髋部先转，肩膀跟着转，最后手臂甩出去，这才是完整的动力链。",
            "很多人转体只转肩膀，髋部不动，那是假转体！"
        ],
        "training_advice": [
            "确保转体充分：发球前侧身站立，髋部和肩膀都要转动，让对手看到你的后背",
            "练习转体动作：不拿球拍，徒手做转体动作，感受髋部带动肩膀的感觉",
            "对着镜子练习：检查转体幅度，目标是能看到自己的后背"
        ]
    },
    "contact_point_late": {
        "phase": "contact",
        "knowledge_keys": [
            "击球时机",
            "击球点位置"
        ],
        "priority": "medium",
        "coach_tips": [
            "击球点晚了，球就会下网或者出界。要提前预判，主动迎球。",
            "击球点要在身体前方，不是在头顶，更不是在身后。",
            "抛球和挥拍要协调，球到了，拍子也要到，这才是时机。"
        ],
        "training_advice": [
            "调整击球时机：抛球后心里默数\"1-2-3\"，在第 3 拍击球，建立节奏感",
            "练习抛球与挥拍的协调性：先慢后快，确保球和拍子同时到达击球点",
            "使用标记物练习：在身体前方放一个标记物，击球时让球拍经过标记物"
        ]
    }
}


PROBLEM_INDEX_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/problem_index.json'
SAMPLE_REGISTRY_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/sample_registry.json'
REPORTS_DIR = '/home/admin/.openclaw/workspace/ai-coach/reports'

# 问题到知识点的映射（真人教练风格）
ISSUE_TO_KNOWLEDGE = {
    'toss_inconsistent': {
        'phase': 'toss',
        'knowledge_keys': ['抛球稳定性', '抛球高度控制', '抛球位置'],
        'priority': 'high',
        'coach_tips': [
            '抛球是发球的灵魂！球抛不稳，后面动作再好也白搭。',
            '手臂伸直，把球稳稳地送上去，不是扔上去。',
            '抛球位置要在身体正前方，偏了就会追着球打。'
        ],
        'training_advice': [
            '练习抛球稳定性：站在发球线，连续抛球 10 次，目标是每次高度都一致',
            '抛球手臂应充分伸直，想象把球轻轻放到天花板上的感觉',
            '抛球位置练习：在身体正前方放一个标记物，抛球时让球经过标记物上方'
        ]
    },
    'knee_bend_insufficient': {
        'phase': 'loading',
        'knowledge_keys': ['膝盖蓄力', '下肢发力', '屈膝角度'],
        'priority': 'high',
        'coach_tips': [
            '记住，发球的力量从地面开始！膝盖不弯曲，就像弹簧没有压紧，怎么可能弹得高？',
            '屈膝不是蹲下，而是蓄力！感受腿部肌肉的张力。',
            '很多人发球只用手臂，那是小孩子的打法。成年人要用全身发力！'
        ],
        'training_advice': [
            '加强膝盖蓄力训练：发球前刻意屈膝，目标角度 120-130 度，对着镜子检查',
            '利用下肢力量发力：想象腿部是弹簧，先压紧再释放，力量从地面传到手臂',
            '练习深蹲跳：每天 3 组，每组 15 次，增强腿部爆发力'
        ]
    },
    'rotation_insufficient': {
        'phase': 'loading',
        'knowledge_keys': ['转体充分性', '髋部旋转', '肩部旋转'],
        'priority': 'high',
        'coach_tips': [
            '转体不够，力量就少一半！侧身，把肩膀转过去，让对手看到你的后背。',
            '髋部先转，肩膀跟着转，最后手臂甩出去，这才是完整的动力链。',
            '很多人转体只转肩膀，髋部不动，那是假转体！'
        ],
        'training_advice': [
            '确保转体充分：发球前侧身站立，髋部和肩膀都要转动，让对手看到你的后背',
            '练习转体动作：不拿球拍，徒手做转体动作，感受髋部带动肩膀的感觉',
            '对着镜子练习：检查转体幅度，目标是能看到自己的后背'
        ]
    },
    'contact_point_late': {
        'phase': 'contact',
        'knowledge_keys': ['击球时机', '击球点位置'],
        'priority': 'medium',
        'coach_tips': [
            '击球点晚了，球就会下网或者出界。要提前预判，主动迎球。',
            '击球点要在身体前方，不是在头顶，更不是在身后。',
            '抛球和挥拍要协调，球到了，拍子也要到，这才是时机。'
        ],
        'training_advice': [
            '调整击球时机：抛球后心里默数"1-2-3"，在第 3 拍击球，建立节奏感',
            '练习抛球与挥拍的协调性：先慢后快，确保球和拍子同时到达击球点',
            '使用标记物练习：在身体前方放一个标记物，击球时让球拍经过标记物'
        ]
    },
}

# 黄金标准阶段要求
GOLDEN_STANDARDS = {
    'toss': {
        'name': '抛球阶段',
        'requirements': ['抛球手臂伸直', '抛球高度稳定', '抛球位置在身体正前方']
    },
    'loading': {
        'name': '蓄力阶段',
        'requirements': ['膝盖充分弯曲', '髋部充分旋转', '肩部充分转动']
    },
    'contact': {
        'name': '击球阶段',
        'requirements': ['击球点准确', '拍面控制良好', '手臂充分伸展']
    },
    'follow_through': {
        'name': '随挥阶段',
        'requirements': ['随挥动作完整', '随挥方向正确', '身体向前移动']
    }
}


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, index_path: str = PROBLEM_INDEX_PATH, 
                 registry_path: str = SAMPLE_REGISTRY_PATH):
        self.index_path = index_path
        self.registry_path = registry_path
        self._reload_data()
    
    def _reload_data(self):
        """重新加载数据（确保获取最新数据）"""
        # 加载索引
        with open(self.index_path, 'r', encoding='utf-8') as f:
            self.index = json.load(f)
        
        # 加载样本登记表
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            self.registry = json.load(f)
        
        # 构建 sample_id 到 sample 的映射
        self.sample_map = {s.get('sample_id'): s for s in self.registry}
        
        # 加载 analysis_results.json（本次分析结果）
        self.analysis_results = []
        analysis_results_path = os.path.join(os.path.dirname(self.index_path), 'analysis_results.json')
        if os.path.exists(analysis_results_path):
            try:
                with open(analysis_results_path, 'r', encoding='utf-8') as f:
                    self.analysis_results = json.load(f)
                print(f"✓ analysis_results.json 已加载 ({len(self.analysis_results)} 条记录)")
            except Exception as e:
                print(f"⚠ analysis_results.json 加载失败：{e}")
        
        # 提取标准示范样本
        self.standard_samples = [
            s for s in self.registry 
            if s.get('sample_category') == 'excellent_demo'
            and s.get('ntrp_level') in ['4.5', '5.0', '5.0+']
            and s.get('quality_grade') == 'A'
        ]
    
    def generate_report(self, user_sample_id: str, 
                       ntrp_level: Optional[str] = None,
                       shadow_mode: bool = False) -> Dict:
        """
        生成结构化报告（最小报告结构）
        
        Args:
            user_sample_id: 用户样本 ID
            ntrp_level: 用户 NTRP 等级（可选）
            shadow_mode: 是否影子模式（可选）
        
        Returns:
            结构化报告
        """
        report = {
            'report_version': 'v2_problem_pool_standard_compare',
            'shadow_mode': shadow_mode,
            'generated_at': datetime.now().isoformat(),
            'user_sample_id': user_sample_id,
            'summary': '',
            'primary_issue': None,
            'secondary_issue': None,
            'matched_problem_pool': None,
            'matched_standard_samples': [],
            'phase_comparison': {},
            'priority_gaps': [],
            'training_advice': [],
            'knowledge_keys': []
        }
        
        # 获取用户样本（优先从 analysis_results.json 读取本次分析结果）
        user_sample = None
        
        # 1. 先尝试从 analysis_results.json 读取
        for result in self.analysis_results:
            if result.get('task_id') == user_sample_id:
                user_sample = result
                print(f"✓ 从 analysis_results.json 读取到本次分析结果")
                break
        
        # 2. 如果没有，再从 sample_registry.json 读取
        if not user_sample:
            if user_sample_id not in self.sample_map:
                report['summary'] = f'未找到样本：{user_sample_id}'
                return report
            user_sample = self.sample_map[user_sample_id]
            print(f"✓ 从 sample_registry.json 读取到样本")
        
        # 1. 问题检索结果
        primary_issue = user_sample.get('primary_issue')
        secondary_issue = user_sample.get('secondary_issue')
        phase_weaknesses = user_sample.get('action_phase_weaknesses', [])
        
        report['primary_issue'] = primary_issue
        report['secondary_issue'] = secondary_issue
        
        # 匹配主问题池
        if primary_issue and primary_issue in ISSUE_TO_KNOWLEDGE:
            issue_info = ISSUE_TO_KNOWLEDGE[primary_issue]
            expected_phase = issue_info.get('phase')
            
            for pool_key, pool_data in self.index['problem_pools'].items():
                if pool_key == 'standard_demos':
                    continue
                if pool_data.get('phase') == expected_phase:
                    report['matched_problem_pool'] = pool_data.get('name')
                    break
            
            report['knowledge_keys'] = issue_info.get('knowledge_keys', [])
        
        # 2. 黄金标准对比结果
        # 选择标准样本
        golden_samples = self.standard_samples[:2]  # 默认选前 2 个
        if ntrp_level:
            # 可以尝试选择 NTRP 相近的标准样本
            pass
        
        # 构建标准样本信息，包含访问方式
        # 提高优秀示范门槛：只选择 5.0 级样本作为标准示范
        high_level_samples = [s for s in golden_samples if s.get('ntrp_level') in ['5.0', '5.0+']]
        if not high_level_samples:
            # 如果没有 5.0 级，使用 4.5 级但标注"良好示范"而非"标准示范"
            high_level_samples = golden_samples[:2]
        else:
            high_level_samples = high_level_samples[:2]
        
        standard_samples_info = []
        for s in high_level_samples:
            sample_info = {
                'sample_id': s.get('sample_id'),
                'ntrp_level': s.get('ntrp_level'),
                'tags': s.get('tags', []),
                'video_url': s.get('cos_url'),  # 如果有 COS URL
                'access_info': '',  # 访问方式说明
                'demo_type': '标准示范' if s.get('ntrp_level') in ['5.0', '5.0+'] else '良好示范'
            }
            
            # 根据 COS URL 是否存在，提供不同的访问方式
            if s.get('cos_url'):
                sample_info['access_info'] = '可直接访问视频链接'
            elif s.get('source_file_path'):
                sample_info['access_info'] = '视频文件已保存，请联系教练获取'
            else:
                sample_info['access_info'] = '请联系教练获取标准示范视频'
            
            standard_samples_info.append(sample_info)
        
        report['matched_standard_samples'] = standard_samples_info
        
        # 添加标准视频库访问说明
        report['standard_video_library_info'] = {
            'description': '标准示范视频库',
            'access_methods': [
                '联系教练获取视频链接',
                '访问训练平台查看标准视频库',
                '在钉钉/QQ 中回复"标准视频"获取访问方式'
            ],
            'note': '建议对照标准视频练习，效果更佳'
        }
        
        # 添加视频分类和样本状态信息
        report['video_category_info'] = {
            'user_video': {
                'category': user_sample.get('sample_category', 'unknown'),
                'cos_status': '✅ 已上传' if user_sample.get('cos_url') else '⏳ 待上传',
                'cos_url': user_sample.get('cos_url')
            },
            'standard_videos': [
                {
                    'sample_id': s.get('sample_id'),
                    'category': 'excellent_demo',
                    'cos_status': '✅ 已上传' if s.get('cos_url') else '⏳ 待上传',
                    'cos_url': s.get('cos_url')
                }
                for s in golden_samples[:2]
            ]
        }
        
        # 3. 阶段对比
        for phase in ['toss', 'loading', 'contact', 'follow_through']:
            phase_name = GOLDEN_STANDARDS.get(phase, {}).get('name', phase)
            has_issue = phase in phase_weaknesses
            
            report['phase_comparison'][phase] = {
                'name': phase_name,
                'status': '需要改进' if has_issue else '良好',
                'has_issue': has_issue,
                'golden_requirements': GOLDEN_STANDARDS.get(phase, {}).get('requirements', [])
            }
        
        # 4. 优先改进项
        if primary_issue:
            report['priority_gaps'].append(f'优先解决：{primary_issue}')
        
        for phase in phase_weaknesses[:2]:
            phase_name = GOLDEN_STANDARDS.get(phase, {}).get('name', phase)
            report['priority_gaps'].append(f'改进 {phase_name} 阶段')
        
        # 5. 训练建议
        if primary_issue and primary_issue in ISSUE_TO_KNOWLEDGE:
            report['training_advice'] = ISSUE_TO_KNOWLEDGE[primary_issue].get('training_advice', [])
        
        # 生成总结（小流量模式：区间 + 置信度）
        ntrp = user_sample.get('ntrp_level', 'unknown')
        ntrp_range = get_ntrp_range(ntrp)
        confidence = get_confidence_info(user_sample)
        
        # 根据置信度调整话术
        if confidence['level'] == '高':
            range_text = f'NTRP 水平{ntrp_range}级'
            confidence_text = f'（置信度：高）'
        elif confidence['level'] == '中':
            range_text = f'NTRP 水平约{ntrp_range}级'
            confidence_text = f'（置信度：中，{",".join(confidence["reasons"][:2])}）'
        else:
            range_text = f'NTRP 水平可能在{ntrp_range}级范围'
            confidence_text = f'（置信度：低，建议人工复核）'

        if primary_issue:
            impact = ISSUE_TO_KNOWLEDGE.get(primary_issue, {}).get('priority', 'medium')
            # 加入教练风格的总结
            coach_tone = ISSUE_TO_KNOWLEDGE.get(primary_issue, {}).get('coach_tips', [])
            if coach_tone:
                coach_tip = coach_tone[0]  # 取第一条教练提示
                # 使用区间评估，避免过硬结论
                report['summary'] = (
                    f'发球分析：{coach_tip} 主要问题为 {primary_issue}，'
                    f'优先级 {impact}。{range_text}{confidence_text}。'
                    f'建议优先改进 {len(phase_weaknesses)} 个阶段，'
                    f'参考 {len(golden_samples)} 个标准示范样本进行练习。'
                )
            else:
                report['summary'] = (
                    f'发球分析：主要问题为 {primary_issue}，'
                    f'优先级 {impact}。{range_text}{confidence_text}。'
                    f'建议优先改进 {len(phase_weaknesses)} 个阶段，'
                    f'参考 {len(golden_samples)} 个标准示范样本进行练习。'
                )
        elif phase_weaknesses:
            report['summary'] = (
                f'{range_text}{confidence_text}。发现 {len(phase_weaknesses)} 个阶段需要改进，'
                f'建议参考标准示范样本进行针对性练习。'
            )
            # 即使没有 primary_issue，也提供通用建议
            if not report['training_advice']:
                report['training_advice'] = [
                    '建议放慢动作速度，专注于动作规范性',
                    '对照标准示范视频，找出动作差异',
                    '分解练习各个阶段，逐步改进'
                ]
        else:
            report['summary'] = f'{range_text}{confidence_text}。动作基本规范，继续保持。'
            # 提供保持性建议
            if not report['training_advice']:
                report['training_advice'] = [
                    '继续保持当前的规范动作',
                    '可以挑战更高难度的发球练习',
                    '定期对比标准示范，保持动作质量'
                ]
        
        return report
    
    def generate_report_for_user(self, user_name: str, 
                                 user_sample_id: str,
                                 ntrp_level: Optional[str] = None) -> str:
        """
        生成用户可读的报告文本
        
        Args:
            user_name: 用户姓名
            user_sample_id: 用户样本 ID
            ntrp_level: 用户 NTRP 等级
        
        Returns:
            用户可读的报告文本
        """
        report = self.generate_report(user_sample_id, ntrp_level)
        
        lines = []
        lines.append("="*60)
        lines.append(f"🎾 {user_name} 的发球分析报告")
        lines.append("="*60)
        lines.append("")
        lines.append(f"📊 {report['summary']}")
        lines.append("")
        
        if report['primary_issue']:
            lines.append("🔍 主要问题:")
            lines.append(f"   - {report['primary_issue']}")
            if report['secondary_issue']:
                lines.append(f"   - {report['secondary_issue']} (次要)")
            lines.append("")
        
        if report['matched_problem_pool']:
            lines.append(f"📦 匹配问题库：{report['matched_problem_pool']}")
            lines.append("")
        
        if report['matched_standard_samples']:
            lines.append("⭐ 参考标准样本:")
            for i, sample in enumerate(report['matched_standard_samples'], 1):
                lines.append(f"   {i}. {sample['sample_id']} (NTRP {sample['ntrp_level']})")
            lines.append("")
        
        if report['phase_comparison']:
            lines.append("📈 阶段对比:")
            for phase, data in report['phase_comparison'].items():
                status = '⚠️  需改进' if data['has_issue'] else '✅ 良好'
                lines.append(f"   {data['name']}: {status}")
            lines.append("")
        
        if report['priority_gaps']:
            lines.append("🎯 优先改进:")
            for gap in report['priority_gaps']:
                lines.append(f"   - {gap}")
            lines.append("")
        
        if report['training_advice']:
            lines.append("💡 训练建议:")
            for i, advice in enumerate(report['training_advice'], 1):
                lines.append(f"   {i}. {advice}")
            lines.append("")
        
        lines.append("="*60)
        
        return "\n".join(lines)
    
    def save_report(self, report: Dict, output_path: Optional[str] = None) -> str:
        """
        保存报告到文件
        
        Args:
            report: 报告字典
            output_path: 输出路径（可选）
        
        Returns:
            实际保存路径
        """
        if not output_path:
            sample_id = report.get('user_sample_id', 'unknown')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"{REPORTS_DIR}/analysis_{sample_id}_{timestamp}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return output_path


def main():
    print("="*60)
    print("📝 报告生成接入测试（最小报告结构）")
    print("="*60)
    print()
    
    # 创建报告生成器
    generator = ReportGenerator()
    
    print(f"📋 样本总数：{len(generator.registry)}")
    print(f"⭐ 标准示范样本：{len(generator.standard_samples)} 个")
    print()
    
    # 测试用例
    test_cases = [
        {
            'name': '测试 1: 抛球问题样本报告',
            'sample_id': 'batch001_video001',
            'ntrp_level': '2.5',
        },
        {
            'name': '测试 2: 蓄力问题样本报告',
            'sample_id': 'batch001_video004',
            'ntrp_level': '3.0',
        },
    ]
    
    for test_case in test_cases:
        print("="*60)
        print(f"🧪 {test_case['name']}")
        print("="*60)
        print()
        
        # 生成结构化报告
        report = generator.generate_report(
            test_case['sample_id'],
            test_case['ntrp_level']
        )
        
        print("📋 结构化报告:")
        print(f"   Summary: {report['summary'][:80]}...")
        print(f"   Primary Issue: {report['primary_issue']}")
        print(f"   Secondary Issue: {report['secondary_issue']}")
        print(f"   Matched Pool: {report['matched_problem_pool']}")
        print(f"   Standard Samples: {len(report['matched_standard_samples'])} 个")
        print(f"   Phase Comparison: {len(report['phase_comparison'])} 个阶段")
        print(f"   Priority Gaps: {len(report['priority_gaps'])} 个")
        print(f"   Training Advice: {len(report['training_advice'])} 条")
        print()
        
        # 生成用户可读报告
        user_report = generator.generate_report_for_user(
            "测试用户",
            test_case['sample_id'],
            test_case['ntrp_level']
        )
        
        print("📄 用户可读报告:")
        print(user_report)
        print()
        
        # 保存报告
        report_path = generator.save_report(report)
        print(f"💾 结构化报告已保存到：{report_path}")
        print()
    
    print("="*60)
    print("✅ 报告生成接入测试完成！")
    print("="*60)
    print()
    print("完整流程:")
    print("   1. 问题检索 ✅")
    print("   2. 黄金标准对比 ✅")
    print("   3. 报告生成 ✅")
    print()
    print("下一步:")
    print("   1. 接入实际用户分析流程")
    print("   2. 优化报告文案和展示")
    print()


if __name__ == '__main__':
    main()
