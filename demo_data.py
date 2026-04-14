"""API 키 없이 방문한 사용자에게 각 핵심 탭의 UI 가 어떻게 생겼는지
즉시 보여주기 위한 프리셋 결과.

v1 은 한국어 콘텐츠만 제공한다. i18n 확장은 후속 작업.
각 딕셔너리의 스키마는 해당 tabs/tab_*.py 렌더러가 기대하는 구조와
정확히 일치해야 한다.
"""

from __future__ import annotations


OPTIMIZER_DEMO = {
    "score": 72,
    "engagement_level": "High",
    "action_breakdown": {
        "reply": {"probability": 45, "weight": 13.5, "contribution": 6.08},
        "like": {"probability": 72, "weight": 0.5, "contribution": 0.36},
        "repost": {"probability": 28, "weight": 1.0, "contribution": 0.28},
        "quote": {"probability": 12, "weight": 6.1, "contribution": 0.73},
        "bookmark": {"probability": 34, "weight": 1.0, "contribution": 0.34},
        "follow": {"probability": 18, "weight": 12.0, "contribution": 2.16},
        "dwell_time": {"probability": 80, "weight": 0.5, "contribution": 0.40},
        "share": {"probability": 22, "weight": 1.0, "contribution": 0.22},
        "photo_expansion": {"probability": 55, "weight": 1.0, "contribution": 0.55},
        "oon_discovery": {"probability": 15, "weight": 1.0, "contribution": 0.15},
    },
    "reasons": [
        "구체적인 숫자와 개인 경험이 포함되어 신뢰도가 높습니다",
        "Hook이 강력하고 독자의 호기심을 바로 자극하는 첫 문장입니다",
        "Reply를 유도하는 자연스러운 질문으로 마무리됩니다",
    ],
    "suggestions": [
        "1줄 요약을 최상단에 추가하면 dwell time이 추가로 올라갑니다",
        "이미지 1~2장을 붙여 photo_expansion 이벤트를 유발해보세요",
        "마지막 CTA를 '당신은 어떠세요?' 같은 짧은 질문으로 바꾸면 reply율이 더 오릅니다",
    ],
    "optimized_post": (
        "3주 전, 저는 '팔로워는 왜 안 늘지?' 하고 있었어요.\n\n"
        "지금은 +487명.\n\n"
        "딱 하나만 바꿨어요 — 매일 같은 시간에 올리고, 첫 문장은 숫자로 시작.\n\n"
        "당신의 '3주 전'은 언제였나요?"
    ),
}


IDEAS_DEMO = {
    "ideas": [
        {
            "title": "주말 2시간, 팔로워 +487명 비결",
            "content": (
                "3주 전, 주말마다 2시간씩 글만 썼어요.\n\n"
                "결과는요? 팔로워 +487명.\n\n"
                "제가 쓴 방법은 딱 하나 — 매일 같은 시간에 올리고, 첫 문장은 숫자로 시작하기.\n\n"
                "당신은 어떤 루틴으로 쓰시나요?"
            ),
            "engagement_level": "High",
            "best_time": "오전 9-10시, 저녁 9-11시",
            "target_actions": ["reply", "like", "follow"],
            "strategy": (
                "개인 경험 + 구체적 숫자 + 질문 마무리의 3박자로 reply율을 최대화합니다. "
                "오전 골든타임에 맞춰 올리면 알고리즘 푸시 확률이 올라가요."
            ),
            "image_prompt": (
                "A cozy weekend morning desk with a laptop, a coffee cup and an open notebook, "
                "soft natural window light, minimalist aesthetic, portrait 9:16 composition, "
                "cinematic warm tones, shallow depth of field, no text, no letters"
            ),
        },
        {
            "title": "1달 만에 콘텐츠 엔진 만든 3단계",
            "content": (
                "콘텐츠 막막하신 분들께.\n\n"
                "1달 전만 해도 저도 똑같았어요.\n\n"
                "지금은 주 5개 자동으로 올립니다. 비결은 3단계:\n\n"
                "1. 관심사 10개 브레인스토밍\n"
                "2. 키워드별 포맷 고정\n"
                "3. 하루 15분만 드래프트\n\n"
                "궁금한 거 있으시면 답글 주세요."
            ),
            "engagement_level": "Very High",
            "best_time": "평일 오후 12-1시",
            "target_actions": ["bookmark", "reply", "follow"],
            "strategy": (
                "리스트 포맷 + 구체적 숫자 + '궁금하면 답글' CTA 조합. "
                "bookmark율이 특히 높게 나오는 공식이에요."
            ),
            "image_prompt": (
                "Three hand-drawn sticky notes on a clean white desk showing numbers 1, 2, 3, "
                "minimal flat illustration style, soft pastel colors, overhead shot, "
                "portrait composition, no text, no letters"
            ),
        },
        {
            "title": "솔로 개발자의 밤 11시 30분 루틴",
            "content": (
                "밤 11시. 본업 끝난 뒤 가장 중요한 30분.\n\n"
                "사이드 프로젝트 진도를 체크하고, 내일 할 일 딱 1개만 적어요.\n\n"
                "이게 1년 쌓이니 솔로로도 앱 하나가 굴러갑니다.\n\n"
                "오늘 밤 당신의 30분은 뭐에 쓰시나요?"
            ),
            "engagement_level": "High",
            "best_time": "저녁 10-11시",
            "target_actions": ["reply", "like", "dwell_time"],
            "strategy": (
                "공감 가능한 시간대 구체화 + 개인사 + 오늘로 이어지는 CTA. "
                "같은 처지의 개발자·창업자에게 강하게 꽂힙니다."
            ),
            "image_prompt": (
                "A late night home office scene with a single warm desk lamp illuminating "
                "a laptop and a small notebook, dark background, cinematic amber mood, "
                "portrait 9:16 composition, no text, no letters"
            ),
        },
    ],
}


CURATOR_DEMO = {
    "recommendations": [
        {
            "summary": "솔로 개발자가 월 $100 MRR 내는 앱을 만드는 5단계 (최근 화제)",
            "why_recommended": (
                "'솔로 개발자' 관심사와 정확히 매치됩니다. 구체적인 수익 숫자와 "
                "실용 가이드가 담긴 포스트라 bookmark율이 높게 나오는 편이에요."
            ),
            "search_keywords": "solo developer $100 MRR",
            "suggested_reply": (
                "5단계 중 2번 마케팅 부분이 저한테 가장 막막한데, 혹시 추천 자료가 있으실까요?"
            ),
            "engagement_hint": "질문형 답글은 원저자의 추가 답변을 유도해 대화 연결에 유리합니다",
        },
        {
            "summary": "AI 코딩 어시스턴트 3개 직접 비교 (Cursor vs Copilot vs Continue)",
            "why_recommended": (
                "AI 도구 관심사 기반. 실사용 후기 포스트는 bookmark + follow 양쪽 모두 유도합니다."
            ),
            "search_keywords": "Cursor Copilot Continue comparison",
            "suggested_reply": "저는 Cursor 쓰는데 Continue는 처음 들어봐요. 로컬 LLM 연결이 되나요?",
            "engagement_hint": "본인 경험 + 구체 질문 조합으로 답글에 무게감을 더하세요",
        },
        {
            "summary": "Build in Public 한 달 후기: 장점과 함정",
            "why_recommended": (
                "솔로 개발 + Build in Public 니치 포스트. 진솔한 후기라 reply가 많이 붙습니다."
            ),
            "search_keywords": "build in public lessons learned",
            "suggested_reply": (
                "저도 이번 주에 첫 공개했는데 반응이 적어 속상하던 참이에요. "
                "언제쯤 반응이 돌았나요?"
            ),
            "engagement_hint": "공감 + 경험 공유 + 열린 질문으로 상호작용 확률을 높이세요",
        },
    ],
}


THREAD_DEMO = {
    "overall_score": 78,
    "thread_flow": {
        "hook_quality": "Strong",
        "optimal_tweet_count": 5,
        "narrative_arc": (
            "Hook → 문제 제기 → 개인 경험 → 실행 방법 → CTA 순으로 자연스럽게 이어집니다. "
            "독자가 끝까지 읽을 동기가 각 단계마다 명확해요."
        ),
        "cta_analysis": (
            "마지막 트윗의 '당신의 3주 전은?' 질문이 reply를 유도하는 표준 패턴. "
            "조금 더 구체적인 질문이면 답글율이 더 올라갑니다."
        ),
    },
    "tweets": [
        {
            "position": 1,
            "score": 82,
            "decay_multiplier": 1.00,
            "effective_score": 82,
            "analysis": (
                "Hook이 강력합니다. 구체적인 숫자(3주, 487명)가 즉시 호기심을 자극하고, "
                "'딱 하나만 바꿨거든요'가 후속 트윗을 읽게 만드는 미끼로 완벽해요."
            ),
        },
        {
            "position": 2,
            "score": 74,
            "decay_multiplier": 0.85,
            "effective_score": 63,
            "analysis": (
                "문제 제기가 명확합니다. 다만 '막막하죠?' 같은 공감 문구를 1개 더 넣으면 "
                "감정 이입이 올라가고 다음 트윗 전환이 더 부드러워집니다."
            ),
        },
        {
            "position": 3,
            "score": 70,
            "decay_multiplier": 0.72,
            "effective_score": 50,
            "analysis": (
                "해결책이 명료하지만 구체성이 살짝 부족합니다. 사용한 도구 이름이나 정확한 "
                "시간대를 1개만 추가해도 체감 신뢰도가 크게 오릅니다."
            ),
        },
        {
            "position": 4,
            "score": 68,
            "decay_multiplier": 0.60,
            "effective_score": 41,
            "analysis": (
                "결과 숫자 비교가 강력합니다. bookmark율이 높게 나올 구간이라 "
                "마지막 CTA 트윗으로 자연스럽게 넘기세요."
            ),
        },
    ],
    "optimized_thread": [
        (
            "3주 전, 저도 '팔로워는 왜 안 늘지?' 하고 있었어요.\n\n"
            "지금은 +487명.\n\n"
            "딱 하나만 바꿨거든요. 🧵"
        ),
        "콘텐츠를 많이 올리는 게 정답인 줄 알았죠.\n\n근데 반응은 0.\n\n막막하더라고요.",
        (
            "그래서 딱 한 가지만 바꿨어요 — 첫 문장을 무조건 숫자로 시작.\n\n"
            "'3주 전', '월 $100', '15분 루틴'...\n\n이렇게요."
        ),
        "효과는 3일 만에 왔어요.\n\n평균 좋아요: 5 → 42\n평균 답글: 0 → 8\n\n숫자 하나가 이렇게 셀 줄 몰랐습니다.",
        "첫 문장만 바꿔도 됩니다. 오늘 하나 올려보세요.\n\n당신의 '3주 전'은 언제였나요?",
    ],
    "strategy_notes": [
        "트윗 1번이 가장 중요 — 여기서 막히면 뒤 4개 트윗이 모두 묻힙니다",
        "중간 트윗(2-3번)은 decay가 크므로 짧고 강하게 유지해야 합니다",
        "마지막 CTA는 열린 질문이 닫힌 질문보다 reply율을 3~5배 올립니다",
    ],
}
