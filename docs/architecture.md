# Architecture

## Goal

The system translates a one-way English audio stream into Chinese subtitles and keeps recent subtitles correctable. The current MVP uses a deterministic demo stream so the correction behavior is stable during review and video recording.

## Runtime Flow

```text
Demo provider / chunked audio stream
  -> subtitle event stream
  -> FastAPI WebSocket
  -> React workspace
  -> live subtitle list
  -> metrics and export preview
```

## Backend

- `backend/app/main.py`
  - FastAPI app entry.
  - `/health` health check.
  - `/api/glossary` glossary endpoint.
  - `/api/providers/diagnostics` provider readiness endpoint.
  - `/api/demo/transcript` final transcript endpoint.
  - `/api/audio/demo` upload endpoint through the provider boundary.
  - `/api/providers` active provider status endpoint.
  - `/api/demo/summary` deterministic after-session summary endpoint.
  - `/api/demo/revisions` subtitle version history endpoint.
  - `/ws/demo` WebSocket subtitle stream.
  - `/ws/audio-stream` chunked microphone audio stream that reuses the subtitle event protocol.

- `backend/app/models.py`
  - Pydantic models for subtitle segments, metrics, glossary terms, and stream events.

- `backend/app/services/demo_stream.py`
  - Deterministic demo provider.
  - Emits `partial`, `stable`, `corrected`, and `final` subtitle events.
  - Includes a correction from `张力机制` to `注意力机制`.
  - Emits a correction trace explaining trigger, reason, latency, version change, and changed terms.
  - Aggregates subtitle revision history so reviewers can inspect version changes.

- `backend/app/services/subtitle_state.py`
  - `SubtitleStateManager` keeps ordered subtitles and prevents final subtitles from being downgraded.
  - `CorrectionEngine` repairs only recent correctable subtitles using glossary terms and a common mistranslation map.

- `backend/app/services/audio_stream.py`
  - Converts browser audio chunks into subtitle stream events for the current MVP.
  - Keeps the audio-stream path independent from the deterministic demo button so the stable demo remains safe.

- `backend/app/providers/`
  - `ASRProvider` and `TranslationProvider` interfaces.
  - Mock providers for the current stable MVP.
  - Future `faster-whisper` and cloud translation providers can be added here.

- `backend/app/services/provider_diagnostics.py`
  - Checks whether mock or real providers are ready.
  - Reports missing dependencies, model paths, API keys, base URLs, and next actions without calling external APIs.

## Frontend

- `frontend/src/main.tsx`
  - Connects to `/ws/demo`.
  - Sends microphone chunks to `/ws/audio-stream`.
  - Upserts subtitle segments by id.
- Displays correction state, glossary hits, metrics, and export preview.
- Displays subtitle revision history for each segment version.
- Displays Provider diagnostics and readiness state.
- Includes an audio upload entry that calls the provider-backed backend endpoint.

- `frontend/src/styles.css`
  - Work-focused UI layout.
  - Highlight styling for corrected subtitles.

## Innovation Points

- Subtitle state machine: `partial -> stable -> corrected -> final`.
- Local correction window: only recent, unlocked subtitles are updated.
- Glossary-assisted correction: terms can trigger local translation repair.
- Common mistranslation map: the correction engine is term-driven rather than tied to one fixed sentence.
- Quantified demo: first subtitle latency, correction latency, glossary hit rate, final stability rate.
- Auditable correction timeline: trigger, reason, latency, version change, and term evidence.
- Subtitle revision ledger: segment id, version, status, confidence, translation, and previous translation.
- After-session summary: key points, keywords, glossary terms, and correction notes.
- Provider diagnostics: local readiness checks before switching from demo providers to real providers.
- Optional browser-native speech playback for final and corrected Chinese subtitles.

## Provider Boundary

The MVP uses a deterministic provider for reliable demonstration. The provider boundary can later be replaced by:

- ASR: `faster-whisper`.
- Translation: cloud LLM or translation API.
- TTS: optional Chinese voice playback.

Default runtime uses mock providers to keep the main branch runnable without model downloads or API keys. Real providers are enabled through environment variables.
