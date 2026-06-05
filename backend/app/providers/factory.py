from app.config import Settings
from app.providers.base import ASRProvider, TranslationProvider
from app.providers.mock import MockASRProvider, MockTranslationProvider


def create_asr_provider(settings: Settings) -> ASRProvider:
    if settings.asr_provider == "mock":
        return MockASRProvider()

    if settings.asr_provider == "faster_whisper":
        from app.providers.faster_whisper_provider import FasterWhisperASRProvider

        return FasterWhisperASRProvider(
            model_path=settings.asr_model_path,
            device=settings.asr_device,
            compute_type=settings.asr_compute_type,
        )

    raise ValueError(f"Unsupported ASR provider: {settings.asr_provider}")


def create_translation_provider(settings: Settings) -> TranslationProvider:
    if settings.translation_provider == "mock":
        return MockTranslationProvider()

    if settings.translation_provider == "openai_compatible":
        from app.providers.openai_compatible import OpenAICompatibleTranslationProvider

        return OpenAICompatibleTranslationProvider(
            api_key=settings.translation_api_key,
            model=settings.translation_model,
            base_url=settings.translation_base_url,
        )

    raise ValueError(f"Unsupported translation provider: {settings.translation_provider}")

