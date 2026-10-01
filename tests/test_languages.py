from language.registry import detect_script_language, get_language

def test_script_detection_for_indic_languages():
    assert detect_script_language("यह एक परीक्षा है") == "hi-IN"
    assert detect_script_language("ఇది ఒక పరీక్ష") == "te-IN"
    assert detect_script_language("இது ஒரு தேர்வு") == "ta-IN"

def test_script_detection_for_cjk():
    assert detect_script_language("こんにちは") == "ja-JP"
    assert detect_script_language("你好") == "zh-CN"

def test_language_metadata():
    assert get_language("hi-IN").translate_code == "hi"
    assert get_language("en-GB").polly_code == "en-GB"

def test_auto_detect_defaults_latin_to_uk_english():
    assert detect_script_language("What is the course fee?") == "en-GB"

def test_arabic_and_urdu_are_not_silently_identical():
    assert detect_script_language("السلام عليكم") == "ar-SA"
    assert detect_script_language("آپ کیسے ہیں") == "ur-PK"
