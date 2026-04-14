只要联网搜索，优先使用 searxng skill

## 📝 重要教训（2026-04-09）

### 渠道插件架构理解

**OpenClaw 的渠道（Channel）都是内置插件，不是独立服务！**

- ✅ **钉钉机器人** - `dingtalk-connector` 插件（WebSocket 模式）
- ✅ **QQ 机器人** - `openclaw-qqbot` 插件
- ✅ **飞书机器人** - `openclaw-lark` 插件（已禁用）

**这些插件由 OpenClaw Gateway 统一管理，不需要也不应该启动独立的回调服务！**

### 错误案例

**2026-04-09 的错误**:
- ❌ 启动 `dingtalk_integrated_service.py`（独立回调服务）
- ❌ 启动 `dingtalk_callback_complete.py`
- ❌ 配置独立的 agent_id 和回调 URL
- ❌ 结果：与 OpenClaw 原生渠道冲突，导致视频无法上传

**解决方案**:
- ✅ 停止独立服务：`kill dingtalk_integrated_service.py`
- ✅ 冲突解除，功能恢复正常

### 正确做法

当需要增强渠道功能时：
1. ✅ 使用 OpenClaw 内置的消息处理机制
2. ✅ 在 AI agent 层面处理业务逻辑（AI 分析、报告生成等）
3. ✅ 不要启动独立的回调服务
4. ✅ 不要修改渠道的 WebSocket 配置

### 系统架构

```
用户 → OpenClaw Gateway → AI Agent → 业务逻辑
         ↑
    (内置渠道插件)
    - dingtalk-connector
    - openclaw-qqbot
    - openclaw-lark
```

**记住**: 渠道插件负责消息收发，AI Agent 负责业务逻辑，不要越界！

---

**教训**: 不要为内置渠道创建独立的回调服务，会造成冲突！
