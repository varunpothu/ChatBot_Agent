import asyncio
import os
from translation.aws import AmazonTranslateProvider

class TranslationService:
    def __init__(self):
        provider=os.getenv("TRANSLATION_PROVIDER","none").lower()
        self.provider=AmazonTranslateProvider() if provider=="aws_translate" else None

    @property
    def enabled(self) -> bool:
        return self.provider is not None

    async def translate(self, text: str, source_language: str, target_language: str) -> str:
        if source_language == target_language:
            return text
        if not self.provider:
            raise RuntimeError("Multilingual translation is not configured.")
        return await asyncio.to_thread(
            self.provider.translate,
            text,
            source_language,
            target_language,
        )
