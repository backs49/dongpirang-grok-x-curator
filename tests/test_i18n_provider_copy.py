import re

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


def test_dead_keys_removed():
    from i18n import _T

    for key in (
        "ideas_copy_image_prompt_title",
        "ideas_copy_image_prompt_caption",
        "img_mascot_toggle",
        "img_mascot_help",
    ):
        assert key not in _T, key


def test_ideas_error_keys_use_pyeoneo_not_yoche():
    # ideas_error_* 는 새 워크스페이스에서도 그대로 노출되는 폴백 문구라
    # 평어체를 지킨다 — 어떤 문장도 요체("요.", "세요.")나 합쇼체("습니다.")로
    # 끝나면 안 된다.
    for key in (
        "ideas_error_insufficient_sources",
        "ideas_error_unsafe_personalized_request",
        "ideas_error_unverified_evidence",
        "ideas_error_grounded_tips_require_grok_cli",
    ):
        ko = _T[key]["ko"]
        for sentence in re.findall(r"[^.]+\.", ko):
            for banned in ("요.", "세요.", "습니다."):
                assert not sentence.endswith(banned), \
                    f"{key}.ko 에 평어체가 아닌 어미가 남아 있다: {sentence!r}"
