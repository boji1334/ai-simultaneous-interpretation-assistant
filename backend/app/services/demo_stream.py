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
    title="Welcome (6.002x-1).webm",
    pageUrl="https://commons.wikimedia.org/wiki/File:Welcome_(6.002x-1).webm",
    mediaUrl=(
        "https://upload.wikimedia.org/wikipedia/commons/transcoded/a/a0/"
        "Welcome_%286.002x-1%29.webm/Welcome_%286.002x-1%29.webm.360p.vp9.webm"
    ),
    license="Creative Commons Attribution-Share Alike 4.0",
    attribution="MIT OpenCourseWare / MITx, via Wikimedia Commons",
    durationSeconds=129,
    scenario="Online course video interpretation",
    note="用于展示观看英文网课时的同步中文字幕；默认字幕流仍由可复现 demo provider 驱动。",
)

VIDEO_GLOSSARY: list[GlossaryTerm] = [
    GlossaryTerm(
        source="MITx",
        target="MITx",
        category="Course",
        description="麻省理工在线学习项目名称，保留原名。",
    ),
    GlossaryTerm(
        source="Circuits and Electronics",
        target="电路与电子学",
        category="Course",
        description="课程名称，应避免误译为普通消费电子产品。",
    ),
    GlossaryTerm(
        source="online learning",
        target="在线学习",
        category="Education",
        description="网课和开放课程场景中的常用术语。",
    ),
    GlossaryTerm(
        source="electrical engineering",
        target="电气工程",
        category="Discipline",
        description="学科名称，需保持专业一致性。",
    ),
]


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
            segmentId="video-002",
            trigger="后续上下文确认课程名称 Circuits and Electronics",
            reason="术语表将课程名锁定为“电路与电子学”，回溯修正先前将 electronics 误译为“电子产品”的字幕。",
            previousTranslation="欢迎来到 6.002x：电路和电子产品。",
            correctedTranslation="很高兴你加入 6.002x：电路与电子学，这是 MITx 的首门课程。",
            changedTerms=["Circuits and Electronics"],
            latencyMs=1210,
            fromVersion=1,
            toVersion=2,
        )
    ]


def video_demo_metrics() -> MetricSnapshot:
    return _metrics(760, 1210, 1.0, 0.94, 1, 16, 17)


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
    """Build a deterministic full-video stream for an external online-course scene."""
    correction_trace = video_demo_correction_traces()[0]

    return [
        DemoEvent(type="session", message="video-demo-session-started", delayMs=100),
        DemoEvent(type="glossary", glossary=VIDEO_GLOSSARY, delayMs=100),
        DemoEvent(
            type="segment",
            delayMs=430,
            segment=_segment(
                "video-001",
                "Welcome to MITx, a worldwide online learning initiative.",
                "欢迎来到 MITx，这是一个面向全球的在线学习项目。",
                SubtitleStatus.PARTIAL,
                1,
                0.0,
                6.5,
                0.81,
                ["MITx", "online learning"],
            ),
        ),
        DemoEvent(
            type="metric",
            delayMs=60,
            metrics=_metrics(760, None, 0.5, 0.0, 0, 0, 1),
        ),
        DemoEvent(
            type="segment",
            delayMs=520,
            segment=_segment(
                "video-001",
                "Welcome to MITx, a worldwide online learning initiative.",
                "欢迎来到 MITx，这是一个面向全球的在线学习项目。",
                SubtitleStatus.FINAL,
                2,
                0.0,
                6.5,
                0.96,
                ["MITx", "online learning"],
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=620,
            segment=_segment(
                "video-002",
                "We are delighted to have you join us for 6.002x, Circuits and Electronics, the inaugural course of MITx.",
                "欢迎来到 6.002x：电路和电子产品。",
                SubtitleStatus.STABLE,
                1,
                6.6,
                13.0,
                0.72,
                ["Circuits and Electronics"],
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=560,
            segment=_segment(
                "video-003",
                "OK, welcome to 6.002. 6.002x is the same as the electronic circuits course taken by MIT students.",
                "好的，欢迎来到 6.002。6.002x 与 MIT 学生学习的电子电路课程相同。",
                SubtitleStatus.FINAL,
                1,
                13.1,
                20.0,
                0.94,
                ["Circuits and Electronics"],
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=520,
            segment=_segment(
                "video-004",
                "It is the first course in an EE, or EECS major at MIT.",
                "这是 MIT 电气工程或电气工程与计算机科学专业的第一门课程。",
                SubtitleStatus.FINAL,
                1,
                20.1,
                26.0,
                0.95,
                ["electrical engineering"],
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=220,
            message="video-window-correction",
            segment=_segment(
                "video-002",
                "We are delighted to have you join us for 6.002x, Circuits and Electronics, the inaugural course of MITx.",
                "很高兴你加入 6.002x：电路与电子学，这是 MITx 的首门课程。",
                SubtitleStatus.CORRECTED,
                2,
                6.6,
                13.0,
                0.95,
                ["Circuits and Electronics"],
                "欢迎来到 6.002x：电路和电子产品。",
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
            metrics=_metrics(760, 1210, 0.75, 0.67, 1, 3, 4),
        ),
        DemoEvent(
            type="segment",
            delayMs=520,
            segment=_segment(
                "video-005",
                "In this course, we had to make the transition from physics to electrical engineering.",
                "在这门课程中，我们会从物理过渡到电气工程。",
                SubtitleStatus.FINAL,
                1,
                26.1,
                33.0,
                0.96,
                ["electrical engineering"],
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=560,
            segment=_segment(
                "video-006",
                "You will learn about many fun things, including the foundations behind cool devices such as the smartphone.",
                "你会学到许多有趣的内容，包括智能手机等酷设备背后的基础原理。",
                SubtitleStatus.FINAL,
                1,
                33.1,
                42.0,
                0.95,
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=560,
            segment=_segment(
                "video-007",
                "The course will be hard, and we want you to stick with us. We hope you have a lot of fun.",
                "这门课会有难度，我们希望你坚持下来，也希望你在课程中收获很多乐趣。",
                SubtitleStatus.FINAL,
                1,
                42.1,
                50.0,
                0.95,
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=520,
            segment=_segment(
                "video-008",
                "Let me start by introducing you to our team. I am Anant Agarwal.",
                "先来介绍一下我们的团队。我是 Anant Agarwal。",
                SubtitleStatus.FINAL,
                1,
                50.1,
                57.0,
                0.96,
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=520,
            segment=_segment(
                "video-009",
                "Like most MIT faculty, I have a wide range of interests, including a fascination around chainsaws.",
                "和大多数 MIT 教师一样，我兴趣广泛，其中还包括对链锯的着迷。",
                SubtitleStatus.FINAL,
                1,
                57.1,
                66.0,
                0.94,
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=440,
            segment=_segment(
                "video-010",
                "Music playing.",
                "音乐播放。",
                SubtitleStatus.FINAL,
                1,
                66.1,
                70.0,
                0.98,
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=560,
            segment=_segment(
                "video-011",
                "Hello, I'm Gerry Sussman, Professor of Electrical Engineering at MIT.",
                "大家好，我是 Gerry Sussman，MIT 电气工程教授。",
                SubtitleStatus.FINAL,
                1,
                70.1,
                77.0,
                0.96,
                ["electrical engineering"],
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=560,
            segment=_segment(
                "video-012",
                "I've been a faculty member here since 1973. I build electronics, optics, and computer software.",
                "我从 1973 年起就在这里任教。我做电子、光学和计算机软件。",
                SubtitleStatus.FINAL,
                1,
                77.1,
                86.0,
                0.95,
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=500,
            segment=_segment(
                "video-013",
                "I repair watches as a hobby.",
                "我还把修表当作爱好。",
                SubtitleStatus.FINAL,
                1,
                86.1,
                91.0,
                0.97,
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=560,
            segment=_segment(
                "video-014",
                "I'm Piotr Mitros, a research scientist at MIT, in charge of developing the software infrastructure for MITx.",
                "我是 Piotr Mitros，MIT 的研究科学家，负责开发 MITx 的软件基础设施。",
                SubtitleStatus.FINAL,
                1,
                91.1,
                102.0,
                0.95,
                ["MITx"],
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=560,
            segment=_segment(
                "video-015",
                "As a graduate student, I spent a lot of time traveling around India, Nigeria, and China.",
                "读研究生时，我花了很多时间在印度、尼日利亚和中国各地走访。",
                SubtitleStatus.FINAL,
                1,
                102.1,
                111.0,
                0.94,
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=560,
            segment=_segment(
                "video-016",
                "It was mostly as part of educational technology projects, so I'm excited to be helping with this course.",
                "这些经历大多属于教育技术项目，所以我很高兴能参与这门课程。",
                SubtitleStatus.FINAL,
                1,
                111.1,
                120.0,
                0.95,
            ),
        ),
        DemoEvent(
            type="segment",
            delayMs=620,
            segment=_segment(
                "video-017",
                "Whether we like chainsaws or watches, we are all passionate educators. We welcome your participation and feedback. Let's get started.",
                "无论我们喜欢链锯还是手表，我们都是充满热情的教育者。欢迎你的参与和反馈。让我们开始吧。",
                SubtitleStatus.FINAL,
                1,
                120.1,
                129.0,
                0.96,
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
