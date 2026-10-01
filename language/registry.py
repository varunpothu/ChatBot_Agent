from dataclasses import dataclass

@dataclass(frozen=True)
class Language:
    code: str
    name: str
    speech_code: str
    translate_code: str
    native_name: str
    model_name: str
    polly_code: str | None = None

LANGUAGES = [
    Language("en-GB","English (UK)","en-GB","en","English","English","en-GB"),
    Language("en-US","English (US)","en-US","en","English","English","en-US"),
    Language("hi-IN","Hindi","hi-IN","hi","हिन्दी","Hindi","hi-IN"),
    Language("te-IN","Telugu","te-IN","te","తెలుగు","Telugu"),
    Language("ta-IN","Tamil","ta-IN","ta","தமிழ்","Tamil"),
    Language("bn-IN","Bengali","bn-IN","bn","বাংলা","Bengali"),
    Language("mr-IN","Marathi","mr-IN","mr","मराठी","Marathi"),
    Language("gu-IN","Gujarati","gu-IN","gu","ગુજરાતી","Gujarati"),
    Language("pa-IN","Punjabi","pa-IN","pa","ਪੰਜਾਬੀ","Punjabi"),
    Language("ur-PK","Urdu","ur-PK","ur","اردو","Urdu"),
    Language("kn-IN","Kannada","kn-IN","kn","ಕನ್ನಡ","Kannada"),
    Language("ml-IN","Malayalam","ml-IN","ml","മലയാളം","Malayalam"),
    Language("es-ES","Spanish","es-ES","es","Español","Spanish","es-ES"),
    Language("fr-FR","French","fr-FR","fr","Français","French","fr-FR"),
    Language("de-DE","German","de-DE","de","Deutsch","German","de-DE"),
    Language("ar-SA","Arabic","ar-SA","ar","العربية","Arabic","arb"),
    Language("it-IT","Italian","it-IT","it","Italiano","Italian","it-IT"),
    Language("pt-PT","Portuguese","pt-PT","pt","Português","Portuguese","pt-PT"),
    Language("ja-JP","Japanese","ja-JP","ja","日本語","Japanese","ja-JP"),
    Language("zh-CN","Chinese (Simplified)","zh-CN","zh","中文","Chinese","cmn-CN"),
]

BY_CODE={x.code:x for x in LANGUAGES}

def get_language(code: str) -> Language:
    try:
        return BY_CODE[code]
    except KeyError:
        raise ValueError(f"Unsupported language: {code}") from None

def detect_script_language(text: str) -> str:
    counts={
        "hi-IN":sum("\u0900"<=c<="\u097F" for c in text),
        "bn-IN":sum("\u0980"<=c<="\u09FF" for c in text),
        "gu-IN":sum("\u0A80"<=c<="\u0AFF" for c in text),
        "pa-IN":sum("\u0A00"<=c<="\u0A7F" for c in text),
        "ta-IN":sum("\u0B80"<=c<="\u0BFF" for c in text),
        "te-IN":sum("\u0C00"<=c<="\u0C7F" for c in text),
        "kn-IN":sum("\u0C80"<=c<="\u0CFF" for c in text),
        "ml-IN":sum("\u0D00"<=c<="\u0D7F" for c in text),
        "ur-PK":sum("\u0600"<=c<="\u06FF" for c in text),
        "ar-SA":sum("\u0600"<=c<="\u06FF" for c in text),
    }
    best=max(counts,key=counts.get)
    # Arabic-script text is ambiguous between Arabic and Urdu; explicit
    # selection is therefore preferred for those languages.
    if best in {"ur-PK","ar-SA"}:
        return best
    return best if counts[best]>=2 else "en-GB"
