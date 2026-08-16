from i18n import get_lang_instruction, normalize_language, translate


def test_translate_accepts_an_explicit_language_without_streamlit_state():
    assert translate("app_title", "en") == "Dongpirang Cat Grok 𝕏"
    assert translate("app_title", "ja") == "東ピラン猫 Grok 𝕏"


def test_invalid_language_uses_korean_and_language_instruction_is_explicit():
    assert normalize_language("fr") == "ko"
    assert "ENGLISH" in get_lang_instruction("en")
    assert "日本語" in get_lang_instruction("ja")
    assert get_lang_instruction("ko") == ""
