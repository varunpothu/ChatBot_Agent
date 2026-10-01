from dataclasses import dataclass
import hashlib
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
    Voice("Aditi","Hindi Female","hi-IN","female"),
    Voice("Lucia","Spanish Female","es-ES","female"),
    Voice("Enrique","Spanish Male","es-ES","male"),
    Voice("Mathieu","French Male","fr-FR","male"),
    Voice("Lea","French Female","fr-FR","female"),
    Voice("Hans","German Male","de-DE","male"),
    Voice("Marlene","German Female","de-DE","female"),
    Voice("Giorgio","Italian Male","it-IT","male"),
    Voice("Carla","Italian Female","it-IT","female"),
    Voice("Ines","Portuguese Female","pt-PT","female"),
    Voice("Cristiano","Portuguese Male","pt-PT","male"),
    Voice("Takumi","Japanese Male","ja-JP","male"),
    Voice("Mizuki","Japanese Female","ja-JP","female"),
    Voice("Zhiyu","Chinese Female","zh-CN","female"),
    Voice("Zeina","Arabic Female","ar-SA","female"),
]

class AmazonPollyProvider:
    def __init__(self):
        import boto3
        self.client=boto3.client("polly",region_name=os.getenv("AWS_REGION","eu-west-2"))
        self.engine=os.getenv("POLLY_ENGINE","neural")

    @staticmethod
    def cache_key(text: str, voice_id: str, engine: str, language: str="") -> str:
        return hashlib.sha256(f"{engine}|{voice_id}|{language}|{text}".encode()).hexdigest()

    def synthesize(self, text: str, voice_id: str, language: str | None = None) -> bytes:
        kwargs={
            "Text":text[:3000],
            "VoiceId":voice_id,
            "OutputFormat":"mp3",
            "Engine":self.engine,
        }
        if language:
            kwargs["LanguageCode"]=language
        result=self.client.synthesize_speech(**kwargs)
        return result["AudioStream"].read()
