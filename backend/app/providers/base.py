from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ASRResult:
    text: str
    confidence: float
    language: str = "en"


@dataclass(frozen=True)
class TranslationResult:
    text: str
    glossary_hits: list[str]


class ASRProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio: bytes, filename: str) -> ASRResult:
        """Transcribe audio bytes into source-language text."""


class TranslationProvider(ABC):
    @abstractmethod
    async def translate(self, text: str, glossary: dict[str, str]) -> TranslationResult:
        """Translate source text into Chinese."""

