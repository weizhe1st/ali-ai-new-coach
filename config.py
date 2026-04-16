#!/usr/bin/env python3
"""
统一配置与环境管理模块

负责集中管理：
- 模型配置（DashScope/Qwen）
- 渠道配置（钉钉/QQ）
- 路径配置（数据/日志/临时目录）
- 运行模式配置（dev/prod）

让各模块不再各自散读环境变量，统一通过本模块获取配置
"""

import os
import sys
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path


@dataclass
class ModelConfig:
    """模型配置"""
    dashscope_api_key: str = ""
    moonshot_api_key: str = ""
    
    # 模型名称
    video_model_name: str = "qwen-vl-max"
    text_model_name: str = "qwen-max"
    image_model_name: str = "qwen-vl-max"
    
    # 分析后端配置
    analysis_backend: str = "legacy"  # legacy | simple | qwen_vl
    
    # 临时开关
    enable_temp_qwen_fallback: bool = False
    
    @classmethod
    def from_env(cls) -> 'ModelConfig':
        """从环境变量加载配置"""
        return cls(
            dashscope_api_key=os.environ.get('DASHSCOPE_API_KEY', ''),
            moonshot_api_key=os.environ.get('MOONSHOT_API_KEY', ''),
            video_model_name=os.environ.get('VIDEO_MODEL_NAME', 'qwen-vl-max'),
            text_model_name=os.environ.get('TEXT_MODEL_NAME', 'qwen-max'),
            image_model_name=os.environ.get('IMAGE_MODEL_NAME', 'qwen-vl-max'),
            analysis_backend=os.environ.get('ANALYSIS_BACKEND', 'complete'),
            enable_temp_qwen_fallback=os.environ.get('ENABLE_TEMP_QWEN_FALLBACK', 'false').lower() in ('true', '1', 'yes')
        )
    
    def validate(self) -> bool:
        """验证必要配置"""
        if not self.dashscope_api_key:
            raise ValueError("DASHSCOPE_API_KEY is required for video analysis")
        return True


@dataclass
class ChannelConfig:
    """渠道配置"""
    # 钉钉配置
    dingtalk_enabled: bool = True
    dingtalk_app_key: str = ""
    dingtalk_app_secret: str = ""
    dingtalk_agent_id: str = ""
    dingtalk_token: str = ""
    dingtalk_secret: str = ""
    
    # QQ 配置
    qq_enabled: bool = True
    qq_app_id: str = ""
    qq_bot_token: str = ""
    qq_secret: str = ""
    
    @classmethod
    def from_env(cls) -> 'ChannelConfig':
        """从环境变量加载配置"""
        return cls(
            dingtalk_enabled=os.environ.get('DINGTALK_ENABLED', 'true').lower() in ('true', '1', 'yes'),
            dingtalk_app_key=os.environ.get('DINGTALK_APP_KEY', ''),
            dingtalk_app_secret=os.environ.get('DINGTALK_APP_SECRET', ''),
            dingtalk_agent_id=os.environ.get('DINGTALK_AGENT_ID', ''),
            dingtalk_token=os.environ.get('DINGTALK_TOKEN', ''),
            dingtalk_secret=os.environ.get('DINGTALK_SECRET', ''),
            qq_enabled=os.environ.get('QQ_ENABLED', 'true').lower() in ('true', '1', 'yes'),
            qq_app_id=os.environ.get('QQ_APP_ID', ''),
            qq_bot_token=os.environ.get('QQ_BOT_TOKEN', ''),
            qq_secret=os.environ.get('QQ_SECRET', '')
        )


@dataclass
class COSConfig:
    """腾讯云 COS 配置"""
    # COS 基础配置
    enabled: bool = True
    secret_id: str = ""
    secret_key: str = ""
    bucket: str = ""
    region: str = ""
    
    # 存储路径前缀
    raw_prefix: str = "raw/"  # 原始视频前缀
    analyzed_prefix: str = "analyzed/"  # 分析后视频前缀
    golden_prefix: str = "golden/"  # 黄金样本前缀
    candidate_prefix: str = "candidate_golden/"  # 候选样本前缀
    
    # 当前年月前缀（自动计算）
    current_month_prefix: str = ""
    
    @classmethod
    def from_env(cls) -> 'COSConfig':
        """从环境变量加载配置"""
        from datetime import datetime
        current_month = datetime.now().strftime('%Y/%m')
        
        return cls(
            enabled=os.environ.get('COS_ENABLED', 'true').lower() in ('true', '1', 'yes'),
            secret_id=os.environ.get('COS_SECRET_ID', ''),
            secret_key=os.environ.get('COS_SECRET_KEY', ''),
            bucket=os.environ.get('COS_BUCKET', ''),
            region=os.environ.get('COS_REGION', ''),
            raw_prefix=os.environ.get('COS_RAW_PREFIX', 'raw/'),
            analyzed_prefix=os.environ.get('COS_ANALYZED_PREFIX', 'analyzed/'),
            golden_prefix=os.environ.get('COS_GOLDEN_PREFIX', 'golden/'),
            candidate_prefix=os.environ.get('COS_CANDIDATE_PREFIX', 'candidate_golden/'),
            current_month_prefix=current_month
        )


@dataclass

@dataclass
class VideoDownloadConfig:
    """视频下载配置"""
    download_dir: str = "/tmp/video_analysis"
    timeout_connect: int = 10  # 连接超时（秒）
    timeout_read: int = 120  # 读取超时（秒）
    max_size_mb: int = 100  # 最大文件大小（MB）
    
    @classmethod
    def from_env(cls) -> 'VideoDownloadConfig':
        """从环境变量加载配置"""
        import os
        return cls(
            download_dir=os.environ.get('VIDEO_DOWNLOAD_DIR', '/tmp/video_analysis'),
            timeout_connect=int(os.environ.get('VIDEO_DOWNLOAD_TIMEOUT_CONNECT', '10')),
            timeout_read=int(os.environ.get('VIDEO_DOWNLOAD_TIMEOUT_READ', '120')),
            max_size_mb=int(os.environ.get('MAX_VIDEO_SIZE_MB', '100'))
        )


@dataclass
class PathConfig:
    """路径配置"""
    # 基础路径
    base_data_dir: str = "./data"
    task_data_dir: str = "./data/tasks"
    log_dir: str = "./logs"
    temp_dir: str = "./tmp"
    
    # 媒体目录
    media_inbound_dir: str = "./media/inbound"
    reports_dir: str = "./reports"
    
    # 数据库路径
    db_path: str = "./data/db/app.db"
    
    # 知识库路径
    knowledge_dir: str = "./fused_knowledge"
    
    @classmethod
    def from_env(cls) -> 'PathConfig':
        """从环境变量加载配置"""
        config = cls(
            base_data_dir=os.environ.get('BASE_DATA_DIR', './data'),
            task_data_dir=os.environ.get('TASK_DATA_DIR', './data/tasks'),
            log_dir=os.environ.get('LOG_DIR', './logs'),
            temp_dir=os.environ.get('TEMP_DIR', './tmp'),
            media_inbound_dir=os.environ.get('MEDIA_INBOUND_DIR', './media/inbound'),
            reports_dir=os.environ.get('REPORTS_DIR', './reports'),
            db_path=os.environ.get('DB_PATH', './data/db/app.db'),
            knowledge_dir=os.environ.get('KNOWLEDGE_DIR', './fused_knowledge')
        )
        
        # 确保使用绝对路径（相对于项目根目录）
        project_root = Path(__file__).parent
        config.base_data_dir = str(project_root / config.base_data_dir.lstrip('./'))
        config.task_data_dir = str(project_root / config.task_data_dir.lstrip('./'))
        config.log_dir = str(project_root / config.log_dir.lstrip('./'))
        config.temp_dir = str(project_root / config.temp_dir.lstrip('./'))
        config.media_inbound_dir = str(project_root / config.media_inbound_dir.lstrip('./'))
        config.reports_dir = str(project_root / config.reports_dir.lstrip('./'))
        config.db_path = str(project_root / config.db_path.lstrip('./'))
        config.knowledge_dir = str(project_root / config.knowledge_dir.lstrip('./'))
        
        return config
    
    def ensure_directories(self):
        """确保所有目录存在"""
        for dir_path in [self.base_data_dir, self.task_data_dir, self.log_dir, 
                        self.temp_dir, self.media_inbound_dir, self.reports_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)


@dataclass
class RuntimeConfig:
    """运行模式配置"""
    # 运行环境
    app_env: str = "dev"  # dev | prod
    debug: bool = True
    
    # 功能开关
    allow_temp_analysis_fallback: bool = False
    verbose_task_logging: bool = True
    
    # 性能配置
    max_video_size_mb: int = 50
    video_analysis_timeout: int = 120
    
    @classmethod
    def from_env(cls) -> 'RuntimeConfig':
        """从环境变量加载配置"""
        app_env = os.environ.get('APP_ENV', 'dev')
        return cls(
            app_env=app_env,
            debug=os.environ.get('DEBUG', 'true' if app_env == 'dev' else 'false').lower() in ('true', '1', 'yes'),
            allow_temp_analysis_fallback=os.environ.get('ALLOW_TEMP_ANALYSIS_FALLBACK', 'false').lower() in ('true', '1', 'yes'),
            verbose_task_logging=os.environ.get('VERBOSE_TASK_LOGGING', 'true').lower() in ('true', '1', 'yes'),
            max_video_size_mb=int(os.environ.get('MAX_VIDEO_SIZE_MB', '50')),
            video_analysis_timeout=int(os.environ.get('VIDEO_ANALYSIS_TIMEOUT', '120'))
        )
    
    def is_production(self) -> bool:
        """是否生产环境"""
        return self.app_env == 'prod'
    
    def is_development(self) -> bool:
        """是否开发环境"""
        return self.app_env == 'dev'


@dataclass
class AppConfig:
    """应用总配置"""
    model: ModelConfig
    channel: ChannelConfig
    paths: PathConfig
    runtime: RuntimeConfig
    cos: COSConfig
    
    @classmethod
    def load(cls) -> 'AppConfig':
        """加载配置（从环境变量）"""
        return cls(
            model=ModelConfig.from_env(),
            channel=ChannelConfig.from_env(),
            paths=PathConfig.from_env(),
            runtime=RuntimeConfig.from_env(),
            cos=COSConfig.from_env()
        )
    
    def initialize(self):
        """初始化配置（创建目录等）"""
        self.paths.ensure_directories()


# 全局配置实例（延迟加载）
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = AppConfig.load()
        _config.initialize()
    return _config


def reload_config() -> AppConfig:
    """重新加载配置"""
    global _config
    _config = AppConfig.load()
    _config.initialize()
    return _config


# 便捷函数
def get_model_config() -> ModelConfig:
    """获取模型配置"""
    return get_config().model


def get_channel_config() -> ChannelConfig:
    """获取渠道配置"""
    return get_config().channel


def get_path_config() -> PathConfig:
    """获取路径配置"""
    return get_config().paths


def get_runtime_config() -> RuntimeConfig:
    """获取运行配置"""
    return get_config().runtime


def get_cos_config() -> COSConfig:
    """获取 COS 配置"""
    return get_config().cos


# 测试
if __name__ == '__main__':
    print("\n" + "="*60)
    print("⚙️  统一配置模块测试")
    print("="*60 + "\n")
    
    # 加载配置
    config = AppConfig.load()
    config.initialize()
    
    # 打印配置摘要
    print("📋 配置摘要")
    print("="*60)
    print()
    
    print("🤖 模型配置")
    print(f"  视频模型：{config.model.video_model_name}")
    print(f"  文本模型：{config.model.text_model_name}")
    print(f"  分析后端：{config.model.analysis_backend}")
    print(f"  临时 fallback: {config.model.enable_temp_qwen_fallback}")
    print()
    
    print("📱 渠道配置")
    print(f"  钉钉启用：{config.channel.dingtalk_enabled}")
    print(f"  QQ 启用：{config.channel.qq_enabled}")
    print()
    
    print("📁 路径配置")
    print(f"  数据目录：{config.paths.base_data_dir}")
    print(f"  任务目录：{config.paths.task_data_dir}")
    print(f"  日志目录：{config.paths.log_dir}")
    print(f"  临时目录：{config.paths.temp_dir}")
    print()
    
    print("🔧 运行配置")
    print(f"  运行环境：{config.runtime.app_env}")
    print(f"  调试模式：{config.runtime.debug}")
    print(f"  详细日志：{config.runtime.verbose_task_logging}")
    print()
    
    print("="*60)
    print("✅ 配置加载成功")
    print("="*60 + "\n")

# ═══════════════════════════════════════════════════════════════════
# 全局常量（供其他模块直接导入）
# ═══════════════════════════════════════════════════════════════════

MODEL_PROVIDER = os.environ.get('MODEL_PROVIDER', 'qwen')
MODEL_NAME = os.environ.get('VIDEO_MODEL_NAME', 'qwen-vl-max')
