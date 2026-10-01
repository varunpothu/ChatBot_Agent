from voice.providers import VOICES

def test_male_and_female_voices_exist():
    genders = {v.gender for v in VOICES}
    assert {"male", "female"} <= genders

def test_uk_and_us_voices_exist():
    languages = {v.language for v in VOICES}
    assert {"en-GB", "en-US"} <= languages

def test_voice_ids_are_unique():
    ids = [v.voice_id for v in VOICES]
    assert len(ids) == len(set(ids))
