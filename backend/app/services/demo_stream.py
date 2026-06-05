from collections.abc import Iterable

from app.models import (
    CorrectionTrace,
    DemoEvent,
    GlossaryTerm,
    MetricSnapshot,
    SubtitleRevision,
    SubtitleSegment,
    SubtitleStatus,
    VideoDemoSource,
)
from app.services.subtitle_state import CorrectionEngine, SubtitleStateManager


GLOSSARY: list[GlossaryTerm] = [
    GlossaryTerm(
        source="attention mechanism",
        target="注意力机制",
        category="AI",
        description="Transformer 模型中用于判断上下文重点的核心机制。",
    ),
    GlossaryTerm(
        source="streaming pipeline",
        target="流式管道",
        category="Architecture",
        description="边接收边处理数据的低延迟处理链路。",
    ),
    GlossaryTerm(
        source="glossary",
        target="术语表",
        category="Product",
        description="用于稳定专业词翻译并触发局部修正。",
    ),
    GlossaryTerm(
        source="latency",
        target="延迟",
        category="Metric",
        description="从音频输入到字幕出现或修正完成的时间差。",
    ),
]

VIDEO_DEMO_SOURCE = VideoDemoSource(
    title="Self-written AI interpretation demo audio",
    pageUrl="",
    mediaUrl="/api/demo/audio",
    mediaType="audio",
    license="Original competition demo text, generated with local TTS",
    attribution="Created for this repository from assets/demo/demo-script.en.txt",
    durationSeconds=31,
    scenario="Synchronized technical talk interpretation",
    note="主演示素材使用自写英文脚本和本地 TTS 音频，字幕时间轴按音频静音边界校准，避免外部视频音频与手工字幕不同步。",
)

VIDEO_GLOSSARY: list[GlossaryTerm] = GLOSSARY


def _segment(
    segment_id: str,
    source_text: str,
    translated_text: str,
    status: SubtitleStatus,
    version: int,
    start_time: float,
    end_time: float | None,
    confidence: float,
    changed_terms: list[str] | None = None,
    previous_translation: str | None = None,
) -> SubtitleSegment:
    return SubtitleSegment(
        id=segment_id,
        sourceText=source_text,
        translatedText=translated_text,
        status=status,
        version=version,
        startTime=start_time,
        endTime=end_time,
        confidence=confidence,
        changedTerms=changed_terms or [],
        previousTranslation=previous_translation,
    )


def _metrics(
    first_latency: int | None,
    correction_latency: int | None,
    glossary_hit_rate: float,
    final_stability_rate: float,
    correction_count: int,
    final_count: int,
    subtitle_count: int,
) -> MetricSnapshot:
    return MetricSnapshot(
        firstSubtitleLatencyMs=first_latency,
        correctionLatencyMs=correction_latency,
        glossaryHitRate=glossary_hit_rate,
        finalStabilityRate=final_stability_rate,
        correctionCount=correction_count,
        finalCount=final_count,
        subtitleCount=subtitle_count,
    )


def demo_correction_traces() -> list[CorrectionTrace]:
    return [
        CorrectionTrace(
            segmentId="seg-003",
            trigger="后续上下文出现 attention mechanism",
            reason="滑动窗口检测到术语表命中，确认原译文中的“张力机制”应回溯修正为“注意力机制”。",
            previousTranslation="这个模型使用张力机制来判断哪些词更重要。",
            correctedTranslation="这个模型使用注意力机制来判断哪些词更重要。",
            changedTerms=["attention mechanism"],
            latencyMs=1480,
            fromVersion=1,
            toVersion=2,
        )
    ]


def final_metrics() -> MetricSnapshot:
    return _metrics(820, 1480, 1.0, 0.8, 1, 4, 5)


def video_demo_correction_traces() -> list[CorrectionTrace]:
    return [
        CorrectionTrace(
            segmentId="video-003",
            trigger="后续上下文出现 attention mechanism",
            reason="滑动窗口检测到术语表命中，确认原译文中的“张力机制”应回溯修正为“注意力机制”。",
            previousTranslation="这个模型使用张力机制来判断哪些词更重要。",
            correctedTranslation="这个模型使用注意力机制来判断哪些词更重要。",
            changedTerms=["attention mechanism"],
            latencyMs=1480,
            fromVersion=1,
            toVersion=2,
        )
    ]


def video_demo_metrics() -> MetricSnapshot:
    return _metrics(820, 1480, 1.0, 0.8, 1, 4, 5)


def build_demo_events() -> list[DemoEvent]:
    """Build a deterministic stream that demonstrates low-latency correction."""
    correction_trace = demo_correction_traces()[0]

    return [
        DemoEvent(type="session", message="demo-session-started", delayMs=100),
        DemoEvent(type="glossary", glossary=GLOSSARY, delayMs=100),
        DemoEvent(
            type="segment",
            delayMs=500,
            segment=_segment(
                "seg-001",
                "Good morning everyone, today we will explore real-time AI interpretation.",
                "大家早上好，今天我们将探索实时 AI 同声传译。",
                SubtitleStatus.PARTIAL,
                1,
                0.0,
                3.2,
                0.79,
            ),
        ),
        DemoEvent(
            type="metric",
            delayMs=80,
            metrics=_metrics(820, None, 0.0, 0.0, 0, 0, 1),
        ),
        DemoEvent(
            type="segment",
            delayMs=650,
            segment=_segment(
                "seg-001",
                "Good morning everyone, today we will explore real-time AI interpretation.",
                "大家早上好，今天我们将探索实时 AI 同声传译。",
                SubtitleStatus.FINAL,
                2,
                0.0,
                3.2,
                0.96,
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=520,
            segment=_segment(
                "seg-002",
                "The first challenge is balancing latency and accuracy in a streaming pipeline.",
                "第一个挑战，是在流式管道中平衡延迟和准确性。",
                SubtitleStatus.STABLE,
                1,
                3.4,
                7.4,
                0.91,
                ["streaming pipeline", "latency"],
            ),
        ),
        DemoEvent(
            type="metric",
            delayMs=80,
            metrics=_metrics(820, None, 0.5, 0.5, 0, 1, 2),
        ),
        DemoEvent(
            type="segment",
            delayMs=650,
            segment=_segment(
                "seg-003",
                "The model uses a tension mechanism to decide which words matter.",
                "这个模型使用张力机制来判断哪些词更重要。",
                SubtitleStatus.STABLE,
                1,
                7.7,
                11.5,
                0.68,
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=650,
            segment=_segment(
                "seg-004",
                "But after the next words arrive, it becomes clear that the speaker means attention mechanism.",
                "但后续词语到达后，可以确定说话者指的是注意力机制。",
                SubtitleStatus.PARTIAL,
                1,
                11.7,
                15.8,
                0.82,
                ["attention mechanism"],
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=250,
            message="local-window-correction",
            segment=_segment(
                "seg-003",
                "The model uses an attention mechanism to decide which words matter.",
                "这个模型使用注意力机制来判断哪些词更重要。",
                SubtitleStatus.CORRECTED,
                2,
                7.7,
                11.5,
                0.94,
                ["attention mechanism"],
                "这个模型使用张力机制来判断哪些词更重要。",
            ),
        ),
        DemoEvent(
            type="correction",
            delayMs=20,
            message="correction-trace-created",
            correction=correction_trace,
        ),
        DemoEvent(
            type="metric",
            delayMs=80,
            metrics=_metrics(820, 1480, 0.75, 0.67, 1, 2, 4),
        ),
        DemoEvent(
            type="segment",
            delayMs=500,
            segment=_segment(
                "seg-004",
                "But after the next words arrive, it becomes clear that the speaker means attention mechanism.",
                "但后续词语到达后，可以确定说话者指的是注意力机制。",
                SubtitleStatus.FINAL,
                2,
                11.7,
                15.8,
                0.96,
                ["attention mechanism"],
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=520,
            segment=_segment(
                "seg-005",
                "A small glossary helps the system keep technical terms consistent.",
                "一个小型术语表可以帮助系统保持技术术语翻译一致。",
                SubtitleStatus.FINAL,
                1,
                16.0,
                19.4,
                0.95,
                ["glossary"],
            ),
        ),
        DemoEvent(
            type="metric",
            delayMs=80,
            metrics=final_metrics(),
        ),
        DemoEvent(type="done", message="demo-session-complete", delayMs=120),
    ]


def build_video_demo_events() -> list[DemoEvent]:
    """Build a deterministic media-synchronized stream for the controlled demo audio."""
    correction_trace = video_demo_correction_traces()[0]

    return [
        DemoEvent(type="session", message="video-demo-session-started", delayMs=100),
        DemoEvent(type="glossary", glossary=VIDEO_GLOSSARY, delayMs=100),
        DemoEvent(
            type="segment",
            delayMs=430,
            segment=_segment(
                "video-001",
                "Good morning everyone, today we will explore real-time AI interpretation.",
                "大家早上好，今天我们将探索实时 AI 同声传译。",
                SubtitleStatus.PARTIAL,
                1,
                0.15,
                5.90,
                0.79,
            ),
        ),
        DemoEvent(
            type="metric",
            delayMs=60,
            metrics=_metrics(820, None, 0.0, 0.0, 0, 0, 1),
        ),
        DemoEvent(
            type="segment",
            delayMs=520,
            segment=_segment(
                "video-001",
                "Good morning everyone, today we will explore real-time AI interpretation.",
                "大家早上好，今天我们将探索实时 AI 同声传译。",
                SubtitleStatus.FINAL,
                2,
                0.15,
                5.90,
                0.96,
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=620,
            segment=_segment(
                "video-002",
                "The first challenge is balancing latency and accuracy in a streaming pipeline.",
                "第一个挑战是在流式管道中平衡延迟和准确性。",
                SubtitleStatus.FINAL,
                1,
                6.80,
                12.14,
                0.95,
                ["latency", "streaming pipeline"],
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=560,
            segment=_segment(
                "video-003",
                "The model uses a tension mechanism to decide which words matter.",
                "这个模型使用张力机制来判断哪些词更重要。",
                SubtitleStatus.STABLE,
                1,
                13.09,
                17.39,
                0.74,
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=520,
            segment=_segment(
                "video-004",
                "But after the next words arrive, it becomes clear that the speaker means attention mechanism.",
                "但后续词语到达后，可以确认说话人指的是注意力机制。",
                SubtitleStatus.FINAL,
                1,
                18.24,
                24.54,
                0.95,
                ["attention mechanism"],
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=220,
            message="video-window-correction",
            segment=_segment(
                "video-003",
                "The model uses a tension mechanism to decide which words matter.",
                "这个模型使用注意力机制来判断哪些词更重要。",
                SubtitleStatus.CORRECTED,
                2,
                13.09,
                17.39,
                0.96,
                ["attention mechanism"],
                "这个模型使用张力机制来判断哪些词更重要。",
            ),
        ),
        DemoEvent(
            type="correction",
            delayMs=20,
            message="video-correction-trace-created",
            correction=correction_trace,
        ),
        DemoEvent(
            type="metric",
            delayMs=80,
            metrics=_metrics(820, 1480, 0.75, 0.67, 1, 3, 4),
        ),
        DemoEvent(
            type="segment",
            delayMs=520,
            segment=_segment(
                "video-005",
                "A small glossary helps the system keep technical terms consistent.",
                "一个小型术语表可以帮助系统保持技术术语翻译一致。",
                SubtitleStatus.FINAL,
                1,
                25.44,
                30.39,
                0.96,
                ["glossary"],
            ),
        ),
        DemoEvent(
            type="metric",
            delayMs=80,
            metrics=video_demo_metrics(),
        ),
        DemoEvent(type="done", message="video-demo-session-complete", delayMs=120),
    ]


def final_segments(events: Iterable[DemoEvent] | None = None) -> list[SubtitleSegment]:
    latest: dict[str, SubtitleSegment] = {}
    for event in events or build_demo_events():
        if event.segment:
            latest[event.segment.id] = event.segment
    return [latest[key] for key in sorted(latest)]


def subtitle_revision_history(events: Iterable[DemoEvent] | None = None) -> list[SubtitleRevision]:
    revisions: dict[tuple[str, int], SubtitleRevision] = {}
    for event in events or build_demo_events():
        if not event.segment:
            continue
        segment = event.segment
        revisions[(segment.id, segment.version)] = SubtitleRevision(
            segmentId=segment.id,
            version=segment.version,
            status=segment.status,
            translatedText=segment.translated_text,
            confidence=segment.confidence,
            changedTerms=segment.changed_terms,
            previousTranslation=segment.previous_translation,
        )
    return [
        revisions[key]
        for key in sorted(revisions, key=lambda item: (item[0], item[1]))
    ]


def apply_demo_correction() -> SubtitleSegment:
    manager = SubtitleStateManager()
    segment = _segment(
        "seg-correction-test",
        "The model uses an attention mechanism to decide which words matter.",
        "这个模型使用张力机制来判断哪些词更重要。",
        SubtitleStatus.STABLE,
        1,
        0.0,
        3.5,
        0.68,
    )
    manager.upsert(segment)

    glossary = {term.source: term.target for term in GLOSSARY}
    corrected = CorrectionEngine(glossary).correct_recent(manager)
    if not corrected:
        raise RuntimeError("demo correction did not produce a corrected segment")
    return corrected[0]
