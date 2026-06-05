from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class SubtitleStatus(StrEnum):
    PARTIAL = "partial"
    STABLE = "stable"
    CORRECTED = "corrected"
    FINAL = "final"


class GlossaryTerm(BaseModel):
    source: str
    target: str
    category: str
    description: str


class SubtitleSegment(BaseModel):
    id: str
    source_text: str = Field(alias="sourceText")
    translated_text: str = Field(alias="translatedText")
    status: SubtitleStatus
    version: int
    start_time: float = Field(alias="startTime")
    end_time: float | None = Field(default=None, alias="endTime")
    confidence: float
    changed_terms: list[str] = Field(default_factory=list, alias="changedTerms")
    previous_translation: str | None = Field(default=None, alias="previousTranslation")

    model_config = {"populate_by_name": True}


class MetricSnapshot(BaseModel):
    first_subtitle_latency_ms: int | None = Field(default=None, alias="firstSubtitleLatencyMs")
    correction_latency_ms: int | None = Field(default=None, alias="correctionLatencyMs")
    glossary_hit_rate: float = Field(alias="glossaryHitRate")
    final_stability_rate: float = Field(alias="finalStabilityRate")
    correction_count: int = Field(alias="correctionCount")
    final_count: int = Field(alias="finalCount")
    subtitle_count: int = Field(alias="subtitleCount")

    model_config = {"populate_by_name": True}


class CorrectionTrace(BaseModel):
    segment_id: str = Field(alias="segmentId")
    trigger: str
    reason: str
    previous_translation: str = Field(alias="previousTranslation")
    corrected_translation: str = Field(alias="correctedTranslation")
    changed_terms: list[str] = Field(alias="changedTerms")
    latency_ms: int = Field(alias="latencyMs")
    from_version: int = Field(alias="fromVersion")
    to_version: int = Field(alias="toVersion")

    model_config = {"populate_by_name": True}


class SubtitleRevision(BaseModel):
    segment_id: str = Field(alias="segmentId")
    version: int
    status: SubtitleStatus
    translated_text: str = Field(alias="translatedText")
    confidence: float
    changed_terms: list[str] = Field(alias="changedTerms")
    previous_translation: str | None = Field(default=None, alias="previousTranslation")

    model_config = {"populate_by_name": True}


class DemoEvent(BaseModel):
    type: Literal["session", "glossary", "segment", "metric", "correction", "done"]
    delay_ms: int = Field(default=0, alias="delayMs")
    message: str | None = None
    segment: SubtitleSegment | None = None
    metrics: MetricSnapshot | None = None
    glossary: list[GlossaryTerm] | None = None
    correction: CorrectionTrace | None = None

    model_config = {"populate_by_name": True}


class VideoDemoSource(BaseModel):
    title: str
    page_url: str = Field(alias="pageUrl")
    media_url: str = Field(alias="mediaUrl")
    license: str
    attribution: str
    duration_seconds: int = Field(alias="durationSeconds")
    scenario: str
    note: str

    model_config = {"populate_by_name": True}


class AudioDemoResult(BaseModel):
    filename: str
    bytes_received: int = Field(alias="bytesReceived")
    source_text: str = Field(alias="sourceText")
    translated_text: str = Field(alias="translatedText")
    confidence: float
    glossary_hits: list[str] = Field(alias="glossaryHits")
    provider: str

    model_config = {"populate_by_name": True}


class ProviderDiagnostic(BaseModel):
    name: str
    kind: Literal["asr", "translation"]
    ready: bool
    mode: Literal["demo", "real"]
    message: str
    action: str


class SummaryResult(BaseModel):
    title: str
    summary: str
    key_points: list[str] = Field(alias="keyPoints")
    keywords: list[str]
    glossary_terms: list[str] = Field(alias="glossaryTerms")
    correction_notes: list[str] = Field(alias="correctionNotes")

    model_config = {"populate_by_name": True}
