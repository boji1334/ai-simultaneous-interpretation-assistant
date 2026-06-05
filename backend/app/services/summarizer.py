from app.models import SubtitleSegment, SubtitleStatus, SummaryResult


def summarize_segments(segments: list[SubtitleSegment]) -> SummaryResult:
    corrected = [segment for segment in segments if segment.status == SubtitleStatus.CORRECTED]
    glossary_terms = sorted({term for segment in segments for term in segment.changed_terms})
    keywords = sorted(
        {
            "实时同传",
            "自动修正",
            "术语表",
            "低延迟",
            "注意力机制",
        }
    )
    correction_notes = [
        f"{segment.previous_translation} -> {segment.translated_text}"
        for segment in corrected
        if segment.previous_translation
    ]

    return SummaryResult(
        title="实时 AI 同声传译演示总结",
        summary=(
            "本次演示展示了系统如何将英文技术讲解实时转换为中文字幕，并在后续上下文到达后，"
            "通过滑动窗口和术语表把错误译文自动修正为更准确的表达。"
        ),
        keyPoints=[
            "字幕以 partial、stable、corrected、final 多状态流转，兼顾实时性和准确性。",
            "系统只修正最近未锁定字幕，避免整屏内容频繁跳动。",
            "术语表将 attention mechanism 稳定映射为注意力机制，提升技术场景翻译质量。",
            "最终字幕可导出为 Markdown 或 SRT，方便课后复盘和视频字幕制作。",
        ],
        keywords=keywords,
        glossaryTerms=glossary_terms,
        correctionNotes=correction_notes,
    )

