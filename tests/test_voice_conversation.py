import pytest
from voice.conversation import VoicePreference, validate_preference, voice_response_policy

def test_valid_voice_preference():
    p = VoicePreference(voice_id="Brian", gender="male", language="en-GB", style="friendly")
    assert validate_preference(p, {"Brian", "Amy"}).voice_id == "Brian"

def test_unknown_voice_rejected():
    p = VoicePreference(voice_id="Unknown", gender="male", language="en-GB")
    with pytest.raises(ValueError):
        validate_preference(p, {"Brian", "Amy"})

def test_styles_are_explicit():
    assert "warm" in voice_response_policy("friendly").lower()
    assert "formal" in voice_response_policy("professional").lower()
    assert "short" in voice_response_policy("concise").lower()
