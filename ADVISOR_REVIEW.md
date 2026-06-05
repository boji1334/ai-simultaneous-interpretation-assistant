# 导师审阅说明

这份文档用于给导师快速判断项目是否符合题目方向、是否值得继续打磨，以及最终提交前还应注意什么。它放在仓库根目录，方便打开仓库后直接访问。

## 快速入口

- 仓库地址：https://github.com/boji1334/ai-simultaneous-interpretation-assistant
- Demo 视频：https://github.com/boji1334/ai-simultaneous-interpretation-assistant/releases/download/demo-video-v1/final-demo.mp4
- README：[README.md](README.md)
- 比赛规则核对：[docs/competition-audit.md](docs/competition-audit.md)
- 最终提交清单：[docs/submission-checklist.md](docs/submission-checklist.md)

## 项目一句话

本项目是面向英文演讲、技术分享、国际会议和网课场景的 AI 同声传译助手。系统将单向英文音频流实时翻译成中文字幕，并在后续上下文到达后自动回溯修正之前的识别或翻译错误。

## 导师建议重点看什么

1. 题目贴合度：是否清楚回应了“实时、中文呈现、自动修正”三个要求。
2. 核心创新点：`partial -> stable -> corrected -> final` 字幕状态机、上下文滑动窗口修正、术语表辅助纠错、版本轨迹和修正时间线。
3. Demo 表达：视频中是否能清楚看到 `张力机制 -> 注意力机制` 的修正瞬间，以及为什么这是题目要求的核心。
4. 工程质量：FastAPI + React/Vite 前后端分层、WebSocket 事件流、Provider 可插拔、测试/CI/冒烟脚本是否足够清晰。
5. 提交规范：PR 是否拆分合理，描述是否完整，README 是否列明依赖和原创边界。

## 当前已完成内容

- 实时字幕演示流。
- 同步自写英文音频素材，中文字幕在英文原文上方同步显示。
- 自动回溯修正：先显示错误译文 `张力机制`，后续上下文出现后修正为 `注意力机制`。
- 修正时间线：记录触发原因、修正延迟、版本变化和命中术语。
- 字幕版本轨迹：展示每条字幕从临时、稳定、已修正到最终状态的变化。
- 术语表、量化指标、Markdown/SRT 导出、会后总结。
- 音频上传、麦克风录音入口、麦克风分片流式入口。
- Provider 架构：默认 Mock 保证评审复现，可切换 faster-whisper 和 OpenAI-compatible 翻译接口。
- Demo 视频已上传，README 已列明视频链接、依赖和原创边界。
- 后端测试、前端构建、单服务冒烟和提交前审计均已通过。

## 关于 Mock Provider 的解释

当前 Demo 默认使用 Mock Provider，是为了保证评审环境下稳定复现“实时字幕流”和“自动修正”两个核心交互。项目并不是把 Mock 当成最终能力，而是把 ASR 和翻译能力抽象成 Provider：

- ASR 默认 `mock`，可切换到 `faster_whisper`。
- 翻译默认 `mock`，可切换到 OpenAI-compatible API。
- `/api/providers/diagnostics` 和前端 Provider 面板会显示当前配置、依赖和就绪状态。

建议 Demo 讲解中主动说明一句：当前演示使用 Mock Provider 保证稳定可复现，真实 faster-whisper 和翻译 API 可通过环境变量切换，核心原创在流式字幕状态机、上下文修正引擎和产品闭环。

## 本地验收命令

```powershell
.\scripts\pre-submit-audit.ps1
.\scripts\check.ps1
.\scripts\smoke-single-service.ps1
```

单服务验收通过后，可访问：

```text
http://127.0.0.1:8000
```

开发模式可访问：

```text
http://127.0.0.1:5173
```

## Demo 视频观看重点

1. 开头说明题目场景和核心要求。
2. 架构页说明 Provider 可替换，原创逻辑在状态机和修正引擎。
3. 实时字幕页说明字幕不是一次性加载，而是按事件流逐条出现。
4. 修正能力页重点看 `张力机制 -> 注意力机制`。
5. 同步素材页说明中文字幕在上、英文原文在下，字幕由播放时间驱动。
6. 演示闭环页说明修正不是静默覆盖，而是可解释、可审计、可复盘。
7. 工程质量页说明测试、CI、单服务冒烟和 PR 记录。

## 需要导师给意见的问题

1. 当前创新点是否足够突出，是否还需要进一步强调“同声传译员听到后文再修前文”的类比？
2. 默认使用 Mock Provider 保证复现，同时保留真实 ASR/翻译 Provider 边界，这个表述是否足够避免“只套 API”的误解？
3. Demo 视频是否需要再上传到 B 站或网盘作为备用链接？
4. 视频旁白是否建议改成真人录音，还是当前神经网络中文旁白已经足够？
5. 最终提交前是否需要补一页更短的项目说明，专门给评委快速扫读？

## 当前风险判断

- 阻塞风险：暂未发现。
- 最大非代码风险：公开视频目前托管在 GitHub Release。建议最终提交前再手动备份到 B 站或网盘，README 中保留备用链接。
- 最大展示风险：真人录音旁白会比 TTS 更有说服力；当前视频已使用更自然的神经网络中文旁白，不是提交阻塞项。
- 最大评审误解风险：评委可能误以为 Mock Provider 代表没有 AI 能力。README 已说明 Provider 边界和可切换真实能力，Demo 中也应主动解释“核心原创在流式状态机、修正引擎和产品闭环”。
