from functools import lru_cache
from os import getenv

from pydantic import BaseModel


class Settings(BaseModel):
    asr_provider: str = "mock"
    asr_model_path: str = "./models/faster-whisper-small"
    asr_device: str = "auto"
    asr_compute_type: str = "auto"
    translation_provider: str = "mock"
    translation_api_key: str = ""
    translation_model: str = "gpt-4o-mini"
    translation_base_url: str = "https://api.openai.com/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings(
        asr_provider=getenv("ASR_PROVIDER", "mock"),
        asr_model_path=getenv("ASR_MODEL_PATH", "./models/faster-whisper-small"),
        asr_device=getenv("ASR_DEVICE", "auto"),
        asr_compute_type=getenv("ASR_COMPUTE_TYPE", "auto"),
        translation_provider=getenv("TRANSLATION_PROVIDER", "mock"),
        translation_api_key=getenv("TRANSLATION_API_KEY", ""),
        translation_model=getenv("TRANSLATION_MODEL", "gpt-4o-mini"),
        translation_base_url=getenv("TRANSLATION_BASE_URL", "https://api.openai.com/v1"),
    )

