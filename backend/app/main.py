import asyncio
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.models import AudioDemoResult
from app.providers.factory import create_asr_provider, create_translation_provider
from app.services.audio_stream import AudioStreamEventPump
from app.services.demo_stream import (
    GLOSSARY,
    build_demo_events,
    demo_correction_traces,
    final_metrics,
    final_segments,
    subtitle_revision_history,
)
from app.services.exporter import to_markdown, to_srt
from app.services.provider_diagnostics import build_provider_diagnostics
from app.services.summarizer import summarize_segments

app = FastAPI(
    title="AI Simultaneous Interpretation Assistant",
    version="0.1.0",
)

settings = get_settings()
asr_provider = create_asr_provider(settings)
translation_provider = create_translation_provider(settings)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "translate-english-backend"}


@app.get("/api/glossary")
def get_glossary() -> list[dict]:
    return [term.model_dump(by_alias=True) for term in GLOSSARY]


@app.get("/api/providers")
def get_provider_status() -> dict[str, str]:
    return {
        "asrProvider": settings.asr_provider,
        "translationProvider": settings.translation_provider,
        "asrModelPath": settings.asr_model_path,
        "translationModel": settings.translation_model,
    }


@app.get("/api/providers/diagnostics")
def get_provider_diagnostics() -> dict[str, list[dict]]:
    return {
        "diagnostics": [
            diagnostic.model_dump()
            for diagnostic in build_provider_diagnostics(settings)
        ]
    }


@app.get("/api/demo/transcript")
def get_demo_transcript() -> dict[str, list[dict]]:
    segments = final_segments()
    return {"segments": [segment.model_dump(by_alias=True) for segment in segments]}


@app.get("/api/demo/export")
def export_demo_transcript(format: str = "markdown") -> dict[str, str]:
    segments = final_segments()
    if format == "srt":
        return {"filename": "ai-interpretation-demo.srt", "content": to_srt(segments)}
    if format != "markdown":
        raise HTTPException(status_code=400, detail="format must be markdown or srt")
    return {"filename": "ai-interpretation-demo.md", "content": to_markdown(segments)}


@app.get("/api/demo/summary")
def get_demo_summary() -> dict:
    return summarize_segments(final_segments()).model_dump(by_alias=True)


@app.get("/api/demo/corrections")
def get_demo_corrections() -> dict[str, list[dict]]:
    return {"corrections": [trace.model_dump(by_alias=True) for trace in demo_correction_traces()]}


@app.get("/api/demo/revisions")
def get_demo_revisions() -> dict[str, list[dict]]:
    return {"revisions": [revision.model_dump(by_alias=True) for revision in subtitle_revision_history()]}


@app.get("/api/demo/snapshot")
def get_demo_snapshot() -> dict:
    segments = final_segments()
    return {
        "segments": [segment.model_dump(by_alias=True) for segment in segments],
        "glossary": [term.model_dump(by_alias=True) for term in GLOSSARY],
        "metrics": final_metrics().model_dump(by_alias=True),
        "corrections": [trace.model_dump(by_alias=True) for trace in demo_correction_traces()],
        "revisions": [revision.model_dump(by_alias=True) for revision in subtitle_revision_history()],
        "summary": summarize_segments(segments).model_dump(by_alias=True),
    }


@app.post("/api/audio/demo")
async def process_demo_audio(file: UploadFile = File(...)) -> dict:
    audio = await file.read()
    glossary = {term.source: term.target for term in GLOSSARY}
    asr_result = await asr_provider.transcribe(audio, file.filename or "audio")
    translation_result = await translation_provider.translate(asr_result.text, glossary)
    result = AudioDemoResult(
        filename=file.filename or "audio",
        bytesReceived=len(audio),
        sourceText=asr_result.text,
        translatedText=translation_result.text,
        confidence=asr_result.confidence,
        glossaryHits=translation_result.glossary_hits,
        provider=f"{settings.asr_provider}+{settings.translation_provider}",
    )
    return result.model_dump(by_alias=True)


@app.websocket("/ws/demo")
async def demo_stream(websocket: WebSocket, speed: float = 1.0) -> None:
    await websocket.accept()
    speed = min(max(speed, 0.2), 4.0)
    try:
        for event in build_demo_events():
            await asyncio.sleep(event.delay_ms / 1000 / speed)
            await websocket.send_json(event.model_dump(by_alias=True, exclude_none=True))
    except WebSocketDisconnect:
        return


@app.websocket("/ws/audio-stream")
async def audio_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    pump = AudioStreamEventPump(events_per_chunk=2)
    try:
        for event in pump.start():
            await websocket.send_json(event.model_dump(by_alias=True, exclude_none=True))

        while True:
            message = await websocket.receive()
            if text := message.get("text"):
                if text == "stop":
                    for event in pump.finish():
                        await websocket.send_json(event.model_dump(by_alias=True, exclude_none=True))
                    await websocket.close()
                    return
                continue

            if audio := message.get("bytes"):
                for event in pump.push_audio_chunk(audio):
                    await websocket.send_json(event.model_dump(by_alias=True, exclude_none=True))
    except WebSocketDisconnect:
        return


if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/")
    def serve_index() -> FileResponse:
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{path:path}")
    def serve_spa(path: str) -> FileResponse:
        requested = FRONTEND_DIST / path
        if requested.is_file():
            return FileResponse(requested)
        return FileResponse(FRONTEND_DIST / "index.html")
