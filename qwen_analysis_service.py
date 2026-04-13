#!/usr/bin/env python3
"""
网球 AI 教练系统 - Qwen 模型分析服务
基于 complete_analysis_service.py 修改，适配 Qwen API
保留知识库检索、MediaPipe 集成等核心功能
"""

import os
import sys
import json
import time
import sqlite3
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# 导入现有模块
from core import (
    PROMPT_VERSION, KNOWLEDGE_BASE_VERSION, MODEL_NAME,
    SYSTEM_PROMPT, check_input_quality, validate_response
)

# ==================== 配置 ====================
DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY')
if not DASHSCOPE_API_KEY:
    raise ValueError(
        "DASHSCOPE_API_KEY environment variable is required. "
        "Please set it before running this script."
    )

DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'xiaolongxia_learning.db')
API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
MODEL_NAME = "qwen-max"  # 可选：qwen-max, qwen-plus, qwen-turbo

# ==================== 知识库检索 ====================

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query_unified_knowledge(level, phase, issue_tags):
    """查询统一知识库 - 使用 coach_knowledge 表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 关键词映射表
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
            
            # 扩展搜索关键词
            search_terms = [tag_str]
            for key, synonyms in keyword_mapping.items():
                if key in tag_str:
                    search_terms.extend(synonyms)
            
            # 去重并限制数量
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
                    if row['common_errors']:
                        content += f"\n常见错误：{row['common_errors']}"
                    if row['correction_method']:
                        content += f"\n纠正方法：{row['correction_method']}"
                    
                    results.append({
                        'coach': row['coach_name'],
                        'phase': row['knowledge_type'],
                        'content': content,
                        'quality': 'A'
                    })
        
        conn.close()
        # 去重
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


def query_similar_cases_from_db(level, limit=3):
    """从数据库查询相似案例"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, level, description, reference_sample_id, sample_count, standards_json
            FROM level_gold_standards
            WHERE level = ?
            ORDER BY sample_count DESC
            LIMIT ?
        ''', (level, limit))
        
        results = []
        for row in cursor.fetchall():
            try:
                standards = json.loads(row['standards_json']) if row['standards_json'] else {}
            except:
                standards = {}
            
            results.append({
                'id': row['id'],
                'level': row['level'],
                'score': 75,
                'description': row['description'],
                'standards': standards
            })
        
        conn.close()
        return results
    except Exception as e:
        print(f"  [案例库] 查询失败：{e}")
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
    
    similar_cases = query_similar_cases_from_db(ntrp_level, limit=2)
    
    return {
        'knowledge': knowledge_context,
        'similar_cases': similar_cases
    }


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
    
    raise ValueError(f"无法解析 JSON，已尝试 5 种策略。原始内容前 500 字：{content[:500]}")


def call_qwen_api(video_url: str, user_text: str = "", system_prompt: str = SYSTEM_PROMPT, max_retries: int = 3) -> dict:
    """
    调用 Qwen API 进行视频分析
    
    Args:
        video_url: 视频 URL（公开可访问的 HTTP/HTTPS 链接）
        user_text: 用户自定义提示
        system_prompt: 系统提示词
        max_retries: 最大重试次数
    
    Returns:
        dict: 解析后的 JSON 结果
    """
    last_error = None
    
    for attempt in range(max_retries + 1):
        if attempt > 0:
            wait = 5 * attempt
            print(f"[重试] 第{attempt}次重试，等待{wait}秒... (上次错误：{last_error})")
            time.sleep(wait)
        
        try:
            headers = {
                "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [
                        {"type": "video_url", "video_url": {"url": video_url}},
                        {"type": "text", "text": f"""请严格按照三步分析法分析这段网球发球视频：

第一步（逐帧观察）：逐阶段描述你看到的具体动作，每个阶段覆盖所有锚点，看不清的写"不可见"。
第二步（标准对照）：将观察结果与三位教练标准对照，明确每个锚点的达标/不达标情况。
第三步（输出 JSON）：基于前两步推导，填写最终 JSON，不得跳过前两步直接给出结论。

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
                raise RuntimeError(f"Qwen API 调用失败，已重试{max_retries}次。最后错误：{last_error}")
            continue
    
    raise RuntimeError("不应到达此处")


# ==================== 主分析函数 ====================

def analyze_video_with_qwen(
    video_url: str,
    video_path: str = None,
    user_text: str = "",
    use_knowledge: bool = True
) -> Dict[str, Any]:
    """
    使用 Qwen 分析网球发球视频
    
    Args:
        video_url: 视频 URL（公开可访问）
        video_path: 本地视频路径（用于质量检查）
        user_text: 用户自定义提示
        use_knowledge: 是否使用知识库检索
    
    Returns:
        dict: 分析结果
    """
    print("\n" + "=" * 60)
    print("🎾 网球 AI 教练系统 - Qwen 模型分析")
    print("=" * 60)
    print(f"视频 URL: {video_url[:80]}...")
    print(f"使用知识库：{'是' if use_knowledge else '否'}")
    print(f"模型：{MODEL_NAME}")
    print()
    
    # 步骤 1: 视频质量检查
    if video_path and os.path.exists(video_path):
        print("[步骤 1] 检查视频质量...")
        quality_ok, quality_info = check_input_quality(video_path)
        if not quality_ok:
            return {
                "status": "error",
                "error": "视频质量检查失败",
                "details": quality_info
            }
        print(f"  ✅ 视频质量合格：{quality_info}")
    else:
        print("[步骤 1] 跳过视频质量检查（无本地文件）")
    
    # 步骤 2: 知识库检索（可选）
    if use_knowledge:
        print("\n[步骤 2] 检索知识库...")
        # 这里可以先做一个初步分析来获取 ntrp_level，然后再检索
        # 简化版：先不检索，等有了初步结果再检索
        print("  ℹ️  知识库检索将在获得初步分析结果后进行")
    else:
        print("\n[步骤 2] 跳过知识库检索")
    
    # 步骤 3: 调用 Qwen API
    print("\n[步骤 3] 调用 Qwen API 进行视频分析...")
    start_time = time.time()
    
    try:
        result = call_qwen_api(video_url, user_text)
        elapsed = time.time() - start_time
        print(f"  ✅ Qwen 分析完成，耗时：{elapsed:.1f}秒")
        
        # 步骤 4: 验证结果
        print("\n[步骤 4] 验证分析结果...")
        is_valid, errors, validated_result = validate_response(result)
        if is_valid:
            print("  ✅ 结果验证通过")
        else:
            print(f"  ⚠️  验证警告：{errors}")
        
        # 步骤 5: 知识库增强（可选）
        if use_knowledge and 'phase_analysis' in result:
            print("\n[步骤 5] 知识库增强...")
            ntrp_level = result.get('ntrp_level', '3.0')
            knowledge_context = build_knowledge_context(result['phase_analysis'], ntrp_level)
            
            if knowledge_context['knowledge'] or knowledge_context['similar_cases']:
                print(f"  ✅ 检索到 {len(knowledge_context['knowledge'])} 条相关知识")
                print(f"  ✅ 检索到 {len(knowledge_context['similar_cases'])} 个相似案例")
                result['knowledge_context'] = knowledge_context
            else:
                print("  ℹ️  未检索到相关知识")
        
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
    print("\n🎾 网球 AI 教练系统 - Qwen 分析服务")
    print(f"测试时间：{datetime.now()}")
    print()
    
    # 示例视频 URL（需要替换为实际视频）
    test_video_url = "https://example.com/tennis_serve.mp4"
    
    print("⚠️  请提供一个公开可访问的视频 URL 进行测试")
    print()
    print("使用方法：")
    print("  1. 将视频上传到 COS/OSS，获取公开 URL")
    print("  2. 修改下面的 test_video_url 变量")
    print("  3. 运行：python3 qwen_analysis_service.py")
    print()
    
    # 取消注释并修改 URL 后运行
    # result = analyze_video_with_qwen(test_video_url, use_knowledge=True)
    # print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
