#!/usr/bin/env node
/**
 * 网球视频分析 Skill - 主入口
 * 自动处理 QQ/钉钉收到的网球发球视频
 */

import { Skill } from '@openclaw/core';
import { TennisAnalyzer } from './analyzer.js';

export default class TennisVideoAnalysisSkill extends Skill {
  private analyzer: TennisAnalyzer;

  constructor() {
    super({
      name: 'tennis-video-analysis',
      version: '1.0.0',
      description: '网球发球视频 AI 分析',
    });

    this.analyzer = new TennisAnalyzer();
  }

  async onMessage(event: any) {
    const { channel, message } = event;

    // 只处理 QQ 和钉钉
    if (!['qqbot', 'dingtalk-connector'].includes(channel)) {
      return;
    }

    // 检查是否是视频消息
    const video = message.attachments?.find((a: any) => a.type === 'video');
    if (!video) {
      return;
    }

    console.log(`[TennisSkill] 收到视频消息：channel=${channel}`);

    // 回复：正在分析
    await this.sendText(event, '✅ 视频已收到，正在分析中...（约 1-2 分钟）');

    try {
      // 分析视频
      const result = await this.analyzer.analyze(video.url);

      // 发送报告
      const report = this.formatReport(result);
      await this.sendText(event, report);

    } catch (error) {
      console.error('[TennisSkill] 分析失败:', error);
      await this.sendText(event, '❌ 分析失败，请重试');
    }
  }

  private formatReport(result: any): string {
    const { ntrp_level, ntrp_level_name, confidence, overall_score, key_issues, training_plan } = result;

    let text = `🎾 网球发球分析报告\n\n`;
    text += `🏆 NTRP 等级：${ntrp_level} (${ntrp_level_name})\n`;
    text += `📊 置信度：${(confidence * 100).toFixed(0)}%\n`;
    text += `💯 综合评分：${overall_score}/100\n\n`;

    if (key_issues && key_issues.length > 0) {
      text += `⚠️ 关键问题:\n`;
      key_issues.slice(0, 3).forEach((issue: any) => {
        const icon = issue.severity === 'high' ? '🔴' : issue.severity === 'medium' ? '🟡' : '🟢';
        text += `${icon} ${issue.issue}\n`;
      });
      text += `\n`;
    }

    if (training_plan && training_plan.length > 0) {
      text += `💡 训练建议:\n`;
      training_plan.slice(0, 3).forEach((item: string, i: number) => {
        text += `${i + 1}. ${item}\n`;
      });
    }

    return text;
  }

  private async sendText(event: any, text: string) {
    // 使用 OpenClaw 的消息发送 API
    await this.context.send({
      channel: event.channel,
      target: event.target,
      message: text,
    });
  }
}
