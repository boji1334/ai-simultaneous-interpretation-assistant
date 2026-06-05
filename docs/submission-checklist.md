# Submission Checklist

## Required Materials

- Public GitHub or Gitee repository.
- Root `README.md`.
- Narrated demo video link in `README.md`.

## Current Repository Evidence

- Runnable backend and frontend.
- WebSocket live subtitle demo.
- Synchronized self-written audio demo with bilingual overlay.
- Chunked microphone audio stream path.
- Automatic correction demo.
- Subtitle revision ledger.
- Glossary-assisted correction.
- Provider boundary for ASR and translation.
- Provider readiness diagnostics.
- Audio upload and microphone entry.
- Markdown and SRT export.
- After-session summary.
- Optional browser-native Chinese voice playback.
- Auditable correction timeline.
- Full fallback snapshot via `加载最终字幕`.
- Tests and CI workflow.
- PR template.
- Narrated demo video uploaded to GitHub Release.

## Before First Official Submission

1. Configure Git username and email.
2. Create a remote GitHub/Gitee repository after the official topic release.
3. Run `.\scripts\pre-submit-audit.ps1`.
4. Run `.\scripts\check.ps1`.
5. Run `.\scripts\smoke-single-service.ps1`.
6. Push the first commit.
7. Submit the repository URL within the official 24-hour window.
8. Continue later work through small PRs.

## Before Final Submission

1. Confirm all commits are inside the selected batch time window.
2. Confirm every PR has a clear title and non-empty description.
3. Run `.\scripts\pre-submit-audit.ps1`.
4. Run `.\scripts\check.ps1`.
5. Run `.\scripts\smoke-single-service.ps1`.
6. Manually verify the correction demo if the video needs a visual rehearsal.
7. Generate or record original demo audio from `assets/demo/demo-script.en.txt`.
8. Record or regenerate a narrated demo video with `python -m pip install -r scripts\demo-video-requirements.txt` and `python scripts\generate-demo-video.py`.
9. Upload the video to an accessible platform.
10. Add the video link to `README.md`.
11. Confirm README lists dependencies and original/third-party boundaries.

Current demo video:

```text
https://github.com/boji1334/ai-simultaneous-interpretation-assistant/releases/download/demo-video-v1/final-demo.mp4
```

## Suggested First PR

Title:

```text
Initialize AI simultaneous interpretation assistant MVP
```

Description:

```text
功能描述：
初始化 AI 同声传译助手 MVP，包含前后端可运行工程、WebSocket 实时字幕演示流、音频分片流式入口、自动修正演示、字幕版本轨迹、术语表、量化指标、Provider 边界与诊断、音频上传、导出、会后总结、README、PR 模板和 CI。

实现思路：
后端使用 FastAPI/Pydantic/WebSocket，前端使用 React/Vite/TypeScript。默认 Mock Provider 保证比赛演示稳定可复现；ASR 和翻译能力通过 Provider 接口解耦。核心原创逻辑包括字幕状态机、上下文滑动窗口修正引擎和术语表辅助修正策略。

测试方式：
- `.\scripts\check.ps1`
- `.\scripts\smoke-single-service.ps1`
- `.\.venv\Scripts\pytest backend`
- `cd frontend && npm run build`
- 启动后访问 `http://127.0.0.1:5173`，点击“启动实时演示”，确认出现“已修正”“注意力机制”“修正时间线”和“1480ms”。

第三方依赖与原创说明：
第三方依赖包括 FastAPI、Pydantic、uvicorn、pytest、httpx、React、Vite、TypeScript。原创部分包括产品流程、字幕状态机、修正引擎、术语表修正、可审计修正时间线、WebSocket 事件协议、Provider 架构、前端交互、导出和演示流程。
```
