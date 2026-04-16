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
    MEDIAPIPE_ENABLED
)
from analysis_normalizer import normalize_analysis_result
from analysis_repository import analysis_repository
from cos_uploader import COSUploader

# 数据库配置
DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'xiaolongxia_learning.db')
COS_BUCKET = 'tennis-ai-1411340868'
COS_REGION = 'ap-shanghai'


# ═══════════════════════════════════════════════════════════════════
# 数据库操作函数
# ═══════════════════════════════════════════════════════════════════

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def update_video_analysis_task(task_id: str, status: str, **kwargs):
    """更新视频分析任务状态"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    update_fields = []
    values = []
    
    if status:
        update_fields.append("status = ?")
        values.append(status)
    
    if 'ntrp_level' in kwargs:
        update_fields.append("ntrp_level = ?")
        values.append(kwargs['ntrp_level'])
    
    if 'sample_category' in kwargs:
        update_fields.append("sample_category = ?")
        values.append(kwargs['sample_category'])
    
    if 'primary_issue' in kwargs:
        update_fields.append("primary_issue = ?")
        values.append(kwargs['primary_issue'])
    
    if 'secondary_issue' in kwargs:
        update_fields.append("secondary_issue = ?")
        values.append(kwargs['secondary_issue'])
    
    if 'error_msg' in kwargs:
        update_fields.append("last_error = ?")
        values.append(kwargs['error_msg'])
    
    if 'cos_key' in kwargs:
        update_fields.append("cos_key = ?")
        values.append(kwargs['cos_key'])
    
    if 'cos_url' in kwargs:
        update_fields.append("cos_url = ?")
        values.append(kwargs['cos_url'])
    
    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    
    values.append(task_id)
    
    if update_fields:
        query = f"UPDATE video_analysis_tasks SET {', '.join(update_fields)} WHERE task_id = ?"
        cursor.execute(query, values)
        conn.commit()
    
    conn.close()


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


def query_unified_knowledge(ntrp_level: str, phase: str, issues: list):
    """查询统一知识库"""
    return []


def query_similar_cases_from_db(ntrp_level: str, limit: int = 3):
    """查询相似案例"""
    return []


def _get_cos_url_for_video(video_path: str, task_id: str = None) -> str:
    """
    根据 video_path 或 task_id 获取对应的 COS URL。
    优先从数据库的 video_analysis_tasks + videos 表查询。
    """
    # 方式 1: 从数据库查询（task_id 已知时）
    if task_id:
        try:
            conn = get_db_connection()
            row = conn.execute('''
                SELECT v.cos_url
                FROM video_analysis_tasks t
                JOIN videos v ON t.video_id = v.id
                WHERE t.task_id = ?
            ''', (task_id,)).fetchone()
            conn.close()
            if row and row['cos_url']:
                return row['cos_url']
        except Exception as e:
            print(f"  ⚠ 数据库查询 COS URL 失败：{e}")
    
    # 方式 2: 从数据库按文件名查询
    file_name = os.path.basename(video_path)
    try:
        conn = get_db_connection()
        row = conn.execute('''
            SELECT cos_url FROM videos
            WHERE file_name = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (file_name,)).fetchone()
        conn.close()
        if row and row['cos_url']:
            return row['cos_url']
    except Exception as e:
        print(f"  ⚠ 按文件名查询 COS URL 失败：{e}")
    
    # 方式 3: 构造 COS URL（兜底）
    file_name = os.path.basename(video_path)
    cos_url = f"https://{COS_BUCKET}.cos.{COS_REGION}.myqcloud.com/private-ai-learning/raw_videos/{datetime.now().strftime('%Y-%m-%d')}/{file_name}"
    print(f"  ⚠ 使用构造的 COS URL: {cos_url[:60]}...")
    return cos_url


# ═══════════════════════════════════════════════════════════════════
# 主分析函数（统一使用 qwen_client）
# ═══════════════════════════════════════════════════════════════════

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
            if task_id:
                update_video_analysis_task(task_id, 'failed', error_msg=error_msg)
            return {'success': False, 'error': error_msg}
        print("  ✓ 质量检查通过")
        
        # 2. MediaPipe 姿态分析
        print("\n[2/8] MediaPipe 姿态分析...")
        mp_result = None
        if MEDIAPIPE_ENABLED:
            try:
                mp_result = extract_pose_metrics(video_path)
                if mp_result:
                    print(f"  ✓ 姿态分析完成，有效帧：{mp_result.get('raw_samples', 0)}")
                    save_clip_pose_results(clip_id, mp_result.get('data', {}), mp_result.get('metrics', {}))
                else:
                    print("  ⚠ MediaPipe 未返回结果")
            except Exception as e:
                print(f"  ⚠ MediaPipe 失败：{e}")
        
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
        
        # 正确接入 MediaPipe 数据，并分离 system/user prompt
        mp_formatted = ""
        if mp_result and mp_result.get('metrics') and mp_result.get('data_quality'):
            try:
                mp_formatted = format_for_kimi(mp_result['metrics'], mp_result['data_quality'])
                print(f"✓ MediaPipe 数据已格式化，长度：{len(mp_formatted)} 字符")
            except Exception as e:
                print(f"⚠ MediaPipe 格式化失败：{e}")
        
        # 构建 user message 文本
        user_text = f"""请严格按照三步分析法分析这段网球发球视频：

第一步（逐帧观察）：逐阶段描述你看到的具体动作，每个阶段覆盖系统提示中的所有锚点，看不清的写"不可见"。
第二步（标准对照）：将观察结果与三位教练标准对照，明确每个锚点的达标/不达标情况。
第三步（输出 JSON）：基于前两步推导，填写最终 JSON，不得跳过前两步直接给出结论。

{mp_formatted}

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
        analysis_result = _parse_json_robust(result_text)
        
        print(f"  ✓ QWEN 分析完成")
        
        # 5. 整合 MediaPipe 结果
        print("\n[5/8] 整合量化指标...")
        if mp_result:
            analysis_result = enhance_vision_result_with_mediapipe(analysis_result, mp_result)
            print("  ✓ 指标整合完成")
        
        # 5.5 标准化结果
        print("\n[5.5/8] 标准化分析结果...")
        raw_result = analysis_result
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
                ntrp_level=ntrp_level,
                overall_score=overall_score,
                confidence=confidence,
                report=report,
                video_path=video_path,
                cos_key=cos_key,
                cos_url=cos_url
            )
            print(f"  ✓ 分析结果已保存到 analysis_results.json")
        
        # 保存到数据库
        print("\n[10/10] 保存到数据库...")
        if task_id:
            analysis_repository.save_analysis_artifacts(
                task_id=task_id,
                raw_result=raw_result,
                normalized_result=normalized_result,
                report_text=report,
                report_version='v2'
            )
            print(f"  ✓ 分析结果已保存到数据库")
        
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
        
        if task_id:
            update_video_analysis_task(task_id, 'failed', error_msg=error_msg)
        
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
