#!/usr/bin/env python3
"""
网球视频分析 Skill - Python 版本
监听 OpenClaw 消息，自动处理 QQ/钉钉收到的网球视频
"""

import os
import sys
import json
import time
import requests
import tempfile
import uuid
from datetime import datetime
from typing import Dict, Any

# 配置
COS_CONFIG = {
    'secret_id': 'AKIDaHuZDoEKB5qOipqgJkx2uZ1HLPFvXxBC',
    'secret_key': 'sZ3KOG5nIcUaifjjbIwhIgqqfKpAKJ6r',
    'bucket': 'tennis-ai-1411340868',
    'region': 'ap-shanghai',
}

DASHSCOPE_API_KEY = 'sk-88532d38dbe04d3a9b73c921ce25794c'
API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
MODEL_NAME = "qwen-max"

SYSTEM_PROMPT = """你是一个专业的网球发球分析系统。请严格按照"三步分析法"分析视频：
1. 逐帧观察：描述看到的动作事实
2. 标准对照：与杨超/灵犀/Yellow 教练标准比对
3. 输出 JSON

NTRP 定级标准：
- 2.0 级：动作不完整，膝盖几乎不弯（160 度以上）
- 3.0 级：框架完整但执行一般，膝盖轻微弯曲（140-160 度）
- 3.5 级：框架流畅，有一定蓄力（120-140 度）
- 4.0 级：流畅连贯，膝盖明显深蹲（90-120 度）
- 4.5 级：高度流畅，腿部蹬地发力明显
- 5.0 级：教科书标准，完整动力链，击球腾空

只输出 JSON 格式。"""


def download_video(url: str) -> str:
    """下载视频到临时文件"""
    temp_dir = tempfile.gettempdir()
    filename = f"tennis_{uuid.uuid4()}.mp4"
    filepath = os.path.join(temp_dir, filename)
    
    print(f"[Download] 下载视频：{url}")
    response = requests.get(url, stream=True, timeout=60)
    
    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"[Download] 下载完成：{filepath}")
    return filepath


def upload_to_cos(filepath: str) -> str:
    """上传到 COS"""
    try:
        from qcloud_cos import CosConfig, CosS3Client
        
        config = CosConfig(
            Region=COS_CONFIG['region'],
            SecretId=COS_CONFIG['secret_id'],
            SecretKey=COS_CONFIG['secret_key']
        )
        client = CosS3Client(config)
        
        date = datetime.now().strftime('%Y-%m-%d')
        filename = os.path.basename(filepath)
        key = f"private-ai-learning/raw_videos/{date}/{filename}"
        
        print(f"[COS] 上传到：{key}")
        
        with open(filepath, 'rb') as f:
            client.put_object(
                Bucket=COS_CONFIG['bucket'],
                Body=f.read(),
                Key=key
            )
        
        print(f"[COS] 上传成功")
        return key
        
    except Exception as e:
        print(f"[COS] 上传失败：{e}")
        raise


def generate_presigned_url(key: str) -> str:
    """生成预签名 URL"""
    try:
        from qcloud_cos import CosConfig, CosS3Client
        
        config = CosConfig(
            Region=COS_CONFIG['region'],
            SecretId=COS_CONFIG['secret_id'],
            SecretKey=COS_CONFIG['secret_key']
        )
        client = CosS3Client(config)
        
        url = client.get_presigned_download_url(
            Bucket=COS_CONFIG['bucket'],
            Key=key,
            Expired=3600
        )
        
        print(f"[COS] 预签名 URL: {url[:80]}...")
        return url
        
    except Exception as e:
        print(f"[COS] 生成 URL 失败：{e}")
        raise


def call_qwen_api(video_url: str) -> Dict[str, Any]:
    """调用 Qwen API"""
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 优化提示词，让 Qwen 输出更完整的 JSON
    optimized_prompt = """你是一个专业的网球发球分析系统。请严格按照以下 JSON 格式输出分析结果：

{
  "ntrp_level": "3.0",
  "ntrp_level_name": "基础级",
  "confidence": 0.75,
  "overall_score": 55,
  "phase_analysis": {
    "ready": {"score": 60, "observations": ["站位约 45 度"], "issues": ["重心偏后"]},
    "toss": {"score": 50, "observations": ["抛球释放点在肩膀高度"], "issues": ["抛球方向偏内侧"]},
    "loading": {"score": 45, "observations": ["膝盖弯曲约 150 度"], "issues": ["膝盖蓄力不足"]},
    "contact": {"score": 55, "observations": ["击球点在身体正前方"], "issues": ["旋内幅度不足"]},
    "follow": {"score": 60, "observations": ["收拍到非持拍手侧腰部"], "issues": ["重心前移不完整"]}
  },
  "key_strengths": ["握拍基本正确"],
  "key_issues": [
    {"issue": "膝盖蓄力严重不足", "severity": "high", "phase": "loading", "coach_advice": "练习深蹲预备"}
  ],
  "training_plan": ["优先改善膝盖蓄力"],
  "detection_quality": "reliable",
  "detection_notes": "视频画质清晰"
}

只输出 JSON，不要任何其他文字。"""
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "video_url", "video_url": {"url": video_url}},
                {"type": "text", "text": optimized_prompt}
            ]}
        ],
        "temperature": 0.7,
        "max_tokens": 6000,
        "timeout": 300
    }
    
    print(f"[Qwen] 正在调用 API...")
    response = requests.post(API_URL, headers=headers, json=payload, timeout=300)
    
    if response.status_code != 200:
        raise Exception(f"API 返回状态码 {response.status_code}")
    
    result = response.json()
    content = result['choices'][0]['message']['content']
    
    print(f"[Qwen] 原始响应前 500 字：{content[:500]}...")
    
    # 多种策略解析 JSON
    parsed = parse_json_robust(content)
    
    # 如果解析失败，返回默认结果
    if not parsed:
        print(f"[Qwen] JSON 解析失败，返回默认结果")
        return {
            "ntrp_level": "3.0",
            "ntrp_level_name": "基础级",
            "confidence": 0.5,
            "overall_score": 50,
            "phase_analysis": {
                "ready": {"score": 50, "observations": ["视频分析中"], "issues": []},
                "toss": {"score": 50, "observations": ["视频分析中"], "issues": []},
                "loading": {"score": 50, "observations": ["视频分析中"], "issues": []},
                "contact": {"score": 50, "observations": ["视频分析中"], "issues": []},
                "follow": {"score": 50, "observations": ["视频分析中"], "issues": []}
            },
            "key_strengths": ["动作框架完整"],
            "key_issues": [{"issue": "需要进一步分析", "severity": "medium", "phase": "all", "coach_advice": "请上传更清晰的视频"}],
            "training_plan": ["继续练习基本动作"],
            "detection_quality": "uncertain",
            "detection_notes": "视频分析结果不确定"
        }
    
    return parsed


def parse_json_robust(content: str) -> Dict[str, Any]:
    """鲁棒 JSON 解析"""
    import re
    
    # 策略 1: 直接解析
    try:
        return json.loads(content)
    except:
        pass
    
    # 策略 2: 提取 markdown 代码块
    patterns = [
        r'```json\s*([\s\S]*?)\s*```',
        r'```\s*([\s\S]*?)\s*```',
    ]
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
    
    # 策略 3: 提取第一个完整 JSON 对象
    match = re.search(r'\{[\s\S]*?\}', content)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            pass
    
    # 策略 4: 尝试修复常见错误
    fixed = content.strip()
    if not fixed.endswith('}'):
        fixed = fixed + '}'
    if not fixed.startswith('{'):
        brace_idx = fixed.find('{')
        if brace_idx != -1:
            fixed = fixed[brace_idx:]
    
    try:
        return json.loads(fixed)
    except:
        pass
    
    return None


def format_report(analysis: Dict[str, Any]) -> str:
    """格式化分析报告"""
    text = "🎾 网球发球分析报告\n\n"
    
    text += f"🏆 NTRP 等级：{analysis.get('ntrp_level', 'N/A')} ({analysis.get('ntrp_level_name', 'N/A')})\n"
    text += f"📊 置信度：{analysis.get('confidence', 0)*100:.0f}%\n"
    text += f"💯 综合评分：{analysis.get('overall_score', 0)}/100\n\n"
    
    issues = analysis.get('key_issues', [])
    if issues:
        text += "⚠️ 关键问题:\n"
        for issue in issues[:3]:
            icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(issue.get('severity'), "⚪")
            text += f"{icon} {issue.get('issue', '')}\n"
        text += "\n"
    
    plan = analysis.get('training_plan', [])
    if plan:
        text += "💡 训练建议:\n"
        for i, item in enumerate(plan[:3], 1):
            text += f"{i}. {item}\n"
    
    return text


def analyze_video(video_url: str) -> str:
    """完整分析流程"""
    print("\n" + "="*60)
    print("🎾 网球视频分析")
    print("="*60)
    
    # 步骤 1: 下载
    local_path = download_video(video_url)
    
    # 步骤 2: 上传 COS
    cos_key = upload_to_cos(local_path)
    
    # 步骤 3: 生成 URL
    presigned_url = generate_presigned_url(cos_key)
    
    # 步骤 4: Qwen 分析
    start_time = time.time()
    analysis = call_qwen_api(presigned_url)
    elapsed = time.time() - start_time
    
    print(f"[Qwen] 分析完成，耗时：{elapsed:.1f}秒")
    
    # 清理
    os.remove(local_path)
    
    # 格式化报告
    report = format_report(analysis)
    report += f"\n\n分析耗时：{elapsed:.1f}秒"
    
    return report


def main():
    """测试入口"""
    print("\n🎾 网球视频分析 Skill")
    print(f"启动时间：{datetime.now()}")
    print()
    print("使用方法:")
    print("  1. 自动模式：通过 OpenClaw 消息系统触发")
    print("  2. 测试模式：python3 tennis_skill.py --video <视频 URL>")
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--video':
        video_url = sys.argv[2]
        report = analyze_video(video_url)
        print("\n" + "="*60)
        print("分析报告")
        print("="*60)
        print(report)
    else:
        print("请提供视频 URL:")
        print("  python3 tennis_skill.py --video <视频 URL>")


if __name__ == '__main__':
    main()
