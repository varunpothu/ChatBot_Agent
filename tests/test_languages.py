from language.registry import detect_script_language, get_language

def test_script_detection_for_indic_languages():
    assert detect_script_language("यह एक परीक्षा है") == "hi-IN"
    assert detect_script_language("ఇది ఒక పరీక్ష") == "te-IN"
    assert detect_script_language("இது ஒரு தேர்வு") == "ta-IN"

def test_language_metadata():
    assert get_language("hi-IN").translate_code == "hi"
    assert get_language("en-GB").polly_code == "en-GB"
