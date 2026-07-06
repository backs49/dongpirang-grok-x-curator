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


AB_DEMO = {
    "post_a": {
        "score": 64,
        "engagement_level": "Medium",
        "strengths": [
            "주제가 명확해서 관심사가 같은 독자에게는 안정적으로 전달됩니다",
            "짧고 읽기 쉬워 dwell time 대비 이탈률이 낮습니다",
            "부담 없는 톤이라 like 확률은 준수합니다",
        ],
        "weaknesses": [
            "질문이나 논점이 없어 reply 유도력이 약합니다 (×13.5 가중치를 놓침)",
            "구체적인 숫자·경험이 없어 bookmark/repost 가치가 낮습니다",
        ],
    },
    "post_b": {
        "score": 81,
        "engagement_level": "High",
        "strengths": [
            "첫 문장의 구체적 숫자(+487명)가 스크롤을 멈추는 강력한 Hook입니다",
            "개인 경험 서사가 있어 dwell time과 신뢰도가 함께 올라갑니다",
            "마지막 열린 질문이 reply(×13.5)를 직접 유도합니다",
            "실용 팁이 담겨 있어 bookmark(×4.0) 확률이 높습니다",
        ],
        "weaknesses": [
            "트렌딩 키워드가 없어 OON discovery 확장성은 보통입니다",
            "리스트 포맷이 아니라서 스캔 가독성이 살짝 아쉽습니다",
        ],
    },
    "winner": "B",
    "score_difference": 17,
    "comparative_analysis": {
        "reply": {
            "advantage": "B",
            "reason": "B는 '당신의 3주 전은?'이라는 열린 질문으로 끝나 답글 문턱이 낮습니다. A는 감상 공유형이라 답글 동기가 약해요.",
        },
        "repost": {
            "advantage": "B",
            "reason": "B의 구체적 성과 숫자는 '나도 해봐야지' 하는 공유 동기를 만듭니다. A는 공유할 실용 가치가 부족합니다.",
        },
        "bookmark": {
            "advantage": "B",
            "reason": "B는 따라 할 수 있는 방법이 담겨 있어 나중에 다시 보려고 저장합니다. A는 저장할 정보가 없어요.",
        },
        "dwell_time": {
            "advantage": "B",
            "reason": "B의 스토리 구조(전→후→방법)가 끝까지 읽게 만듭니다. A는 한눈에 다 읽혀 체류 시간이 짧습니다.",
        },
        "oon_discovery": {
            "advantage": "B",
            "reason": "'팔로워 성장'은 보편적 관심사라 팔로워 밖 노출 가능성이 상대적으로 높습니다. 둘 다 트렌딩 키워드는 없는 점이 아쉽습니다.",
        },
    },
    "improvement_for_loser": [
        "첫 문장에 구체적 숫자를 넣어 Hook을 강화하세요 (예상 +8점)",
        "마지막에 독자에게 묻는 열린 질문 한 줄을 추가하세요 (예상 +6점)",
        "본인 경험 한 토막을 넣어 신뢰도와 체류 시간을 올리세요 (예상 +4점)",
    ],
    "best_of_both": (
        "3주 전만 해도 '팔로워는 왜 안 늘지?' 하던 저였어요.\n\n"
        "지금은 +487명. 바꾼 건 딱 하나 — 매일 같은 시간, 첫 문장은 숫자로 시작.\n\n"
        "오늘 밤 글 하나만 이렇게 올려보세요.\n\n"
        "당신이 요즘 붙잡고 있는 목표는 뭔가요?"
    ),
}


SCHEDULER_DEMO = {
    "schedule": [
        {
            "position": 1,
            "topic_summary": "팔로워 +487명 성장 후기 (개인 경험 스토리)",
            "recommended_time": "저녁 7:00",
            "recommended_day": "오늘",
            "reason": (
                "퇴근 후 18-20시는 하루 중 engagement 피크 시간대입니다. "
                "가장 강력한 스토리형 콘텐츠를 여기에 배치해 첫 포스트의 "
                "감쇠 없는 노출(1.0)을 최대로 활용하세요."
            ),
            "decay_from_previous": 1.0,
            "expected_visibility": "Very High",
        },
        {
            "position": 2,
            "topic_summary": "AI 코딩 도구 3종 비교 (정보성 리스트)",
            "recommended_time": "오전 10:30",
            "recommended_day": "내일",
            "reason": (
                "오전 업무 시간대는 전문 인사이트에 최적이고 dwell time 점수가 높습니다. "
                "전날 저녁 포스트와 15시간 이상 간격을 두어 Author Diversity 감쇠를 "
                "사실상 초기화합니다. 주제도 스토리→정보성으로 교차됩니다."
            ),
            "decay_from_previous": 0.95,
            "expected_visibility": "High",
        },
        {
            "position": 3,
            "topic_summary": "밤 루틴 공감형 질문 포스트 (가벼운 대화 유도)",
            "recommended_time": "저녁 10:30",
            "recommended_day": "내일",
            "reason": (
                "심야 22-24시는 체류 시간이 길고 깊은 대화가 이루어지는 시간대라 "
                "질문형 포스트의 reply 확률이 높습니다. 같은 날 오전 포스트와 "
                "12시간 간격 + 형식 교차(리스트→질문)로 감쇠를 최소화합니다."
            ),
            "decay_from_previous": 0.88,
            "expected_visibility": "High",
        },
    ],
    "posting_order": [1, 2, 3],
    "topic_diversity_score": 82,
    "time_gap_analysis": (
        "세 포스트 모두 12시간 이상 간격이라 Author Diversity 감쇠가 거의 발생하지 "
        "않습니다 (최저 0.88). 스토리→정보성 리스트→공감형 질문으로 주제와 형식이 "
        "교차 배치되어 각 포스트가 독립적으로 평가될 확률이 높습니다."
    ),
    "decay_visualization": [
        {"post": 1, "visibility_percent": 100},
        {"post": 2, "visibility_percent": 95},
        {"post": 3, "visibility_percent": 88},
    ],
    "overall_strategy": (
        "가장 강력한 성장 후기를 engagement 피크(퇴근 후)에 먼저 올려 팔로우 전환을 "
        "노리는 배치입니다. 이후 포스트는 오전 인사이트·심야 대화형으로 시간대 특성과 "
        "형식을 맞췄습니다. 첫 포스트에서 유입된 새 팔로워가 다음 날 두 포스트를 "
        "연달아 보게 되므로, 프로필 고정 트윗을 미리 정리해두면 팔로우 전환율이 "
        "추가로 올라갑니다."
    ),
}


RISK_DEMO = {
    "risk_level": "medium",
    "risk_score": 42,
    "summary": (
        "전체적으로 안전한 홍보성 포스트지만, 과도한 해시태그와 외부 링크 조합이 "
        "스팸 필터에 걸릴 수 있고 '무조건 돈 번다' 류의 수익 보장 표현이 수익화 "
        "정책상 허위 정보로 분류될 위험이 있습니다."
    ),
    "risk_items": [
        {
            "category": "visibility",
            "category_label": "노출 제한 위험",
            "severity": "medium",
            "description": (
                "해시태그 6개 + 외부 링크 조합은 스팸 시그널로 분류될 수 있습니다. "
                "해시태그는 2개 이하로 줄이고 링크는 답글로 옮기는 것이 안전합니다."
            ),
            "affected_phrase": "#부업 #재테크 #수익화 #돈버는법 #사이드잡 #N잡",
        },
        {
            "category": "monetization",
            "category_label": "수익 중지 위험",
            "severity": "medium",
            "description": (
                "'무조건', '100% 보장' 같은 수익 보장 표현은 검증되지 않은 주장으로 "
                "간주되어 수익화 심사에서 불리하게 작용할 수 있습니다."
            ),
            "affected_phrase": "이 방법이면 무조건 월 100만 원은 법니다",
        },
    ],
    "risky_phrases": [
        {
            "phrase": "이 방법이면 무조건 월 100만 원은 법니다",
            "reason": "검증 불가능한 수익 보장 표현은 허위 정보·사기성 콘텐츠로 신고될 수 있습니다",
            "suggestion": "저는 이 방법으로 3개월 차에 월 100만 원을 만들었어요 (개인 경험 기준)",
        },
        {
            "phrase": "#부업 #재테크 #수익화 #돈버는법 #사이드잡 #N잡",
            "reason": "해시태그 5개 이상은 스팸 필터 트리거 조건에 해당합니다",
            "suggestion": "#부업 하나만 남기거나 해시태그 없이 본문 키워드로 자연스럽게 녹이세요",
        },
    ],
    "safe_version": (
        "3개월 전 시작한 사이드 프로젝트가 이번 달 처음으로 월 100만 원을 넘겼어요.\n\n"
        "제가 한 건 딱 세 가지 — 매일 기록, 주 1회 회고, 그리고 꾸준한 공유.\n\n"
        "과정이 궁금하신 분은 답글 남겨주세요. 정리해서 공유할게요."
    ),
    "checklist": [
        {"item": "혐오 표현", "passed": True, "note": "차별·비하 표현 없음"},
        {"item": "폭력/위협", "passed": True, "note": "해당 없음"},
        {"item": "허위 정보", "passed": False, "note": "'무조건 월 100만 원' 수익 보장 표현이 검증 불가"},
        {"item": "개인정보", "passed": True, "note": "노출된 개인정보 없음"},
        {"item": "스팸 요소", "passed": False, "note": "해시태그 6개는 스팸 필터 기준(5개+) 초과"},
        {"item": "외부 링크", "passed": False, "note": "본문 내 외부 링크는 노출 감소 요인 — 답글로 이동 권장"},
    ],
}


def _build_sample_analytics_csv() -> str:
    """성과 추적 탭 체험용 샘플 CSV. 날짜를 항상 최근 90일 안에 생성해
    수익화 진행률 UI 가 의미 있게 보이도록 한다."""
    from datetime import datetime, timedelta

    rows = [
        ("솔로 개발 3개월 회고, 매출 0원에서 배운 것", 82, 45210, 1890, 720, 95, 60, 210),
        ("AI 도구 월 30만원어치 써본 솔직 후기", 75, 28400, 1120, 430, 51, 38, 160),
        ("퇴근 후 2시간 루틴 공개", 60, 12800, 510, 210, 22, 15, 80),
        ("첫 유료 사용자 후기 스레드", 45, 9600, 380, 140, 18, 11, 55),
        ("개발 일지 #12 — 작은 기능 하나", 30, 3100, 95, 40, 4, 3, 12),
        ("오늘의 버그 일기", 14, 1900, 60, 22, 2, 1, 8),
        ("주말 아침 커밋 인증", 7, 5400, 230, 90, 9, 6, 30),
    ]
    lines = ['"Tweet text","time","impressions","engagements","likes","replies","retweets","bookmarks"']
    now = datetime.now()
    for text, days_ago, imp, eng, likes, replies, rts, bms in rows:
        ts = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M +0000")
        lines.append(f'"{text}","{ts}","{imp}","{eng}","{likes}","{replies}","{rts}","{bms}"')
    return "\n".join(lines) + "\n"


SAMPLE_ANALYTICS_CSV = _build_sample_analytics_csv()
