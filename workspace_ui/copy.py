"""워크스페이스 전용 문구 — 한국어/영어/일본어를 한 매핑에 모은다.

i18n.py 의 dict-of-dicts 모양을 그대로 따른다. 나중에 두 사전을 합칠 때
기계적으로 옮길 수 있어야 하기 때문이다. 여기 없는 키는 기존 i18n 사전으로
위임하므로, 레거시 Streamlit 앱과 공유하는 문구는 복사하지 않는다.

언어는 Streamlit 세션이 아니라 NiceGUI 사용자 스토리지에서 읽는다.
"""

from __future__ import annotations

from nicegui import app

from i18n import normalize_language, translate


DEFAULT_LANGUAGE = "ko"

# 설정 다이얼로그의 언어 선택지. i18n.LANGUAGES 와 같은 순서/표기를 쓴다.
LANGUAGE_OPTIONS = {"ko": "한국어", "en": "English", "ja": "日本語"}

_W = {
    # ─── 하단 내비게이션 ───
    "nav_create": {
        "ko": "만들기",
        "en": "Create",
        "ja": "作成",
    },
    "nav_polish": {
        "ko": "다듬기",
        "en": "Polish",
        "ja": "推敲",
    },
    "nav_publish": {
        "ko": "발행",
        "en": "Publish",
        "ja": "公開",
    },

    # ─── 영역 안내문 ───
    "create_hint": {
        "ko": "주제 한 줄이면 방향 세 개를 받고, 그중 하나로 포스트 한 편을 쓴다.",
        "en": "One line of topic gives three directions; pick one and write a single post.",
        "ja": "テーマを一行書けば方向を3つ受け取り、その1つでポストを1本書く。",
    },
    "polish_hint": {
        "ko": "이미 써 둔 포스트를 x-algorithm 기준으로 다듬는다.",
        "en": "Rework a post you already wrote against x-algorithm scoring.",
        "ja": "すでに書いたポストを x-algorithm の基準で磨き直す。",
    },
    "publish_hint": {
        "ko": "초안, 예약, 발행 기록을 한 화면에서 본다.",
        "en": "See drafts, schedules, and publishing history in one place.",
        "ja": "下書き・予約・公開履歴を一画面で見る。",
    },
    "area_pending": {
        "ko": "이 영역은 곧 연결된다.",
        "en": "This area is being wired up.",
        "ja": "この領域はまもなく接続される。",
    },

    # ─── 설정 ───
    "settings_title": {
        "ko": "설정",
        "en": "Settings",
        "ja": "設定",
    },
    "settings_open": {
        "ko": "설정 열기",
        "en": "Open settings",
        "ja": "設定を開く",
    },
    "settings_language": {
        "ko": "언어",
        "en": "Language",
        "ja": "言語",
    },
    "settings_theme": {
        "ko": "테마",
        "en": "Theme",
        "ja": "テーマ",
    },
    "settings_theme_light": {
        "ko": "밝게",
        "en": "Light",
        "ja": "ライト",
    },
    "settings_theme_dark": {
        "ko": "어둡게",
        "en": "Dark",
        "ja": "ダーク",
    },
    "settings_engine": {
        "ko": "엔진",
        "en": "Engine",
        "ja": "エンジン",
    },
    "settings_engine_hint": {
        "ko": "로컬 CLI 와 데모만 쓴다. 이 워크스페이스는 API 키를 받지 않는다.",
        "en": "Local CLIs and Demo only. This workspace never takes an API key.",
        "ja": "ローカル CLI と Demo のみ。このワークスペースは API キーを受け取らない。",
    },
    "settings_api_notice": {
        "ko": "xAI API 가 필요하면 기존 Streamlit 앱에서 쓴다. 여기서는 키를 입력받지도, 저장하지도 않는다.",
        "en": "Need the xAI API? Use the legacy Streamlit app. Keys are never entered or stored here.",
        "ja": "xAI API が必要なら従来の Streamlit アプリを使う。ここではキーを入力も保存もしない。",
    },
    "settings_save": {
        "ko": "저장",
        "en": "Save",
        "ja": "保存",
    },
    "settings_close": {
        "ko": "닫기",
        "en": "Close",
        "ja": "閉じる",
    },
}


def current_language() -> str:
    """사용자 스토리지에 저장된 언어. 스토리지가 없으면 한국어."""
    return normalize_language(stored_language())


def stored_language() -> str | None:
    """저장된 언어 원본값. UI 컨텍스트 밖에서는 None."""
    try:
        return app.storage.user.get("language")
    except (RuntimeError, KeyError, AssertionError):
        # 요청 컨텍스트 밖(워커/임포트 시점)에서는 스토리지가 없다.
        return None


def copy(key: str, language: str | None = None, **kwargs) -> str:
    """워크스페이스 문구를 돌려준다. 매핑에 없으면 i18n 사전으로 위임한다."""
    lang = current_language() if language is None else normalize_language(language)
    entry = _W.get(key)
    if entry is None:
        return translate(key, lang, **kwargs)
    text = entry.get(lang, entry.get(DEFAULT_LANGUAGE, key))
    # i18n.translate 와 같은 규칙: kwargs 가 있을 때만 format 한다.
    # 문구에 들어 있는 리터럴 중괄호가 KeyError 를 내지 않게 하기 위해서다.
    if kwargs:
        text = text.format(**kwargs)
    return text
