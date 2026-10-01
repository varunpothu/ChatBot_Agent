from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import AsyncIterable, Iterable

from voice.stt import Transcript


@dataclass(frozen=True)
class TranscribeAudioConfig:
    language: str = "en-GB"
    sample_rate_hz: int = 16000
    media_encoding: str = "pcm"


class AmazonTranscribeStreamingProvider:
    """Server-side real-time Amazon Transcribe adapter."""

    def __init__(self, region: str | None = None):
        self.region = region or os.getenv("AWS_REGION", "eu-west-2")

    async def transcribe_stream(
        self,
        audio_chunks: AsyncIterable[bytes] | Iterable[bytes],
        config: TranscribeAudioConfig,
    ) -> Transcript:
        try:
            from amazon_transcribe.client import TranscribeStreamingClient
            from amazon_transcribe.handlers import TranscriptResultStreamHandler
        except ImportError as exc:
            raise RuntimeError(
                "Install the optional voice dependency before enabling Amazon Transcribe streaming."
            ) from exc

        client = TranscribeStreamingClient(region=self.region)
        stream = await client.start_stream_transcription(
            language_code=config.language,
            media_sample_rate_hz=config.sample_rate_hz,
            media_encoding=config.media_encoding,
        )
        final_segments: list[str] = []

        class Handler(TranscriptResultStreamHandler):
            async def handle_transcript_event(self, transcript_event):
                for result in transcript_event.transcript.results:
                    if getattr(result, "is_partial", False):
                        continue
                    alternatives = getattr(result, "alternatives", []) or []
                    if alternatives:
                        text = (getattr(alternatives[0], "transcript", "") or "").strip()
                        if text:
                            final_segments.append(text)

        async def write():
            if hasattr(audio_chunks, "__aiter__"):
                async for chunk in audio_chunks:
                    if chunk:
                        await stream.input_stream.send_audio_event(audio_chunk=chunk)
            else:
                for chunk in audio_chunks:
                    if chunk:
                        await stream.input_stream.send_audio_event(audio_chunk=chunk)
            await stream.input_stream.end_stream()

        await asyncio.gather(write(), Handler(stream.output_stream).handle_events())
        return Transcript(
            text=" ".join(final_segments).strip(),
            language=config.language,
            confidence=0.0,
            provider="amazon-transcribe-streaming",
        )

    def transcribe(self, audio: bytes, language: str) -> Transcript:
        async def chunks():
            size = int(os.getenv("TRANSCRIBE_CHUNK_BYTES", "32000"))
            for start in range(0, len(audio), size):
                yield audio[start:start + size]

        return asyncio.run(
            self.transcribe_stream(
                chunks(),
                TranscribeAudioConfig(
                    language=language,
                    sample_rate_hz=int(os.getenv("TRANSCRIBE_SAMPLE_RATE_HZ", "16000")),
                    media_encoding=os.getenv("TRANSCRIBE_MEDIA_ENCODING", "pcm"),
                ),
            )
        )
