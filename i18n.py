"""Internationalization module — Korean (default), English, Japanese."""

import streamlit as st

LANGUAGES = {"ko": "한국어", "en": "English", "ja": "日本語"}

LANG_INSTRUCTION = {
    "ko": "",
    "en": (
        "\n\n**CRITICAL OUTPUT LANGUAGE RULE — READ CAREFULLY:**\n"
        "EVERY text value in the JSON response MUST be written in ENGLISH, "
        "regardless of the source content's language. This includes `summary`, "
        "`why_recommended`, `engagement_hint`, `suggested_reply`, `search_keywords`, "
        "and every other field. Even when the referenced post is in Korean, Japanese, "
        "or any other language, your reply examples and descriptions MUST be in ENGLISH. "
        "Do NOT match the language of the original post — always use ENGLISH for output."
    ),
    "ja": (
        "\n\n**重要な出力言語ルール — 必ず読んでください:**\n"
        "JSON応答内のすべてのテキスト値は、元のコンテンツの言語に関わらず、"
        "必ず **日本語** で記述してください。`summary`、`why_recommended`、"
        "`engagement_hint`、`suggested_reply`、`search_keywords` など、"
        "すべてのフィールドが対象です。参照するポストが韓国語・英語・その他の言語であっても、"
        "リプライ例や説明文は **必ず日本語** で書いてください。"
        "元のポストの言語に合わせず、常に **日本語** で出力してください。"
    ),
}

# 큐레이터가 탐색해야 할 콘텐츠 언어권 (사용자 UI 언어 기준).
# 프롬프트에 {language_pair} 플레이스홀더로 주입되며, 영어는 디폴트
# 공용어로 항상 포함시켜 OOD(Out-of-Network Discovery) 폭을 넓게 유지한다.
LANG_CONTENT_PAIR = {
    "ko": "Korean and English",
    "en": "English",
    "ja": "Japanese and English",
}

# 프롬프트 필드 설명에 직접 박아넣을 출력 언어 이름.
# suggested_reply 같은 필드가 "자연스러운 리플"이라는 한국어 설명에 앵커링되어
# 엉뚱한 언어로 나오는 것을 막기 위해, 필드 설명 자체에 목표 언어를 명시한다.
LANG_OUTPUT_NAME = {
    "ko": "Korean",
    "en": "English",
    "ja": "Japanese",
}

_T = {
    # ─── App-level ───
    "app_title": {
        "ko": "동피랑고양이 Grok 𝕏",
        "en": "Dongpirang Cat Grok 𝕏",
        "ja": "東ピラン猫 Grok 𝕏",
    },
    "app_caption": {
        "ko": "x-algorithm 기반 X 포스트 최적화",
        "en": "X Post Optimization based on x-algorithm",
        "ja": "x-algorithmベースのXポスト最適化",
    },
    "app_caption_main": {
        "ko": "x-algorithm의 Phoenix Scorer & Candidate Pipeline 원리 기반",
        "en": "Based on x-algorithm Phoenix Scorer & Candidate Pipeline",
        "ja": "x-algorithm Phoenix Scorer & Candidate Pipelineに基づく",
    },
    "api_key_label": {
        "ko": "🔑 Grok API Key 입력",
        "en": "🔑 Enter Grok API Key",
        "ja": "🔑 Grok APIキーを入力",
    },
    "ai_engine_label": {
        "ko": "실행 엔진",
        "en": "AI engine",
        "ja": "実行エンジン",
    },
    "provider_status_ready": {
        "ko": "사용 가능",
        "en": "Ready",
        "ja": "使用可能",
    },
    "provider_status_unavailable": {
        "ko": "사용할 수 없음",
        "en": "Unavailable",
        "ja": "使用不可",
    },
    "local_generation_needed": {
        "ko": "로컬 생성을 사용하려면 Claude 또는 Grok CLI 로그인이 필요합니다.",
        "en": "Local generation requires a logged-in Claude or Grok CLI.",
        "ja": "ローカル生成にはClaudeまたはGrok CLIのログインが必要です。",
    },
    "curator_fallback_notice": {
        "ko": "현재 엔진은 실시간 X 검색을 사용할 수 없어 검색 키워드와 답글 초안만 생성합니다.",
        "en": "The current engine cannot use live X search, so it will generate search keywords and reply drafts only.",
        "ja": "現在のエンジンではリアルタイムX検索を使用できないため、検索キーワードと返信案のみ生成します。",
    },
    "api_key_help": {
        "ko": "console.x.ai에서 발급받으세요. xAI 엔진뿐 아니라 이미지·영상 생성에도 쓰여요.",
        "en": "Get yours at console.x.ai. Used for the xAI engine and for image/video generation.",
        "ja": "console.x.aiで取得してください。xAIエンジンだけでなく画像・動画生成にも使われます。",
    },
    "api_key_warning": {
        "ko": "⚠️ Grok API Key는 한 번만 보여집니다.\n생성 즉시 저장하세요!",
        "en": "⚠️ Grok API Key is shown only once.\nSave it immediately!",
        "ja": "⚠️ Grok APIキーは一度だけ表示されます。\nすぐに保存してください！",
    },
    "api_key_privacy": {
        "ko": "🔒 입력한 키는 이 브라우저에만 저장돼요. 서버·분석 어디에도 남지 않아요.",
        "en": "🔒 Your key stays in this browser only — never stored on the server or in analytics.",
        "ja": "🔒 入力したキーはこのブラウザにのみ保存されます。サーバーや分析には残りません。",
    },
    "model_select": {
        "ko": "모델 선택",
        "en": "Select Model",
        "ja": "モデル選択",
    },
    "model_help": {
        "ko": "grok-4.1-fast-reasoning: 빠른 응답 / grok-4.20-reasoning: 깊은 분석",
        "en": "grok-4.1-fast-reasoning: Fast / grok-4.20-reasoning: Deep analysis",
        "ja": "grok-4.1-fast-reasoning: 高速 / grok-4.20-reasoning: 深い分析",
    },
    "cli_default_model_note": {
        "ko": "비용 효율 모델로 고정: Grok=grok-4.5(CLI 기본) · Claude=Sonnet · Codex=기본 모델(추론 medium)",
        "en": "Cost-efficient models pinned: Grok=grok-4.5 (CLI default) · Claude=Sonnet · Codex=default model (medium reasoning)",
        "ja": "コスト効率モデルに固定: Grok=grok-4.5（CLI既定）・Claude=Sonnet・Codex=既定モデル（推論medium）",
    },
    "ja_model_warning": {
        "ko": "💡 일본어는 **grok-4.20-reasoning** 모델을 권장합니다. grok-4.1-fast-reasoning 은 간혹 큐레이터의 추천 리플이 한국어로 섞여 나올 수 있어요.",
        "en": "💡 For Japanese output, **grok-4.20-reasoning** is recommended. grok-4.1-fast-reasoning occasionally leaks Korean into curator suggested replies.",
        "ja": "💡 日本語出力には **grok-4.20-reasoning** を推奨します。grok-4.1-fast-reasoning は、キュレーターの推奨リプライに韓国語が混ざることがあります。",
    },
    "follow_btn": {
        "ko": "🐦 @mangodaon 팔로우하기",
        "en": "🐦 Follow @mangodaon",
        "ja": "🐦 @mangodaonをフォロー",
    },
    "api_required": {
        "ko": "⚠️ 이 기능을 사용하려면 사이드바에서 사용 가능한 AI 엔진을 선택해주세요.",
        "en": "⚠️ Select an available AI engine in the sidebar to use this feature.",
        "ja": "⚠️ この機能を使用するには、サイドバーで利用可能なAIエンジンを選択してください。",
    },
    "demo_banner": {
        "ko": "🎬 **데모 모드** — 미리 만들어둔 예시 결과를 보여드리고 있어요. 왼쪽 사이드바에서 사용 가능한 AI 엔진을 선택하면 본인의 입력으로 직접 생성할 수 있습니다.",
        "en": "🎬 **Demo mode** — You are viewing a preset example result. Select an available AI engine in the sidebar to generate with your own input.",
        "ja": "🎬 **デモモード** — あらかじめ用意されたサンプル結果を表示しています。サイドバーで利用可能なAIエンジンを選択すると、ご自身の入力で生成できます。",
    },
    "demo_key_needed": {
        "ko": "왼쪽 사이드바에서 사용 가능한 AI 엔진을 선택하면 본인 입력으로 분석할 수 있어요.",
        "en": "Select an available AI engine in the sidebar to run analysis on your own input.",
        "ja": "サイドバーで利用可能なAIエンジンを選択すると、ご自身の入力で分析できます。",
    },
    "footer_title": {
        "ko": "**동피랑고양이 Grok 𝕏**",
        "en": "**Dongpirang Cat Grok 𝕏**",
        "ja": "**東ピラン猫 Grok 𝕏**",
    },
    "footer_caption": {
        "ko": "x-algorithm 기반 X 포스트 최적화 도구",
        "en": "X Post Optimization Tool based on x-algorithm",
        "ja": "x-algorithmベースのXポスト最適化ツール",
    },
    "footer_share": {
        "ko": "🐦 이 앱을 X에 공유하기",
        "en": "🐦 Share this app on X",
        "ja": "🐦 このアプリをXで共有",
    },
    "footer_follow": {
        "ko": "👤 이 앱 만든 사람 팔로우하기 @mangodaon",
        "en": "👤 Follow the creator @mangodaon",
        "ja": "👤 制作者をフォロー @mangodaon",
    },
    "lang_label": {
        "ko": "🌐 언어 / Language",
        "en": "🌐 Language",
        "ja": "🌐 言語",
    },
    "theme_label": {
        "ko": "🎨 테마",
        "en": "🎨 Theme",
        "ja": "🎨 テーマ",
    },

    # ─── Tab names ───
    "tab_optimizer": {
        "ko": "📝 포스트 최적화",
        "en": "📝 Optimize",
        "ja": "📝 ポスト最適化",
    },
    "tab_ideas": {
        "ko": "💡 아이디어 생성",
        "en": "💡 Ideas",
        "ja": "💡 アイデア生成",
    },
    "tab_curator": {
        "ko": "🔍 피드 큐레이터",
        "en": "🔍 Curator",
        "ja": "🔍 キュレーター",
    },
    "tab_thread": {
        "ko": "🧵 스레드 최적화",
        "en": "🧵 Thread",
        "ja": "🧵 スレッド",
    },
    "tab_scheduler": {
        "ko": "📅 포스팅 스케줄러",
        "en": "📅 Schedule",
        "ja": "📅 スケジュール",
    },
    "tab_ab": {
        "ko": "⚖️ A/B 비교",
        "en": "⚖️ A/B",
        "ja": "⚖️ A/B",
    },
    "tab_risk": {
        "ko": "⚠️ 리스크 체크",
        "en": "⚠️ Risk",
        "ja": "⚠️ リスク",
    },
    "tab_unfollow": {
        "ko": "🔄 언팔 추적",
        "en": "🔄 Unfollow",
        "ja": "🔄 アンフォロー",
    },
    "tab_performance": {
        "ko": "📈 성과 추적",
        "en": "📈 Performance",
        "ja": "📈 パフォーマンス",
    },
    "tab_publish_queue": {
        "ko": "📤 발행 큐",
        "en": "📤 Queue",
        "ja": "📤 発行キュー",
    },

    # ─── Publish Queue Tab ───
    "pq_subheader": {
        "ko": "발행 큐 & 소재 인박스",
        "en": "Publish Queue & Material Inbox",
        "ja": "発行キュー＆ネタ受信箱",
    },
    "pq_caption": {
        "ko": "경험 한 줄을 던져두면 AI가 포스트로 빚어냅니다. 승인한 초안은 발행 슬롯(평일 08·19시, 토 10시)에 배정돼요.",
        "en": "Drop a one-line experience and AI shapes it into a post. Approved drafts get assigned to publish slots (weekdays 08:00/19:00, Sat 10:00).",
        "ja": "経験を一行置いておくと、AIがポストに仕上げます。承認した下書きは発行スロット（平日08・19時、土10時）に割り当てられます。",
    },
    "pq_inbox_title": {
        "ko": "💡 소재 인박스",
        "en": "💡 Material inbox",
        "ja": "💡 ネタ受信箱",
    },
    "pq_inbox_caption": {
        "ko": "오늘 겪은 일, 배운 것, 숫자 하나 — 짧아도 됩니다. 진짜 경험만이 좋은 포스트가 돼요.",
        "en": "Something you did, learned, or measured today — one line is enough. Real experiences make the best posts.",
        "ja": "今日あったこと、学んだこと、数字ひとつ — 短くてOK。本当の経験こそ良いポストになります。",
    },
    "pq_inbox_placeholder": {
        "ko": "예: 오늘 버그 3시간 잡았는데 원인은 오타였다",
        "en": "e.g. Spent 3 hours on a bug today — it was a typo",
        "ja": "例: 今日3時間バグを追ったら原因はタイポだった",
    },
    "pq_inbox_add": {
        "ko": "➕ 추가",
        "en": "➕ Add",
        "ja": "➕ 追加",
    },
    "pq_inbox_empty": {
        "ko": "소재가 없어요. 한 줄 던져두면 초안이 시작됩니다.",
        "en": "No materials yet. Drop a line to start a draft.",
        "ja": "ネタがありません。一行置くと下書きが始まります。",
    },
    "pq_draft_btn": {
        "ko": "✍️ 초안 만들기",
        "en": "✍️ Draft it",
        "ja": "✍️ 下書き作成",
    },
    "pq_draft_spinner": {
        "ko": "소재를 포스트로 빚는 중…",
        "en": "Shaping your material into a post…",
        "ja": "ネタをポストに仕上げ中…",
    },
    "pq_queue_title": {
        "ko": "📤 초안 큐",
        "en": "📤 Draft queue",
        "ja": "📤 下書きキュー",
    },
    "pq_queue_empty": {
        "ko": "큐가 비어 있어요. 소재에서 초안을 만들어 보세요.",
        "en": "The queue is empty. Create a draft from a material above.",
        "ja": "キューは空です。上のネタから下書きを作ってみてください。",
    },
    "pq_draft_text_label": {
        "ko": "초안 본문",
        "en": "Draft text",
        "ja": "下書き本文",
    },
    "pq_slot_label": {
        "ko": "발행 예정",
        "en": "Scheduled",
        "ja": "発行予定",
    },
    "pq_approve": {
        "ko": "✅ 승인",
        "en": "✅ Approve",
        "ja": "✅ 承認",
    },
    "pq_reject": {
        "ko": "🚫 반려",
        "en": "🚫 Reject",
        "ja": "🚫 却下",
    },
    "pq_post_now": {
        "ko": "𝕏 지금 올리기",
        "en": "𝕏 Post now",
        "ja": "𝕏 今すぐ投稿",
    },
    "pq_worker_note": {
        "ko": "승인된 초안 {n}개가 슬롯에 배정돼 있어요. 자동 발행 워커(4c)가 연결되면 이 시각에 자동으로 올라갑니다. 그 전까지는 '지금 올리기'로 수동 발행하세요.",
        "en": "{n} approved draft(s) assigned to slots. Once the auto-publish worker (4c) is connected they'll go out at those times. Until then, use 'Post now' to publish manually.",
        "ja": "承認済み下書き{n}件がスロットに割り当てられています。自動発行ワーカー(4c)が接続されると、その時刻に自動投稿されます。それまでは「今すぐ投稿」で手動投稿してください。",
    },
    "pq_error_note": {
        "ko": "⚠️ 발행 결과를 알 수 없어요 (처리 중 중단됨). X에 이미 올라갔는지 확인한 뒤 다시 승인하세요.",
        "en": "⚠️ Publish outcome unknown (interrupted mid-flight). Check X to see if it was already posted before re-approving.",
        "ja": "⚠️ 公開結果が不明です（処理中に中断）。再承認する前に、Xに既に投稿されていないか確認してください。",
    },
    "pq_publishing_note": {
        "ko": "🔄 지금 발행 처리 중이에요. 잠시 후 새로고침해서 결과를 확인하세요.",
        "en": "🔄 Publishing is in progress. Refresh in a moment to check the result.",
        "ja": "🔄 現在発行処理中です。しばらくしてから更新して結果を確認してください。",
    },
    "pq_pillar_bip": {
        "ko": "빌드 인 퍼블릭",
        "en": "Build in public",
        "ja": "ビルド・イン・パブリック",
    },
    "pq_pillar_retro": {
        "ko": "회고",
        "en": "Retrospective",
        "ja": "振り返り",
    },
    "pq_pillar_tip": {
        "ko": "팁",
        "en": "Tip",
        "ja": "ヒント",
    },
    "pq_pillar_curation": {
        "ko": "큐레이션",
        "en": "Curation",
        "ja": "キュレーション",
    },

    # ─── Performance Tab ───
    "perf_subheader": {
        "ko": "실측 성과 & 수익화 진행률",
        "en": "Real Performance & Monetization Progress",
        "ja": "実測パフォーマンス＆収益化の進捗",
    },
    "perf_caption": {
        "ko": "X 애널리틱스 CSV를 업로드하면 실제 노출 데이터로 수익화 요건 진행률과 '먹히는 패턴'을 분석합니다.",
        "en": "Upload your X analytics CSV to track monetization progress and find what actually works from real impression data.",
        "ja": "XアナリティクスのCSVをアップロードすると、実際の表示データで収益化要件の進捗と「効くパターン」を分析します。",
    },
    "perf_howto_title": {
        "ko": "📥 CSV 내보내는 방법",
        "en": "📥 How to export the CSV",
        "ja": "📥 CSVのエクスポート方法",
    },
    "perf_howto_body": {
        "ko": (
            "1. X에서 **프리미엄 → 애널리틱스** (analytics.x.com) 로 이동\n"
            "2. 포스트 활동 화면에서 기간을 선택하고 **데이터 내보내기(Export data)** 클릭\n"
            "3. 받은 CSV를 아래에 업로드하세요\n\n"
            "형식이 궁금하면 샘플 CSV를 받아 먼저 체험해 보세요."
        ),
        "en": (
            "1. On X, open **Premium → Analytics** (analytics.x.com)\n"
            "2. In the post activity view, pick a date range and click **Export data**\n"
            "3. Upload the CSV below\n\n"
            "Not sure about the format? Download the sample CSV and try it first."
        ),
        "ja": (
            "1. Xで **プレミアム → アナリティクス** (analytics.x.com) を開く\n"
            "2. ポストアクティビティ画面で期間を選び **データをエクスポート** をクリック\n"
            "3. 受け取ったCSVを下にアップロード\n\n"
            "形式が不明な場合は、サンプルCSVをダウンロードして試してください。"
        ),
    },
    "perf_sample_download": {
        "ko": "⬇️ 샘플 CSV 다운로드",
        "en": "⬇️ Download sample CSV",
        "ja": "⬇️ サンプルCSVをダウンロード",
    },
    "perf_upload_label": {
        "ko": "애널리틱스 CSV 업로드",
        "en": "Upload analytics CSV",
        "ja": "アナリティクスCSVをアップロード",
    },
    "perf_upload_hint": {
        "ko": "CSV를 업로드하면 대시보드가 나타납니다. 위의 샘플 CSV로 먼저 체험해 볼 수도 있어요.",
        "en": "Upload a CSV to see the dashboard. You can also try the sample CSV above first.",
        "ja": "CSVをアップロードするとダッシュボードが表示されます。上のサンプルCSVで先に試すこともできます。",
    },
    "perf_parse_error": {
        "ko": "CSV에서 노출수(impressions) 열을 찾지 못했어요. X 애널리틱스에서 내보낸 원본 CSV인지 확인해 주세요.",
        "en": "Couldn't find an impressions column in the CSV. Please check it's the original export from X analytics.",
        "ja": "CSVからインプレッション列が見つかりませんでした。Xアナリティクスからの元のエクスポートか確認してください。",
    },
    "perf_total_posts": {
        "ko": "포스트 수",
        "en": "Posts",
        "ja": "ポスト数",
    },
    "perf_total_impressions": {
        "ko": "총 노출",
        "en": "Total impressions",
        "ja": "総インプレッション",
    },
    "perf_recent_impressions": {
        "ko": "최근 90일 노출",
        "en": "Last 90 days",
        "ja": "直近90日",
    },
    "perf_engagement_rate": {
        "ko": "평균 참여율",
        "en": "Avg engagement",
        "ja": "平均エンゲージ率",
    },
    "perf_no_dates": {
        "ko": "날짜 열을 읽지 못해 전체 데이터를 최근 성과로 간주했어요. 90일 계산이 정확하려면 time/날짜 열이 있는 CSV를 사용하세요.",
        "en": "No date column found, so all data was treated as recent. Use a CSV with a time/date column for an accurate 90-day window.",
        "ja": "日付列が読めなかったため、全データを直近の実績として扱いました。正確な90日計算にはtime/日付列のあるCSVを使ってください。",
    },
    "perf_monetization_title": {
        "ko": "💰 수익화 요건 진행률",
        "en": "💰 Monetization progress",
        "ja": "💰 収益化要件の進捗",
    },
    "perf_monetization_progress": {
        "ko": "최근 3개월 노출 **{current} / {target}** ({pct}%)",
        "en": "Impressions in the last 3 months: **{current} / {target}** ({pct}%)",
        "ja": "直近3ヶ月のインプレッション: **{current} / {target}** ({pct}%)",
    },
    "perf_target_reached": {
        "ko": "🎉 노출 요건을 이미 충족했어요! 나머지 요건을 확인하세요.",
        "en": "🎉 You've already met the impressions requirement! Check the remaining criteria.",
        "ja": "🎉 インプレッション要件はすでに達成しています！残りの要件を確認してください。",
    },
    "perf_estimate": {
        "ko": "일평균 노출 {daily} 기준, 현재 속도라면 약 **{days}일** 후 500만 도달 예상입니다.",
        "en": "At {daily} impressions/day, you'll reach 5M in roughly **{days} days** at the current pace.",
        "ja": "1日平均{daily}インプレッションなら、現在のペースで約**{days}日**後に500万に到達する見込みです。",
    },
    "perf_checklist_title": {
        "ko": "수익화 요건 체크리스트",
        "en": "Monetization checklist",
        "ja": "収益化要件チェックリスト",
    },
    "perf_followers_input": {
        "ko": "현재 팔로워 수 (직접 입력)",
        "en": "Current follower count (manual)",
        "ja": "現在のフォロワー数（手入力）",
    },
    "perf_premium_check": {
        "ko": "X 프리미엄 구독 중",
        "en": "Subscribed to X Premium",
        "ja": "Xプレミアムに加入中",
    },
    "perf_check_impressions": {
        "ko": "최근 3개월 유기적 노출 500만 회",
        "en": "5M organic impressions in the last 3 months",
        "ja": "直近3ヶ月で500万オーガニックインプレッション",
    },
    "perf_check_followers": {
        "ko": "팔로워 500명 이상",
        "en": "500+ followers",
        "ja": "フォロワー500人以上",
    },
    "perf_check_premium": {
        "ko": "X 프리미엄 구독",
        "en": "X Premium subscription",
        "ja": "Xプレミアム加入",
    },
    "perf_top_posts": {
        "ko": "🏆 상위 포스트",
        "en": "🏆 Top posts",
        "ja": "🏆 上位ポスト",
    },
    "perf_bottom_posts": {
        "ko": "📉 하위 포스트",
        "en": "📉 Bottom posts",
        "ja": "📉 下位ポスト",
    },
    "perf_insight_title": {
        "ko": "🤖 실측 기반 AI 인사이트",
        "en": "🤖 AI insights from real data",
        "ja": "🤖 実測データに基づくAIインサイト",
    },
    "perf_insight_btn": {
        "ko": "🔍 내 계정에서 먹히는 패턴 분석",
        "en": "🔍 Analyze what works on my account",
        "ja": "🔍 自分のアカウントで効くパターンを分析",
    },
    "perf_insight_spinner": {
        "ko": "실측 데이터에서 패턴을 분석 중…",
        "en": "Analyzing patterns from your real data…",
        "ja": "実測データからパターンを分析中…",
    },
    "perf_weak_points": {
        "ko": "개선이 필요한 부분",
        "en": "Areas to improve",
        "ja": "改善が必要な点",
    },
    "perf_action_plan": {
        "ko": "📋 이번 주 실행 계획",
        "en": "📋 This week's action plan",
        "ja": "📋 今週のアクションプラン",
    },

    # ─── Common ───
    "post_label": {
        "ko": "포스트 내용",
        "en": "Post content",
        "ja": "ポスト内容",
    },
    "post_placeholder": {
        "ko": "분석하고 싶은 포스트 내용을 입력하세요...",
        "en": "Enter the post content you want to analyze...",
        "ja": "分析したいポストの内容を入力してください...",
    },
    "image_desc_label": {
        "ko": "🖼️ 이미지 설명 (선택)",
        "en": "🖼️ Image description (optional)",
        "ja": "🖼️ 画像説明（任意）",
    },
    "image_desc_placeholder": {
        "ko": "예: 일몰 사진, 코드 스크린샷",
        "en": "e.g., sunset photo, code screenshot",
        "ja": "例：夕焼け写真、コードスクリーンショット",
    },
    "enter_post": {
        "ko": "포스트 내용을 입력해주세요.",
        "en": "Please enter your post content.",
        "ja": "ポスト内容を入力してください。",
    },
    "post_to_x": {
        "ko": "𝕏 에 게시",
        "en": "Post to 𝕏",
        "ja": "𝕏 に投稿",
    },

    # ─── Optimizer Tab ───
    "opt_subheader": {
        "ko": "포스트 Optimizer & Engagement Predictor",
        "en": "Post Optimizer & Engagement Predictor",
        "ja": "ポストOptimizer & Engagement Predictor",
    },
    "opt_caption": {
        "ko": "x-algorithm의 Multi-Action Prediction 원리로 포스트를 분석합니다",
        "en": "Analyze posts using x-algorithm's Multi-Action Prediction",
        "ja": "x-algorithmのMulti-Action Predictionでポストを分析します",
    },
    "opt_hashtag_label": {
        "ko": "#️⃣ 해시태그 (선택)",
        "en": "#️⃣ Hashtags (optional)",
        "ja": "#️⃣ ハッシュタグ（任意）",
    },
    "opt_hashtag_placeholder": {
        "ko": "예: #AI #개발 #Python",
        "en": "e.g., #AI #dev #Python",
        "ja": "例：#AI #開発 #Python",
    },
    "opt_analyze_btn": {
        "ko": "🔍 x-algorithm 분석",
        "en": "🔍 x-algorithm Analysis",
        "ja": "🔍 x-algorithm分析",
    },
    "opt_spinner": {
        "ko": "선택한 AI 엔진이 x-algorithm 분석 중...",
        "en": "The selected AI engine is analyzing with x-algorithm...",
        "ja": "選択したAIエンジンがx-algorithmで分析中...",
    },
    "opt_score": {
        "ko": "x-algorithm 점수",
        "en": "x-algorithm Score",
        "ja": "x-algorithmスコア",
    },
    "opt_engagement": {
        "ko": "참여 예측 등급",
        "en": "Engagement Level",
        "ja": "エンゲージメント予測",
    },
    "opt_reasons": {
        "ko": "📊 분석 이유",
        "en": "📊 Analysis Reasons",
        "ja": "📊 分析理由",
    },
    "opt_suggestions": {
        "ko": "💡 개선 제안",
        "en": "💡 Improvement Suggestions",
        "ja": "💡 改善提案",
    },
    "opt_optimized": {
        "ko": "✨ 최적화된 포스트",
        "en": "✨ Optimized Post",
        "ja": "✨ 最適化されたポスト",
    },
    "opt_viral_tag": {
        "ko": "바이럴 태그 자동 추가",
        "en": "Auto-add viral tag",
        "ja": "バイラルタグ自動追加",
    },
    "opt_action_analysis": {
        "ko": "📊 Multi-Action 점수 분석",
        "en": "📊 Multi-Action Score Analysis",
        "ja": "📊 Multi-Actionスコア分析",
    },
    "opt_action_caption": {
        "ko": "각 행동 유형별 예측 확률과 가중 기여도",
        "en": "Predicted probability and weighted contribution by action type",
        "ja": "各行動タイプの予測確率と加重貢献度",
    },
    "opt_total_score": {
        "ko": "총 가중 점수",
        "en": "Total Weighted Score",
        "ja": "総加重スコア",
    },
    "opt_strongest": {
        "ko": "최강 행동",
        "en": "Strongest Action",
        "ja": "最強行動",
    },
    "opt_weakest": {
        "ko": "최약 행동",
        "en": "Weakest Action",
        "ja": "最弱行動",
    },

    # ─── Action Labels ───
    "action_reply": {
        "ko": "💬 답글",
        "en": "💬 Reply",
        "ja": "💬 リプライ",
    },
    "action_repost": {
        "ko": "🔄 리포스트",
        "en": "🔄 Repost",
        "ja": "🔄 リポスト",
    },
    "action_like": {
        "ko": "❤️ 좋아요",
        "en": "❤️ Like",
        "ja": "❤️ いいね",
    },
    "action_quote": {
        "ko": "💭 인용",
        "en": "💭 Quote",
        "ja": "💭 引用",
    },
    "action_bookmark": {
        "ko": "🔖 북마크",
        "en": "🔖 Bookmark",
        "ja": "🔖 ブックマーク",
    },
    "action_follow": {
        "ko": "👤 팔로우",
        "en": "👤 Follow",
        "ja": "👤 フォロー",
    },
    "action_dwell_time": {
        "ko": "⏱️ 체류시간",
        "en": "⏱️ Dwell Time",
        "ja": "⏱️ 滞在時間",
    },
    "action_share": {
        "ko": "📤 공유",
        "en": "📤 Share",
        "ja": "📤 共有",
    },
    "action_photo_expansion": {
        "ko": "🖼️ 이미지 확대",
        "en": "🖼️ Photo Expand",
        "ja": "🖼️ 画像拡大",
    },
    "action_oon_discovery": {
        "ko": "🌐 OON 발견",
        "en": "🌐 OON Discovery",
        "ja": "🌐 OON発見",
    },

    # ─── Ideas Tab ───
    "ideas_subheader": {
        "ko": "오늘 올릴 포스트 아이디어 5개",
        "en": "5 Post Ideas for Today",
        "ja": "今日投稿するポストアイデア5つ",
    },
    "ideas_caption": {
        "ko": "x-algorithm 최적화된 포스트 아이디어를 생성합니다. (AI 생성 글 그대로 복붙하지 말고 본인 생각을 더해주세요.)",
        "en": "Generate x-algorithm optimized post ideas. (Don't just copy-paste AI-generated text — add your own thoughts.)",
        "ja": "x-algorithm最適化されたポストアイデアを生成します。（AI生成文をそのままコピペせず、自分の考えを加えてください。）",
    },
    "ideas_keyword_label": {
        "ko": "관심사 / 키워드",
        "en": "Interests / Keywords",
        "ja": "関心事 / キーワード",
    },
    "ideas_keyword_placeholder": {
        "ko": "예: AI, 프로그래밍, 스타트업, 한국 여행",
        "en": "e.g., AI, programming, startups, travel",
        "ja": "例：AI、プログラミング、スタートアップ、旅行",
    },
    "ideas_generate_btn": {
        "ko": "💡 아이디어 생성",
        "en": "💡 Generate Ideas",
        "ja": "💡 アイデア生成",
    },
    "ideas_enter_keyword": {
        "ko": "관심사나 키워드를 입력해주세요.",
        "en": "Please enter interests or keywords.",
        "ja": "関心事やキーワードを入力してください。",
    },
    "ideas_spinner": {
        "ko": "선택한 AI 엔진이 x-algorithm 최적화 아이디어 생성 중...",
        "en": "The selected AI engine is generating x-algorithm optimized ideas...",
        "ja": "選択したAIエンジンがx-algorithm最適化アイデアを生成中...",
    },
    "ideas_job_submitted": {
        "ko": "아이디어 생성 요청을 보냈습니다. 연결이 끊겨도 같은 URL에서 결과를 확인할 수 있습니다.",
        "en": "Idea generation has started. Reopen this URL to see the result if your connection drops.",
        "ja": "アイデア生成を開始しました。接続が切れても同じURLで結果を確認できます。",
    },
    "ideas_job_running": {
        "ko": "{engine}에서 아이디어를 생성하고 있습니다. 이 화면을 떠나도 작업은 계속됩니다.",
        "en": "{engine} is generating ideas. The job continues even if you leave this screen.",
        "ja": "{engine}がアイデアを生成中です。この画面を離れても処理は続きます。",
    },
    "ideas_job_missing": {
        "ko": "이 아이디어 생성 작업을 찾을 수 없습니다. 새로 생성해 주세요.",
        "en": "This idea-generation job could not be found. Please start a new one.",
        "ja": "このアイデア生成ジョブが見つかりません。新しく生成してください。",
    },
    "ideas_strategy": {
        "ko": "전략 보기",
        "en": "View Strategy",
        "ja": "戦略を見る",
    },
    "ideas_length_label": {
        "ko": "원하는 포스트 길이 (선택)",
        "en": "Desired Post Length (optional)",
        "ja": "希望するポスト長さ（任意）",
    },
    "ideas_length_help": {
        "ko": "0 = 자동 (200–500자 권장). 100–1000자 범위에서 직접 지정 가능.",
        "en": "0 = auto (200–500 chars recommended). Set 100–1000 to specify.",
        "ja": "0 = 自動（200〜500文字推奨）。100〜1000文字で指定可能。",
    },
    # ─── 아이디어 탭: 글쓰기/이미지 모드 ───
    "ideas_mode_label": {
        "ko": "글쓰기 모드",
        "en": "Writing mode",
        "ja": "文体モード",
    },
    "ideas_content_type_label": {
        "ko": "생성 유형",
        "en": "Generation type",
        "ja": "生成タイプ",
    },
    "ideas_content_type_ideas": {
        "ko": "일반 아이디어",
        "en": "Regular ideas",
        "ja": "通常アイデア",
    },
    "ideas_content_type_grounded_tip": {
        "ko": "근거 기반 팁",
        "en": "Source-backed tips",
        "ja": "根拠付きヒント",
    },
    "ideas_tip_category_label": {
        "ko": "팁 분야",
        "en": "Tip category",
        "ja": "ヒントの分野",
    },
    "ideas_tip_category_daily": {
        "ko": "일상",
        "en": "Daily life",
        "ja": "暮らし",
    },
    "ideas_tip_category_health": {
        "ko": "건강",
        "en": "Health",
        "ja": "健康",
    },
    "ideas_tip_category_finance": {
        "ko": "금융",
        "en": "Finance",
        "ja": "金融",
    },
    "ideas_tip_category_it_builder": {
        "ko": "IT 빌더",
        "en": "IT builder",
        "ja": "ITビルダー",
    },
    "ideas_references_label": {
        "ko": "참고 URL 또는 메모 (선택)",
        "en": "Reference URLs or notes (optional)",
        "ja": "参考URL・メモ（任意）",
    },
    "ideas_references_help": {
        "ko": "검색 단서로만 사용합니다. 여기에 적은 내용이나 URL은 자동으로 사실·출처가 되지 않습니다.",
        "en": "Used only as research leads. Text or URLs here are not automatically treated as facts or sources.",
        "ja": "検索の手がかりとしてのみ使います。ここに書いた内容やURLが自動的に事実・出典になることはありません。",
    },
    "ideas_grok_research_note": {
        "ko": "Grok CLI가 웹 검색으로 서로 다른 출처를 두 곳 이상 확인한 뒤 팁을 작성합니다.",
        "en": "Grok CLI verifies at least two independent web sources before writing the tips.",
        "ja": "Grok CLIがウェブ検索で異なる出典を2件以上確認してからヒントを作成します。",
    },
    "ideas_health_finance_notice": {
        "ko": "건강·금융 팁은 일반 정보용입니다. 개인 증상·처방·복용량 또는 보유 종목·매수·매도 판단은 다루지 않습니다.",
        "en": "Health and finance tips are general information only, not personal diagnosis, treatment, holdings, or buy/sell decisions.",
        "ja": "健康・金融のヒントは一般情報です。個人の症状・処方・服用量や保有銘柄・売買判断は扱いません。",
    },
    "ideas_experimental_modes": {
        "ko": "🧪 실험실 모드",
        "en": "🧪 Experimental modes",
        "ja": "🧪 実験モード",
    },
    "ideas_sources": {
        "ko": "출처 보기",
        "en": "View sources",
        "ja": "出典を見る",
    },
    "ideas_verified_at": {
        "ko": "출처 확인: {at}",
        "en": "Sources verified: {at}",
        "ja": "出典確認: {at}",
    },
    "ideas_error_insufficient_sources": {
        "ko": "서로 다른 신뢰할 수 있는 출처를 두 곳 이상 확인하지 못했습니다. 주제를 조금 더 구체적으로 바꿔 다시 시도해 주세요.",
        "en": "We could not verify two independent reliable sources. Try a more specific topic.",
        "ja": "異なる信頼できる出典を2件以上確認できませんでした。テーマをもう少し具体的にして再試行してください。",
    },
    "ideas_error_unsafe_personalized_request": {
        "ko": "건강·금융 팁은 일반 정보만 제공합니다. 개인 증상·처방·복용량이나 보유 종목·매수·매도 판단은 요청할 수 없습니다.",
        "en": "Health and finance tips provide general information only; personal symptoms, prescriptions, holdings, and buy/sell decisions are not supported.",
        "ja": "健康・金融のヒントは一般情報のみです。個人の症状・処方・服用量や保有銘柄・売買判断には対応していません。",
    },
    "ideas_error_unverified_evidence": {
        "ko": "생성 결과의 근거 URL을 확인할 수 없어 표시하지 않았습니다. 다시 생성해 주세요.",
        "en": "The generated evidence URLs could not be verified, so the result was not shown. Please try again.",
        "ja": "生成結果の根拠URLを確認できなかったため表示しませんでした。もう一度生成してください。",
    },
    "ideas_error_grounded_tips_require_grok_cli": {
        "ko": "근거 기반 팁에는 웹 조사가 가능한 Grok CLI가 필요합니다. Grok CLI 로그인을 확인해 주세요.",
        "en": "Source-backed tips require Grok CLI with web research. Check the Grok CLI login.",
        "ja": "根拠付きヒントにはウェブ調査ができるGrok CLIが必要です。Grok CLIのログインを確認してください。",
    },
    "img_style_label": {
        "ko": "이미지 스타일",
        "en": "Image style",
        "ja": "画像スタイル",
    },
    "ideas_char_count": {
        "ko": "{n}자",
        "en": "{n} chars",
        "ja": "{n}文字",
    },
    "ideas_len_warn": {
        "ko": "지정 길이 {target}자에서 ±10% 이상 벗어남",
        "en": "More than ±10% off the requested {target} chars",
        "ja": "指定文字数{target}から±10%以上ずれています",
    },
    "ideas_lint_s1": {
        "ko": "AI 상투 표현 감지 (자동 재작성 실패): {items}",
        "en": "AI-cliché detected (auto-rewrite failed): {items}",
        "ja": "AI常套句を検出（自動リライト失敗）: {items}",
    },
    "ideas_lint_s2": {
        "ko": "문체 주의: {items}",
        "en": "Style caution: {items}",
        "ja": "文体注意: {items}",
    },
    "ideas_to_queue_btn": {
        "ko": "초안 큐로 보내기",
        "en": "Send to draft queue",
        "ja": "下書きキューへ送る",
    },
    "ideas_queued_toast": {
        "ko": "발행 큐에 초안으로 추가됨",
        "en": "Added to publish queue as a draft",
        "ja": "公開キューに下書きとして追加されました",
    },
    "ideas_queue_error": {
        "ko": "큐 추가 실패: {err}",
        "en": "Failed to add to queue: {err}",
        "ja": "キュー追加に失敗: {err}",
    },
    # ─── 보이스 카드 ───
    "voice_expander": {
        "ko": "🎙️ 내 목소리 (보이스 카드)",
        "en": "🎙️ My voice (voice card)",
        "ja": "🎙️ 私の声（ボイスカード）",
    },
    "voice_input_label": {
        "ko": "본인이 직접 쓴 포스트를 붙여넣기",
        "en": "Paste posts you actually wrote",
        "ja": "自分で書いたポストを貼り付け",
    },
    "voice_help": {
        "ko": "포스트 사이는 빈 줄 또는 --- 로 구분. 반응 좋았던 글일수록 좋음. 등록하면 모든 생성에 문체 예시로 주입됨.",
        "en": "Separate posts with a blank line or ---. Injected into every generation as voice examples.",
        "ja": "ポストの間は空行または --- で区切ります。すべての生成に文体例として注入されます。",
    },
    "voice_analyze_btn": {
        "ko": "분석·저장",
        "en": "Analyze & save",
        "ja": "分析して保存",
    },
    "voice_saved": {
        "ko": "보이스 카드 저장 완료",
        "en": "Voice card saved",
        "ja": "ボイスカードを保存しました",
    },
    "voice_need_input": {
        "ko": "포스트를 1개 이상 붙여넣어 주세요",
        "en": "Paste at least one post",
        "ja": "ポストを1件以上貼り付けてください",
    },
    "voice_count": {
        "ko": "등록된 예시 {n}개",
        "en": "{n} examples registered",
        "ja": "登録済みの例 {n}件",
    },
    "ideas_image_prompt_title": {
        "ko": "🖼️ 이 포스트에 어울리는 이미지 프롬프트",
        "en": "🖼️ Image prompt matching this post",
        "ja": "🖼️ このポストに合う画像プロンプト",
    },
    "ideas_image_prompt_caption": {
        "ko": "선택한 이미지 스타일이 적용된 최종 프롬프트 — 이미지 생성 AI에 바로 붙여넣어 쓸 수 있습니다",
        "en": "Final prompt with the selected image style applied — paste it into any image AI",
        "ja": "選択した画像スタイルが適用された最終プロンプト — 画像生成AIにそのまま貼り付けられます",
    },
    "ideas_legacy_prompt_note": {
        "ko": "구버전 이력의 프롬프트 — 스타일이 이미 포함돼 있어 새 스타일 모드 없이 그대로 사용합니다",
        "en": "Legacy prompt from old history — it already embeds a style, so style modes are bypassed",
        "ja": "旧バージョン履歴のプロンプト — スタイルが既に含まれているため、スタイルモードを適用せずそのまま使用します",
    },
    "img_generate_btn": {
        "ko": "🎨 이미지 바로 생성",
        "en": "🎨 Generate image now",
        "ja": "🎨 画像をすぐ生成",
    },
    "img_generating": {
        "ko": "이미지 생성 중… ({engine}) 최대 몇 분 걸릴 수 있어요.",
        "en": "Generating image… ({engine}) This can take a few minutes.",
        "ja": "画像を生成中… ({engine}) 数分かかることがあります。",
    },
    "img_engine_note": {
        "ko": "이미지 엔진: {engine}",
        "en": "Image engine: {engine}",
        "ja": "画像エンジン: {engine}",
    },
    "img_engine_label": {
        "ko": "이미지 엔진",
        "en": "Image Engine",
        "ja": "画像エンジン",
    },
    "hist_expander": {
        "ko": "🗂 아이디어 생성 이력",
        "en": "🗂 Idea generation history",
        "ja": "🗂 アイデア生成履歴",
    },
    "hist_empty": {
        "ko": "아직 저장된 생성 이력이 없어요. 아이디어를 생성하면 자동으로 여기에 쌓입니다.",
        "en": "No saved history yet. Generated ideas are archived here automatically.",
        "ja": "保存された履歴はまだありません。アイデアを生成すると自動的にここに保存されます。",
    },
    "hist_count_caption": {
        "ko": "총 {n}건 · 최신순",
        "en": "{n} entries · newest first",
        "ja": "全{n}件・新しい順",
    },
    "hist_restore_btn": {
        "ko": "📥 불러오기",
        "en": "📥 Load",
        "ja": "📥 読み込む",
    },
    "hist_edit_btn": {
        "ko": "✏️ 키워드로 재생성",
        "en": "✏️ Reuse keywords",
        "ja": "✏️ キーワードで再生成",
    },
    "media_hist_expander": {
        "ko": "🖼 이미지·영상 생성 이력",
        "en": "🖼 Generated media history",
        "ja": "🖼 画像・動画の生成履歴",
    },
    "media_hist_empty": {
        "ko": "아직 생성된 이미지/영상이 없어요.",
        "en": "No generated images or videos yet.",
        "ja": "生成された画像・動画はまだありません。",
    },
    "media_hist_count": {
        "ko": "표시 개수",
        "en": "Items to show",
        "ja": "表示件数",
    },
    "img_engine_none": {
        "ko": "로컬 Codex CLI 또는 xAI API 키가 있으면 여기서 바로 이미지를 만들 수 있어요. 지금은 위 프롬프트를 복사해 외부 도구에서 생성해 주세요.",
        "en": "With a local Codex CLI or an xAI API key you can generate the image right here. For now, copy the prompt above into an external tool.",
        "ja": "ローカルのCodex CLIまたはxAI APIキーがあれば、ここで直接画像を生成できます。今は上のプロンプトをコピーして外部ツールで生成してください。",
    },
    "img_download": {
        "ko": "⬇️ 이미지 다운로드 (JPG)",
        "en": "⬇️ Download image (JPG)",
        "ja": "⬇️ 画像をダウンロード（JPG）",
    },
    "img_error": {
        "ko": "이미지 생성에 실패했어요: {err}",
        "en": "Image generation failed: {err}",
        "ja": "画像の生成に失敗しました: {err}",
    },
    "vid_generate_btn": {
        "ko": "🎬 이 이미지로 영상 만들기",
        "en": "🎬 Animate this image into a video",
        "ja": "🎬 この画像から動画を作成",
    },
    "vid_generating": {
        "ko": "영상 생성 중… 보통 1~3분 걸려요.",
        "en": "Generating video… This usually takes 1–3 minutes.",
        "ja": "動画を生成中… 通常1〜3分かかります。",
    },
    "vid_need_key": {
        "ko": "🎬 로컬 Grok CLI 또는 xAI API 키가 있으면 이 이미지를 영상으로 만들 수 있어요.",
        "en": "🎬 Install the local Grok CLI or enter an xAI API key to animate this image into a video.",
        "ja": "🎬 ローカルGrok CLIかxAI APIキーがあれば、この画像から動画を作成できます。",
    },
    "vid_duration_label": {
        "ko": "영상 길이 (초)",
        "en": "Video length (seconds)",
        "ja": "動画の長さ（秒）",
    },
    "vid_resolution_label": {
        "ko": "해상도",
        "en": "Resolution",
        "ja": "解像度",
    },
    "vid_cost_note": {
        "ko": "비용 안내: 480p 초당 $0.01 · 720p 초당 $0.05 (xAI 과금)",
        "en": "Cost: $0.01/sec at 480p · $0.05/sec at 720p (billed by xAI)",
        "ja": "料金: 480pは秒あたり$0.01・720pは秒あたり$0.05（xAI課金）",
    },
    "vid_free_note": {
        "ko": "Grok CLI(Imagine)로 생성 — 구독 사용량에 포함, 추가 과금 없음. 길이는 6초/10초로 맞춰져요.",
        "en": "Generated with Grok CLI (Imagine) — included in your subscription, no extra billing. Length snaps to 6s/10s.",
        "ja": "Grok CLI（Imagine）で生成 — サブスクリプションに含まれ、追加課金なし。長さは6秒/10秒になります。",
    },
    "vid_download": {
        "ko": "⬇️ MP4 다운로드",
        "en": "⬇️ Download MP4",
        "ja": "⬇️ MP4をダウンロード",
    },
    "vid_error": {
        "ko": "영상 생성에 실패했어요: {err}",
        "en": "Video generation failed: {err}",
        "ja": "動画の生成に失敗しました: {err}",
    },

    # ─── Curator Tab ───
    "cur_subheader": {
        "ko": "Personalized Feed Curator",
        "en": "Personalized Feed Curator",
        "ja": "パーソナライズドフィードキュレーター",
    },
    "cur_caption": {
        "ko": "선택한 AI 엔진으로 관심사 기반 추천 포스트를 찾습니다",
        "en": "Find recommended posts based on your interests with the selected AI engine",
        "ja": "選択したAIエンジンで関心ベースのおすすめポストを探します",
    },
    "cur_interest_label": {
        "ko": "관심사 입력",
        "en": "Enter Interests",
        "ja": "関心事を入力",
    },
    "cur_interest_placeholder": {
        "ko": "예: 한국 테크 뉴스, AI 프로그래밍, 스타트업 트렌드",
        "en": "e.g., tech news, AI programming, startup trends",
        "ja": "例：テックニュース、AIプログラミング、スタートアップトレンド",
    },
    "cur_search_btn": {
        "ko": "🔍 실시간 추천",
        "en": "🔍 Real-time Recommendations",
        "ja": "🔍 リアルタイムおすすめ",
    },
    "cur_enter_interest": {
        "ko": "관심사를 입력해주세요.",
        "en": "Please enter your interests.",
        "ja": "関心事を入力してください。",
    },
    "cur_spinner": {
        "ko": "선택한 AI 엔진이 추천을 준비 중...",
        "en": "The selected AI engine is preparing recommendations...",
        "ja": "選択したAIエンジンがおすすめを準備中...",
    },
    "cur_why": {
        "ko": "💡 왜 추천했나요?",
        "en": "💡 Why recommended?",
        "ja": "💡 なぜおすすめ？",
    },
    "cur_search_x": {
        "ko": "🔍 X에서 관련 포스트 검색",
        "en": "🔍 Search related posts on X",
        "ja": "🔍 Xで関連ポストを検索",
    },
    "cur_reply_caption": {
        "ko": "💬 추천 리플 (복사해서 사용하세요)",
        "en": "💬 Suggested reply (copy and use)",
        "ja": "💬 おすすめリプライ（コピーして使用）",
    },

    # ─── Thread Tab ───
    "thr_subheader": {
        "ko": "🧵 스레드 최적화기",
        "en": "🧵 Thread Optimizer",
        "ja": "🧵 スレッド最適化",
    },
    "thr_caption": {
        "ko": "Author Diversity 감쇠를 고려한 스레드 구조 분석",
        "en": "Thread structure analysis considering Author Diversity decay",
        "ja": "Author Diversity減衰を考慮したスレッド構造分析",
    },
    "thr_input_label": {
        "ko": "스레드 내용",
        "en": "Thread content",
        "ja": "スレッド内容",
    },
    "thr_input_placeholder": {
        "ko": "각 트윗을 --- 또는 빈 줄로 구분하세요...\n\n첫 번째 트윗 내용\n---\n두 번째 트윗 내용\n---\n세 번째 트윗 내용",
        "en": "Separate each tweet with --- or blank lines...\n\nFirst tweet\n---\nSecond tweet\n---\nThird tweet",
        "ja": "各ツイートを---または空行で区切ってください...\n\n1つ目のツイート\n---\n2つ目のツイート\n---\n3つ目のツイート",
    },
    "thr_detected": {
        "ko": "감지된 트윗 수: {n}개",
        "en": "Detected tweets: {n}",
        "ja": "検出されたツイート数：{n}件",
    },
    "thr_analyze_btn": {
        "ko": "🧵 스레드 분석",
        "en": "🧵 Analyze Thread",
        "ja": "🧵 スレッド分析",
    },
    "thr_enter_content": {
        "ko": "스레드 내용을 입력해주세요.",
        "en": "Please enter your thread content.",
        "ja": "スレッド内容を入力してください。",
    },
    "thr_spinner": {
        "ko": "선택한 AI 엔진이 스레드를 분석 중...",
        "en": "The selected AI engine is analyzing the thread...",
        "ja": "選択したAIエンジンがスレッドを分析中...",
    },
    "thr_overall_score": {
        "ko": "전체 스레드 점수",
        "en": "Overall Thread Score",
        "ja": "全体スレッドスコア",
    },
    "thr_hook_quality": {
        "ko": "Hook 품질",
        "en": "Hook Quality",
        "ja": "Hook品質",
    },
    "thr_optimal_count": {
        "ko": "최적 트윗 수",
        "en": "Optimal Tweet Count",
        "ja": "最適ツイート数",
    },
    "thr_per_tweet": {
        "ko": "📊 트윗별 분석",
        "en": "📊 Per-Tweet Analysis",
        "ja": "📊 ツイート別分析",
    },
    "thr_score": {
        "ko": "점수",
        "en": "Score",
        "ja": "スコア",
    },
    "thr_multiplier": {
        "ko": "노출 배율",
        "en": "Visibility Multiplier",
        "ja": "露出倍率",
    },
    "thr_analysis": {
        "ko": "분석 보기",
        "en": "View Analysis",
        "ja": "分析を見る",
    },
    "thr_flow": {
        "ko": "📊 스레드 흐름 분석",
        "en": "📊 Thread Flow Analysis",
        "ja": "📊 スレッドフロー分析",
    },
    "thr_narrative": {
        "ko": "내러티브 아크",
        "en": "Narrative Arc",
        "ja": "ナラティブアーク",
    },
    "thr_cta": {
        "ko": "CTA 분석",
        "en": "CTA Analysis",
        "ja": "CTA分析",
    },
    "thr_optimized": {
        "ko": "✨ 최적화된 스레드",
        "en": "✨ Optimized Thread",
        "ja": "✨ 最適化されたスレッド",
    },
    "thr_strategy_notes": {
        "ko": "💡 전략 노트",
        "en": "💡 Strategy Notes",
        "ja": "💡 戦略ノート",
    },
    "thr_post_first": {
        "ko": "𝕏 에 첫 트윗 게시",
        "en": "Post first tweet to 𝕏",
        "ja": "𝕏 に最初のツイートを投稿",
    },

    # ─── Scheduler Tab ───
    "sch_subheader": {
        "ko": "📅 포스팅 스케줄러",
        "en": "📅 Posting Scheduler",
        "ja": "📅 投稿スケジューラー",
    },
    "sch_caption": {
        "ko": "Author Diversity 감쇠를 최소화하는 최적 포스팅 일정",
        "en": "Optimal posting schedule minimizing Author Diversity decay",
        "ja": "Author Diversity減衰を最小化する最適な投稿スケジュール",
    },
    "sch_post_count": {
        "ko": "포스트 수",
        "en": "Number of posts",
        "ja": "ポスト数",
    },
    "sch_topic_label": {
        "ko": "주제/설명",
        "en": "Topic/Description",
        "ja": "テーマ/説明",
    },
    "sch_topic_placeholder": {
        "ko": "예: AI 트렌드 분석",
        "en": "e.g., AI trend analysis",
        "ja": "例：AIトレンド分析",
    },
    "sch_content_label": {
        "ko": "내용 (선택)",
        "en": "Content (optional)",
        "ja": "内容（任意）",
    },
    "sch_content_placeholder": {
        "ko": "이미 작성한 내용이 있으면 입력...",
        "en": "Enter content if already written...",
        "ja": "既に作成した内容があれば入力...",
    },
    "sch_generate_btn": {
        "ko": "📅 최적 스케줄 생성",
        "en": "📅 Generate Optimal Schedule",
        "ja": "📅 最適スケジュール生成",
    },
    "sch_enter_topic": {
        "ko": "최소 1개 포스트의 주제를 입력해주세요.",
        "en": "Please enter at least one post topic.",
        "ja": "少なくとも1つのポストテーマを入力してください。",
    },
    "sch_spinner": {
        "ko": "선택한 AI 엔진이 최적 스케줄을 설계 중...",
        "en": "The selected AI engine is designing the optimal schedule...",
        "ja": "選択したAIエンジンが最適スケジュールを設計中...",
    },
    "sch_diversity_score": {
        "ko": "주제 다양성 점수",
        "en": "Topic Diversity Score",
        "ja": "テーマ多様性スコア",
    },
    "sch_posting_order": {
        "ko": "추천 포스팅 순서",
        "en": "Recommended Posting Order",
        "ja": "おすすめ投稿順序",
    },
    "sch_timeline": {
        "ko": "📋 추천 타임라인",
        "en": "📋 Recommended Timeline",
        "ja": "📋 おすすめタイムライン",
    },
    "sch_visibility": {
        "ko": "노출 예상",
        "en": "Expected Visibility",
        "ja": "露出予想",
    },
    "sch_decay": {
        "ko": "📉 Author Diversity 감쇠",
        "en": "📉 Author Diversity Decay",
        "ja": "📉 Author Diversity減衰",
    },
    "sch_visibility_pct": {
        "ko": "노출 {pct}%",
        "en": "Visibility {pct}%",
        "ja": "露出 {pct}%",
    },
    "sch_time_gap": {
        "ko": "⏱️ 시간 간격 분석",
        "en": "⏱️ Time Gap Analysis",
        "ja": "⏱️ 時間間隔分析",
    },
    "sch_overall_strategy": {
        "ko": "💡 전체 전략",
        "en": "💡 Overall Strategy",
        "ja": "💡 全体戦略",
    },

    # ─── A/B Compare Tab ───
    "ab_subheader": {
        "ko": "⚖️ A/B 비교 분석기",
        "en": "⚖️ A/B Comparison Analyzer",
        "ja": "⚖️ A/B比較分析",
    },
    "ab_caption": {
        "ko": "두 포스트를 나란히 비교하여 승자를 판별합니다",
        "en": "Compare two posts side by side to determine the winner",
        "ja": "2つのポストを並べて比較し、勝者を判定します",
    },
    "ab_post_a": {
        "ko": "포스트 A",
        "en": "Post A",
        "ja": "ポスト A",
    },
    "ab_post_b": {
        "ko": "포스트 B",
        "en": "Post B",
        "ja": "ポスト B",
    },
    "ab_placeholder_a": {
        "ko": "첫 번째 포스트 내용...",
        "en": "First post content...",
        "ja": "1つ目のポスト内容...",
    },
    "ab_placeholder_b": {
        "ko": "두 번째 포스트 내용...",
        "en": "Second post content...",
        "ja": "2つ目のポスト内容...",
    },
    "ab_compare_btn": {
        "ko": "⚖️ 비교 분석",
        "en": "⚖️ Compare & Analyze",
        "ja": "⚖️ 比較分析",
    },
    "ab_enter_both": {
        "ko": "두 포스트 모두 입력해주세요.",
        "en": "Please enter both posts.",
        "ja": "両方のポストを入力してください。",
    },
    "ab_spinner": {
        "ko": "선택한 AI 엔진이 두 포스트를 비교 분석 중...",
        "en": "The selected AI engine is comparing both posts...",
        "ja": "選択したAIエンジンが2つのポストを比較分析中...",
    },
    "ab_winner": {
        "ko": "🏆 포스트 {w} 승리! (+{d}점)",
        "en": "🏆 Post {w} wins! (+{d} points)",
        "ja": "🏆 ポスト {w} 勝利！(+{d}点)",
    },
    "ab_score_label": {
        "ko": "포스트 {l} 점수",
        "en": "Post {l} Score",
        "ja": "ポスト {l} スコア",
    },
    "ab_grade": {
        "ko": "등급",
        "en": "Grade",
        "ja": "等級",
    },
    "ab_strengths": {
        "ko": "💪 강점",
        "en": "💪 Strengths",
        "ja": "💪 強み",
    },
    "ab_weaknesses": {
        "ko": "⚠️ 약점",
        "en": "⚠️ Weaknesses",
        "ja": "⚠️ 弱点",
    },
    "ab_action_compare": {
        "ko": "📊 행동별 비교 분석",
        "en": "📊 Action-by-Action Comparison",
        "ja": "📊 行動別比較分析",
    },
    "ab_improve": {
        "ko": "💡 포스트 {l} 개선 제안",
        "en": "💡 Improvement Suggestions for Post {l}",
        "ja": "💡 ポスト {l} 改善提案",
    },
    "ab_best_post": {
        "ko": "✨ 최적 합성 포스트",
        "en": "✨ Best Combined Post",
        "ja": "✨ 最適合成ポスト",
    },

    # ─── Risk Check Tab ───
    "risk_subheader": {
        "ko": "⚠️ 리스크 체크",
        "en": "⚠️ Risk Check",
        "ja": "⚠️ リスクチェック",
    },
    "risk_caption": {
        "ko": "수익 중지 · 계정 정지 · 노출 제한 위험을 사전 분석합니다",
        "en": "Pre-analyze risks: demonetization, suspension, visibility filtering",
        "ja": "収益停止・アカウント停止・露出制限リスクを事前分析します",
    },
    "risk_warning": {
        "ko": "요즘 X가 수익 중지와 계정 정지를 자주 하고 있습니다. 올리기 전에 미리 체크해보세요.",
        "en": "X has been frequently suspending monetization and accounts lately. Check before posting.",
        "ja": "最近Xは収益停止やアカウント停止を頻繁に行っています。投稿前にチェックしましょう。",
    },
    "risk_placeholder": {
        "ko": "리스크를 체크할 포스트 내용을 입력하세요...",
        "en": "Enter the post content to check for risks...",
        "ja": "リスクをチェックするポスト内容を入力してください...",
    },
    "risk_image_placeholder": {
        "ko": "예: 정치인 합성 사진, 폭력적 장면 등",
        "en": "e.g., political deepfake, violent scene",
        "ja": "例：政治家の合成写真、暴力的なシーン等",
    },
    "risk_analyze_btn": {
        "ko": "⚠️ 리스크 분석하기",
        "en": "⚠️ Analyze Risks",
        "ja": "⚠️ リスク分析する",
    },
    "risk_spinner": {
        "ko": "선택한 AI 엔진이 리스크를 분석하고 있습니다...",
        "en": "The selected AI engine is analyzing risks...",
        "ja": "選択したAIエンジンがリスクを分析しています...",
    },
    "risk_level_label": {
        "ko": "전체 위험도",
        "en": "Overall Risk Level",
        "ja": "全体リスクレベル",
    },
    "risk_score_label": {
        "ko": "위험 점수",
        "en": "Risk Score",
        "ja": "リスクスコア",
    },
    "risk_low": {"ko": "낮음", "en": "Low", "ja": "低"},
    "risk_medium": {"ko": "중간", "en": "Medium", "ja": "中"},
    "risk_high": {"ko": "높음", "en": "High", "ja": "高"},
    "risk_critical": {"ko": "매우 높음", "en": "Critical", "ja": "非常に高い"},
    "risk_msg_low": {
        "ko": "안전한 포스트입니다!",
        "en": "This post is safe!",
        "ja": "安全なポストです！",
    },
    "risk_msg_medium": {
        "ko": "일부 주의가 필요합니다.",
        "en": "Some caution needed.",
        "ja": "一部注意が必要です。",
    },
    "risk_msg_high": {
        "ko": "수정을 강력히 권장합니다.",
        "en": "Modification is strongly recommended.",
        "ja": "修正を強くお勧めします。",
    },
    "risk_msg_critical": {
        "ko": "게시하면 안 됩니다!",
        "en": "Do NOT post this!",
        "ja": "投稿してはいけません！",
    },
    "risk_checklist": {
        "ko": "📋 안전 체크리스트",
        "en": "📋 Safety Checklist",
        "ja": "📋 安全チェックリスト",
    },
    "risk_items_title": {
        "ko": "🔍 위험 항목 ({n}건)",
        "en": "🔍 Risk Items ({n})",
        "ja": "🔍 リスク項目（{n}件）",
    },
    "risk_phrases_title": {
        "ko": "📍 위험 문구 ({n}건)",
        "en": "📍 Risky Phrases ({n})",
        "ja": "📍 危険フレーズ（{n}件）",
    },
    "risk_phrase_label": {
        "ko": "위험 문구:",
        "en": "Risky phrase:",
        "ja": "危険フレーズ：",
    },
    "risk_safe_alt": {
        "ko": "안전한 대체:",
        "en": "Safe alternative:",
        "ja": "安全な代替：",
    },
    "risk_safe_version": {
        "ko": "✅ 안전하게 수정된 포스트",
        "en": "✅ Safely Modified Post",
        "ja": "✅ 安全に修正されたポスト",
    },
    "risk_post_safe": {
        "ko": "𝕏 에 안전한 버전으로 게시",
        "en": "Post safe version to 𝕏",
        "ja": "𝕏 に安全なバージョンで投稿",
    },

    # ─── Unfollow Tab ───
    "unf_subheader": {
        "ko": "🔄 언팔 추적",
        "en": "🔄 Unfollow Tracker",
        "ja": "🔄 アンフォロー追跡",
    },
    "unf_caption": {
        "ko": "팔로워 리스트를 비교하여 언팔/신규 팔로워를 추적합니다",
        "en": "Compare follower lists to track unfollows/new followers",
        "ja": "フォロワーリストを比較してアンフォロー/新規フォロワーを追跡します",
    },
    "unf_safe_info": {
        "ko": (
            "**📋 안전한 방법: X 공식 데이터 아카이브**\n\n"
            "1. [X 설정](https://x.com/settings/download_your_data) → '데이터 아카이브 요청'\n"
            "2. 24~48시간 후 다운로드 링크 이메일 수신\n"
            "3. 압축 해제 후 `data/follower.js` 파일을 여기에 업로드\n\n"
            "이 방법은 X 공식 기능이므로 계정 정지 위험이 **전혀 없습니다**."
        ),
        "en": (
            "**📋 Safe method: X Official Data Archive**\n\n"
            "1. [X Settings](https://x.com/settings/download_your_data) → 'Request data archive'\n"
            "2. Download link will be emailed in 24-48 hours\n"
            "3. Extract and upload `data/follower.js` file here\n\n"
            "This is an official X feature with **zero risk** of account suspension."
        ),
        "ja": (
            "**📋 安全な方法：X公式データアーカイブ**\n\n"
            "1. [X設定](https://x.com/settings/download_your_data) → 'データアーカイブをリクエスト'\n"
            "2. 24〜48時間後にダウンロードリンクがメールで届きます\n"
            "3. 解凍後、`data/follower.js`ファイルをここにアップロード\n\n"
            "これはX公式機能なのでアカウント停止のリスクは**一切ありません**。"
        ),
    },
    "unf_fast_expander": {
        "ko": "⚡ 더 빠르게 하고 싶다면 (주의)",
        "en": "⚡ Want it faster? (Caution)",
        "ja": "⚡ もっと早くしたい場合（注意）",
    },
    "unf_fast_warning": {
        "ko": (
            "⚠️ **Chrome 확장 프로그램 사용 시 주의사항**\n\n"
            "- 비공식 도구는 X 이용약관 위반으로 **계정 정지** 위험이 있습니다.\n"
            "- 단시간 대량 요청 시 일시/영구 정지될 수 있습니다.\n"
            "- 사용 시 CSV로 내보내기 후 여기에 업로드하세요.\n\n"
            "**권장:** X 공식 아카이브를 이용하세요."
        ),
        "en": (
            "⚠️ **Chrome extension usage warning**\n\n"
            "- Unofficial tools risk **account suspension** by violating X's ToS.\n"
            "- Mass requests may lead to temporary/permanent suspension.\n"
            "- Export as CSV and upload here.\n\n"
            "**Recommended:** Use X's official archive."
        ),
        "ja": (
            "⚠️ **Chrome拡張機能使用時の注意事項**\n\n"
            "- 非公式ツールはX利用規約違反で**アカウント停止**のリスクがあります。\n"
            "- 短時間の大量リクエストで一時/永久停止される可能性があります。\n"
            "- CSVでエクスポートしてここにアップロードしてください。\n\n"
            "**推奨：** X公式アーカイブをご利用ください。"
        ),
    },
    "unf_upload_title": {
        "ko": "📂 팔로워 리스트 업로드",
        "en": "📂 Upload Follower Lists",
        "ja": "📂 フォロワーリストをアップロード",
    },
    "unf_followers_file": {
        "ko": "팔로워 파일 (필수)",
        "en": "Followers file (required)",
        "ja": "フォロワーファイル（必須）",
    },
    "unf_followers_help": {
        "ko": "follower.js 또는 팔로워 CSV 파일",
        "en": "follower.js or followers CSV file",
        "ja": "follower.jsまたはフォロワーCSVファイル",
    },
    "unf_following_file": {
        "ko": "팔로잉 파일 (선택 — 맞팔 구분용)",
        "en": "Following file (optional — for mutual detection)",
        "ja": "フォロー中ファイル（任意 — 相互フォロー判定用）",
    },
    "unf_following_help": {
        "ko": "following.js 또는 팔로잉 CSV 파일",
        "en": "following.js or following CSV file",
        "ja": "following.jsまたはフォローCSVファイル",
    },
    "unf_parse_error": {
        "ko": "파일에서 팔로워를 찾을 수 없습니다. 파일 형식을 확인해주세요.",
        "en": "Could not find followers in the file. Please check the file format.",
        "ja": "ファイルからフォロワーが見つかりません。ファイル形式を確認してください。",
    },
    "unf_detected": {
        "ko": "팔로워 **{n}**명 감지",
        "en": "**{n}** followers detected",
        "ja": "フォロワー **{n}**人検出",
    },
    "unf_following_detected": {
        "ko": "팔로잉 **{n}**명 감지 (맞팔: **{m}**명)",
        "en": "**{n}** following detected (mutual: **{m}**)",
        "ja": "フォロー中 **{n}**人検出（相互：**{m}**人）",
    },
    "unf_snapshot_label": {
        "ko": "스냅샷 라벨",
        "en": "Snapshot label",
        "ja": "スナップショットラベル",
    },
    "unf_save_btn": {
        "ko": "📸 스냅샷 저장",
        "en": "📸 Save Snapshot",
        "ja": "📸 スナップショット保存",
    },
    "unf_saved": {
        "ko": "스냅샷 '{label}' 저장 완료 (팔로워 {n}명)",
        "en": "Snapshot '{label}' saved ({n} followers)",
        "ja": "スナップショット '{label}' 保存完了（フォロワー{n}人）",
    },
    "unf_csv_download": {
        "ko": "📥 팔로워 리스트 CSV 다운로드",
        "en": "📥 Download Followers CSV",
        "ja": "📥 フォロワーリストCSVダウンロード",
    },
    "unf_compare_title": {
        "ko": "📊 스냅샷 비교",
        "en": "📊 Compare Snapshots",
        "ja": "📊 スナップショット比較",
    },
    "unf_need_snapshots": {
        "ko": "현재 저장된 스냅샷: **{n}개**\n\n비교하려면 **최소 2개의 스냅샷**이 필요합니다.\n서로 다른 시점의 팔로워 파일을 업로드하고 저장하세요.",
        "en": "Saved snapshots: **{n}**\n\nYou need **at least 2 snapshots** to compare.\nUpload and save follower files from different time points.",
        "ja": "保存済みスナップショット：**{n}個**\n\n比較するには**最低2つのスナップショット**が必要です。\n異なる時点のフォロワーファイルをアップロードして保存してください。",
    },
    "unf_old_snapshot": {
        "ko": "이전 스냅샷",
        "en": "Previous Snapshot",
        "ja": "以前のスナップショット",
    },
    "unf_new_snapshot": {
        "ko": "현재 스냅샷",
        "en": "Current Snapshot",
        "ja": "現在のスナップショット",
    },
    "unf_diff_warning": {
        "ko": "서로 다른 스냅샷을 선택하세요.",
        "en": "Please select different snapshots.",
        "ja": "異なるスナップショットを選択してください。",
    },
    "unf_compare_btn": {
        "ko": "🔍 비교하기",
        "en": "🔍 Compare",
        "ja": "🔍 比較する",
    },
    "unf_unfollowed": {
        "ko": "😢 언팔",
        "en": "😢 Unfollowed",
        "ja": "😢 アンフォロー",
    },
    "unf_new_followers": {
        "ko": "🎉 새 팔로워",
        "en": "🎉 New Followers",
        "ja": "🎉 新規フォロワー",
    },
    "unf_unchanged": {
        "ko": "🤝 유지",
        "en": "🤝 Unchanged",
        "ja": "🤝 維持",
    },
    "unf_mutual_unf": {
        "ko": "💔 맞팔이었다가 언팔한 사람 ({n}명)",
        "en": "💔 Mutual followers who unfollowed ({n})",
        "ja": "💔 相互フォローだったのにアンフォローした人（{n}人）",
    },
    "unf_mutual_caption": {
        "ko": "내가 팔로우 중인데 상대가 언팔한 사람들",
        "en": "People you follow who unfollowed you",
        "ja": "あなたがフォロー中なのに相手がアンフォローした人",
    },
    "unf_simple_unf": {
        "ko": "👋 단순 언팔한 사람 ({n}명)",
        "en": "👋 Simple unfollows ({n})",
        "ja": "👋 単純アンフォロー（{n}人）",
    },
    "unf_no_unfollows": {
        "ko": "🎉 언팔한 사람이 없습니다!",
        "en": "🎉 No one unfollowed you!",
        "ja": "🎉 アンフォローした人はいません！",
    },
    "unf_new_title": {
        "ko": "🎉 새로 팔로우한 사람 ({n}명)",
        "en": "🎉 New followers ({n})",
        "ja": "🎉 新規フォロワー（{n}人）",
    },
    "unf_table_user": {
        "ko": "사용자",
        "en": "User",
        "ja": "ユーザー",
    },
    "unf_table_profile": {
        "ko": "프로필",
        "en": "Profile",
        "ja": "プロフィール",
    },
    "unf_view_on_x": {
        "ko": "X에서 보기",
        "en": "View on X",
        "ja": "Xで見る",
    },
    "unf_show_more": {
        "ko": "나머지 {n}명 더 보기",
        "en": "Show {n} more",
        "ja": "残り{n}人を表示",
    },
    "unf_download_snapshots": {
        "ko": "📥 스냅샷 백업 (JSON)",
        "en": "📥 Backup Snapshots (JSON)",
        "ja": "📥 スナップショットバックアップ (JSON)",
    },
    "unf_upload_snapshots": {
        "ko": "📤 스냅샷 복원 (JSON)",
        "en": "📤 Restore Snapshots (JSON)",
        "ja": "📤 スナップショット復元 (JSON)",
    },
    "unf_upload_success": {
        "ko": "✅ 스냅샷 {n}개 복원 완료",
        "en": "✅ {n} snapshots restored",
        "ja": "✅ {n}件復元完了",
    },
    "unf_upload_error": {
        "ko": "JSON 파싱 실패. 올바른 스냅샷 파일인지 확인하세요.",
        "en": "Failed to parse JSON. Please check the snapshot file.",
        "ja": "JSON解析失敗。正しいスナップショットファイルか確認してください。",
    },
    "unf_export_unfollowed": {
        "ko": "📥 언팔 목록 CSV",
        "en": "📥 Unfollowed CSV",
        "ja": "📥 アンフォローCSV",
    },
    "unf_export_new": {
        "ko": "📥 새 팔로워 CSV",
        "en": "📥 New Followers CSV",
        "ja": "📥 新フォロワーCSV",
    },
    "unf_export_mutual": {
        "ko": "📥 맞팔 언팔 CSV",
        "en": "📥 Mutual Unfollowed CSV",
        "ja": "📥 相互アンフォローCSV",
    },
    "unf_unfollow_back": {
        "ko": "🚫 나도 언팔",
        "en": "🚫 Unfollow back",
        "ja": "🚫 フォロー解除",
    },
}


def get_lang() -> str:
    """Get current language from session state."""
    return st.session_state.get("lang", "ko")


def normalize_language(language: str | None) -> str:
    """Normalize a language code, falling back to Korean for unknown values."""
    return language if language in LANGUAGES else "ko"


def translate(key: str, language: str | None = None, **kwargs) -> str:
    """Translate a key to an explicit language, or the current Streamlit language."""
    entry = _T.get(key)
    if not entry:
        return key
    lang = get_lang() if language is None else normalize_language(language)
    text = entry.get(lang, entry.get("ko", key))
    if kwargs:
        text = text.format(**kwargs)
    return text


def t(key: str, **kwargs) -> str:
    """Translate a key to the current language."""
    return translate(key, **kwargs)


def get_action_labels() -> dict:
    """Return action label mapping for current language."""
    return {
        "reply": t("action_reply"),
        "repost": t("action_repost"),
        "like": t("action_like"),
        "quote": t("action_quote"),
        "bookmark": t("action_bookmark"),
        "follow": t("action_follow"),
        "dwell_time": t("action_dwell_time"),
        "share": t("action_share"),
        "photo_expansion": t("action_photo_expansion"),
        "oon_discovery": t("action_oon_discovery"),
    }


def get_lang_instruction(language: str | None = None) -> str:
    """Get the language instruction suffix for Grok prompts."""
    lang = get_lang() if language is None else normalize_language(language)
    return LANG_INSTRUCTION.get(lang, "")


def get_content_language_pair(language: str | None = None) -> str:
    """Get the content-language pair the curator should explore, based on UI language."""
    lang = get_lang() if language is None else normalize_language(language)
    return LANG_CONTENT_PAIR.get(lang, LANG_CONTENT_PAIR["ko"])


def get_output_language_name(language: str | None = None) -> str:
    """Get the English name of the target output language for embedding in prompts."""
    lang = get_lang() if language is None else normalize_language(language)
    return LANG_OUTPUT_NAME.get(lang, LANG_OUTPUT_NAME["ko"])
