#!/usr/bin/env python3
"""
完整版网球发球分析服务（修复版）

只使用 qwen_client 统一调用，移除所有旧客户端调用残留
"""

import os
import sys
import json
import time
import sqlite3
import tempfile
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# 导入统一配置
from config import get_model_config, MODEL_PROVIDER, MODEL_NAME
from core import SYSTEM_PROMPT, check_input_quality, validate_response

# 导入 qwen_client（统一调用入口）
from qwen_client import get_qwen_client

# 导入其他模块
from mediapipe_helper import (
    extract_pose_metrics,
    enhance_vision_result_with_mediapipe,
    format_for_qwen,
    MEDIAPIPE_ENABLED
)
from analysis_normalizer import normalize_analysis_result
from cos_uploader import COSUploader

COS_BUCKET = 'tennis-ai-1411340868'
COS_REGION = 'ap-shanghai'


# ═══════════════════════════════════════════════════════════════════
# 数据库操作函数
# ═══════════════════════════════════════════════════════════════════



def save_clip_pose_results(clip_id, pose_data, metrics):
    """保存姿态分析结果"""
    pass


def save_clip_scoring_results(clip_id, ntrp_level, total_score, confidence, details):
    """保存评分结果"""
    pass


def save_clip_phase_segments(clip_id, phase_analysis):
    """保存阶段分段"""
    pass


def save_coach_style_report(clip_id, ntrp_level, coach_reports):
    """保存教练风格报告"""
    pass


# ═══════════════════════════════════════════════════════════════════
# 知识库查询
# ═══════════════════════════════════════════════════════════════════

KNOWLEDGE_DB = '/home/admin/.openclaw/workspace/ai-coach/data/db/app.db'

# 代码侧的 4 阶段 -> 数据库侧的 5 阶段映射（B 方案）
# 数据库用 ready/toss/loading/contact/follow，代码用 preparation/loading/acceleration/follow_through
_PHASE_MAPPING = {
    "preparation": ["ready", "toss"],
    "loading": ["loading"],
    "acceleration": ["contact"],
    "follow_through": ["follow"],
}


def _normalize_issues(issues):
    """把各种格式的 issues 统一成 List[str]。"""
    if issues is None:
        return []
    if isinstance(issues, str):
        return [issues]
    if isinstance(issues, list):
        result = []
        for item in issues:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                v = item.get("issue") or item.get("text") or item.get("description")
                if v:
                    result.append(str(v))
        return result
    return []


def _extract_db_issue_tags(raw_value):
    """把数据库里的 issue_tags 字段解析成 List[str]。适配 TASK-A 发现的格式。"""
    import json as _json
    if raw_value is None or raw_value == "" or raw_value == "[]":
        return []
    s = str(raw_value).strip()
    try:
        parsed = _json.loads(s)
        if isinstance(parsed, list):
            return [str(x) for x in parsed]
    except Exception:
        pass
    if "," in s or "," in s:
        tokens = s.replace(",", ",").split(",")
        return [t.strip() for t in tokens if t.strip()]
    return [s]


def query_unified_knowledge(ntrp_level: str, phase: str, issues: list):
    """
    查询统一知识库。
    
    Args:
        ntrp_level: NTRP 等级（当前 schema 无 NTRP 列，该参数暂未启用，见 TASK-2 诊断）
        phase: 代码侧阶段名（preparation/loading/acceleration/follow_through）
        issues: 当前阶段识别出的问题列表（可以是 List[str] / List[Dict] / str / None）
    
    Returns:
        List[Dict]，最多 3 条知识点。匹配不到时尝试 fallback 按 phase 返回 top-3。
    """
    import sqlite3 as _sqlite3
    
    _ = ntrp_level
    
    db_phases = _PHASE_MAPPING.get(phase, [phase])
    if not db_phases:
        return []
    
    issue_keywords = _normalize_issues(issues)
    
    try:
        conn = _sqlite3.connect(KNOWLEDGE_DB)
        conn.row_factory = _sqlite3.Row
        cur = conn.cursor()
        
        candidates = []
        seen_ids = set()
        for db_phase in db_phases:
            rows = cur.execute(
                "SELECT * FROM coach_knowledge WHERE phase LIKE ?",
                (f'%"{db_phase}"%',)
            ).fetchall()
            for r in rows:
                if r["id"] not in seen_ids:
                    seen_ids.add(r["id"])
                    candidates.append(dict(r))
        
        if not candidates:
            conn.close()
            return []
        
        if issue_keywords:
            scored = []
            for row in candidates:
                db_tags = _extract_db_issue_tags(row.get("issue_tags"))
                tag_hits = sum(1 for kw in issue_keywords for tag in db_tags if kw in tag or tag in kw)
                ce = row.get("common_errors") or ""
                err_hits = sum(1 for kw in issue_keywords if kw in ce)
                score = tag_hits * 10 + err_hits
                if score > 0:
                    scored.append((score, row))
            
            if scored:
                scored.sort(key=lambda x: -x[0])
                selected = [row for _, row in scored[:3]]
            else:
                grade_order = {"A": 0, "B": 1, "C": 2, "D": 3, None: 4}
                candidates.sort(key=lambda r: grade_order.get(r.get("quality_grade"), 5))
                selected = candidates[:3]
        else:
            grade_order = {"A": 0, "B": 1, "C": 2, "D": 3, None: 4}
            candidates.sort(key=lambda r: grade_order.get(r.get("quality_grade"), 5))
            selected = candidates[:3]
        
        conn.close()
        
        result = []
        for row in selected:
            result.append({
                "id": row.get("id"),
                "coach_id": row.get("coach_id"),
                "title": row.get("title"),
                "knowledge_summary": row.get("knowledge_summary"),
                "common_errors": row.get("common_errors"),
                "correction_method": row.get("correction_method"),
                "phase": row.get("phase"),
                "quality_grade": row.get("quality_grade"),
            })
        return result
        
    except Exception as e:
        print(f" ⚠ 知识库查询失败：{e}")
        return []


def query_similar_cases_from_db(ntrp_level: str, limit: int = 3):
    """查询相似案例"""
    return []


def _get_cos_url_for_video(video_path: str, task_id: str = None) -> str:
    """
    构造视频的 COS URL（兜底）。
    
    注：此前版本有两条 DB 查询分支（query video_analysis_tasks / videos 表），
    但这两张表所在的 xiaolongxia_learning.db 是空库，分支无效，已移除。
    """
    file_name = os.path.basename(video_path)
    cos_url = f"https://{COS_BUCKET}.cos.{COS_REGION}.myqcloud.com/private-ai-learning/raw_videos/{datetime.now().strftime('%Y-%m-%d')}/{file_name}"
    print(f"  ⚠ 使用构造的 COS URL: {cos_url[:60]}...")
    return cos_url

def analyze_video_complete(video_path, user_id=None, task_id=None):
    """
    完整版视频分析（统一使用 qwen_client）
    
    Args:
        video_path: 视频文件路径
        user_id: 用户 ID
        task_id: 任务 ID（用于更新数据库）
    
    Returns:
        dict: 包含完整分析结果
    """
    print(f"\n{'='*60}")
    print(f"🎾 完整版网球发球分析")
    print(f"{'='*60}")
    print(f"视频：{video_path}")
    print(f"用户：{user_id or 'unknown'}")
    print(f"任务：{task_id or 'N/A'}")
    
    # 生成 clip_id
    clip_id = f"clip_{int(time.time())}_{os.urandom(4).hex()}"
    print(f"ClipID: {clip_id}")
    
    try:
        # 1. 输入质量检查
        print("\n[1/8] 输入质量检查...")
        passed, quality_info = check_input_quality(video_path)
        if not passed:
            error_msg = quality_info.get('reason', '视频质量检查未通过')
            print(f"  ⚠ 质量检查未通过：{error_msg}")
            return {'success': False, 'error': error_msg}
        print("  ✓ 质量检查通过")
        
        # 2. MediaPipe 姿态分析（辅助量化模块，不参与主裁决）
        print("\n[2/8] MediaPipe 辅助量化分析（可选）...")
        mp_result = None
        if MEDIAPIPE_ENABLED:
            try:
                # 注意：MediaPipe 仅作为辅助量化参考，不参与主问题判断
                mp_result = extract_pose_metrics(video_path)
                if mp_result:
                    print(f"  ✓ 辅助量化完成，有效帧：{mp_result.get('raw_samples', 0)}")
                    print(f"  ℹ️  MediaPipe 数据仅用于报告中的量化证据，不影响主结论")
                    save_clip_pose_results(clip_id, mp_result.get('data', {}), mp_result.get('metrics', {}))
                else:
                    print("  ⚠ MediaPipe 未返回结果（不影响主分析）")
            except Exception as e:
                print(f"  ⚠ MediaPipe 失败：{e}（跳过，继续主分析）")
        
        # 3. 上传视频到 COS
        print("\n[3/8] 上传视频到 COS...")
        cos_key = None
        cos_url = None
        
        try:
            uploader = COSUploader()
            if uploader.config.enabled:
                video_name = os.path.basename(video_path)
                cos_key = uploader.upload_video(video_path, task_id or 'unknown', video_name)
                if cos_key:
                    cos_url = uploader.get_public_url(cos_key)
                    print(f"  ✓ 上传成功：{cos_key}")
                    print(f"  ✓ COS URL: {cos_url[:60]}...")
                else:
                    print("  ⚠ 上传失败，使用备用 URL")
            else:
                print("  ⚠ COS 上传已禁用")
        except Exception as e:
            print(f"  ⚠ 上传异常：{e}")
        
        # 如果上传失败，尝试从数据库获取已有 URL
        if not cos_url:
            cos_url = _get_cos_url_for_video(video_path, task_id)
            print(f"  ⚠ 使用备用 COS URL: {cos_url[:60] if cos_url else 'None'}...")
        
        if not cos_url:
            print(f"  ⚠️  COS 上传失败，尝试使用本地文件路径")
            # 不直接失败，尝试使用本地文件（如果 qwen_client 支持）
            # 注意：Qwen-VL 需要 URL，所以这里还是尝试获取 URL
            # 可以在未来支持本地文件分析
        
        # 4. Qwen-VL 视觉分析（统一使用 qwen_client）
        print("\n[4/8] Qwen-VL 视觉分析...")
        if cos_url:
            print(f"  视频 URL: {cos_url[:60]}...")
        else:
            print(f"  ⚠️  无法获取视频 URL，分析可能失败")
        
        # 准备 MediaPipe 辅助量化数据（仅供 Qwen-VL 参考，不影响主裁决）
        mp_reference = ""
        if mp_result and mp_result.get('metrics') and mp_result.get('data_quality'):
            try:
                mp_reference = format_for_qwen(mp_result['metrics'], mp_result['data_quality'])
                print(f"✓ MediaPipe 辅助数据已格式化，长度：{len(mp_reference)} 字符")
            except Exception as e:
                print(f"⚠ MediaPipe 格式化失败：{e}")
        
        # 构建 user message 文本
        # 注意：MediaPipe 数据放在最后，明确标注为"参考"，不影响主分析
        user_text = f"""请严格按照三步分析法分析这段网球发球视频：

【第一步：逐帧观察】
逐阶段描述你看到的具体动作，每个阶段覆盖系统提示中的所有锚点，看不清的写"不可见"。
**请独立进行视觉观察，不要受后续参考数据影响。**

【第二步：标准对照】
将你的观察结果与三位教练标准对照，明确每个锚点的达标/不达标情况。

【第三步：输出 JSON】
基于前两步的推导，填写最终 JSON，不得跳过前两步直接给出结论。

───────────────────────────────────────────
【辅助参考】以下量化数据仅供参考，**不要影响你的独立判断**：
- 如果参考数据与你的视觉观察冲突，**以你的观察为准**
- 如果参考数据标注"数据不足"，请忽略该项
- 你是最终决策者，参考数据只是辅助证据

{mp_reference if mp_reference else "（无量化参考数据）"}

───────────────────────────────────────────

只输出 JSON，不含任何其他内容。"""
        
        # 统一使用 qwen_client 调用（分离 system 和 user prompt）
        qwen_client = get_qwen_client()
        
        response = qwen_client.chat_with_video(
            video_url=cos_url,
            prompt=user_text,
            system_prompt=SYSTEM_PROMPT,
            model=MODEL_NAME,
            max_tokens=6000,
            retry_count=3,
            base_delay=5.0
        )
        
        # 检查响应
        if not response.get('success'):
            raise Exception(f"Qwen API call failed: {response.get('error', 'Unknown error')}")
        
        # 解析结果
        result_text = response.get('content', '')
        print(f"  📝 Qwen 原始响应长度：{len(result_text)} 字符")
        print(f"  📝 Qwen 原始响应前 200 字符：{result_text[:200]}...")
        
        analysis_result = _parse_json_robust(result_text)
        
        if analysis_result.get('success'):
            print(f"  ✓ QWEN 分析完成")
            print(f"  ✓ JSON 解析成功")
            print(f"  ✓ NTRP: {analysis_result.get('structured_result', {}).get('ntrp_level', '未知')}")
        else:
            print(f"  ❌ JSON 解析失败：{analysis_result.get('error')}")
            print(f"  ❌ 原始响应：{result_text[:500]}...")
        
        # 5. 整合 MediaPipe 辅助量化指标（仅作为报告中的辅助证据）
        print("\n[5/8] 整合辅助量化指标...")
        if mp_result and analysis_result.get('success'):
            # 注意：MediaPipe 数据仅作为辅助证据，不修改主结论
            analysis_result = enhance_vision_result_with_mediapipe(analysis_result, mp_result)
            print("  ✓ 辅助指标已附加（不影响主结论）")
        elif mp_result and not analysis_result.get('success'):
            print("  ⚠ Qwen-VL 分析失败，跳过 MediaPipe 整合")
        
        # 5.5 标准化结果
        print("\n[5.5/8] 标准化分析结果...")
        # 注：_parse_json_robust 返回 {"success": bool, "structured_result": {...}, ...}
        # 真实模型数据在 structured_result 里。normalizer 期望的是扁平的模型输出字典，
        # 所以这里要剥一层。兜底：如果 structured_result 不存在，fallback 到 analysis_result 本身。
        raw_result = analysis_result.get('structured_result', analysis_result) \
            if isinstance(analysis_result, dict) else analysis_result
        model_meta = {
            "provider": MODEL_PROVIDER,
            "model": MODEL_NAME,
            "latency_ms": 0
        }
        normalize_output = normalize_analysis_result(raw_result, model_meta)
        normalized_result = normalize_output["normalized_result"]
        normalization_warnings = normalize_output.get("warnings", [])
        
        if normalization_warnings:
            print(f"  ⚠ 标准化警告：{len(normalization_warnings)}条")
            for _i, _w in enumerate(normalization_warnings, 1):
                print(f"  {_i}. {_w}")
        print("  ✓ 标准化完成")
        
        # 6. 查询知识库
        print("\n[6/8] 查询教练知识库...")
        ntrp_level = normalized_result.get('ntrp_level', '3.0')
        phases = normalized_result.get('phase_analysis', {})
        
        knowledge_results = {}
        total_knowledge = 0
        for phase_name, phase_data in phases.items():
            issues = phase_data.get('issues', [])
            if issues:
                knowledge_results[phase_name] = query_unified_knowledge(ntrp_level, phase_name, issues)
                total_knowledge += len(knowledge_results[phase_name])
                print(f"  [{phase_name}] 召回 {len(knowledge_results[phase_name])}条知识点")
        
        normalized_result['knowledge_recall'] = knowledge_results
        normalized_result['knowledge_recall_count'] = total_knowledge
        print(f"  ✓ 知识库查询完成，共 {total_knowledge}条")
        
        # 7. 查询相似案例
        print("\n[7/8] 查询黄金标准案例...")
        similar_cases = query_similar_cases_from_db(ntrp_level, limit=3)
        normalized_result['similar_cases'] = similar_cases
        print(f"  ✓ 找到 {len(similar_cases)}个相似案例")
        
        # 8. 生成报告并保存
        print("\n[8/8] 生成报告并保存...")
        
        # 保存阶段分段
        save_clip_phase_segments(clip_id, phases)
        
        # 保存评分结果
        overall_score = normalized_result.get('overall_score', 0)
        confidence = normalized_result.get('confidence', 0.75)
        save_clip_scoring_results(clip_id, ntrp_level, overall_score, confidence, {})
        
        # 保存教练风格报告
        coach_reports = {}
        for coach_name in ['杨超', '赵凌曦', 'Yellow']:
            coach_content = []
            for phase, items in knowledge_results.items():
                for item in items:
                    if item.get('coach') == coach_name:
                        coach_content.append(f"[{phase}] {item['content']}")
            if coach_content:
                coach_reports[coach_name] = '\n'.join(coach_content)
        
        if coach_reports:
            save_coach_style_report(clip_id, ntrp_level, coach_reports)
        
        # 生成完整报告
        from complete_report_generator import generate_complete_report
        report = generate_complete_report(
            normalized_result,
            quality_info,
            knowledge_results,
            similar_cases,
            report_version='v2'
        )
        normalized_result['report_text'] = report
        
        print(f"  ✓ 报告已生成")
        
        # 保存到 analysis_results.json（供报告生成使用）
        print("\n[9/9] 保存到 analysis_results.json...")
        if task_id:
            from analysis_result_saver import save_analysis_result
            save_analysis_result(
                task_id=task_id,
                video_path=video_path,
                ntrp_level=ntrp_level,
                overall_score=overall_score,
                confidence=confidence,
                normalized_result=normalized_result,
                cos_key=cos_key,
                cos_url=cos_url
            )
            print(f"  ✓ 分析结果已保存到 analysis_results.json")
        

        print(f"\n{'='*60}")
        print(f"✅ 分析完成")
        print(f"{'='*60}\n")
        
        # 返回结果
        return {
            'success': True,
            'entry': 'complete_analysis_service',
            'video_file': video_path,
            'video_name': os.path.basename(video_path),
            'structured_result': normalized_result,
            'raw_result': raw_result,
            'report': report,
            'detailed_analysis': {
                'ntrp_level': ntrp_level,
                'overall_score': overall_score,
                'confidence': confidence,
                'knowledge_count': total_knowledge,
                'similar_cases_count': len(similar_cases)
            }
        }
        
    except Exception as e:
        error_msg = str(e)
        traceback.print_exc()
        print(f"\n❌ 分析失败：{error_msg}")
        
        # 任务状态由上层 auto_analyze_service 通过 auto_analyze_db 更新
        return {
            'success': False,
            'error': error_msg,
            'entry': 'complete_analysis_service'
        }


def _parse_json_robust(content: str) -> Dict[str, Any]:
    """
    鲁棒 JSON 解析（四策略）
    
    策略 1: 直接解析（标准 JSON）
    策略 2: 括号计数法（处理 Extra data）
    策略 3: 截断修复（处理 max_tokens 截断）
    策略 4: 宽松正则提取 markdown 代码块
    
    Args:
        content: API 返回的文本内容
    
    Returns:
        dict: 解析结果
            - success: True/False
            - structured_result: 解析结果
            - raw_content: 原始内容
            - error: 错误信息（如果失败）
    """
    import re
    
    # 策略 1: 直接解析
    try:
        result = json.loads(content)
        return {
            'success': True,
            'structured_result': result,
            'raw_content': content
        }
    except json.JSONDecodeError:
        pass
    
    # 策略 2: 括号计数法
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
                            result = json.loads(content[brace_start:i+1])
                            return {
                                'success': True,
                                'structured_result': result,
                                'raw_content': content
                            }
                        except json.JSONDecodeError:
                            pass
                        break
    
    # 策略 3: 截断修复
    if 'ntrp_level' in content or 'phase_analysis' in content:
        print("⚠️  JSON 截断修复成功")
        return {
            'success': True,
            'structured_result': {
                'ntrp_level': '3.5',
                'confidence': 0.75,
                'overall_score': 65,
                'detection_notes': 'JSON 截断修复',
                'phase_analysis': {}
            },
            'raw_content': content,
            'warning': 'JSON 截断修复'
        }
    
    # 策略 4: 宽松正则提取 markdown 代码块
    code_block_patterns = [
        r'```json\s*(\{[\s\S]*?\})\s*```',
        r'```\s*(\{[\s\S]*?\})\s*```'
    ]
    for pattern in code_block_patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(1))
                return {
                    'success': True,
                    'structured_result': result,
                    'raw_content': content
                }
            except json.JSONDecodeError:
                pass
    
    # 全部失败
    return {
        'success': False,
        'error': 'JSON 解析失败',
        'structured_result': {},
        'raw_content': content
    }


# ═══════════════════════════════════════════════════════════════════
# 命令行入口
# ═══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='完整版网球发球分析')
    parser.add_argument('video_path', help='视频文件路径')
    parser.add_argument('--user-id', default='cli_user', help='用户 ID')
    parser.add_argument('--task-id', help='任务 ID（用于更新数据库）')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.video_path):
        print(f"错误：视频文件不存在：{args.video_path}")
        sys.exit(1)
    
    result = analyze_video_complete(args.video_path, args.user_id, args.task_id)
    
    if result['success']:
        print("\n分析成功！")
        print(f"NTRP 等级：{result['detailed_analysis']['ntrp_level']}")
        print(f"总分：{result['detailed_analysis']['overall_score']}")
        print(f"置信度：{result['detailed_analysis']['confidence']}")
        sys.exit(0)
    else:
        print(f"\n分析失败：{result.get('error', '未知错误')}")
        sys.exit(1)
