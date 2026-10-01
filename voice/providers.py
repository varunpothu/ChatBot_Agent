from dataclasses import dataclass

@dataclass(frozen=True)
class Voice:
    voice_id: str
    label: str
    language: str

VOICES = [
    Voice("en-GB-voice-1","British voice 1","en-GB"),
    Voice("en-GB-voice-2","British voice 2","en-GB"),
    Voice("en-US-voice-1","US voice 1","en-US"),
    Voice("en-US-voice-2","US voice 2","en-US"),
]

class VoiceProvider:
    def synthesize(self, text: str, voice_id: str) -> bytes:
        raise NotImplementedError("Connect Amazon Polly or another TTS provider.")
