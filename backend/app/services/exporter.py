from app.models import SubtitleSegment, SubtitleStatus


EXPORTABLE_STATUSES = {SubtitleStatus.CORRECTED, SubtitleStatus.FINAL}


def exportable_segments(segments: list[SubtitleSegment]) -> list[SubtitleSegment]:
    return [segment for segment in segments if segment.status in EXPORTABLE_STATUSES]


def format_timestamp(seconds: float) -> str:
    total_ms = int(round(seconds * 1000))
    hours = total_ms // 3_600_000
    total_ms %= 3_600_000
    minutes = total_ms // 60_000
    total_ms %= 60_000
    secs = total_ms // 1000
    ms = total_ms % 1000
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def to_markdown(segments: list[SubtitleSegment]) -> str:
    lines = ["# AI 同声传译字幕", ""]
    for index, segment in enumerate(exportable_segments(segments), start=1):
        end_time = segment.end_time if segment.end_time is not None else segment.start_time
        lines.extend(
            [
                f"## {index}. {segment.start_time:.1f}s - {end_time:.1f}s",
                "",
                f"**EN**: {segment.source_text}",
                "",
                f"**ZH**: {segment.translated_text}",
                "",
                f"`{segment.status.value}` / v{segment.version}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def to_srt(segments: list[SubtitleSegment]) -> str:
    blocks: list[str] = []
    for index, segment in enumerate(exportable_segments(segments), start=1):
        end_time = segment.end_time if segment.end_time is not None else segment.start_time + 2
        blocks.append(
            "\n".join(
                [
                    str(index),
                    f"{format_timestamp(segment.start_time)} --> {format_timestamp(end_time)}",
                    segment.translated_text,
                    segment.source_text,
                ]
            )
        )
    return "\n\n".join(blocks) + "\n"

