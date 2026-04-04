import streamlit as st
from utils import generate_tweet_intent_url, append_viral_tag

ACTION_LABELS_KR = {
    "reply": "💬 답글",
    "repost": "🔄 리포스트",
    "like": "❤️ 좋아요",
    "quote": "💭 인용",
    "bookmark": "🔖 북마크",
    "follow": "👤 팔로우",
    "dwell_time": "⏱️ 체류시간",
    "share": "📤 공유",
    "photo_expansion": "🖼️ 이미지 확대",
}


def render_optimizer_tab(grok, app_url, viral_tag):
    st.subheader("포스트 Optimizer & Engagement Predictor")
    st.caption("x-algorithm의 Multi-Action Prediction 원리로 포스트를 분석합니다")

    post_text = st.text_area(
        "포스트 내용",
        height=120,
        placeholder="분석하고 싶은 포스트 내용을 입력하세요...",
    )

    col1, col2 = st.columns(2)
    with col1:
        image_desc = st.text_input("🖼️ 이미지 설명 (선택)", placeholder="예: 일몰 사진, 코드 스크린샷")
    with col2:
        hashtags = st.text_input("#️⃣ 해시태그 (선택)", placeholder="예: #AI #개발 #Python")

    if st.button("🔍 x-algorithm 분석", use_container_width=True, type="primary"):
        if not post_text.strip():
            st.warning("포스트 내용을 입력해주세요.")
        else:
            with st.spinner("Grok이 x-algorithm 분석 중..."):
                result = grok.optimize_post(post_text, image_desc, hashtags)

            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state.optimize_result = result

    if "optimize_result" not in st.session_state:
        return

    result = st.session_state.optimize_result

    col_score, col_level = st.columns([1, 2])
    with col_score:
        score = result.get("score", 0)
        st.metric("x-algorithm 점수", f"{score}/100")
    with col_level:
        level = result.get("engagement_level", "Unknown")
        level_colors = {
            "Very High": "🟢", "High": "🔵", "Medium": "🟡", "Low": "🔴"
        }
        st.metric("참여 예측 등급", f"{level_colors.get(level, '⚪')} {level}")

    # ─── Multi-Action 점수 대시보드 ───
    if "action_breakdown" in result:
        _render_action_dashboard(result["action_breakdown"])

    with st.expander("📊 분석 이유", expanded=True):
        for reason in result.get("reasons", []):
            st.markdown(f"- {reason}")

    with st.expander("💡 개선 제안", expanded=True):
        for suggestion in result.get("suggestions", []):
            st.markdown(f"- {suggestion}")

    st.subheader("✨ 최적화된 포스트")
    optimized = result.get("optimized_post", "")

    add_viral = st.checkbox(
        f"최적화된 포스트에 '{viral_tag}' 자동 추가",
        value=False,
    )

    if add_viral:
        optimized = append_viral_tag(optimized, viral_tag)

    st.code(optimized, language=None)

    post_url = generate_tweet_intent_url(optimized)
    st.link_button("𝕏 에 게시", post_url, use_container_width=True)


def _render_action_dashboard(breakdown):
    with st.expander("📊 Multi-Action 점수 분석", expanded=True):
        st.caption("각 행동 유형별 예측 확률과 가중 기여도")

        sorted_actions = sorted(
            breakdown.items(),
            key=lambda x: x[1].get("contribution", 0),
            reverse=True,
        )

        for action_name, data in sorted_actions:
            label = ACTION_LABELS_KR.get(action_name, action_name)
            prob = data.get("probability", 0)
            weight = data.get("weight", 0)
            contrib = data.get("contribution", 0)

            col_label, col_bar, col_numbers = st.columns([2, 5, 3])
            with col_label:
                st.markdown(f"**{label}**")
            with col_bar:
                st.progress(min(prob, 100) / 100)
            with col_numbers:
                st.caption(f"확률 {prob}% × {weight} = **{contrib:.1f}**")

        st.divider()

        total = sum(d.get("contribution", 0) for d in breakdown.values())
        top_action = max(breakdown, key=lambda k: breakdown[k].get("contribution", 0))
        weakest_action = min(breakdown, key=lambda k: breakdown[k].get("contribution", 0))

        cols = st.columns(3)
        cols[0].metric("총 가중 점수", f"{total:.1f}")
        cols[1].metric("최강 행동", ACTION_LABELS_KR.get(top_action, top_action))
        cols[2].metric("최약 행동", ACTION_LABELS_KR.get(weakest_action, weakest_action))
