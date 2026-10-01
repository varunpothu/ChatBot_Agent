import pytest
from translation.service import TranslationService

class FakeProvider:
    def translate(self, text, source_language, target_language):
        return f"{target_language}:{text}"

@pytest.mark.asyncio
async def test_translation_service_uses_provider():
    service=TranslationService()
    service.provider=FakeProvider()
    assert await service.translate("hello","en","hi") == "hi:hello"

@pytest.mark.asyncio
async def test_same_language_skips_provider():
    service=TranslationService()
    service.provider=None
    assert await service.translate("hello","en","en") == "hello"
