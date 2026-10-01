from language.registry import LANGUAGES

DEFAULT_POLLY_VOICES = {
    "en-GB": {"male": "Brian", "female": "Amy"},
    "en-US": {"male": "Matthew", "female": "Joanna"},
    "hi-IN": {"male": None, "female": "Aditi"},
    "es-ES": {"male": "Enrique", "female": "Lucia"},
    "fr-FR": {"male": "Mathieu", "female": "Lea"},
    "de-DE": {"male": "Hans", "female": "Marlene"},
    "it-IT": {"male": "Giorgio", "female": "Carla"},
    "pt-PT": {"male": "Cristiano", "female": "Ines"},
    "ja-JP": {"male": "Takumi", "female": "Mizuki"},
    "zh-CN": {"male": None, "female": "Zhiyu"},
    "ar-SA": {"male": None, "female": "Zeina"},
}

def available_polly_voice(language: str, gender: str = "female") -> str | None:
    return DEFAULT_POLLY_VOICES.get(language, {}).get(gender)

def language_capabilities() -> list[dict]:
    return [
        {
            "code": language.code,
            "name": language.name,
            "native_name": language.native_name,
            "speech_code": language.speech_code,
            "translate_code": language.translate_code,
            "polly_code": language.polly_code,
            "cloud_tts": language.polly_code is not None,
        }
        for language in LANGUAGES
    ]
