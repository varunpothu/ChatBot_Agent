from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Voice:
    voice_id: str
    label: str
    language: str
    gender: str
    style: str = "conversational"

VOICES = [
    Voice("Matthew","US Male","en-US","male"),
    Voice("Joanna","US Female","en-US","female"),
    Voice("Brian","British Male","en-GB","male"),
    Voice("Amy","British Female","en-GB","female"),
]

class AmazonPollyProvider:
    def __init__(self):
        import boto3
        self.client = boto3.client("polly", region_name=os.getenv("AWS_REGION", "eu-west-2"))

    def synthesize(self, text: str, voice_id: str) -> bytes:
        result = self.client.synthesize_speech(
            Text=text,
            VoiceId=voice_id,
            OutputFormat="mp3",
            Engine="neural",
        )
        return result["AudioStream"].read()
