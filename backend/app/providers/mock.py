from app.providers.base import ASRProvider, ASRResult, TranslationProvider, TranslationResult


class MockASRProvider(ASRProvider):
    async def transcribe(self, audio: bytes, filename: str) -> ASRResult:
        if not audio:
            return ASRResult(text="", confidence=0.0)

        return ASRResult(
            text=(
                "The model uses an attention mechanism to decide which words matter. "
                "A glossary keeps technical terms consistent."
            ),
            confidence=0.93,
        )


class MockTranslationProvider(TranslationProvider):
    async def translate(self, text: str, glossary: dict[str, str]) -> TranslationResult:
        hits = [term for term in glossary if term in text.lower()]
        translated = "这个模型使用注意力机制来判断哪些词更重要。术语表可以保持技术术语翻译一致。"
        return TranslationResult(text=translated, glossary_hits=hits)

