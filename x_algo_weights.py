"""X 추천 알고리즘의 실제 랭킹 가중치 — 프롬프트가 참조하는 단일 출처.

예전 프롬프트는 분석가 추정치(Reply ×13.5, Repost ×11~20)를 썼다. 공개된
소스의 값과 다르다. 값이 바뀌면 여기만 고친다.

출처: github.com/xai-org/x-algorithm home-mixer/params/param.rs
(config feature-switch 미러, 커밋 a707cc2 2026-09-29 동기화)
"""

from __future__ import annotations

SOURCE = "xai-org/x-algorithm home-mixer/params/param.rs (2026-09-29)"

# 가중 점수 = Σ weight × 예측값. 음수는 감점.
WEIGHTS: dict[str, float] = {
    "share_via_copy_link": 20.0,
    "reply": 5.0,
    "quote": 5.0,
    "share_via_dm": 5.0,
    "follow_author": 4.0,
    "share": 2.0,
    "retweet": 1.0,
    "favorite": 0.5,
    "click_dwell_time": 0.4,  # 2026-09-29 신설 (0 → 0.4)
    "click": 0.3,  # 2026-09-29 0.4 → 0.3
    "open_link": 0.2,
    "video_open": 0.07,
    "dwell": 0.05,
    "photo_expand": 0.05,
    "quoted_click": 0.05,
    "post_unexplored": 0.02,
    "dwell_time": 0.004,
    "profile_click": 0.0,
    "not_dwelled": -0.02,
    "block_author": -31.2,
    "not_interested": -47.52,  # 2026-09-29 -43.2 → -47.52
    "mute_author": -58.8,
    "report": -234.0,
}

# 포스트 분석 화면의 행동별 막대. 키는 i18n get_action_labels() 와 맞춘다.
BREAKDOWN_ACTIONS: dict[str, tuple[str, float]] = {
    "share_link": ("링크 복사로 공유", WEIGHTS["share_via_copy_link"]),
    "reply": ("답글", WEIGHTS["reply"]),
    "quote": ("인용", WEIGHTS["quote"]),
    "follow": ("작성자 팔로우", WEIGHTS["follow_author"]),
    "share": ("공유", WEIGHTS["share"]),
    "repost": ("리포스트", WEIGHTS["retweet"]),
    "like": ("좋아요", WEIGHTS["favorite"]),
    "click_dwell": ("눌러서 끝까지 읽기", WEIGHTS["click_dwell_time"]),
    "click": ("눌러보기", WEIGHTS["click"]),
    "not_interested": ("관심 없음", WEIGHTS["not_interested"]),
}


def weights_block() -> str:
    """프롬프트에 넣는 가중치 설명."""
    positive = ", ".join(f"{k} {v:g}" for k, v in WEIGHTS.items() if v > 0)
    negative = ", ".join(f"{k} {v:g}" for k, v in WEIGHTS.items() if v < 0)
    return (
        f"공개 소스 기준 실제 가중치({SOURCE}):\n"
        f"- 가점: {positive}\n"
        f"- 감점: {negative}\n"
        "- 해석: 링크 복사 공유(20)가 가장 크고, 답글·인용·DM 공유(5), 팔로우(4)가 뒤를 잇는다. "
        "좋아요(0.5)는 작다. 감점은 가점보다 훨씬 크다. 관심 없음 한 번(-47.52)이 답글 9개 이상을 지운다.\n"
        "- 2026-09-29 변경: 클릭 0.4→0.3, 클릭 후 머문 시간 0→0.4 신설, 관심 없음 -43.2→-47.52. "
        "눌러보고 바로 나가는 글(제목만 자극적인 글)은 손해이고, 눌러서 끝까지 읽게 되는 글이 유리하다. "
        "클릭 후 머문 시간은 10초 같은 기준선이 아니라 길수록 계속 오르는 값이다.\n"
        "- 이 값들은 공개 소스의 실제 값이다. 가중치를 말할 때는 이 값만 쓴다."
    )


def breakdown_schema() -> str:
    """optimizer JSON 예시의 action_breakdown 줄들."""
    lines = []
    for key, (label, weight) in BREAKDOWN_ACTIONS.items():
        lines.append(
            f'    "{key}": {{"probability": 0-100 정수 ({label}), "weight": {weight:g}, '
            '"contribution": probability/100*weight 소수점 2자리}'
        )
    return "{\n" + ",\n".join(lines) + "\n  }"
