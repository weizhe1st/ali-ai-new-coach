#!/usr/bin/env python3
"""
简化版 OpenClaw 集成 - 直接调用 Qwen API 分析视频
不依赖 openai 库，使用 requests 直接调用
"""

import os
import sys
import json
import time
import base64
import requests
from datetime import datetime

# 配置
VIDEO_INPUT_DIR = '/home/admin/.openclaw/workspace/media/inbound'
DASHSCOPE_API_KEY = 'sk-88532d38dbe04d3a9b73c921ce25794c'
API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
MODEL_NAME = "qwen-vl-max"

# 知识库路径
KNOWLEDGE_FILE = '/home/admin/.openclaw/workspace/ai-coach/fused_knowledge/fusion_report_v3.json'

# 已处理的视频
processed_videos = set()


def load_knowledge():
    """加载教练知识库"""
    if not os.path.exists(KNOWLEDGE_FILE):
        return None
    
    with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_video(video_path):
    """使用 Qwen-VL 分析视频"""
    
    print(f"\n📹 分析视频：{os.path.basename(video_path)}")
    
    # 加载知识库
    knowledge = load_knowledge()
    if knowledge:
        print(f"  ✅ 知识库：{knowledge['summary']['total_knowledge_items']} 条")
    
    # 读取视频
    with open(video_path, 'rb') as f:
        video_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    # 系统提示词（三步分析法 + 通俗化要求）
    system_prompt = """你是一个专业的网球发球分析系统。

【要求】
1. 使用"三步分析法"：逐帧观察 → 标准对照 → 输出 JSON
2. 对照 169 条教练知识（杨超 71 条、灵犀 41 条、Yellow 57 条）
3. 输出通俗易懂的分析报告，避免专业术语

【输出格式】
必须是合法 JSON：
{
  "ntrp_level": "3.0|3.5|4.0|4.5|5.0",
  "confidence": 0.0-1.0,
  "overall_score": 0-100,
  "key_issues": [{"phase": "...", "severity": "critical|major|minor", "description": "..."}],
  "highlights": ["..."],
  "training_priorities": ["..."],
  "detailed_analysis": {"ready": "...", "toss": "...", "loading": "...", "contact": "...", "follow": "..."},
  "coach_references": {"杨超": [...], "灵犀": [...], "Yellow": [...]}
}
"""
    
    # 调用 API
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "video_url", "video_url": {"url": f"data:video/mp4;base64,{video_base64}"}},
                    {"type": "text", "text": "请分析这个网球发球视频，输出 JSON 格式结果。"}
                ]
            }
        ],
        "max_tokens": 3000
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # 解析 JSON
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            analysis = json.loads(content[json_start:json_end])
        else:
            analysis = {"raw_analysis": content}
        
        print(f"  ✅ 分析完成：NTRP {analysis.get('ntrp_level')}")
        return analysis
        
    except Exception as e:
        print(f"  ❌ 分析失败：{e}")
        return None


def generate_report(analysis):
    """生成通俗化报告"""
    
    if not analysis:
        return "❌ 分析失败"
    
    ntrp_level = analysis.get('ntrp_level', '?')
    confidence = analysis.get('confidence', 0) * 100
    overall_score = analysis.get('overall_score', 0)
    
    # 术语转换
    def simplify(text):
        replacements = {
            '奖杯位置': '手肘抬高姿势',
            '肘部未高于肩膀': '手肘抬得不够高',
            '旋内': '前臂旋转',
            '动力链': '力量传递',
            '随挥': '收尾动作',
        }
        for tech, simple in replacements.items():
            text = text.replace(tech, simple)
        return text
    
    # 构建报告
    lines = []
    lines.append(f"🎾 网球发球分析报告")
    lines.append(f"")
    lines.append(f"📊 综合评估")
    lines.append(f"  NTRP 等级：{ntrp_level}")
    lines.append(f"  置信度：{confidence:.0f}%")
    lines.append(f"  综合评分：{overall_score}/100")
    lines.append(f"")
    
    # 亮点
    highlights = analysis.get('highlights', [])
    if highlights:
        lines.append(f"✅ 做得好的地方")
        for h in highlights:
            lines.append(f"  ✓ {simplify(h)}")
        lines.append(f"")
    
    # 问题
    key_issues = analysis.get('key_issues', [])
    if key_issues:
        lines.append(f"⚠️ 需要改进")
        severity_map = {'critical': '🔴', 'major': '🟠', 'minor': '🟡'}
        for issue in key_issues:
            emoji = severity_map.get(issue.get('severity', 'minor'), '⚪')
            phase = issue.get('phase', '')
            desc = simplify(issue.get('description', ''))
            lines.append(f"  {emoji} [{phase}] {desc}")
        lines.append(f"")
    
    # 训练建议
    priorities = analysis.get('training_priorities', [])
    if priorities:
        lines.append(f"💪 训练建议")
        for i, p in enumerate(priorities[:3], 1):
            lines.append(f"  {i}. {simplify(p)}")
        lines.append(f"")
    
    # 教练知识点
    coach_refs = analysis.get('coach_references', {})
    if coach_refs:
        lines.append(f"📚 教练知识点")
        for coach, refs in coach_refs.items():
            if refs:
                lines.append(f"  👤 {coach}: {len(refs)} 条")
        lines.append(f"")
    
    return '\n'.join(lines)


def check_new_video():
    """检查新视频"""
    
    if not os.path.exists(VIDEO_INPUT_DIR):
        return None
    
    video_files = []
    for f in os.listdir(VIDEO_INPUT_DIR):
        if f.endswith(('.mp4', '.MP4', '.MOV', '.avi')):
            full_path = os.path.join(VIDEO_INPUT_DIR, f)
            mtime = os.path.getmtime(full_path)
            # 只处理最近 5 分钟的文件
            if time.time() - mtime < 300:
                if full_path not in processed_videos:
                    video_files.append((full_path, mtime))
    
    if not video_files:
        return None
    
    video_files.sort(key=lambda x: x[1], reverse=True)
    return video_files[0][0]


def main():
    """主循环"""
    
    print("\n" + "="*60)
    print("🎾 网球 AI 教练 - 简化集成服务")
    print("="*60)
    print(f"监听目录：{VIDEO_INPUT_DIR}")
    print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print(f"\n✅ 服务已启动，等待视频上传...\n")
    print(f"提示：在钉钉中发送网球视频，系统将自动分析\n")
    
    check_interval = 3  # 每 3 秒检查一次
    
    while True:
        try:
            video_path = check_new_video()
            
            if video_path:
                print(f"\n📹 检测到新视频：{os.path.basename(video_path)}")
                
                # 分析视频
                analysis = analyze_video(video_path)
                
                if analysis:
                    # 生成报告
                    report = generate_report(analysis)
                    
                    # 显示报告
                    print(f"\n{'='*60}")
                    print(report)
                    print(f"{'='*60}\n")
                    
                    # 保存报告
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    report_file = f'/home/admin/.openclaw/workspace/ai-coach/reports/report_{timestamp}.txt'
                    os.makedirs(os.path.dirname(report_file), exist_ok=True)
                    with open(report_file, 'w', encoding='utf-8') as f:
                        f.write(report)
                    print(f"💾 报告已保存：{report_file}")
                    
                    # 标记为已处理
                    processed_videos.add(video_path)
                
                # 清理临时文件（可选）
                # os.remove(video_path)
            
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  服务已停止")
            break
        except Exception as e:
            print(f"\n❌ 错误：{e}")
            import traceback
            traceback.print_exc()
            time.sleep(check_interval)


if __name__ == '__main__':
    main()
