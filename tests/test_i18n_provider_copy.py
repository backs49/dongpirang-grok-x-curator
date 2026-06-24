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
