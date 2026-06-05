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
8. Show the glossary panel and explain that `attention mechanism` is mapped to `注意力机制`.
9. Click `查看 Provider` to explain the stable Mock Provider and the future `faster-whisper` / cloud translation boundary.
10. Optionally record microphone audio or upload an audio file from the audio entry panel and explain that this route already goes through the provider boundary.
11. Show metrics:
    - first subtitle latency
    - correction latency
    - glossary hit rate
    - final stability rate
12. Click `复制字幕`, `下载 MD`, or `下载 SRT` and show the bilingual transcript export.
13. Click `生成总结` and show the summary, key points, keywords, and correction notes.
14. Optionally click `开启语音` and explain that final/corrected Chinese subtitles can be spoken by the browser.
15. If the live stream needs a fallback, click `加载最终字幕` and show that it loads the full snapshot: final subtitles, glossary, metrics, correction timeline, and summary.

## Closing

The original implementation focuses on the product logic: subtitle state machine, correction engine, glossary-assisted repair, WebSocket event protocol, UI states, export flow, and after-session summary. ASR and translation providers are replaceable bottom-layer capabilities.
