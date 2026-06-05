import tempfile
from pathlib import Path

from app.providers.base import ASRProvider, ASRResult


class FasterWhisperASRProvider(ASRProvider):
    def __init__(self, model_path: str, device: str = "auto", compute_type: str = "auto") -> None:
        self.model_path = model_path
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def _load_model(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise RuntimeError(
                    "faster-whisper is not installed. Install it before using ASR_PROVIDER=faster_whisper."
                ) from exc

            kwargs = {"device": self.device}
            if self.compute_type != "auto":
                kwargs["compute_type"] = self.compute_type
            self._model = WhisperModel(self.model_path, **kwargs)
        return self._model

    async def transcribe(self, audio: bytes, filename: str) -> ASRResult:
        suffix = Path(filename).suffix or ".wav"
        temp_path = ""
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(audio)
                temp_file.flush()

            segments, info = self._load_model().transcribe(temp_path, vad_filter=True)
            text = " ".join(segment.text.strip() for segment in segments).strip()
            confidence = max(0.0, min(1.0, float(getattr(info, "language_probability", 0.0))))
            language = getattr(info, "language", "en") or "en"
        finally:
            if temp_path:
                Path(temp_path).unlink(missing_ok=True)

        return ASRResult(text=text, confidence=confidence, language=language)
