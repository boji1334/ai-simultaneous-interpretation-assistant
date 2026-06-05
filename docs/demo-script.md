# Demo Script

## Opening

This project is an AI simultaneous interpretation assistant for English talks, technical sharing, international meetings, and online courses. The core challenge is not only translation, but balancing low latency with later correction.

## Steps

1. Start the backend and frontend.
2. Open `http://127.0.0.1:5173`.
3. Click `启动实时演示`.
4. Explain that subtitles are streamed through WebSocket.
5. Point out the subtitle states:
   - `临时`: fast low-latency subtitle.
   - `稳定`: readable but still correctable subtitle.
   - `已修正`: updated after later context arrives.
   - `最终`: locked subtitle for transcript export.
6. Pause at the correction moment:
   - Initial translation: `这个模型使用张力机制来判断哪些词更重要。`
   - Corrected translation: `这个模型使用注意力机制来判断哪些词更重要。`
7. Show the correction timeline and explain the trigger, reason, `1480ms` correction latency, and `v1 -> v2` version update.
8. Click `启动视频同传`.
9. Explain that this panel represents the online-course / talk-watching scenario from the official prompt.
10. Point out the video subtitle overlay:
   - Initial translation: `欢迎来到 6.002x：电路和电子产品。`
   - Corrected translation: `欢迎来到 6.002x：电路与电子学。`
11. Show the video source card and mention the Creative Commons license and attribution.
12. Show the glossary panel and explain that `attention mechanism` maps to `注意力机制`, while `Circuits and Electronics` maps to `电路与电子学`.
13. Click `查看 Provider` to explain the stable Mock Provider and the future `faster-whisper` / cloud translation boundary.
14. Optionally record microphone audio or upload an audio/video file from the media entry panel and explain that this route already goes through the provider boundary.
15. Show metrics:
    - first subtitle latency
    - correction latency
    - glossary hit rate
    - final stability rate
16. Click `复制字幕`, `下载 MD`, or `下载 SRT` and show the bilingual transcript export.
17. Click `生成总结` and show the summary, key points, keywords, and correction notes.
18. Optionally click `开启语音` and explain that final/corrected Chinese subtitles can be spoken by the browser.
19. If the live stream needs a fallback, click `加载最终字幕` and show that it loads the full snapshot: final subtitles, glossary, metrics, correction timeline, and summary.

## Closing

The original implementation focuses on the product logic: subtitle state machine, correction engine, glossary-assisted repair, WebSocket event protocol, video subtitle overlay, UI states, export flow, and after-session summary. ASR and translation providers are replaceable bottom-layer capabilities.
