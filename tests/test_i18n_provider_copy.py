from i18n import _T


GENERIC_PROVIDER_COPY_KEYS = [
    "api_required",
    "demo_banner",
    "demo_key_needed",
    "opt_spinner",
    "ideas_spinner",
    "cur_caption",
    "cur_spinner",
    "thr_spinner",
    "sch_spinner",
    "ab_spinner",
    "risk_spinner",
]


def test_generic_provider_copy_does_not_claim_grok_only():
    for key in GENERIC_PROVIDER_COPY_KEYS:
        entry = _T[key]
        for lang, text in entry.items():
            assert "Grok" not in text, f"{key}.{lang} still claims Grok-only execution"


def test_ideas_mode_ui_keys_exist():
    from i18n import _T

    keys = [
        "ideas_mode_label", "img_style_label",
        "ideas_char_count", "ideas_len_warn",
        "ideas_lint_s1", "ideas_lint_s2",
        "ideas_to_queue_btn", "ideas_queued_toast", "ideas_queue_error",
        "voice_expander", "voice_input_label", "voice_help",
        "voice_analyze_btn", "voice_saved", "voice_need_input", "voice_count",
    ]
    for key in keys:
        assert key in _T, key
        for lang in ("ko", "en", "ja"):
            assert _T[key][lang], f"{key}/{lang}"
