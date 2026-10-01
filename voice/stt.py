from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class Transcript:
    text: str
    language: str
    confidence: float
    provider: str

class SpeechToTextProvider(Protocol):
    def transcribe(self, audio: bytes, language: str) -> Transcript:
        ...

class BrowserTranscriptProvider:
    """Browser speech recognition is handled by the web client.

    This server-side provider exists as an explicit boundary so production
    deployments can replace it with Amazon Transcribe without changing the
    conversation orchestration layer.
    """

    def transcribe(self, audio: bytes, language: str) -> Transcript:
        raise NotImplementedError(
            "Server-side STT is not configured. Use browser STT locally or "
            "configure the Amazon Transcribe adapter for production."
        )

class AmazonTranscribeProvider:
    def transcribe(self, audio: bytes, language: str) -> Transcript:
        raise NotImplementedError(
            "Amazon Transcribe adapter is intentionally isolated here. "
            "Production wiring belongs in the infrastructure layer."
        )
