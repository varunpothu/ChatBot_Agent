from voice.providers import VOICES

def test_voice_catalog_has_male_and_female_options():
    genders = {voice.gender for voice in VOICES}
    assert {"male", "female"} <= genders

def test_voice_catalog_has_uk_and_us_options():
    languages = {voice.language for voice in VOICES}
    assert {"en-GB", "en-US"} <= languages

def test_voice_ids_are_unique():
    ids = [voice.voice_id for voice in VOICES]
    assert len(ids) == len(set(ids))
