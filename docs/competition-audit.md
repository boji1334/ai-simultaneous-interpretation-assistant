# Competition Audit

This document maps the current project to the official XEngineer submission and review rules. Keep it updated before every major PR and before final submission.

## Review Mapping

| Review Dimension | Weight | Current Evidence | Remaining Work |
| --- | ---: | --- | --- |
| Product completeness and innovation | 40% | Runnable live subtitle workspace, synchronized self-written audio demo, WebSocket streams, chunked microphone stream path, correction highlight, correction timeline, subtitle revision ledger, glossary, metrics, export, summary, optional voice playback | No blocker; optional final UI rehearsal before submission |
| Development process and quality | 40% | FastAPI/React split, Provider interfaces, Provider diagnostics, state manager, correction engine, tests, CI workflow, PR template, scripts, repeated small PRs | No blocker; keep future changes as small PRs |
| Demo and presentation | 20% | Narrated PPT-style demo video, natural Chinese neural narration, deterministic correction moment, README video link, GitHub Release asset, Bilibili backup link | No blocker; manually confirm both video links before final submission |

## Official Requirement Checklist

| Official Requirement | Status | Evidence |
| --- | --- | --- |
| One-way audio stream interpretation | Implemented for demo/upload/stream path | `/ws/audio-stream`, `POST /api/audio/demo`, microphone/file upload UI, Provider boundary |
| Real-time and smooth Chinese output | Implemented | `/ws/demo`, React subtitle list, caption bar |
| Subtitle or voice presentation | Implemented | Subtitle UI and browser `speechSynthesis` toggle |
| Automatic correction of previous ASR/translation errors | Implemented | Correction from `张力机制` to `注意力机制`; correction trace; subtitle revision ledger; glossary-driven `CorrectionEngine` tests |
| README document | Implemented | Root `README.md` |
| Public GitHub/Gitee repository | Implemented | `https://github.com/boji1334/ai-simultaneous-interpretation-assistant` |
| Demo video | Implemented | GitHub Release video and Bilibili backup link listed in README |
| Continuous PR and commit history | Implemented | Multiple merged PRs with scoped titles and descriptions |
| Commit timestamps inside selected batch | Implemented so far | Current commits are inside `2026-06-05 00:00 - 2026-06-07 23:59`; keep future commits inside the same window |
| Third-party dependencies listed | Implemented | README original boundary and dependency sections |
| Third-party Provider readiness visible | Implemented | `/api/providers/diagnostics`, Provider panel diagnostics |
| PR descriptions non-empty and accurate | Implemented | PR template plus actual PR descriptions with function, implementation, and tests |

## Invalid Submission Risk Controls

- Keep all future commits inside the third batch time window.
- Keep PR descriptions non-empty and aligned with the actual code changes.
- Keep future changes scoped to one feature or one documentation fix per PR.
- Keep dependency and Provider disclosure in README.
- Do not use copyrighted TED/YouTube audio directly in the demo. The main demo uses self-written text and generated TTS audio.
- Avoid final-day bulk imports; continue with small PRs if any further work is needed.

## Current PR Evidence

- #1: MVP implementation.
- #2: Official prompt and video material policy alignment.
- #3-#9: Video/material/synchronized caption iteration.
- #10: Final demo video link.
- #11: PPT-style demo video layout polish.
- #12: Natural neural narration upgrade.
- #13: Demo video generation dependency hardening.
- Additional review packet: mentor handoff guide and final audit refresh.

These PRs show a continuous engineering trail rather than a single final bulk import.

## Verification Evidence

Latest local verification commands:

```powershell
.\scripts\pre-submit-audit.ps1
.\scripts\check.ps1
.\scripts\smoke-single-service.ps1
```

Latest verified coverage:

- Backend tests: 26 passed.
- Frontend production build: passed.
- Single-service smoke: passed for home page, APIs, WebSocket demo stream, video demo stream, audio-stream path, and export.
- Demo video generation dependencies: documented in `scripts/demo-video-requirements.txt`.

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

## Final Manual Checks

1. Open the GitHub Release video link and confirm it plays.
2. Open the Bilibili backup link and confirm it plays.
3. Submit the repository URL and README demo video link before the official deadline.
