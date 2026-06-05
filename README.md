# AI 同声传译助手

面向英文演讲、技术分享、国际会议和网课场景的实时 AI 同传工具。系统将单向外语音频流转换为中文内容，并通过字幕、可选语音播报、术语表和上下文回溯修正，帮助用户跟上内容节奏。

当前版本已经形成可运行 MVP：后端 FastAPI、前端 React/Vite、WebSocket 实时字幕流、音频分片流式入口、自动修正演示、术语表、量化指标、导出、会后总结、音频上传和麦克风入口均已实现。

## 比赛信息

- 比赛方向：七牛云 XEngineer 第三批次
- 议题：题目二：AI 同声传译助手
- 批次时间：2026-06-05 00:00 - 2026-06-07 23:59
- 官方核心要求：通过 AI 能力，将单向音频流实时、流畅地翻译成中文，以字幕或语音形式呈现，并具备自动修正之前识别或翻译错误的能力。
- 提交材料：公开 GitHub/Gitee 仓库、README、demo 视频。
- 过程要求：仓库需在开题后创建，议题发布后 24 小时内提交仓库地址，开发周期内保持持续 PR 和 commit 记录，所有 commit 时间戳必须落在所选批次时间内。

## 官方题目原文

题目二：AI 同声传译助手

用户经常需要观看英语（或其他外语）演讲、技术分享、国际会议或网课，请开发一款 AI 同声传译助手，帮助用户降低语言门槛，提升信息获取效率。

要求：通过 AI 能力，将单向音频流实时、流畅地翻译成中文，以字幕或语音形式呈现，帮助用户跟上内容节奏。系统需具备修正能力，能够自动纠正之前识别或翻译的错误。

本项目围绕题目中的三个关键词展开：`实时`、`中文呈现`、`自动修正`。默认演示使用可复现的 Mock Provider 保证评审稳定性，同时保留真实 ASR/翻译 Provider 接入点；demo 视频优先展示观看英文演讲或网课时的同步字幕、回溯修正、版本轨迹和量化指标。

## 核心亮点

1. 实时字幕状态机：`partial -> stable -> corrected -> final`，同时兼顾低延迟和可读稳定性。
2. 上下文回溯修正：后续语义到达后，只修正最近未锁定的字幕，避免整屏跳动。
3. 术语表辅助纠错：基于术语表和常见误译映射修复最近字幕，例如将错误翻译 `张力机制` 修正为专业术语 `注意力机制`。
4. 可插拔 Provider 架构：ASR、翻译能力与核心业务逻辑解耦，默认 Mock 稳定演示，可切换 `faster-whisper` 和 OpenAI-compatible 翻译接口。
5. 量化演示指标：首字幕延迟、修正延迟、术语命中率、最终稳定率，便于 demo 视频表达效果。
6. 赛后复盘能力：支持 Markdown/SRT 导出和会后总结，覆盖学习与会议场景的完整闭环。
7. 可选中文语音播报：使用浏览器本地 `speechSynthesis` 播报最终或已修正字幕，避免引入额外云 TTS 风险。
8. 自写 demo 素材，避免直接使用 TED、YouTube 或网课原声带来的版权风险。
9. 可审计修正时间线：记录触发原因、修正延迟、版本变化和命中术语，让“自动修正”可解释。
10. 字幕版本轨迹：开放每条字幕的版本、状态、置信度和译文变化，让评委能看到系统如何从错误走向修正。
11. Provider 配置诊断：切换真实 ASR/翻译前可检查依赖、模型路径、API Key 和环境变量配置。

## 当前功能

- 后端健康检查：`GET /health`
- 术语表接口：`GET /api/glossary`
- Provider 状态：`GET /api/providers`
- Provider 诊断：`GET /api/providers/diagnostics`
- 实时演示流：`GET /ws/demo`
- 外部视频演示流：`GET /ws/video-demo`
- 音频分片流式同传：`GET /ws/audio-stream`
- 外部视频素材：`GET /api/video-demo/source`
- 外部视频快照：`GET /api/video-demo/snapshot`
- 最终字幕：`GET /api/demo/transcript`
- 完整演示快照：`GET /api/demo/snapshot`
- 字幕导出：`GET /api/demo/export?format=markdown|srt`
- 会后总结：`GET /api/demo/summary`
- 修正记录：`GET /api/demo/corrections`
- 字幕版本轨迹：`GET /api/demo/revisions`
- 音频上传演示：`POST /api/audio/demo`
- 前端实时字幕工作台
- 外部英文网课视频播放器与双语字幕浮层：中文同传显示在上方，英文原文同步显示在下方，字幕按视频播放时间逐条出现，后文到达后再触发局部修正
- 麦克风录音入口
- 麦克风流式同传入口
- 音频/视频文件上传入口
- 修正高亮、版本号、修正前文本展示
- 修正时间线和修正原因展示
- 字幕版本轨迹展示
- 量化指标面板
- 术语表、Provider、导出和总结面板
- Provider 诊断就绪状态展示

## 快速启动

### 一键检查

```powershell
.\scripts\check.ps1
```

该脚本会安装后端依赖、运行后端测试、安装前端依赖并构建前端。

### 提交前审计

```powershell
.\scripts\pre-submit-audit.ps1
```

该脚本会检查关键文件、可疑乱码、未清理占位标记、开发端口、Git 身份、远程仓库和当前工作区状态，适合每个 PR 前运行。

### 单服务运行时验收

```powershell
.\scripts\smoke-single-service.ps1
```

该脚本会构建前端、启动 FastAPI 单服务，并自动验证首页、字幕 API、最终快照、SRT 导出、`/ws/demo` 和 `/ws/audio-stream`，结束后自动停止服务。

### 开发模式

```powershell
.\scripts\start-dev.ps1
```

访问：

```text
http://127.0.0.1:5173
```

停止服务：

```powershell
.\scripts\stop-dev.ps1
```

### 手动启动

后端：

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -e backend[dev]
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

前端：

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Vite 会把 `/api` 和 `/ws` 代理到 `http://127.0.0.1:8000`。

### 单服务部署模式

```powershell
cd frontend
npm run build
cd ..
.\.venv\Scripts\uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

访问：

```text
http://127.0.0.1:8000
```

## Demo 使用方式

1. 启动后端和前端。
2. 打开 `http://127.0.0.1:5173`。
3. 点击 `启动实时演示`。
4. 观察字幕从临时/稳定状态逐步进入最终状态。
5. 重点观察第三条字幕：系统先显示 `张力机制`，随后根据后续上下文和术语表修正为 `注意力机制`。
6. 查看右侧指标：首字幕延迟、修正延迟、术语命中率、最终稳定率。
7. 查看修正时间线，说明触发原因、版本变化和 `1480ms` 修正延迟。
8. 查看字幕版本轨迹，说明 `seg-003` 如何从 `stable/v1` 更新到 `corrected/v2`。
9. 点击 `查看 Provider`，说明当前稳定演示使用 Mock Provider，并展示 Provider 诊断结果；真实 ASR/翻译可通过环境变量切换。
10. 点击 `复制字幕`、`下载 MD` 或 `下载 SRT` 展示导出能力。
11. 点击 `生成总结` 展示摘要、关键点、关键词和修正记录。
12. 可选点击 `开启语音`，展示中文语音播报。
13. 可选点击 `开始流式同传`，展示浏览器将麦克风音频分片通过 WebSocket 推送到后端，并复用同一套字幕事件协议返回实时字幕与修正。
14. 可选通过麦克风录音或文件上传展示音频进入 Provider 边界的流程。

如果现场演示需要快速兜底，可以点击 `加载最终字幕`。该按钮会加载完整演示快照，包括最终字幕、术语表、量化指标、修正时间线和会后总结。

演示音频建议使用 `assets/demo/demo-script.en.txt` 中的自写英文文本生成或录制，避免版权风险并稳定触发修正场景。

可在 Windows 上使用系统离线语音生成 demo WAV：

```powershell
.\scripts\generate-demo-audio.ps1
```

默认输出为 `assets/demo/demo-en.wav`。该文件用于本地录制 demo 视频，可按比赛仓库体积策略决定是否提交。

如需下载公开视频素材用于本地录屏，可运行：

```powershell
.\scripts\download-demo-video.ps1
```

默认下载 Wikimedia Commons 上的 MITx 在线课程欢迎视频到 `assets/demo/external-course-demo.webm`。视频文件由 `.gitignore` 排除，仓库只保留下载脚本、来源页、授权说明和演示代码。

Demo 视频链接将在最终提交阶段更新到 README；当前仓库已提供可复现的本地演示流程、脚本和演示素材说明。

## 技术架构

```text
Audio input / Demo stream
  -> ASR Provider
  -> Translation Provider
  -> SubtitleStateManager
  -> CorrectionEngine (glossary + common mistranslation map)
  -> CorrectionTrace
  -> SubtitleRevision history
  -> FastAPI WebSocket
  -> React subtitle workspace
  -> Provider diagnostics
  -> Export / Summary / Voice playback
```

### 后端

- Python
- FastAPI
- WebSocket
- Pydantic
- pytest
- 可选 `faster-whisper`
- 可选 OpenAI-compatible 翻译接口

### 前端

- React
- Vite
- TypeScript
- WebSocket
- MediaRecorder
- Browser `speechSynthesis`

## Provider 配置

默认配置使用 Mock Provider，保证评审和 demo 视频稳定可复现，不依赖模型下载或外部 API Key。

```powershell
# 默认稳定演示
set ASR_PROVIDER=mock
set TRANSLATION_PROVIDER=mock
```

真实 ASR 可切换到本地 `faster-whisper`：

```powershell
pip install -e backend[ai]
set ASR_PROVIDER=faster_whisper
set ASR_MODEL_PATH=./models/faster-whisper-small
set ASR_DEVICE=auto
set ASR_COMPUTE_TYPE=auto
```

真实翻译可切换到 OpenAI-compatible 接口：

```powershell
set TRANSLATION_PROVIDER=openai_compatible
set TRANSLATION_API_KEY=replace-with-api-key
set TRANSLATION_MODEL=gpt-4o-mini
set TRANSLATION_BASE_URL=https://api.openai.com/v1
```

环境变量示例见 `.env.example`。

## 原创边界

### 自主实现部分

- 产品需求拆解与交互设计
- 前后端完整工程实现
- WebSocket 实时字幕事件协议
- `SubtitleStateManager` 字幕状态机
- `CorrectionEngine` 上下文回溯修正引擎
- 术语表命中、常见误译映射与局部修正策略
- 修正高亮、版本号、修正前后对比 UI
- 量化指标展示
- 修正时间线与可解释修正记录
- 字幕版本轨迹与修正账本
- Markdown/SRT 导出
- 会后总结接口与展示
- Provider 可插拔架构
- Provider 配置诊断与赛前自检接口
- 演示流程与比赛提交文档

### 第三方能力与依赖

- ASR 底层能力：Mock Provider；可选 `faster-whisper`
- 翻译底层能力：Mock Provider；可选 OpenAI-compatible API
- 后端框架：FastAPI、Pydantic、uvicorn、python-multipart、httpx
- 前端框架：React、Vite、TypeScript
- 测试与工具：pytest、GitHub Actions

第三方库仅作为基础框架或底层模型能力接入，作品核心创新点是实时字幕状态机、上下文修正引擎、术语表修正策略、工程化 Provider 架构和完整交互闭环。

## 项目结构

```text
translate_english/
  README.md
  .env.example
  .github/
    PULL_REQUEST_TEMPLATE.md
    workflows/ci.yml
  assets/demo/
  backend/
    app/
      main.py
      models.py
      providers/
      services/
      tests/
    pyproject.toml
  docs/
    architecture.md
    competition-audit.md
    demo-material.md
    demo-script.md
    deployment.md
    pr-plan.md
    submission-checklist.md
  frontend/
    src/
      main.tsx
      styles.css
      config.ts
    package.json
  scripts/
    check.ps1
    generate-demo-audio.ps1
    pre-submit-audit.ps1
    runtime_smoke.py
    smoke-single-service.ps1
    start-dev.ps1
    stop-dev.ps1
```

## 开发与 PR 规范

比赛要求持续交付，不能最后一天一次性导入全部代码。建议按小 PR 拆分：

1. 初始化 README、目录骨架、PR 模板、CI。
2. 增加后端健康检查和基础模型。
3. 增加前端工作台骨架。
4. 增加 WebSocket 演示流。
5. 增加字幕状态机。
6. 增加上下文修正引擎。
7. 增加术语表与修正高亮。
8. 增加音频上传和麦克风入口。
9. 增加导出与会后总结。
10. 增加真实 ASR/翻译 Provider。
11. 完善测试、部署文档和 demo 视频链接。

每个 PR 描述必须包含：

- 功能描述：本 PR 做了什么，如何使用。
- 实现思路：关键技术选型和核心逻辑。
- 测试方式：如何验证功能正常。
- 第三方依赖与原创说明：新增依赖、模型、API 或复用代码来源。

## 验证记录

当前本地验证命令：

```powershell
.\scripts\check.ps1
.\scripts\smoke-single-service.ps1
.\scripts\pre-submit-audit.ps1
```

当前验证结果：

- 后端测试：19 passed
- 前端构建：passed
- 单服务部署：已通过首页、API、WebSocket 演示流、音频分片流和导出验收
- 开发模式：支持 Vite 代理 `/api` 和 `/ws`

## 官方要求核对

| 官方要求 | 当前状态 |
| --- | --- |
| 符合题目方向 | 已覆盖单向音频流、实时中文字幕、可选语音、自动修正 |
| 作品完整度 | 已有可运行前后端、实时字幕、修正、修正时间线、术语表、导出、总结 |
| 创新性 | 字幕状态机、滑动窗口修正、术语表辅助修正、可审计修正时间线、字幕版本轨迹、量化指标 |
| 工程质量 | 前后端分层、Provider 架构、测试、CI、脚本、文档 |
| README | 已提供启动、架构、依赖、原创边界和比赛规则说明 |
| Demo 视频 | 最终提交前录制并补链接 |
| 持续 PR/commit | 需要推送远程仓库后按小 PR 继续交付 |
| commit 时间戳 | 需要确保所有提交在 2026-06-05 00:00 至 2026-06-07 23:59 内 |

## 下一步

1. 配置 Git 用户名和邮箱。
2. 创建开题后的 GitHub/Gitee 空仓库。
3. 推送首个 commit 并创建第一个 PR。
4. 在官方 24 小时窗口内提交仓库地址。
5. 后续功能继续按小 PR 合并。
6. 录制 demo 视频并将链接写入 README。
