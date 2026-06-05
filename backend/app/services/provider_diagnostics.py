from importlib.util import find_spec
from pathlib import Path

from app.config import Settings
from app.models import ProviderDiagnostic


def build_provider_diagnostics(settings: Settings) -> list[ProviderDiagnostic]:
    return [
        _asr_diagnostic(settings),
        _translation_diagnostic(settings),
    ]


def _asr_diagnostic(settings: Settings) -> ProviderDiagnostic:
    if settings.asr_provider == "mock":
        return ProviderDiagnostic(
            name="mock",
            kind="asr",
            ready=True,
            mode="demo",
            message="Mock ASR is ready for deterministic demo playback.",
            action="Use ASR_PROVIDER=faster_whisper when switching to a local real ASR model.",
        )

    if settings.asr_provider == "faster_whisper":
        dependency_ready = find_spec("faster_whisper") is not None
        model_path = Path(settings.asr_model_path)
        path_ready = model_path.exists() or not _looks_like_local_path(settings.asr_model_path)
        ready = dependency_ready and path_ready
        if ready:
            message = "faster-whisper dependency and model reference are available."
            action = "Keep ASR_MODEL_PATH, ASR_DEVICE and ASR_COMPUTE_TYPE aligned with the demo machine."
        elif not dependency_ready:
            message = "faster-whisper is not installed in the current Python environment."
            action = "Run pip install -e backend[ai] before using ASR_PROVIDER=faster_whisper."
        else:
            message = f"ASR model path does not exist: {settings.asr_model_path}"
            action = "Download the model or set ASR_MODEL_PATH to an existing local model directory."

        return ProviderDiagnostic(
            name="faster_whisper",
            kind="asr",
            ready=ready,
            mode="real",
            message=message,
            action=action,
        )

    return ProviderDiagnostic(
        name=settings.asr_provider,
        kind="asr",
        ready=False,
        mode="real",
        message=f"Unsupported ASR provider: {settings.asr_provider}",
        action="Set ASR_PROVIDER to mock or faster_whisper.",
    )


def _translation_diagnostic(settings: Settings) -> ProviderDiagnostic:
    if settings.translation_provider == "mock":
        return ProviderDiagnostic(
            name="mock",
            kind="translation",
            ready=True,
            mode="demo",
            message="Mock translation is ready for deterministic demo playback.",
            action="Use TRANSLATION_PROVIDER=openai_compatible when switching to a real translation API.",
        )

    if settings.translation_provider == "openai_compatible":
        has_key = bool(settings.translation_api_key.strip())
        has_model = bool(settings.translation_model.strip())
        has_base_url = settings.translation_base_url.startswith(("http://", "https://"))
        ready = has_key and has_model and has_base_url
        missing: list[str] = []
        if not has_key:
            missing.append("TRANSLATION_API_KEY")
        if not has_model:
            missing.append("TRANSLATION_MODEL")
        if not has_base_url:
            missing.append("TRANSLATION_BASE_URL")

        return ProviderDiagnostic(
            name="openai_compatible",
            kind="translation",
            ready=ready,
            mode="real",
            message=(
                "OpenAI-compatible translation configuration is complete."
                if ready
                else f"Missing or invalid translation configuration: {', '.join(missing)}"
            ),
            action=(
                "Keep API quota and network access stable for the demo."
                if ready
                else "Set the missing environment variables before enabling the real translation provider."
            ),
        )

    return ProviderDiagnostic(
        name=settings.translation_provider,
        kind="translation",
        ready=False,
        mode="real",
        message=f"Unsupported translation provider: {settings.translation_provider}",
        action="Set TRANSLATION_PROVIDER to mock or openai_compatible.",
    )


def _looks_like_local_path(value: str) -> bool:
    return value.startswith((".", "/", "\\")) or ":" in value
