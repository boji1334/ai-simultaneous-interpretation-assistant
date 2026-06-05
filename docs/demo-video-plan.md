# Demo Video Plan

Use this as a 3 to 5 minute narrated video outline. The goal is to show product value first, then prove the engineering quality.

## Recording Setup

1. Run `.\scripts\check.ps1` once before recording.
2. The default synchronized demo audio is already included at `assets/demo/demo-en.wav`. If it needs to be regenerated on Windows:

```powershell
.\scripts\generate-demo-audio.ps1
```

3. Optionally download the public online-course video only as secondary material:

```powershell
.\scripts\download-demo-video.ps1
```

4. Start single-service mode:

```powershell
.\scripts\smoke-single-service.ps1
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

5. Open:

```text
http://127.0.0.1:8000
```

## Video Flow

1. Opening: explain that the project targets English talks, tech sharing, meetings, and online courses.
2. Click `查看 Provider`: explain the default stable Mock Provider and replaceable `faster-whisper` / cloud translation boundary.
3. Click `启动实时演示`: show subtitles streaming in order.
4. Pause on the correction: show `张力机制 -> 注意力机制`.
5. Show `修正时间线`: explain trigger, reason, `1480ms`, and `v1 -> v2`.
6. Click `加载同步素材`, then `启动同步同传`: show the self-written English audio synchronized with Chinese interpretation above and English source text below.
7. Pause on the media correction: show `张力机制 -> 注意力机制` triggered by the later `attention mechanism` context.
8. Show source card: mention the material is self-written/generated for the competition, so timing and copyright are both controlled.
9. Show metrics: first subtitle latency, correction latency, glossary hit rate, final stability rate.
10. Show glossary: explain why `attention mechanism` stays consistent.
11. Click `生成总结`: show summary, key points, terms, and correction notes.
12. Click `下载 MD` or `下载 SRT`: show export capability.
13. Click `加载最终字幕`: explain this is a fallback snapshot for stable review/demo.
14. Closing: mention tests, CI, PR records, original boundaries, and legal demo material.

## Suggested Narration

```text
大家好，这是我们的 AI 同声传译助手，面向英文技术分享、国际会议和网课场景。它不是简单地把 ASR 和翻译串起来，而是在实时字幕里引入了状态机和上下文回溯修正。

这里可以看到 Provider 状态。当前演示默认使用 Mock Provider 保证比赛视频和评审复现稳定；真实 ASR 和翻译能力通过 Provider 边界替换，例如本地 faster-whisper 和 OpenAI-compatible 翻译接口。

现在启动实时演示。字幕会从临时、稳定、已修正到最终状态流转。重点看第三条，系统一开始把 tension mechanism 翻成张力机制，但后续上下文出现 attention mechanism 后，系统会回溯修正为注意力机制。

右侧的修正时间线记录了为什么修、修正延迟、版本变化和命中的术语。这里可以看到修正延迟是 1480 毫秒，版本从 v1 更新到 v2。这也是本作品区别于普通翻译工具的核心创新点。

接下来切到同步素材同传。这里使用的是我们自写英文脚本生成的 TTS 音频，系统在播放器上叠加双语字幕：中文同传在上方，英文原文在下方，方便评委对照“说了什么”和“翻成什么”。相比直接使用公开视频，这个主 demo 的音频、英文原文和中文翻译时间轴完全可控，不会出现音频和字幕错位。可以看到系统先把 tension mechanism 译成张力机制，后续上下文出现 attention mechanism 后，字幕回溯修正为注意力机制，并保留修正前文本、版本变化和修正原因。

下方还有术语表、量化指标、字幕导出和会后总结。最终字幕可以导出为 Markdown 或 SRT，便于课后复盘或制作字幕。

如果现场演示需要快速复现，可以点击加载最终字幕，系统会加载完整演示快照，包括最终字幕、术语表、指标、修正时间线和总结。

工程上，项目采用 React/Vite/TypeScript 和 FastAPI/WebSocket，核心原创部分包括字幕状态机、滑动窗口修正引擎、术语表辅助修正、可审计修正时间线和 Provider 架构。README 中也列明了第三方依赖和原创边界。
```

## Must Capture

- `已修正`
- `注意力机制`
- `修正时间线`
- `1480ms`
- `v1 -> v2`
- `attention mechanism`
- `同步素材同传`
- 中文同传在上方，英文原文在下方
- `实时 AI 同声传译演示总结`
- Export buttons
- Provider panel
- Fallback snapshot via `加载最终字幕`
