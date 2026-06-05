from dataclasses import dataclass, field

from app.models import SubtitleSegment, SubtitleStatus


LOCKED_STATUSES = {SubtitleStatus.FINAL}
COMMON_MISTRANSLATIONS = {
    "attention mechanism": ["张力机制", "注意机制", "关注机制"],
    "streaming pipeline": ["流管道", "串流管道"],
    "latency": ["潜伏期", "迟滞"],
    "glossary": ["词汇表", "名词表"],
}


@dataclass
class SubtitleStateManager:
    """Maintain ordered subtitles and versioned state updates."""

    segments: dict[str, SubtitleSegment] = field(default_factory=dict)

    def upsert(self, segment: SubtitleSegment) -> SubtitleSegment:
        current = self.segments.get(segment.id)
        if current and current.status in LOCKED_STATUSES:
            return current

        if current and segment.version <= current.version:
            segment = segment.model_copy(update={"version": current.version + 1})

        self.segments[segment.id] = segment
        return segment

    def recent_correctable(self, window_size: int) -> list[SubtitleSegment]:
        ordered = self.ordered()
        candidates = [
            segment for segment in ordered if segment.status not in LOCKED_STATUSES
        ]
        return candidates[-window_size:]

    def ordered(self) -> list[SubtitleSegment]:
        return sorted(self.segments.values(), key=lambda segment: segment.start_time)


class CorrectionEngine:
    """Apply glossary-assisted local repair to recent subtitle segments."""

    def __init__(self, glossary: dict[str, str], window_size: int = 5) -> None:
        self.glossary = {key.lower(): value for key, value in glossary.items()}
        self.window_size = window_size

    def correct_recent(self, manager: SubtitleStateManager) -> list[SubtitleSegment]:
        corrected: list[SubtitleSegment] = []
        for segment in manager.recent_correctable(self.window_size):
            repaired = self._repair_segment(segment)
            if repaired:
                corrected.append(manager.upsert(repaired))
        return corrected

    def _repair_segment(self, segment: SubtitleSegment) -> SubtitleSegment | None:
        source = segment.source_text.lower()
        translated = segment.translated_text
        changed_terms: list[str] = []

        for term, target in self.glossary.items():
            if term not in source:
                continue

            for mistranslation in COMMON_MISTRANSLATIONS.get(term, []):
                if mistranslation in translated and target not in translated:
                    translated = translated.replace(mistranslation, target)
                    changed_terms.append(term)

        if not changed_terms:
            return None

        return segment.model_copy(
            update={
                "translated_text": translated,
                "status": SubtitleStatus.CORRECTED,
                "version": segment.version + 1,
                "confidence": max(segment.confidence, 0.94),
                "changed_terms": sorted(set(segment.changed_terms + changed_terms)),
                "previous_translation": segment.translated_text,
            }
        )
