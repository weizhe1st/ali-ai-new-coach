# 🎾 网球视频分析 Skill

自动处理 QQ/钉钉机器人收到的网球发球视频，进行 AI 分析并返回报告。

## 功能

- ✅ 监听 QQ/钉钉收到的视频消息
- ✅ 下载视频并上传到腾讯 COS
- ✅ 调用 Qwen API 进行视频分析
- ✅ 返回 NTRP 等级和训练建议

## 配置

在 `~/.openclaw/openclaw.json` 中添加：

```json
{
  "skills": {
    "tennis-video-analysis": {
      "enabled": true,
      "cos": {
        "secret_id": "AKIDaHuZDoEKB5qOipqgJkx2uZ1HLPFvXxBC",
        "secret_key": "sZ3KOG5nIcUaifjjbIwhIgqqfKpAKJ6r",
        "bucket": "tennis-ai-1411340868",
        "region": "ap-shanghai"
      },
      "qwen": {
        "api_key": "sk-88532d38dbe04d3a9b73c921ce25794c",
        "model": "qwen-max"
      }
    }
  }
}
```

## 使用方法

**自动触发：**
- 在 QQ/钉钉中发送网球发球视频给机器人
- 机器人自动分析并返回报告

**手动触发：**
```bash
openclaw skill tennis-video-analysis analyze --video /path/to/video.mp4
```

## 输出示例

```
🎾 网球发球分析报告

🏆 NTRP 等级：3.0 (基础级)
📊 置信度：75%
💯 综合评分：55/100

⚠️ 关键问题:
🔴 膝盖蓄力严重不足（约 150 度）
🟡 抛球方向偏向身体内侧
🟢 旋内动作幅度不足

💡 训练建议:
1. 优先改善膝盖蓄力：对镜子练习奖杯姿势
2. 抛球稳定性专项：每天 50 次单独抛球练习
3. 旋内专项：握短拍练习旋内击球
```

## 文件结构

```
tennis-video-analysis/
├── SKILL.md              # 本文件
├── index.ts              # 主入口
├── analyzer.ts           # 分析逻辑
├── cos-uploader.ts       # COS 上传
└── package.json          # 依赖
```

## 依赖

- Node.js >= 18
- @openclaw/core
- qcloud-cos-sdk
- axios

## 许可证

MIT
