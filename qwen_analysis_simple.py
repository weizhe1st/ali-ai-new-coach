#!/usr/bin/env python3
"""
网球 AI 教练系统 - Qwen 分析服务（简化版）
不依赖 cv2/mediapipe，专注于 Qwen API 调用和知识库检索
"""

import os
import sys
import json
import time
import sqlite3
import requests
from datetime import datetime
from typing import Dict, Any, List

# ==================== 配置 ====================
DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY')
if not DASHSCOPE_API_KEY:
    raise ValueError(
        "DASHSCOPE_API_KEY environment variable is required. "
        "Please set it before running this script."
    )

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'xiaolongxia_learning.db')
API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
MODEL_NAME = "qwen-max"

# ==================== 系统提示词（完整三步分析法） ====================
SYSTEM_PROMPT = """你是一个专业的网球发球分析系统。你将收到一段网球发球视频，请严格按照"三步分析法"完成分析。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
三步分析法（必须按顺序执行，不得跳步）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【第一步：逐帧观察】
先不评分，只描述你看到的动作事实。每个阶段至少描述 3 个具体的肢体状态。
描述要求：用数字和方向词，不用模糊形容词。
  ✓ 正确："肘部与肩膀齐平，约低于标准位置 15 度"
  ✗ 错误："肘部位置还可以"

【第二步：标准对照】
将观察结果与三位教练标准逐条比对，列出达标项和不达标项。

【第三步：输出 JSON】
基于前两步的推导，填写最终 JSON。禁止跳过前两步直接填写。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
三位教练的评估标准
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 杨超教练（71 条）— 分级标准权威

NTRP 等级核心定义：
- 3.0 级：四大核心——稳定抛球、大陆式握拍、完整挥拍轨迹、合理击球点。有形但执行质量一般。
- 4.0 级：能控制旋转方向和旋转量，一发成功率 65%+，二发成功率 85%+。上旋二发从球的 7 点向 1 点方向刷。
- 5.0 级：完整腿部动力链。力量占比：腿部 40%、核心转体 30%、手臂挥拍 20%、手腕旋内 10%。膝盖弯曲约 120-130 度。

关键技术标准：
- 大陆式握拍：虎口对准 2 号面
- 抛球：正前上方、一臂高度、落点稳定、与发球方向一致
- 奖杯位置：球拍背后最低点，肘部必须高于肩膀
- 击球点：身体正前方一拍头距离，手臂完全伸展
- 旋内：前臂从外旋到内旋，收拍到非持拍手侧腰部
- 挥拍轨迹：倒 C 形 → 背挠 → 加速 → 旋内
- 节奏：1-2-3 数拍法（1=准备，2=蓄力奖杯，3=击球）

### 赵凌曦教练（41 条）— 节奏与纠错

- 发球节奏 1-2-3：拉拍停顿 → 蓄力奖杯 → 加速击球，停顿感是关键
- 顶髋是重心后摆后的自然前倾，不是主动后仰
- 架拍僵硬的根源是手腕手肘过紧，不是手臂力量不足
- 抛球方向必须与发球方向一致，不能偏向身体内侧
- 旋内击球的本质：拍头低于球，从下向上包裹，而非甩拍

### Yellow 教练（57 条）— 动作细节

- 站位：侧身 45 度对网，脚尖指向右网柱（右手持拍）
- 握拍：检查点是小指侧手掌边缘贴在拍柄第 2 斜面
- 抛球手：释放球时手指自然张开，手掌朝上送出
- 蓄力：非持拍手落下时，持拍手同步上提，形成镜像对称
- 击球：击球瞬间屏住呼吸，身体停止转动，只有手臂旋内
- 随挥：收拍后持拍手自然垂落到非持拍手侧，不要刻意制动

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
五阶段观察锚点（第一步必须覆盖以下要点）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

每个阶段在 observations 中必须描述以下锚点，看不清的写"不可见"，不可省略：

【准备阶段 ready】
1. 站位角度（相对于网的身体朝向，约几度侧身）
2. 持拍手握拍位置（虎口大致在第几斜面）
3. 非持拍手托球高度（腰部/胸部/肩部）
4. 重心分布（前脚/后脚偏重，还是均匀）

【抛球阶段 toss】
1. 抛球手释放点（低于/齐平/高于肩膀）
2. 球的飞行方向（正前上方/偏左/偏右/偏后）
3. 持拍手同步动作（是否同步向后拉拍）
4. 抛球一致性（多次发球的话，落点是否稳定）

【蓄力阶段 loading】
1. 膝盖弯曲程度（估计角度：170 度=几乎不弯，120 度=明显深蹲，90 度=深蹲）
2. 肘部高度（低于/齐平/高于肩膀，估计差距）
3. 身体侧转角度（肩膀转向角度，约几度）
4. 停顿感（是否有明显的奖杯停顿，还是一气呵成没有停顿）

【击球阶段 contact】
1. 击球点位置（身体正前方/侧方，估计距离）
2. 手臂伸展程度（完全伸直/微弯/明显弯曲）
3. 是否有旋内动作（拍头是否从外向内甩出）
4. 击球时身体状态（是否腾空，重心是否前移）

【随挥阶段 follow】
1. 收拍方向（非持拍手侧腰部/身体前方/其他）
2. 重心转移（是否完成前移，落脚在哪）
3. 身体最终朝向（是否转向目标方向）
4. 整体放松程度（动作是否自然收尾还是强行制动）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NTRP 定级标准（严格执行，膝盖是分水岭）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2.0 级（入门）：动作不完整，无背挠，抛球不稳，膝盖几乎不弯（160 度以上）
3.0 级（基础）：框架完整但执行质量一般，膝盖轻微弯曲（140-160 度），旋内不充分
3.5 级（进阶）：框架流畅，有一定蓄力（120-140 度），旋内存在但不完整
4.0 级（熟练）：流畅连贯，膝盖明显深蹲（90-120 度），转肩明显，旋内完整
4.5 级（高级）：高度流畅，腿部蹬地发力明显，旋转意图清晰
5.0 级（精通）：教科书标准，完整动力链，击球腾空，极为放松
5.0+ 级（专业）：职业水平，完美动力链，击球点极高

评分红线：
1. 看"质"不看"形"：有框架 ≠ 执行到位
2. 短板决定上限：最弱的阶段决定整体等级上限
3. 看不清就写"不可见"，不猜测，不编造
4. 业余选手容易高估，4.5+ 要非常谨慎
5. 多次发球取平均水平，不取最好的一次

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
输出格式（只输出 JSON，不含任何其他内容和 markdown 标记）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{
  "serves_detected": [
    {"index": 1, "time_range": "0s-8s", "quality_note": "动作完整"}
  ],
  "ntrp_level": "3.0",
  "ntrp_level_name": "基础级",
  "confidence": 0.75,
  "overall_score": 55,
  "serves_observed": 2,
  "phase_analysis": {
    "ready": {
      "score": 60,
      "observations": ["站位约 45 度侧身对网"],
      "anchors": {"stance_angle": "约 45 度"},
      "issues": ["重心偏后"],
      "coach_reference": "Yellow 标准：脚尖指向右网柱"
    },
    "toss": {
      "score": 50,
      "observations": ["抛球释放点在肩膀高度"],
      "anchors": {"release_height": "肩膀高度"},
      "issues": ["抛球方向偏内侧"],
      "coach_reference": "赵凌曦标准：抛球方向必须与发球方向一致"
    },
    "loading": {
      "score": 45,
      "observations": ["膝盖弯曲约 150 度"],
      "anchors": {"knee_angle": "约 150 度"},
      "issues": ["膝盖蓄力严重不足"],
      "coach_reference": "杨超标准：膝盖弯曲 120-130 度"
    },
    "contact": {
      "score": 55,
      "observations": ["击球点在身体正前方"],
      "anchors": {"contact_position": "正前方"},
      "issues": ["旋内幅度不足"],
      "coach_reference": "赵凌曦标准：旋内是拍头低于球从下向上包裹"
    },
    "follow": {
      "score": 60,
      "observations": ["收拍到非持拍手侧腰部"],
      "anchors": {"racket_finish": "非持拍手侧腰部"},
      "issues": ["重心前移不完整"],
      "coach_reference": "Yellow 标准：收拍后持拍手自然垂落"
    }
  },
  "consistency_note": "两次发球中，第二次抛球明显偏右",
  "key_strengths": ["握拍基本正确"],
  "key_issues": [
    {"issue": "膝盖蓄力严重不足（约 150 度）", "severity": "high", "phase": "loading", "coach_advice": "每次发球前有意识地做深蹲预备"}
  ],
  "training_plan": ["优先改善膝盖蓄力：对镜子练习奖杯姿势"],
  "detection_quality": "reliable",
  "detection_notes": "视频画质清晰，全身可见",
  "level_reasoning": "膝盖弯曲约 150 度，蓄力明显不足，这是 3.0 级的典型特征"
}"""


# ==================== 知识库检索 ====================

def query_unified_knowledge(level, phase, issue_tags):
    """查询统一知识库"""
    try:
        if not os.path.exists(DB_PATH):
            print(f"  ℹ️  数据库不存在：{DB_PATH}")
            return []
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        keyword_mapping = {
            '膝盖蓄力': ['膝盖', '蓄力', '弯曲', '重心', 'loading', '奖杯'],
            '抛球': ['抛球', 'toss', '释放', '落点'],
            '奖杯姿势': ['奖杯', 'trophy', '肘部', '肩膀', 'loading'],
            '旋内': ['旋内', 'pron', '包裹', '刷球', 'contact'],
            '随挥': ['随挥', 'follow', '收拍', 'follow-through'],
            '击球点': ['击球点', 'contact', '高度', '最高点'],
            '握拍': ['握拍', 'grip', '大陆式'],
            '重心': ['重心', '平衡', '转移', '蹬地']
        }
        
        results = []
        for tag in issue_tags:
            tag_str = tag if isinstance(tag, str) else str(tag)
            search_terms = [tag_str]
            for key, synonyms in keyword_mapping.items():
                if key in tag_str:
                    search_terms.extend(synonyms)
            search_terms = list(set(search_terms))[:5]
            
            for term in search_terms:
                cursor.execute('''
                    SELECT coach_name, knowledge_type, title, summary, 
                           key_elements, common_errors, correction_method
                    FROM coach_knowledge
                    WHERE summary LIKE ? OR title LIKE ? OR key_elements LIKE ?
                    ORDER BY quality_grade DESC, confidence DESC
                    LIMIT 2
                ''', (f'%{term}%', f'%{term}%', f'%{term}%'))
                
                for row in cursor.fetchall():
                    content = f"{row['title']}：{row['summary']}"
                    if row['key_elements']:
                        content += f"\n关键要素：{row['key_elements']}"
                    if row['correction_method']:
                        content += f"\n纠正方法：{row['correction_method']}"
                    
                    results.append({
                        'coach': row['coach_name'],
                        'phase': row['knowledge_type'],
                        'content': content,
                        'quality': 'A'
                    })
        
        conn.close()
        seen = set()
        unique_results = []
        for r in results:
            key = (r['coach'], r['content'][:50])
            if key not in seen:
                seen.add(key)
                unique_results.append(r)
        
        return unique_results[:10]
    except Exception as e:
        print(f"  [知识库] 查询失败：{e}")
        return []


def build_knowledge_context(phase_analysis, ntrp_level):
    """构建知识库上下文"""
    knowledge_context = []
    
    for phase_name, phase_data in phase_analysis.items():
        if isinstance(phase_data, dict):
            issues = phase_data.get('issues', [])
            if issues:
                issue_tags = [iss.get('issue') if isinstance(iss, dict) else str(iss) for iss in issues]
                knowledge_results = query_unified_knowledge(ntrp_level, phase_name, issue_tags)
                if knowledge_results:
                    knowledge_context.append({
                        'phase': phase_name,
                        'knowledge': knowledge_results
                    })
    
    return {'knowledge': knowledge_context}


# ==================== Qwen API 调用 ====================

def _parse_json_robust(content: str) -> dict:
    """鲁棒 JSON 解析（5 种策略）"""
    import re
    content = content.strip()
    
    # 策略 1: 直接解析
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # 策略 2: 提取 markdown 代码块
    code_block_patterns = [
        r'```json\s*(\{[\s\S]*?\})\s*```',
        r'```\s*(\{[\s\S]*?\})\s*```',
    ]
    for pattern in code_block_patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
    
    # 策略 3: 提取第一个完整 JSON 对象
    brace_start = content.find('{')
    if brace_start != -1:
        depth = 0
        in_string = False
        escape_next = False
        for i, ch in enumerate(content[brace_start:], start=brace_start):
            if escape_next:
                escape_next = False
                continue
            if ch == '\\' and in_string:
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if not in_string:
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(content[brace_start:i+1])
                        except json.JSONDecodeError:
                            pass
                        break
    
    # 策略 4: 截断修复
    truncated_patterns = [
        (r'("\w+":\s*"[^"]*)(?:[^"}]*)$', r'\1"}'),
        (r'("\w+":\s*\d+)(?:[^\d}]*)$', r'\1}'),
    ]
    for pattern, replacement in truncated_patterns:
        fixed = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        if fixed != content:
            try:
                return json.loads(fixed)
            except json.JSONDecodeError:
                pass
    
    # 策略 5: 宽松提取
    json_like_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_like_pattern, content, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    raise ValueError(f"无法解析 JSON。原始内容前 500 字：{content[:500]}")


def call_qwen_api(video_url: str, user_text: str = "", max_retries: int = 3) -> dict:
    """调用 Qwen API 进行视频分析"""
    last_error = None
    
    for attempt in range(max_retries + 1):
        if attempt > 0:
            wait = 5 * attempt
            print(f"[重试] 第{attempt}次重试，等待{wait}秒...")
            time.sleep(wait)
        
        try:
            headers = {
                "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": [
                        {"type": "video_url", "video_url": {"url": video_url}},
                        {"type": "text", "text": f"""请严格按照三步分析法分析这段网球发球视频：

第一步（逐帧观察）：逐阶段描述你看到的具体动作，每个阶段覆盖所有锚点。
第二步（标准对照）：将观察结果与三位教练标准对照。
第三步（输出 JSON）：基于前两步推导，填写最终 JSON。

{user_text or ''}

只输出 JSON，不含任何其他内容。"""}
                    ]}
                ],
                "temperature": 1,
                "max_tokens": 6000,
                "timeout": 300
            }
            
            print(f"[Qwen] 正在调用 API...")
            response = requests.post(API_URL, headers=headers, json=payload, timeout=300)
            
            if response.status_code != 200:
                raise Exception(f"API 返回状态码 {response.status_code}: {response.text[:500]}")
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            print(f"[Qwen] API 调用成功，正在解析 JSON...")
            return _parse_json_robust(content)
                
        except ValueError:
            raise
        except Exception as e:
            last_error = str(e)
            if attempt == max_retries:
                raise RuntimeError(f"Qwen API 调用失败。最后错误：{last_error}")
            continue
    
    raise RuntimeError("不应到达此处")


# ==================== 主分析函数 ====================

def analyze_video_with_qwen(video_url: str, user_text: str = "", use_knowledge: bool = True) -> Dict[str, Any]:
    """使用 Qwen 分析网球发球视频"""
    print("\n" + "=" * 60)
    print("🎾 网球 AI 教练系统 - Qwen 模型分析")
    print("=" * 60)
    print(f"视频 URL: {video_url[:80]}...")
    print(f"使用知识库：{'是' if use_knowledge else '否'}")
    print(f"模型：{MODEL_NAME}")
    print()
    
    print("[步骤 1] 调用 Qwen API 进行视频分析...")
    start_time = time.time()
    
    try:
        result = call_qwen_api(video_url, user_text)
        elapsed = time.time() - start_time
        print(f"  ✅ Qwen 分析完成，耗时：{elapsed:.1f}秒")
        
        # 知识库增强
        if use_knowledge and 'phase_analysis' in result:
            print("\n[步骤 2] 知识库增强...")
            ntrp_level = result.get('ntrp_level', '3.0')
            knowledge_context = build_knowledge_context(result['phase_analysis'], ntrp_level)
            
            if knowledge_context['knowledge']:
                total_items = sum(len(k['knowledge']) for k in knowledge_context['knowledge'])
                print(f"  ✅ 检索到 {total_items} 条相关知识")
                result['knowledge_context'] = knowledge_context
            else:
                print("  ℹ️  未检索到相关知识（数据库可能为空）")
        
        return {
            "status": "success",
            "result": result,
            "model": MODEL_NAME,
            "analysis_time": elapsed
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"  ❌ 分析失败：{e}")
        return {
            "status": "error",
            "error": str(e),
            "model": MODEL_NAME,
            "analysis_time": elapsed
        }


# ==================== 测试入口 ====================

def main():
    """测试函数"""
    print("\n🎾 网球 AI 教练系统 - Qwen 分析服务（简化版）")
    print(f"测试时间：{datetime.now()}")
    print()
    print("✅ 配置检查:")
    print(f"  - API Key: {DASHSCOPE_API_KEY[:15]}...")
    print(f"  - 模型：{MODEL_NAME}")
    print(f"  - 数据库：{DB_PATH}")
    print()
    
    # 测试文本对话
    print("=" * 60)
    print("测试：Qwen 文本对话（无需视频）")
    print("=" * 60)
    
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "你是一个专业的网球教练。"},
            {"role": "user", "content": "你好，请介绍一下网球发球的 3 个关键要点。"}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        result = response.json()
        
        if response.status_code == 200:
            content = result['choices'][0]['message']['content']
            print(f"✅ API 调用成功！\n")
            print(f"Qwen 回答:\n{content}")
        else:
            print(f"❌ API 调用失败：{response.status_code}")
            print(f"错误：{json.dumps(result, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ 错误：{e}")
    
    print("\n" + "=" * 60)
    print("下一步：视频分析测试")
    print("=" * 60)
    print()
    print("使用方法：")
    print("  1. 准备一个公开可访问的网球发球视频 URL")
    print("  2. 修改下面的 test_video_url 变量")
    print("  3. 取消注释最后一行代码")
    print("  4. 运行：python3 qwen_analysis_simple.py")
    print()
    
    # 示例：
    # test_video_url = "https://your-cos-url.com/tennis_serve.mp4"
    # result = analyze_video_with_qwen(test_video_url, use_knowledge=True)
    # print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
