# PR Plan

Each PR should implement one small, reviewable change and keep the main branch runnable.

## Suggested PR Sequence

1. Project initialization and runnable skeleton.
2. Subtitle event models and WebSocket demo stream.
3. React live subtitle workspace.
4. Correction highlight and glossary panel.
5. Metrics cards and export preview.
6. Backend tests for health, glossary, transcript, and WebSocket stream.
7. Documentation polish and demo script.
8. `faster-whisper` ASR provider.
9. Translation provider.
10. File upload or microphone input.
11. Optional TTS playback.

## PR Description Template

- 功能描述：说明该 PR 新增或修改了什么。
- 实现思路：说明核心逻辑和技术选型。
- 测试方式：列出命令和手动验证步骤。
- 第三方依赖与原创说明：说明新增依赖、模型或复用代码来源。

