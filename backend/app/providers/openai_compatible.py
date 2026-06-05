import httpx

from app.providers.base import TranslationProvider, TranslationResult


class OpenAICompatibleTranslationProvider(TranslationProvider):
    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def translate(self, text: str, glossary: dict[str, str]) -> TranslationResult:
        if not self.api_key:
            raise RuntimeError("TRANSLATION_API_KEY is required for openai_compatible provider.")

        glossary_prompt = "\n".join(f"- {source} => {target}" for source, target in glossary.items())
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a real-time interpretation assistant. Translate English into concise, "
                        "natural Chinese. Respect the glossary exactly when terms appear."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Glossary:\n{glossary_prompt}\n\nEnglish:\n{text}\n\nChinese:",
                },
            ],
            "temperature": 0.2,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        translated = data["choices"][0]["message"]["content"].strip()
        hits = [source for source in glossary if source.lower() in text.lower()]
        return TranslationResult(text=translated, glossary_hits=hits)

