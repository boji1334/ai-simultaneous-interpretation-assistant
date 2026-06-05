from fastapi.testclient import TestClient
from pathlib import Path

from app.main import app
from app.config import Settings
from app.models import SubtitleSegment, SubtitleStatus
from app.providers.faster_whisper_provider import FasterWhisperASRProvider
from app.services.demo_stream import apply_demo_correction
from app.services.provider_diagnostics import build_provider_diagnostics
from app.services.subtitle_state import CorrectionEngine, SubtitleStateManager


def test_health_check() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_glossary_contains_attention_mechanism() -> None:
    client = TestClient(app)

    response = client.get("/api/glossary")

    assert response.status_code == 200
    terms = response.json()
    assert any(term["source"] == "attention mechanism" for term in terms)


def test_provider_status_defaults_to_mock() -> None:
    client = TestClient(app)

    response = client.get("/api/providers")

    assert response.status_code == 200
    payload = response.json()
    assert payload["asrProvider"] == "mock"
    assert payload["translationProvider"] == "mock"


def test_provider_diagnostics_defaults_to_ready_mock() -> None:
    client = TestClient(app)

    response = client.get("/api/providers/diagnostics")

    assert response.status_code == 200
    diagnostics = response.json()["diagnostics"]
    assert len(diagnostics) == 2
    assert {item["kind"] for item in diagnostics} == {"asr", "translation"}
    assert all(item["ready"] for item in diagnostics)
    assert all(item["mode"] == "demo" for item in diagnostics)


def test_provider_diagnostics_flags_missing_translation_key() -> None:
    settings = Settings(
        translation_provider="openai_compatible",
        translation_api_key="",
        translation_model="gpt-4o-mini",
        translation_base_url="https://api.openai.com/v1",
    )

    diagnostics = build_provider_diagnostics(settings)
    translation = next(item for item in diagnostics if item.kind == "translation")

    assert not translation.ready
    assert translation.mode == "real"
    assert "TRANSLATION_API_KEY" in translation.message


def test_demo_transcript_contains_corrected_translation() -> None:
    client = TestClient(app)

    response = client.get("/api/demo/transcript")

    assert response.status_code == 200
    segments = response.json()["segments"]
    corrected = next(segment for segment in segments if segment["id"] == "seg-003")
    assert corrected["status"] == "corrected"
    assert "注意力机制" in corrected["translatedText"]
    assert corrected["version"] == 2


def test_demo_websocket_stream_has_metric_and_done_events() -> None:
    client = TestClient(app)

    with client.websocket_connect("/ws/demo?speed=4") as websocket:
        event_types: list[str] = []
        corrected_seen = False
        correction_trace_seen = False
        while True:
            event = websocket.receive_json()
            event_types.append(event["type"])
            if event["type"] == "segment":
                segment = event["segment"]
                corrected_seen = corrected_seen or segment["status"] == "corrected"
            if event["type"] == "correction":
                correction = event["correction"]
                correction_trace_seen = correction["segmentId"] == "seg-003"
            if event["type"] == "done":
                break

    assert "metric" in event_types
    assert corrected_seen
    assert correction_trace_seen
    assert event_types[-1] == "done"


def test_audio_stream_websocket_advances_from_audio_chunks() -> None:
    client = TestClient(app)

    with client.websocket_connect("/ws/audio-stream") as websocket:
        setup_types = [websocket.receive_json()["type"], websocket.receive_json()["type"]]
        event_types: list[str] = []
        corrected_seen = False
        correction_trace_seen = False

        for _ in range(7):
            websocket.send_bytes(b"audio-chunk")
            for _ in range(2):
                event = websocket.receive_json()
                event_types.append(event["type"])
                if event["type"] == "segment":
                    corrected_seen = corrected_seen or event["segment"]["status"] == "corrected"
                if event["type"] == "correction":
                    correction_trace_seen = event["correction"]["segmentId"] == "seg-003"
                if event["type"] == "done":
                    break
            if corrected_seen and correction_trace_seen:
                break

        websocket.send_text("stop")
        final_event = None
        while final_event != "done":
            final_event = websocket.receive_json()["type"]

    assert setup_types == ["session", "glossary"]
    assert "metric" in event_types
    assert corrected_seen
    assert correction_trace_seen
    assert final_event == "done"


def test_demo_audio_upload_uses_provider_boundary() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/audio/demo",
        files={"file": ("demo.wav", b"fake-audio-bytes", "audio/wav")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["bytesReceived"] > 0
    assert payload["provider"] == "mock+mock"
    assert "attention mechanism" in payload["sourceText"]
    assert "注意力机制" in payload["translatedText"]


def test_demo_export_markdown_and_srt() -> None:
    client = TestClient(app)

    markdown = client.get("/api/demo/export?format=markdown")
    srt = client.get("/api/demo/export?format=srt")

    assert markdown.status_code == 200
    assert markdown.json()["filename"].endswith(".md")
    assert "注意力机制" in markdown.json()["content"]
    assert srt.status_code == 200
    assert srt.json()["filename"].endswith(".srt")
    assert "00:00:07,700 --> 00:00:11,500" in srt.json()["content"]


def test_demo_export_rejects_unknown_format() -> None:
    client = TestClient(app)

    response = client.get("/api/demo/export?format=txt")

    assert response.status_code == 400
    assert response.json()["detail"] == "format must be markdown or srt"


def test_demo_summary_contains_correction_notes() -> None:
    client = TestClient(app)

    response = client.get("/api/demo/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "实时 AI 同声传译演示总结"
    assert "注意力机制" in payload["keywords"]
    assert "attention mechanism" in payload["glossaryTerms"]
    assert any("张力机制" in note and "注意力机制" in note for note in payload["correctionNotes"])


def test_demo_corrections_explain_repair() -> None:
    client = TestClient(app)

    response = client.get("/api/demo/corrections")

    assert response.status_code == 200
    corrections = response.json()["corrections"]
    assert corrections[0]["segmentId"] == "seg-003"
    assert corrections[0]["latencyMs"] == 1480
    assert corrections[0]["fromVersion"] == 1
    assert corrections[0]["toVersion"] == 2
    assert "张力机制" in corrections[0]["previousTranslation"]
    assert "注意力机制" in corrections[0]["correctedTranslation"]
    assert corrections[0]["changedTerms"] == ["attention mechanism"]


def test_demo_revisions_expose_subtitle_version_history() -> None:
    client = TestClient(app)

    response = client.get("/api/demo/revisions")

    assert response.status_code == 200
    revisions = response.json()["revisions"]
    seg_003 = [revision for revision in revisions if revision["segmentId"] == "seg-003"]
    assert [revision["version"] for revision in seg_003] == [1, 2]
    assert seg_003[0]["status"] == "stable"
    assert seg_003[1]["status"] == "corrected"
    assert "张力机制" in seg_003[0]["translatedText"]
    assert "注意力机制" in seg_003[1]["translatedText"]
    assert seg_003[1]["previousTranslation"] == seg_003[0]["translatedText"]


def test_demo_snapshot_contains_complete_fallback_state() -> None:
    client = TestClient(app)

    response = client.get("/api/demo/snapshot")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["segments"]) == 5
    assert any(term["source"] == "attention mechanism" for term in payload["glossary"])
    assert payload["metrics"]["correctionLatencyMs"] == 1480
    assert payload["metrics"]["glossaryHitRate"] == 1.0
    assert payload["corrections"][0]["segmentId"] == "seg-003"
    assert any(revision["segmentId"] == "seg-003" for revision in payload["revisions"])
    assert payload["summary"]["title"] == "实时 AI 同声传译演示总结"


def test_video_demo_source_exposes_license_and_media_url() -> None:
    client = TestClient(app)

    response = client.get("/api/video-demo/source")

    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Self-written AI interpretation demo audio"
    assert payload["mediaUrl"] == "/api/demo/audio"
    assert payload["mediaType"] == "audio"
    assert "Original competition demo text" in payload["license"]
    assert "technical talk" in payload["scenario"].lower()


def test_demo_audio_endpoint_serves_generated_wav() -> None:
    client = TestClient(app)

    response = client.get("/api/demo/audio")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/wav")
    assert len(response.content) > 1000


def test_video_demo_snapshot_contains_corrected_course_term() -> None:
    client = TestClient(app)

    response = client.get("/api/video-demo/snapshot")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["segments"]) == 5
    assert payload["segments"][-1]["endTime"] >= 30
    corrected = next(segment for segment in payload["segments"] if segment["id"] == "video-003")
    assert corrected["status"] == "corrected"
    assert "注意力机制" in corrected["translatedText"]
    assert payload["corrections"][0]["segmentId"] == "video-003"
    assert payload["metrics"]["correctionLatencyMs"] == 1480
    assert any(term["source"] == "attention mechanism" for term in payload["glossary"])


def test_video_demo_websocket_stream_exposes_correction() -> None:
    client = TestClient(app)

    with client.websocket_connect("/ws/video-demo?speed=4") as websocket:
        corrected_seen = False
        correction_trace_seen = False
        done_seen = False
        while not done_seen:
            event = websocket.receive_json()
            if event["type"] == "segment":
                segment = event["segment"]
                corrected_seen = corrected_seen or (
                    segment["id"] == "video-003" and segment["status"] == "corrected"
                )
            if event["type"] == "correction":
                correction_trace_seen = event["correction"]["segmentId"] == "video-003"
            done_seen = event["type"] == "done"

    assert corrected_seen
    assert correction_trace_seen
    assert done_seen


def test_correction_engine_repairs_recent_segment() -> None:
    corrected = apply_demo_correction()

    assert corrected.status == SubtitleStatus.CORRECTED
    assert corrected.version == 2
    assert corrected.previous_translation == "这个模型使用张力机制来判断哪些词更重要。"
    assert corrected.translated_text == "这个模型使用注意力机制来判断哪些词更重要。"
    assert corrected.changed_terms == ["attention mechanism"]


def test_state_manager_does_not_downgrade_final_segment() -> None:
    manager = SubtitleStateManager()
    final = SubtitleSegment(
        id="seg-final",
        sourceText="Final text",
        translatedText="最终文本",
        status=SubtitleStatus.FINAL,
        version=3,
        startTime=1.0,
        endTime=2.0,
        confidence=0.98,
    )
    partial = final.model_copy(
        update={
            "translated_text": "临时文本",
            "status": SubtitleStatus.PARTIAL,
            "version": 1,
        }
    )

    manager.upsert(final)
    result = manager.upsert(partial)

    assert result.translated_text == "最终文本"
    assert result.status == SubtitleStatus.FINAL


def test_state_manager_does_not_correct_locked_final_segment() -> None:
    manager = SubtitleStateManager()
    final = SubtitleSegment(
        id="seg-final",
        sourceText="The model uses an attention mechanism.",
        translatedText="这个模型使用张力机制。",
        status=SubtitleStatus.FINAL,
        version=3,
        startTime=1.0,
        endTime=2.0,
        confidence=0.98,
    )
    corrected = final.model_copy(
        update={
            "translated_text": "这个模型使用注意力机制。",
            "status": SubtitleStatus.CORRECTED,
            "version": 4,
            "previous_translation": final.translated_text,
        }
    )

    manager.upsert(final)
    result = manager.upsert(corrected)

    assert result.translated_text == "这个模型使用张力机制。"
    assert result.status == SubtitleStatus.FINAL
    assert result.version == 3


def test_correction_engine_respects_recent_window() -> None:
    manager = SubtitleStateManager()
    glossary = {"attention mechanism": "注意力机制"}
    engine = CorrectionEngine(glossary, window_size=1)

    old_segment = SubtitleSegment(
        id="old",
        sourceText="The model uses an attention mechanism.",
        translatedText="这个模型使用张力机制。",
        status=SubtitleStatus.STABLE,
        version=1,
        startTime=0.0,
        endTime=1.0,
        confidence=0.7,
    )
    recent_segment = SubtitleSegment(
        id="recent",
        sourceText="This segment is about latency.",
        translatedText="这一句讨论延迟。",
        status=SubtitleStatus.STABLE,
        version=1,
        startTime=2.0,
        endTime=3.0,
        confidence=0.9,
    )

    manager.upsert(old_segment)
    manager.upsert(recent_segment)
    corrected = engine.correct_recent(manager)

    assert corrected == []
    assert manager.segments["old"].translated_text == "这个模型使用张力机制。"


def test_correction_engine_uses_glossary_for_multiple_terms() -> None:
    manager = SubtitleStateManager()
    glossary = {
        "attention mechanism": "注意力机制",
        "streaming pipeline": "流式管道",
        "latency": "延迟",
    }
    engine = CorrectionEngine(glossary)
    segment = SubtitleSegment(
        id="seg-pipeline",
        sourceText="The streaming pipeline reduces latency.",
        translatedText="这个流管道可以降低潜伏期。",
        status=SubtitleStatus.STABLE,
        version=1,
        startTime=0.0,
        endTime=2.0,
        confidence=0.72,
    )

    manager.upsert(segment)
    corrected = engine.correct_recent(manager)

    assert len(corrected) == 1
    assert corrected[0].translated_text == "这个流式管道可以降低延迟。"
    assert corrected[0].changed_terms == ["latency", "streaming pipeline"]
    assert corrected[0].previous_translation == "这个流管道可以降低潜伏期。"


def test_correction_engine_skips_already_correct_term() -> None:
    manager = SubtitleStateManager()
    glossary = {"attention mechanism": "注意力机制"}
    engine = CorrectionEngine(glossary)
    segment = SubtitleSegment(
        id="seg-correct",
        sourceText="The model uses an attention mechanism.",
        translatedText="这个模型使用注意力机制。",
        status=SubtitleStatus.STABLE,
        version=1,
        startTime=0.0,
        endTime=2.0,
        confidence=0.92,
    )

    manager.upsert(segment)
    corrected = engine.correct_recent(manager)

    assert corrected == []
    assert manager.segments["seg-correct"].version == 1


def test_faster_whisper_confidence_uses_language_probability(tmp_path, monkeypatch) -> None:
    class FakeSegment:
        text = " hello "

    class FakeInfo:
        language_probability = 0.87
        language = "en"

    captured_paths: list[str] = []

    class FakeModel:
        def transcribe(self, path: str, vad_filter: bool) -> tuple[list[FakeSegment], FakeInfo]:
            assert Path(path).exists()
            captured_paths.append(path)
            return [FakeSegment()], FakeInfo()

    provider = FasterWhisperASRProvider("fake-model")
    monkeypatch.setattr(provider, "_load_model", lambda: FakeModel())

    import asyncio

    result = asyncio.run(provider.transcribe(b"fake-audio", "demo.wav"))

    assert result.text == "hello"
    assert result.confidence == 0.87
    assert result.language == "en"
    assert captured_paths
    assert not Path(captured_paths[0]).exists()
