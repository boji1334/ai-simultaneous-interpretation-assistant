# Competition Audit

This document maps the current project to the official XEngineer submission and review rules. Keep it updated before every major PR and before final submission.

## Review Mapping

| Review Dimension | Weight | Current Evidence | Remaining Work |
| --- | ---: | --- | --- |
| Product completeness and innovation | 40% | Runnable live subtitle workspace, WebSocket stream, chunked microphone stream path, correction highlight, correction timeline, subtitle revision ledger, glossary, metrics, export, summary, optional voice playback | Record final demo video and polish scenario script |
| Development process and quality | 40% | FastAPI/React split, Provider interfaces, Provider diagnostics, state manager, correction engine, tests, CI workflow, PR template, scripts | Push to remote, create small PRs, keep commit timestamps inside batch window |
| Demo and presentation | 20% | `docs/demo-script.md`, deterministic correction moment, export and summary flows | Upload narrated demo video and put link in README |

## Official Requirement Checklist

| Official Requirement | Status | Evidence |
| --- | --- | --- |
| One-way audio stream interpretation | Implemented for demo/upload/stream path | `/ws/audio-stream`, `POST /api/audio/demo`, microphone/file upload UI, Provider boundary |
| Real-time and smooth Chinese output | Implemented | `/ws/demo`, React subtitle list, caption bar |
| Subtitle or voice presentation | Implemented | Subtitle UI and browser `speechSynthesis` toggle |
| Automatic correction of previous ASR/translation errors | Implemented | Correction from `张力机制` to `注意力机制`; correction trace; subtitle revision ledger; glossary-driven `CorrectionEngine` tests |
| README document | Implemented | Root `README.md` |
| Public GitHub/Gitee repository | Pending external setup | Need remote URL from team |
| Demo video | Pending final recording | Add URL to README before final submission |
| Continuous PR and commit history | Pending remote workflow | Do not import all code at the end |
| Commit timestamps inside selected batch | Pending commits | Commit only inside `2026-06-05 00:00 - 2026-06-07 23:59` |
| Third-party dependencies listed | Implemented | README original boundary and dependency sections |
| Third-party Provider readiness visible | Implemented | `/api/providers/diagnostics`, Provider panel diagnostics |
| PR descriptions non-empty and accurate | Prepared | `.github/PULL_REQUEST_TEMPLATE.md` |

## Invalid Submission Risk Controls

- Do not push commits outside the third batch time window.
- Do not leave PR descriptions blank.
- Do not merge unrelated changes into one large PR.
- Do not omit dependency or Provider disclosure from README.
- Do not use copyrighted TED/YouTube audio directly in the demo. Use self-written text or generated TTS audio.
- Do not rely only on a final-day bulk import. Continue with small PRs after the initial commit.

## First PR Recommendation

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
- `.\.venv\Scripts\pytest backend`
- `cd frontend && npm run build`
- 启动后访问 `http://127.0.0.1:5173`，点击“启动实时演示”，确认出现“已修正”“注意力机制”“修正时间线”和“1480ms”。

第三方依赖与原创说明：
第三方依赖包括 FastAPI、Pydantic、uvicorn、pytest、httpx、React、Vite、TypeScript。原创部分包括产品流程、字幕状态机、修正引擎、术语表修正、可审计修正时间线、WebSocket 事件协议、Provider 架构、前端交互、导出和演示流程。
```

## Demo Video Must Show

1. Start the app and open the workspace.
2. Show live subtitle streaming.
3. Pause on the correction moment from `张力机制` to `注意力机制`.
4. Explain the correction timeline: trigger, reason, latency, and version change.
5. Explain `partial -> stable -> corrected -> final`.
6. Show glossary and metrics.
7. Show Provider status, diagnostics, and original/third-party boundary.
8. Show subtitle revision history for `seg-003`.
9. Show export and summary.
10. Mention test/build verification.
