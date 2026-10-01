from dataclasses import dataclass
from typing import Literal

VoiceGender=Literal["male","female"]
ConversationStyle=Literal["friendly","professional","concise"]

@dataclass(frozen=True)
class VoicePreference:
    voice_id:str="Brian"
    gender:VoiceGender="male"
    language:str="en-GB"
    style:ConversationStyle="friendly"
    auto_speak:bool=False

@dataclass(frozen=True)
class ConversationTurn:
    user_text:str
    assistant_text:str
    grounded:bool
    citations:int
    voice_id:str
    language:str
    latency_ms:float

def validate_preference(preference:VoicePreference,allowed_voice_ids:set[str],allowed_languages:set[str])->VoicePreference:
    if preference.voice_id not in allowed_voice_ids:raise ValueError("Unknown voice")
    if preference.language not in allowed_languages:raise ValueError("Unsupported language")
    if preference.gender not in {"male","female"}:raise ValueError("Unsupported voice gender")
    if preference.style not in {"friendly","professional","concise"}:raise ValueError("Unsupported conversation style")
    return preference

def voice_response_policy(style:ConversationStyle)->dict[str,str]:
    return {
        "friendly":"Use warm, clear, encouraging language while preserving factual precision.",
        "professional":"Use clear, formal and direct language while preserving factual precision.",
        "concise":"Use short, direct responses and avoid unnecessary repetition.",
    }[style]
