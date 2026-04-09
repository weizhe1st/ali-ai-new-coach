#!/usr/bin/env python3
"""
初始化黄金标准数据库表
"""

import sqlite3
import json
import os

DB_PATH = '/home/admin/.openclaw/workspace/ai-coach/data/db/app.db'

# NTRP 黄金标准数据（基于杨超教练标准）
GOLD_STANDARDS = {
    '3.0': {
        'description': '基础级：掌握基本发球动作框架',
        'standards': {
            'ready': {
                'stance': '侧身 45 度对网，双脚与肩同宽',
                'grip': '大陆式握拍（虎口对准 2 号面）',
                'posture': '身体略微前倾，重心在前脚'
            },
            'toss': {
                'height': '一臂高度，稳定不晃动',
                'direction': '与发球方向一致',
                'position': '身体正前上方'
            },
            'loading': {
                'trophy_position': '肘部高于肩膀，球拍在背后最低点',
                'knee_bend': '膝盖弯曲，准备蹬地',
                'core_engagement': '核心收紧，准备转体'
            },
            'contact': {
                'arm_extension': '手臂完全伸展',
                'contact_point': '身体正前方一拍头距离',
                'racket_face': '拍面正对击球方向'
            },
            'follow': {
                'completion': '随挥完整，拍头越过身体中线',
                'balance': '落地平稳，重心转移完成'
            }
        }
    },
    '3.5': {
        'description': '进阶级：动作连贯，有一定控制力',
        'standards': {
            'ready': {
                'stance': '侧身 45 度，脚尖指向右网柱',
                'grip': '稳定大陆式握拍',
                'posture': '放松但专注'
            },
            'toss': {
                'height': '稳定在一臂高度',
                'direction': '与发球方向一致，无明显偏移',
                'release': '手指自然张开，手掌朝上送出'
            },
            'loading': {
                'trophy_position': '肘部明显高于肩膀',
                'knee_bend': '明显屈膝蓄力',
                'rhythm': '1-2-3 节奏清晰'
            },
            'contact': {
                'arm_extension': '手臂基本完全伸展',
                'contact_point': '身体正前方',
                'pronation': '开始使用前臂旋内'
            },
            'follow': {
                'completion': '随挥至非持拍手侧腰部',
                'balance': '身体完全转向球网'
            }
        }
    },
    '4.0': {
        'description': '中级：能控制旋转和成功率',
        'standards': {
            'ready': {
                'stance': '稳定侧身，准备充分',
                'grip': '大陆式握拍稳固',
                'mental': '专注，有明确战术意图'
            },
            'toss': {
                'height': '精准控制',
                'direction': '完全一致，落点稳定',
                'consistency': '多次发球抛球一致性好'
            },
            'loading': {
                'trophy_position': '标准奖杯位置',
                'knee_bend': '深度屈膝（约 120-130 度）',
                'leg_drive': '腿部开始发力'
            },
            'contact': {
                'arm_extension': '完全伸展',
                'contact_point': '精准控制',
                'spin_control': '能控制旋转方向和量',
                'first_serve': '一发成功率 65%+',
                'second_serve': '二发成功率 85%+'
            },
            'follow': {
                'completion': '完整随挥',
                'recovery': '快速回位准备下一拍'
            }
        }
    },
    '4.5': {
        'description': '中高级：动力链完整，旋转控制优秀',
        'standards': {
            'loading': {
                'trophy_position': '完美奖杯位置',
                'knee_bend': '深度蓄力',
                'hip_rotation': '髋部充分打开'
            },
            'contact': {
                'kinetic_chain': '腿 - 核心 - 手臂力量传递流畅',
                'spin': '上旋二发从 7 点向 1 点刷',
                'power': '力量充足且可控'
            }
        }
    },
    '5.0': {
        'description': '高级：完整动力链，职业级动作',
        'standards': {
            'loading': {
                'trophy_position': '完美',
                'knee_bend': '120-130 度',
                'leg_power': '腿部贡献 40% 力量',
                'core_power': '核心转体贡献 30% 力量'
            },
            'contact': {
                'arm_power': '手臂挥拍贡献 20% 力量',
                'wrist_power': '手腕旋内贡献 10% 力量',
                'timing': '时机完美',
                'consistency': '高度一致性'
            }
        }
    }
}


def init_gold_standards():
    """初始化黄金标准表"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS level_gold_standards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT UNIQUE NOT NULL,
            description TEXT,
            standards_json TEXT,
            sample_count INTEGER DEFAULT 0,
            reference_sample_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 插入数据
    for level, data in GOLD_STANDARDS.items():
        standards_json = json.dumps(data['standards'], ensure_ascii=False)
        
        cursor.execute('''
            INSERT OR REPLACE INTO level_gold_standards 
            (level, description, standards_json, sample_count)
            VALUES (?, ?, ?, ?)
        ''', (level, data['description'], standards_json, 0))
        
        print(f"✅ 已插入 NTRP {level} 黄金标准")
    
    conn.commit()
    
    # 验证
    cursor.execute('SELECT level, description FROM level_gold_standards ORDER BY level')
    rows = cursor.fetchall()
    
    print(f"\n{'='*60}")
    print("📊 黄金标准表已创建")
    print(f"{'='*60}")
    for row in rows:
        print(f"  NTRP {row[0]}: {row[1]}")
    
    conn.close()
    print(f"\n💾 数据库：{DB_PATH}")


if __name__ == '__main__':
    init_gold_standards()
