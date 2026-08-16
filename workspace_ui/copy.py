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

    # ─── 만들기: 주제 한 줄 ───
    "create_topic_label": {
        "ko": "무엇에 대해 쓸까",
        "en": "What are you writing about?",
        "ja": "何について書く?",
    },
    "create_topic_placeholder": {
        "ko": "주제 한 줄. 예) 배포 실수로 배운 것",
        "en": "One line. e.g. what a bad deploy taught me",
        "ja": "テーマを一行。例) デプロイ失敗から学んだこと",
    },
    "create_topic_required": {
        "ko": "주제 한 줄을 먼저 적는다.",
        "en": "Write one line of topic first.",
        "ja": "まずテーマを一行書く。",
    },
    "create_type_ideas": {
        "ko": "일반 아이디어",
        "en": "Regular idea",
        "ja": "通常アイデア",
    },
    "create_type_grounded": {
        "ko": "사실 기반 팁",
        "en": "Fact-based tip",
        "ja": "事実ベースのヒント",
    },
    "create_options": {
        "ko": "옵션",
        "en": "Options",
        "ja": "オプション",
    },
    "create_length_auto": {
        "ko": "자동",
        "en": "Auto",
        "ja": "自動",
    },
    "create_directions_cta": {
        "ko": "방향 3개 보기",
        "en": "See three directions",
        "ja": "方向を3つ見る",
    },
    "create_busy": {
        "ko": "이미 만드는 중이다. 끝나면 카드가 뜬다.",
        "en": "Already working. The cards appear when it finishes.",
        "ja": "すでに作成中。終わればカードが出る。",
    },

    # ─── 만들기: 방향 카드 ───
    "create_directions_title": {
        "ko": "방향 3개",
        "en": "Three directions",
        "ja": "3つの方向",
    },
    "create_directions_hint": {
        "ko": "하나만 고른다. 고른 방향으로만 한 편을 쓴다.",
        "en": "Pick one. Only that direction becomes a post.",
        "ja": "1つだけ選ぶ。選んだ方向だけを1本にする。",
    },
    "create_field_angle": {
        "ko": "각도",
        "en": "Angle",
        "ja": "角度",
    },
    "create_field_core": {
        "ko": "핵심",
        "en": "Core",
        "ja": "核",
    },
    "create_direction_select": {
        "ko": "이 방향으로 쓰기",
        "en": "Write this one",
        "ja": "この方向で書く",
    },

    # ─── 다듬기: 원문 입력 ───
    "polish_input_label": {
        "ko": "다듬을 포스트",
        "en": "Post to rework",
        "ja": "磨き直すポスト",
    },
    "polish_input_placeholder": {
        "ko": "이미 써 둔 포스트 원문을 붙여넣는다.",
        "en": "Paste a post you already wrote.",
        "ja": "すでに書いたポストの原文を貼り付ける。",
    },
    "polish_input_required": {
        "ko": "다듬을 원문을 먼저 붙여넣는다.",
        "en": "Paste the original post first.",
        "ja": "まず原文を貼り付ける。",
    },
    "polish_submit_cta": {
        "ko": "다듬기 시작",
        "en": "Start optimizing",
        "ja": "推敲を始める",
    },

    # ─── 다듬기: 결과 ───
    "polish_result_title": {
        "ko": "다듬은 결과",
        "en": "Optimized result",
        "ja": "磨き直した結果",
    },
    "polish_open_editor": {
        "ko": "에디터에서 계속 고치기",
        "en": "Continue in the editor",
        "ja": "エディタで編集を続ける",
    },

    # ─── 작업 상태 ───
    "job_queued": {
        "ko": "차례를 기다린다.",
        "en": "Waiting in line.",
        "ja": "順番を待っている。",
    },
    "job_running": {
        "ko": "쓰는 중이다. 화면을 닫아도 계속된다.",
        "en": "Working. It keeps going even if you close this.",
        "ja": "作成中。画面を閉じても続く。",
    },
    "job_missing": {
        "ko": "저장된 작업을 찾을 수 없다.",
        "en": "That saved job is gone.",
        "ja": "保存された処理が見つからない。",
    },
    "job_failed": {
        "ko": "만들지 못했다.",
        "en": "It could not be created.",
        "ja": "作成できなかった。",
    },
    "job_failed_detail": {
        "ko": "만들지 못했다: {detail}",
        "en": "It could not be created: {detail}",
        "ja": "作成できなかった: {detail}",
    },
    "job_retry": {
        "ko": "다시 시도",
        "en": "Try again",
        "ja": "再試行",
    },
    "invalid_directions": {
        "ko": "방향 카드 3장을 제대로 받지 못했다. 주제를 조금 더 구체적으로 적고 다시 시도한다.",
        "en": "The three direction cards came back malformed. Make the topic more specific and try again.",
        "ja": "方向カード3枚を正しく受け取れなかった。テーマをもう少し具体的にして再試行する。",
    },
    "invalid_direction": {
        "ko": "고른 방향이 온전하지 않다. 카드를 다시 받아 고른다.",
        "en": "The selected direction was incomplete. Get the cards again and pick one.",
        "ja": "選んだ方向が不完全だった。カードを取り直して選ぶ。",
    },
    "invalid_post": {
        "ko": "본문이 빈 채로 돌아왔다. 다시 시도한다.",
        "en": "The post came back without a body. Try again.",
        "ja": "本文が空のまま返ってきた。再試行する。",
    },

    # ─── 에디터 ───
    "editor_title": {
        "ko": "완성한 포스트",
        "en": "Finished post",
        "ja": "完成したポスト",
    },
    "editor_hint": {
        "ko": "고치면 발행 큐 초안에 자동으로 저장된다.",
        "en": "Edits autosave into the publish-queue draft.",
        "ja": "編集すると公開キューの下書きに自動保存される。",
    },
    "editor_open_x": {
        "ko": "X 작성 화면 열기",
        "en": "Open the X composer",
        "ja": "Xの作成画面を開く",
    },
    "editor_save": {
        "ko": "발행 큐에 저장",
        "en": "Save to publish queue",
        "ja": "公開キューに保存",
    },
    "editor_mark_published": {
        "ko": "게시했음",
        "en": "I posted it",
        "ja": "投稿した",
    },
    "editor_saved": {
        "ko": "발행 큐에 저장했다.",
        "en": "Saved to the publish queue.",
        "ja": "公開キューに保存した。",
    },
    "editor_published": {
        "ko": "발행 기록에 남겼다.",
        "en": "Recorded as published.",
        "ja": "公開済みとして記録した。",
    },
    "editor_publish_failed": {
        "ko": "이미 발행된 글이라 기록하지 않았다.",
        "en": "Already published, so nothing was recorded.",
        "ja": "すでに公開済みのため記録しなかった。",
    },
    "editor_empty": {
        "ko": "본문이 비어 있다.",
        "en": "The post body is empty.",
        "ja": "本文が空だ。",
    },
    "queue_busy": {
        "ko": "저장 잠금 대기 시간이 지났다. 잠시 뒤 다시 시도한다.",
        "en": "Timed out waiting for the queue lock. It will retry shortly.",
        "ja": "保存ロックの待ち時間を超えた。少し後に再試行する。",
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
