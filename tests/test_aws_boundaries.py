import asyncio

import pytest

from knowledge.textract import AmazonTextractProvider
from voice.transcribe_streaming import AmazonTranscribeStreamingProvider, TranscribeAudioConfig


def test_textract_maps_lines_to_source_locations():
    class FakeTextractClient:
        def detect_document_text(self, **_kwargs):
            return {
                "Blocks": [
                    {"BlockType": "PAGE", "Page": 1},
                    {"BlockType": "LINE", "Text": "First line", "Page": 1},
                    {"BlockType": "LINE", "Text": "Second line", "Page": 1},
                ]
            }

    provider = object.__new__(AmazonTextractProvider)
    provider.client = FakeTextractClient()
    result = provider.detect_s3("bucket", "documents/file.png", filename="file.png")

    assert result.text == "First line\nSecond line"
    assert [x.page for x in result.locations] == [1, 1]


def test_transcribe_provider_reports_missing_optional_sdk(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "amazon_transcribe":
            raise ImportError("missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    provider = AmazonTranscribeStreamingProvider(region="eu-west-2")

    async def one_chunk():
        yield b"audio"

    with pytest.raises(RuntimeError, match="optional voice dependency"):
        asyncio.run(provider.transcribe_stream(one_chunk(), TranscribeAudioConfig()))
