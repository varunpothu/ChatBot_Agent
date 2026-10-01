from dataclasses import dataclass
import hashlib
import os
import time

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
        self.voice_cache_ttl=float(os.getenv("POLLY_VOICE_CACHE_TTL_SECONDS","21600"))
        self._voice_cache={}


    def discover_voices(self, language: str | None = None, engine: str | None = None) -> list[Voice]:
        """Discover actual Polly voices for the configured region and engine."""
        cache_key=(language or "", engine or self.engine)
        cached=self._voice_cache.get(cache_key)
        now=time.monotonic()
        if cached and now-cached[0] < self.voice_cache_ttl:
            return cached[1]

        kwargs={"Engine":engine or self.engine}
        if language:
            kwargs["LanguageCode"]=language
            kwargs["IncludeAdditionalLanguageCodes"]=True

        voices=[]
        token=None
        while True:
            if token:
                kwargs["NextToken"]=token
            else:
                kwargs.pop("NextToken",None)
            response=self.client.describe_voices(**kwargs)
            for item in response.get("Voices",[]):
                voice_id=item.get("Id","")
                if voice_id:
                    voices.append(
                        Voice(
                            voice_id,
                            item.get("Name") or voice_id,
                            item.get("LanguageCode",""),
                            str(item.get("Gender","")).lower(),
                            style="polly",
                        )
                    )
            token=response.get("NextToken")
            if not token:
                break

        self._voice_cache[cache_key]=(now,voices)
        return voices

    def resolve_voice(
        self,
        language: str,
        gender: str,
        requested_voice_id: str | None = None,
        fallback_voice_id: str | None = None,
    ) -> str | None:
        candidates=self.discover_voices(language=language,engine=self.engine)
        by_id={voice.voice_id:voice for voice in candidates}
        if requested_voice_id in by_id:
            return requested_voice_id
        target_gender=gender.lower()
        for voice in candidates:
            if voice.gender.lower()==target_gender:
                return voice.voice_id
        return fallback_voice_id if fallback_voice_id in by_id else None

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
