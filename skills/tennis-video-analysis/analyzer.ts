/**
 * 网球视频分析器
 * 下载视频 → 上传 COS → Qwen API 分析
 */

import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { v4 as uuidv4 } from 'uuid';

const COS = require('cos-nodejs-sdk-v5');

export class TennisAnalyzer {
  private cos: any;
  private qwenApiKey: string;
  private qwenModel: string;

  constructor() {
    // COS 配置
    this.cos = new COS({
      SecretId: process.env.COS_SECRET_ID || 'AKIDaHuZDoEKB5qOipqgJkx2uZ1HLPFvXxBC',
      SecretKey: process.env.COS_SECRET_KEY || 'sZ3KOG5nIcUaifjjbIwhIgqqfKpAKJ6r',
    });

    // Qwen 配置
    this.qwenApiKey = process.env.DASHSCOPE_API_KEY || 'sk-88532d38dbe04d3a9b73c921ce25794c';
    this.qwenModel = 'qwen-max';
  }

  async analyze(videoUrl: string): Promise<any> {
    console.log('[Analyzer] 开始分析视频:', videoUrl);

    // 步骤 1: 下载视频
    const localPath = await this.downloadVideo(videoUrl);
    console.log('[Analyzer] 视频下载完成:', localPath);

    // 步骤 2: 上传到 COS
    const cosKey = await this.uploadToCos(localPath);
    console.log('[Analyzer] 视频上传 COS 完成:', cosKey);

    // 步骤 3: 生成预签名 URL
    const presignedUrl = await this.generatePresignedUrl(cosKey);
    console.log('[Analyzer] 预签名 URL:', presignedUrl);

    // 步骤 4: 调用 Qwen API
    const analysis = await this.callQwenApi(presignedUrl);
    console.log('[Analyzer] Qwen 分析完成');

    // 清理临时文件
    fs.unlinkSync(localPath);

    return analysis;
  }

  private async downloadVideo(url: string): Promise<string> {
    const tempDir = os.tmpdir();
    const filename = `tennis_${uuidv4()}.mp4`;
    const filePath = path.join(tempDir, filename);

    const response = await axios.get(url, {
      responseType: 'stream',
      timeout: 60000,
    });

    const writer = fs.createWriteStream(filePath);
    response.data.pipe(writer);

    return new Promise((resolve, reject) => {
      writer.on('finish', () => resolve(filePath));
      writer.on('error', reject);
    });
  }

  private async uploadToCos(filePath: string): Promise<string> {
    const date = new Date().toISOString().split('T')[0];
    const filename = path.basename(filePath);
    const key = `private-ai-learning/raw_videos/${date}/${filename}`;

    return new Promise((resolve, reject) => {
      this.cos.putObject({
        Bucket: 'tennis-ai-1411340868',
        Region: 'ap-shanghai',
        Key: key,
        Body: fs.createReadStream(filePath),
      }, (err: any, data: any) => {
        if (err) reject(err);
        else resolve(key);
      });
    });
  }

  private async generatePresignedUrl(key: string): Promise<string> {
    return new Promise((resolve, reject) => {
      this.cos.getObjectUrl({
        Bucket: 'tennis-ai-1411340868',
        Region: 'ap-shanghai',
        Key: key,
        Expires: 3600, // 1 小时
      }, (err: any, data: any) => {
        if (err) reject(err);
        else resolve(data.Url);
      });
    });
  }

  private async callQwenApi(videoUrl: string): Promise<any> {
    const systemPrompt = `你是一个专业的网球发球分析系统。请严格按照"三步分析法"分析视频：
1. 逐帧观察：描述看到的动作事实
2. 标准对照：与杨超/灵犀/Yellow 教练标准比对
3. 输出 JSON：基于前两步推导

NTRP 定级标准：
- 2.0 级：动作不完整，膝盖几乎不弯（160 度以上）
- 3.0 级：框架完整但执行一般，膝盖轻微弯曲（140-160 度）
- 3.5 级：框架流畅，有一定蓄力（120-140 度）
- 4.0 级：流畅连贯，膝盖明显深蹲（90-120 度）
- 4.5 级：高度流畅，腿部蹬地发力明显
- 5.0 级：教科书标准，完整动力链，击球腾空

只输出 JSON 格式。`;

    const response = await axios.post(
      'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
      {
        model: this.qwenModel,
        messages: [
          { role: 'system', content: systemPrompt },
          {
            role: 'user',
            content: [
              { type: 'video_url', video_url: { url: videoUrl } },
              { type: 'text', text: '请分析这段网球发球视频，只输出 JSON。' }
            ]
          }
        ],
        max_tokens: 6000,
        temperature: 1,
      },
      {
        headers: {
          'Authorization': `Bearer ${this.qwenApiKey}`,
          'Content-Type': 'application/json',
        },
        timeout: 300000, // 5 分钟
      }
    );

    const content = response.data.choices[0].message.content;
    return this.parseJson(content);
  }

  private parseJson(content: string): any {
    // 提取 JSON
    const match = content.match(/\{[\s\S]*\}/);
    if (match) {
      return JSON.parse(match[0]);
    }
    return JSON.parse(content);
  }
}
