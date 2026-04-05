"""Internationalization module — Korean (default), English, Japanese."""

import streamlit as st

LANGUAGES = {"ko": "한국어", "en": "English", "ja": "日本語"}

LANG_INSTRUCTION = {
    "ko": "",
    "en": "\n\n**IMPORTANT: All text values in the JSON response MUST be written in English.**",
    "ja": "\n\n**IMPORTANT: JSON応答内のすべてのテキスト値は日本語で書いてください。**",
}

_T = {
    # ─── App-level ───
    "app_title": {
        "ko": "🔥 동피랑 Grok X 추천기",
        "en": "🔥 Dongpirang Grok X Curator",
        "ja": "🔥 東ピラン Grok X キュレーター",
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
    "api_key_help": {
        "ko": "console.x.ai에서 발급받으세요",
        "en": "Get yours at console.x.ai",
        "ja": "console.x.aiで取得してください",
    },
    "api_key_remember": {
        "ko": "🔑 API 키 기억하기",
        "en": "🔑 Remember API Key",
        "ja": "🔑 APIキーを保存",
    },
    "api_key_remember_help": {
        "ko": "브라우저 쿠키에 저장. 새로고침해도 유지됩니다.",
        "en": "Saved in browser cookies. Persists after refresh.",
        "ja": "ブラウザCookieに保存。更新後も維持されます。",
    },
    "api_key_warning": {
        "ko": "⚠️ Grok API Key는 한 번만 보여집니다.\n생성 즉시 저장하세요!",
        "en": "⚠️ Grok API Key is shown only once.\nSave it immediately!",
        "ja": "⚠️ Grok APIキーは一度だけ表示されます。\nすぐに保存してください！",
    },
    "model_select": {
        "ko": "모델 선택",
        "en": "Select Model",
        "ja": "モデル選択",
    },
    "model_help": {
        "ko": "grok-4-1-fast-reasoning: 빠른 응답 / grok-4.20-reasoning: 깊은 분석",
        "en": "grok-4-1-fast-reasoning: Fast / grok-4.20-reasoning: Deep analysis",
        "ja": "grok-4-1-fast-reasoning: 高速 / grok-4.20-reasoning: 深い分析",
    },
    "follow_btn": {
        "ko": "🐦 @mangodaon 팔로우하기",
        "en": "🐦 Follow @mangodaon",
        "ja": "🐦 @mangodaonをフォロー",
    },
    "api_required": {
        "ko": "⚠️ 이 기능을 사용하려면 사이드바에서 Grok API 키를 입력해주세요. 👉 [console.x.ai](https://console.x.ai)",
        "en": "⚠️ Enter your Grok API key in the sidebar to use this feature. 👉 [console.x.ai](https://console.x.ai)",
        "ja": "⚠️ この機能を使用するには、サイドバーでGrok APIキーを入力してください。 👉 [console.x.ai](https://console.x.ai)",
    },
    "footer_title": {
        "ko": "**동피랑 Grok X 추천기** 🔥",
        "en": "**Dongpirang Grok X Curator** 🔥",
        "ja": "**東ピラン Grok X キュレーター** 🔥",
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

    # ─── Tab names ───
    "tab_optimizer": {
        "ko": "📝 포스트 최적화",
        "en": "📝 Post Optimizer",
        "ja": "📝 ポスト最適化",
    },
    "tab_ideas": {
        "ko": "💡 아이디어 생성",
        "en": "💡 Idea Generator",
        "ja": "💡 アイデア生成",
    },
    "tab_curator": {
        "ko": "🔍 피드 큐레이터",
        "en": "🔍 Feed Curator",
        "ja": "🔍 フィードキュレーター",
    },
    "tab_thread": {
        "ko": "🧵 스레드 최적화",
        "en": "🧵 Thread Optimizer",
        "ja": "🧵 スレッド最適化",
    },
    "tab_scheduler": {
        "ko": "📅 포스팅 스케줄러",
        "en": "📅 Posting Scheduler",
        "ja": "📅 投稿スケジューラー",
    },
    "tab_ab": {
        "ko": "⚖️ A/B 비교",
        "en": "⚖️ A/B Compare",
        "ja": "⚖️ A/B比較",
    },
    "tab_risk": {
        "ko": "⚠️ 리스크 체크",
        "en": "⚠️ Risk Check",
        "ja": "⚠️ リスクチェック",
    },
    "tab_unfollow": {
        "ko": "🔄 언팔 추적",
        "en": "🔄 Unfollow Tracker",
        "ja": "🔄 アンフォロー追跡",
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
        "ko": "Grok이 x-algorithm 분석 중...",
        "en": "Grok is analyzing with x-algorithm...",
        "ja": "Grokがx-algorithmで分析中...",
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
        "ko": "x-algorithm 최적화된 포스트 아이디어를 생성합니다",
        "en": "Generate x-algorithm optimized post ideas",
        "ja": "x-algorithm最適化されたポストアイデアを生成します",
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
        "ko": "Grok이 x-algorithm 최적화 아이디어 생성 중...",
        "en": "Grok is generating x-algorithm optimized ideas...",
        "ja": "Grokがx-algorithm最適化アイデアを生成中...",
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

    # ─── Curator Tab ───
    "cur_subheader": {
        "ko": "Personalized Feed Curator",
        "en": "Personalized Feed Curator",
        "ja": "パーソナライズドフィードキュレーター",
    },
    "cur_caption": {
        "ko": "Grok의 실시간 검색으로 관심사 기반 추천 포스트를 찾습니다",
        "en": "Find recommended posts based on your interests using Grok's real-time search",
        "ja": "Grokのリアルタイム検索で関心ベースのおすすめポストを検索します",
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
        "ko": "Grok이 X에서 실시간 검색 중...",
        "en": "Grok is searching X in real-time...",
        "ja": "GrokがXでリアルタイム検索中...",
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
        "ko": "Grok이 스레드를 분석 중...",
        "en": "Grok is analyzing the thread...",
        "ja": "Grokがスレッドを分析中...",
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
        "ko": "Grok이 최적 스케줄을 설계 중...",
        "en": "Grok is designing the optimal schedule...",
        "ja": "Grokが最適スケジュールを設計中...",
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
        "ko": "Grok이 두 포스트를 비교 분석 중...",
        "en": "Grok is comparing both posts...",
        "ja": "Grokが2つのポストを比較分析中...",
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
        "ko": "Grok이 리스크를 분석하고 있습니다...",
        "en": "Grok is analyzing risks...",
        "ja": "Grokがリスクを分析しています...",
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
}


def get_lang() -> str:
    """Get current language from session state."""
    return st.session_state.get("lang", "ko")


def t(key: str, **kwargs) -> str:
    """Translate a key to the current language."""
    lang = get_lang()
    entry = _T.get(key)
    if not entry:
        return key
    text = entry.get(lang, entry.get("ko", key))
    if kwargs:
        text = text.format(**kwargs)
    return text


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


def get_lang_instruction() -> str:
    """Get the language instruction suffix for Grok prompts."""
    return LANG_INSTRUCTION.get(get_lang(), "")
