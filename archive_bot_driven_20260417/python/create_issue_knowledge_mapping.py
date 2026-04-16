#!/usr/bin/env python3
"""
从杨超知识库创建 ISSUE_TO_KNOWLEDGE 映射
"""

import json
from datetime import datetime

# 加载知识库
with open('yangchao_coach/knowledge_base/yangchao_knowledge_v2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

items = data.get('knowledge_items', [])
print(f"加载知识库：{len(items)}条")

# 创建问题类型到知识点的映射
ISSUE_TO_KNOWLEDGE = {}

# 抛球问题
toss_items = [item for item in items if any(kw in item.get('title', '') for kw in ['抛球', 'toss'])]
if toss_items:
    ISSUE_TO_KNOWLEDGE['toss_inconsistent'] = {
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
    }

# 蓄力问题
loading_items = [item for item in items if any(kw in item.get('title', '') for kw in ['蓄力', '膝盖', '屈膝'])]
if loading_items:
    ISSUE_TO_KNOWLEDGE['knee_bend_insufficient'] = {
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
    }

# 转体问题
rotation_items = [item for item in items if any(kw in item.get('title', '') for kw in ['转体', '转髋'])]
if rotation_items:
    ISSUE_TO_KNOWLEDGE['rotation_insufficient'] = {
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
    }

# 击球点问题
contact_items = [item for item in items if any(kw in item.get('title', '') for kw in ['击球点', '击球时机'])]
if contact_items:
    ISSUE_TO_KNOWLEDGE['contact_point_late'] = {
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
    }

# 随挥问题
follow_items = [item for item in items if any(kw in item.get('title', '') for kw in ['随挥', '随球'])]
if follow_items:
    ISSUE_TO_KNOWLEDGE['follow_through_insufficient'] = {
        'phase': 'follow_through',
        'knowledge_keys': ['随挥完整性', '随挥方向'],
        'priority': 'medium',
        'coach_tips': [
            '随挥不完整，力量就浪费了！让球拍自然地挥到身体左侧。',
            '随挥是动作的结束，也是下一个动作的准备。',
            '很多人击球后就停了，那是半途而废。要把动作做完！'
        ],
        'training_advice': [
            '完整随挥练习：发球后让球拍自然地挥到身体左侧，保持结束姿势 2 秒',
            '检查随挥方向：随挥应该指向目标方向，不是向下或向上',
            '录像检查：录制自己的发球，检查随挥是否完整'
        ]
    }

# 保存 ISSUE_TO_KNOWLEDGE
with open('data/issue_to_knowledge_enhanced.json', 'w', encoding='utf-8') as f:
    json.dump(ISSUE_TO_KNOWLEDGE, f, ensure_ascii=False, indent=2)

print(f"✅ 创建 ISSUE_TO_KNOWLEDGE 映射：{len(ISSUE_TO_KNOWLEDGE)}个问题类型")
print()

# 显示映射
for issue, knowledge in ISSUE_TO_KNOWLEDGE.items():
    print(f"{issue}:")
    print(f"  阶段：{knowledge['phase']}")
    print(f"  知识点：{knowledge['knowledge_keys']}")
    print(f"  优先级：{knowledge['priority']}")
    print(f"  教练提示：{len(knowledge['coach_tips'])}条")
    print(f"  训练建议：{len(knowledge['training_advice'])}条")
    print()

print("="*70)
print("✅ 知识点映射创建完成！")
print("="*70)
