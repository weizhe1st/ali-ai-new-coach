# 项目当前状态

**最后更新**：2026-04-17（bot-driven 归档后）

## 唯一生产入口

```bash
nohup python3.8 auto_analyze_service.py > logs/auto_analyze.log 2>&1 &
```

守护进程每 60 秒扫描 `MEDIA_DIR`（由 OpenClaw 落地用户上传的视频），发现新视频则调用 `complete_analysis_service.analyze_video_complete()`，结果通过 OpenClaw runtime 注入的 `message.send()` 推送到钉钉。

## 生产代码闭包（13 个文件）

```
auto_analyze_service.py # 主循环 + 扫描 + 任务调度
auto_analyze_db.py # DB 层（video_files / analysis_tasks / message_logs）
complete_analysis_service.py # 分析内核（COS 上传 → Qwen-VL → 解析）
complete_report_generator.py # 报告生成器
report_generation_integration.py # 知识库整合 + 报告 JSON 组装
qwen_client.py # Qwen-VL 统一客户端
core.py # SYSTEM_PROMPT / 质量检查 / 响应校验
mediapipe_helper.py # MediaPipe 辅助量化（可选）
analysis_normalizer.py # 结果规范化
analysis_repository.py # 另一个 DB 层（xiaolongxia_learning.db）
analysis_result_saver.py # analysis_results.json 写入
cos_uploader.py # 腾讯云 COS 客户端
config.py # 统一配置
```

## 已知遗留问题（见 review 报告）

- **P0-1** 密钥明文散落在多个文件（归档后仅剩 `.env`，但仍需轮换）
- **P0-3** 两个 SQLite DB + 一个 JSON 文件作为事实来源互不同步
- **P1-1** 钉钉推送 target 硬编码为单一用户
- **P1-2** `process_task` 状态转换为乐观假设
- **P1-3** 报告发送失败被静默吞掉
- **P1-4** `from message import send` 是 OpenClaw runtime 注入
- **P1-5** MediaPipe 模型文件 `pose_landmarker_lite.task` 已移出根目录，`mediapipe_helper.py` 需要改为从 `models_bin/` 加载或按需下载

## 归档目录

`archive_bot_driven_20260417/` —— 2026-04-17 从生产代码中剥离的 bot-driven 幽灵架构（adapters/router/task_executor/analysis_service/reply_builder/sample_archive_service/knowledge_gold_analyzer 等约 5000 行），保留供查阅。
