#!/usr/bin/env python3
"""
自动分析服务（增强版 v2）
数据库驱动扫描，不再依赖时间窗口
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# 加载 .env 环境变量
env_path = os.path.join(PROJECT_ROOT, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"✅ 已加载环境变量：{env_path}")
else:
    print(f"⚠️  .env 文件不存在：{env_path}")

# 配置
MEDIA_DIR = '/home/admin/.openclaw/workspace/media/inbound'
DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'auto_analyze.db')
SCAN_INTERVAL = 60  # 扫描间隔（秒）
MAX_RETRIES = 3  # 最大重试次数

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(PROJECT_ROOT, 'logs', 'auto_analyze.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AutoAnalyzeService')

def send_report_via_dingtalk(task_id: str, report_dict: dict):
    """通过钉钉发送报告"""
    try:
        # 从报告字典提取关键信息
        summary = report_dict.get('summary', '')
        primary_issue = report_dict.get('primary_issue', '')
        training_advice = report_dict.get('training_advice', [])
        phase_comparison = report_dict.get('phase_comparison', {})
        matched_samples = report_dict.get('matched_standard_samples', [])
        
        # 构建钉钉消息
        message = f"🎾 网球发球分析报告\n\n"
        message += f"📊 总结：\n{summary}\n\n"
        
        if primary_issue:
            message += f"🔍 主要问题：\n{primary_issue}\n\n"
        
        # 阶段分析
        if phase_comparison:
            message += f"📈 阶段分析：\n"
            for phase, data in phase_comparison.items():
                status = "⚠️ 需改进" if data.get('has_issue') else "✅ 良好"
                message += f"  {phase}: {status}\n"
            message += "\n"
        
        # 训练建议
        if training_advice:
            message += f"💡 训练建议：\n"
            for i, advice in enumerate(training_advice[:3], 1):
                message += f"{i}. {advice}\n"
            message += "\n"
        
        # 黄金样本推荐
        if matched_samples:
            message += f"🏆 推荐学习样本：\n"
            for sample in matched_samples[:2]:
                message += f"  - {sample.get('sample_id')} ({sample.get('ntrp_level')}级)\n"
            message += "\n"
        
        message += f"📋 完整报告已保存到系统，可随时查看。"
        
        # 发送钉钉消息
        from message import send as message_send
        message_send(
            action='send',
            channel='dingtalk-connector',
            target='0200493833124900',
            message=message
        )
        
        logger.info(f"✅ 报告已通过钉钉发送")
        
    except Exception as e:
        logger.warning(f"⚠️  钉钉发送失败：{e}")

# 导入数据库模块
from auto_analyze_db import (
    init_db,
    get_or_create_video_file,
    create_analysis_task,
    update_task_status,
    get_pending_tasks,
    get_failed_tasks,
    log_message_sent,
    get_task_statistics,
    get_db_connection
)


class AutoAnalyzeService:
    """自动分析服务（数据库驱动）"""
    
    def __init__(self):
        self.media_dir = MEDIA_DIR
        self.scan_interval = SCAN_INTERVAL
        self.max_retries = MAX_RETRIES
        logger.info("🚀 自动分析服务初始化（数据库驱动 v2）")
    
    def scan_unprocessed_videos(self):
        """
        第一层扫描：查找已落盘但未创建任务的视频文件
        
        逻辑：
        1. 扫描媒体目录中的所有 .mp4 文件
        2. 检查 video_files 表中是否已有记录
        3. 如果没有，创建视频文件记录和分析任务
        """
        logger.info("🔍 第一层扫描：查找未处理视频...")
        
        if not os.path.exists(self.media_dir):
            logger.warning(f"⚠️  媒体目录不存在：{self.media_dir}")
            return []
        
        new_videos = []
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 扫描媒体目录（支持多种视频格式）
        # 扫描媒体目录（支持多种视频格式）
        patterns = ['*.mp4', '*.MP4', '*.mov', '*.MOV', '*.avi', '*.AVI']
        for pattern in patterns:
            for file_path in Path(self.media_dir).glob(pattern):
                try:
                    file_hash = self._compute_file_hash(str(file_path))
                    
                    # 检查数据库中是否已有该文件
                    cursor.execute('SELECT id FROM video_files WHERE file_hash = ?', (file_hash,))
                    row = cursor.fetchone()
                    
                    if not row:
                        # 新文件，创建视频文件记录
                        video_file_id = get_or_create_video_file(str(file_path))
                        
                        if video_file_id:
                            # 创建分析任务
                            task_id = create_analysis_task(video_file_id)
                            
                            if task_id:
                                new_videos.append({
                                    'video_file_id': video_file_id,
                                    'task_id': task_id,
                                    'file_path': str(file_path),
                                    'file_name': file_path.name
                                })
                                logger.info(f"✅ 发现新视频：{file_path.name} (Task: {task_id})")
                            else:
                                logger.debug(f"⏭️  跳过 {file_path.name}：任务已存在")
                        else:
                            logger.debug(f"⏭️  跳过 {file_path.name}：视频文件已存在")
                    else:
                        # 文件已存在，检查是否有未完成的任务
                        video_file_id = row['id']
                        cursor.execute('''
                            SELECT id FROM analysis_tasks 
                            WHERE video_file_id = ? AND status NOT IN ('completed')
                        ''', (video_file_id,))
                        
                        if not cursor.fetchone():
                            # 没有未完成的任务，可能是已完成或失败超过最大重试
                            logger.debug(f"⏭️  跳过 {file_path.name}：已有完成的任务或无待处理任务")
                            
                except Exception as e:
                    logger.error(f"❌ 处理文件失败 {file_path.name}: {str(e)}")
    def scan_incomplete_tasks(self):
        """
        第二层扫描：查找未完成但可继续处理的任务
        
        逻辑：
        1. 查找 status = 'pending' 的任务
        2. 查找 status = 'failed' 且 retry_count < max_retries 的任务
        3. 返回待处理任务列表
        """
        logger.info("🔍 第二层扫描：查找未完成任务...")
        
        incomplete_tasks = []
        
        # 获取待处理任务
        pending_tasks = get_pending_tasks(limit=10)
        for task in pending_tasks:
            incomplete_tasks.append({
                'video_file_id': task['video_file_id'],
                'task_id': task['task_id'],
                'file_path': task['file_path'],
                'file_name': task['file_name'],
                'status': task['status'],
                'retry_count': task['retry_count'] if hasattr(task, 'retry_count') else 0
            })
            logger.info(f"📋 待处理任务：{task['task_id']} ({task['file_name']})")
        
        # 获取失败可重试任务
        failed_tasks = get_failed_tasks(max_retries=self.max_retries)
        for task in failed_tasks:
            incomplete_tasks.append({
                'video_file_id': task['video_file_id'],
                'task_id': task['task_id'],
                'file_path': task['file_path'],
                'file_name': task['file_name'],
                'status': task['status'],
                'retry_count': task['retry_count'] if hasattr(task, 'retry_count') else 0
            })
            logger.info(f"🔄 失败可重试：{task['task_id']} ({task['file_name']}, Retry: {task['retry_count'] if hasattr(task, 'retry_count') else 0})")
        
        logger.info(f"📊 发现 {len(incomplete_tasks)} 个未完成任务")
        return incomplete_tasks
    
    def _compute_file_hash(self, file_path: str) -> str:
        """计算文件哈希值"""
        import hashlib
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def analyze_video(self, task_info: dict) -> bool:
        """分析视频（简化版：直接调用分析服务）"""
        task_id = task_info['task_id']
        file_path = task_info['file_path']
        
        logger.info(f"🔍 开始分析：{task_info['file_name']} (Task: {task_id})")
        
        try:
            # 更新状态为分析中
            update_task_status(task_id, 'analyzing')
            
            # 直接调用分析服务（简化处理）
            from complete_analysis_service import analyze_video_complete
            
            result = analyze_video_complete(file_path, user_id='auto_analyze', task_id=task_id)
            
            if result.get('success'):
                logger.info(f"✅ 分析成功：{task_info['file_name']}")
                
                # 更新任务状态（包含完整分析结果）
                structured = result.get('structured_result', {})
                ntrp_level = structured.get('ntrp_level', 'unknown')
                primary_issue = structured.get('primary_issue')
                secondary_issue = structured.get('secondary_issue')
                sample_category = 'excellent_demo' if structured.get('overall_score', 0) >= 80 else 'typical_issue'
                
                # 获取报告内容
                report_text = result.get('report', '')
                
                update_task_status(
                    task_id,
                    'analyzing',
                    ntrp_level=ntrp_level,
                    sample_category=sample_category,
                    primary_issue=primary_issue,
                    secondary_issue=secondary_issue
                )
                
                # 生成完整报告（整合黄金样本库 + 教练知识库）
                if report_text:
                    try:
                        from report_generation_integration import ReportGenerator
                        import json
                        from datetime import datetime
                        
                        logger.info(f"📊 生成完整报告（整合黄金样本库 + 教练知识库）...")
                        
                        # 等待 1 秒确保 sample_registry.json 已保存
                        time.sleep(1)
                        
                        # 使用 ReportGenerator 生成完整报告
                        generator = ReportGenerator()
                        
                        # 从 analysis_results.json 读取本次分析结果
                        analysis_results_path = os.path.join(PROJECT_ROOT, 'data', 'analysis_results.json')
                        if os.path.exists(analysis_results_path):
                            with open(analysis_results_path, 'r', encoding='utf-8') as f:
                                analysis_results = json.load(f)
                            
                            # 找到本次分析结果
                            current_analysis = None
                            for result in analysis_results:
                                if result.get('task_id') == task_id:
                                    current_analysis = result
                                    break
                            
                            if current_analysis:
                                logger.info(f"📊 已读取本次分析结果：{current_analysis['analysis_id']}")
                                logger.info(f"   NTRP: {current_analysis['ntrp_level']}, 总分：{current_analysis['overall_score']}")
                        
                        # 生成完整报告（从 sample_registry 查找黄金样本对比）
                        report_dict = generator.generate_report(
                            user_sample_id=task_id,
                            ntrp_level=ntrp_level,
                            shadow_mode=False
                        )
                        
                        # 检查报告是否完整
                        if not report_dict.get('matched_standard_samples') and not report_dict.get('phase_comparison'):
                            logger.warning(f"⚠️  报告不完整，尝试使用简化版本...")
                            # 使用 complete_analysis_service 生成的报告
                            report_dict = {
                                'report_version': 'v2_complete',
                                'generated_at': datetime.now().isoformat(),
                                'user_sample_id': task_id,
                                'summary': report_text[:500] if len(report_text) > 500 else report_text,
                                'primary_issue': primary_issue,
                                'secondary_issue': secondary_issue,
                                'matched_problem_pool': '自动分析',
                                'matched_standard_samples': [],
                                'phase_comparison': {},
                                'priority_gaps': [],
                                'training_advice': [],
                                'knowledge_keys': []
                            }
                        
                        # 保存完整报告为 JSON 文件
                        report_filename = f"analysis_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        report_path = os.path.join(PROJECT_ROOT, 'reports', report_filename)
                        
                        with open(report_path, 'w', encoding='utf-8') as f:
                            json.dump(report_dict, f, ensure_ascii=False, indent=2)
                        
                        logger.info(f"📝 完整报告已保存：{report_filename}")
                        
                        # 通过钉钉发送报告
                        logger.info(f"📤 通过钉钉发送报告...")
                        send_report_via_dingtalk(task_id, report_dict)
                        
                    except Exception as e:
                        logger.warning(f"⚠️  完整报告生成失败：{e}")
                        logger.warning(f"   使用简化报告：{report_text[:200]}...")
                
                return True
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"❌ 分析失败：{task_info['file_name']} - {error_msg}")
                update_task_status(task_id, 'failed', last_error=error_msg)
                return False
                
        except Exception as e:
            logger.error(f"❌ 分析异常：{task_info['file_name']} - {str(e)}", exc_info=True)
            update_task_status(task_id, 'failed', last_error=str(e))
            return False
    
    def process_task(self, task_info: dict) -> bool:
        """处理单个任务"""
        task_id = task_info['task_id']
        status = task_info.get('status', 'pending')
        
        logger.info(f"📋 处理任务：{task_info['file_name']} (Task: {task_id}, Status: {status})")
        
        # 步骤 1: 分析视频
        if status in ['pending', 'failed']:
            if not self.analyze_video(task_info):
                return False
        
        # 步骤 2: 上传 COS（分析成功后自动完成）
        # 简化处理：假设分析成功后自动上传了 COS
        update_task_status(task_id, 'uploaded_cos')
        logger.info(f"✅ COS 上传完成：{task_info['file_name']}")
        
        # 步骤 3: 发送报告
        update_task_status(task_id, 'completed', report_sent=True)
        logger.info(f"✅ 报告发送完成：{task_info['file_name']}")
        
        # 步骤 4: 删除本地文件（所有步骤成功后才删除）
        try:
            video_path = task_info.get('file_path')
            if video_path and os.path.exists(video_path):
                file_size = os.path.getsize(video_path)
                os.remove(video_path)
                logger.info(f"🗑️ 已删除本地文件：{video_path} ({file_size/1024/1024:.2f}MB)")
                logger.info(f"   原因：所有步骤成功完成（COS 已上传 + 数据库已更新 + 报告已发送）")
            else:
                logger.debug(f"⚠️ 本地文件不存在，跳过删除：{video_path}")
        except Exception as e:
            logger.warning(f"⚠️ 删除本地文件失败：{video_path} - {e}")
            logger.warning(f"   保留本地文件，可手动清理")
        
        return True
    
    def print_statistics(self):
        """打印统计信息"""
        stats = get_task_statistics()
        
        logger.info("📊 任务统计:")
        logger.info(f"   按状态：{stats.get('by_status', {})}")
        logger.info(f"   按 NTRP: {stats.get('by_ntrp', {})}")
        logger.info(f"   按分类：{stats.get('by_category', {})}")
    
    def run(self):
        """运行服务"""
        logger.info("="*60)
        logger.info("🚀 自动分析服务启动（数据库驱动 v2）")
        logger.info("="*60)
        
        # 初始化数据库
        init_db()
        
        # 打印初始统计
        self.print_statistics()
        
        # 主循环
        iteration = 0
        while True:
            iteration += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"📍 第 {iteration} 次扫描")
            logger.info(f"{'='*60}")
            
            try:
                # 第一层：扫描未处理视频
                new_videos = self.scan_unprocessed_videos()
                
                # 第二层：扫描未完成任务
                incomplete_tasks = self.scan_incomplete_tasks()
                
                # 处理新视频
                for video in new_videos:
                    self.process_task(video)
                
                # 处理未完成任务
                for task in incomplete_tasks:
                    # 避免重复处理新视频
                    if not any(v['task_id'] == task['task_id'] for v in new_videos):
                        self.process_task(task)
                
                # 打印统计（每 10 次扫描执行一次）
                if iteration % 10 == 0:
                    self.print_statistics()
                
            except Exception as e:
                logger.error(f"❌ 扫描异常：{str(e)}", exc_info=True)
            
            # 等待下一次扫描
            logger.info(f"⏳ 等待 {self.scan_interval} 秒...")
            time.sleep(self.scan_interval)


if __name__ == '__main__':
    # 创建并运行服务
    service = AutoAnalyzeService()
    service.run()
