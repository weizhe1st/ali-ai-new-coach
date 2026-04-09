#!/usr/bin/env python3
"""
OpenClaw 渠道集成 - 监听钉钉视频消息并调用原系统分析
"""

import os
import sys
import time
import sqlite3
from pathlib import Path
from datetime import datetime

# 项目路径
PROJECT_ROOT = '/home/admin/.openclaw/workspace/ai-coach'
sys.path.insert(0, PROJECT_ROOT)

# 导入原系统核心模块
from complete_analysis_service import analyze_video_complete
from complete_report_generator import generate_complete_report
from analysis_repository import save_analysis_to_db

# 配置
VIDEO_INPUT_DIR = '/home/admin/.openclaw/workspace/media/inbound'
DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'db', 'app.db')

# 已处理的视频记录（避免重复处理）
processed_videos = set()


def check_new_video():
    """检查新的视频文件"""
    
    if not os.path.exists(VIDEO_INPUT_DIR):
        return None
    
    # 获取最新的视频文件
    video_files = []
    for f in os.listdir(VIDEO_INPUT_DIR):
        if f.endswith(('.mp4', '.MOV', '.avi', '.MP4')):
            full_path = os.path.join(VIDEO_INPUT_DIR, f)
            # 只处理最近 5 分钟内的文件
            mtime = os.path.getmtime(full_path)
            if time.time() - mtime < 300:  # 5 分钟
                if full_path not in processed_videos:
                    video_files.append((full_path, mtime))
    
    if not video_files:
        return None
    
    # 返回最新的视频
    video_files.sort(key=lambda x: x[1], reverse=True)
    return video_files[0][0]


def process_video(video_path):
    """处理视频分析"""
    
    print(f"\n{'='*60}")
    print(f"🎾 开始处理视频分析")
    print(f"{'='*60}")
    print(f"视频：{video_path}")
    
    try:
        # 1. 验证视频
        print("\n[1/5] 验证视频...")
        from video_validator import validate_video
        is_valid, video_info = validate_video(video_path)
        
        if not is_valid:
            print(f"  ❌ 视频验证失败：{video_info.get('error', '未知错误')}")
            return None
        
        print(f"  ✅ 视频有效：{video_info.get('duration', 0):.1f}秒，{video_info.get('size_mb', 0):.1f}MB")
        
        # 2. AI 分析
        print("\n[2/5] AI 视频分析...")
        analysis_result = analyze_video_complete(
            video_path=video_path,
            user_id='dingtalk_user',  # 可以从消息中获取
            task_id=None
        )
        
        if not analysis_result or not analysis_result.get('success'):
            print(f"  ❌ 分析失败：{analysis_result.get('error', '未知错误')}")
            return None
        
        print(f"  ✅ 分析完成：NTRP {analysis_result.get('analysis', {}).get('ntrp_level')}")
        
        # 3. 生成报告
        print("\n[3/5] 生成分析报告...")
        normalized_result = analysis_result.get('analysis', {})
        
        # 生成通俗化报告
        from complete_report_generator import generate_complete_report, simplify_technical_term
        
        # 先标准化结果
        from analysis_normalizer import normalize_analysis_result
        normalized = normalize_analysis_result(
            ai_result=normalized_result,
            mp_metrics=analysis_result.get('mp_metrics'),
            knowledge_results=analysis_result.get('knowledge_results')
        )
        
        # 生成报告
        report = generate_complete_report(
            normalized_result=normalized,
            quality_info={'status': 'ok'},
            knowledge_results=analysis_result.get('knowledge_results'),
            similar_cases=analysis_result.get('similar_cases'),
            mp_metrics=analysis_result.get('mp_metrics')
        )
        
        # 通俗化处理
        simple_report = simplify_technical_term(report)
        
        print(f"  ✅ 报告已生成")
        
        # 4. 保存到数据库
        print("\n[4/5] 保存分析结果...")
        save_analysis_to_db(
            video_path=video_path,
            analysis=normalized_result,
            user_id='dingtalk_user'
        )
        print(f"  ✅ 数据库已更新")
        
        # 5. 清理临时文件
        print("\n[5/5] 清理临时文件...")
        os.remove(video_path)
        processed_videos.add(video_path)
        print(f"  ✅ 临时文件已删除")
        
        print(f"\n{'='*60}")
        print(f"✅ 视频分析完成！")
        print(f"{'='*60}\n")
        
        return simple_report
        
    except Exception as e:
        print(f"\n❌ 处理失败：{e}")
        import traceback
        traceback.print_exc()
        return None


def send_to_dingtalk(report, user_id):
    """发送报告到钉钉（通过 OpenClaw 渠道）"""
    
    # 这里需要通过 OpenClaw 的消息 API 发送
    # 目前简化为打印输出
    print("\n📱 发送报告到钉钉:")
    print(report)
    
    # TODO: 集成 OpenClaw 消息发送
    # 可以使用 OpenClaw 的 message 工具或渠道 API


def main():
    """主循环 - 监听新视频"""
    
    print("\n" + "="*60)
    print("🎾 网球 AI 教练 - OpenClaw 集成服务")
    print("="*60)
    print(f"监听目录：{VIDEO_INPUT_DIR}")
    print(f"数据库：{DB_PATH}")
    print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    # 检查数据库
    if not os.path.exists(DB_PATH):
        print(f"⚠️  数据库不存在，创建中...")
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.close()
        print(f"✅ 数据库已创建")
    
    print("✅ 服务已启动，等待视频上传...\n")
    print("提示：在钉钉中发送网球视频，系统将自动分析并回复\n")
    
    # 主循环
    check_interval = 3  # 每 3 秒检查一次
    
    while True:
        try:
            # 检查新视频
            video_path = check_new_video()
            
            if video_path:
                print(f"\n📹 检测到新视频：{os.path.basename(video_path)}")
                
                # 处理视频
                report = process_video(video_path)
                
                if report:
                    # 发送报告（这里简化为打印）
                    send_to_dingtalk(report, 'dingtalk_user')
                    print("✅ 报告已发送")
            
            # 等待下一次检查
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  服务已停止")
            break
        except Exception as e:
            print(f"\n❌ 错误：{e}")
            time.sleep(check_interval)


if __name__ == '__main__':
    main()
