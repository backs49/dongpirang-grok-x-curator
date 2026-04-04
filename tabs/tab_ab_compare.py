import streamlit as st
from utils import append_viral_tag, generate_tweet_intent_url

ACTION_LABELS_KR = {
    "reply": "💬 답글",
    "repost": "🔄 리포스트",
    "bookmark": "🔖 북마크",
    "dwell_time": "⏱️ 체류시간",
    "oon_discovery": "🌐 OON 발견",
}


def render_ab_compare_tab(grok, app_url, viral_tag):
    st.subheader("⚖️ A/B 비교 분석기")
    st.caption("두 포스트를 나란히 비교하여 승자를 판별합니다")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### 포스트 A")
        post_a = st.text_area(
            "포스트 A",
            height=150,
            key="ab_post_a",
            placeholder="첫 번째 포스트 내용...",
            label_visibility="collapsed",
        )
    with col_b:
        st.markdown("### 포스트 B")
        post_b = st.text_area(
            "포스트 B",
            height=150,
            key="ab_post_b",
            placeholder="두 번째 포스트 내용...",
            label_visibility="collapsed",
        )

    if st.button("⚖️ 비교 분석", use_container_width=True, type="primary"):
        if not post_a.strip() or not post_b.strip():
            st.warning("두 포스트 모두 입력해주세요.")
        else:
            with st.spinner("Grok이 두 포스트를 비교 분석 중..."):
                result = grok.compare_posts(post_a, post_b)

            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state.ab_result = result

    if "ab_result" not in st.session_state:
        return

    result = st.session_state.ab_result
    winner = result.get("winner", "?")
    diff = result.get("score_difference", 0)

    # ─── 승자 발표 ───
    st.success(f"🏆 포스트 {winner} 승리! (+{diff}점)")

    # ─── 좌우 비교 ───
    col_a, col_b = st.columns(2)

    for col, label, key in [(col_a, "A", "post_a"), (col_b, "B", "post_b")]:
        with col:
            data = result.get(key, {})
            is_winner = winner == label
            score = data.get("score", 0)

            delta_val = f"+{diff}" if is_winner else f"-{diff}"
            st.metric(f"포스트 {label} 점수", f"{score}/100", delta=delta_val)
            st.caption(f"등급: {data.get('engagement_level', 'N/A')}")

            with st.expander("💪 강점"):
                for s in data.get("strengths", []):
                    st.markdown(f"- {s}")

            with st.expander("⚠️ 약점"):
                for w in data.get("weaknesses", []):
                    st.markdown(f"- {w}")

    # ─── 행동별 비교 분석 ───
    with st.expander("📊 행동별 비교 분석", expanded=True):
        comparative = result.get("comparative_analysis", {})
        for action, data in comparative.items():
            col_name, col_adv, col_reason = st.columns([2, 1, 5])
            col_name.markdown(f"**{ACTION_LABELS_KR.get(action, action)}**")
            col_adv.markdown(f"**{data.get('advantage', '?')}**")
            col_reason.caption(data.get("reason", ""))

    # ─── 패자 개선 제안 ───
    loser = "A" if winner == "B" else "B"
    with st.expander(f"💡 포스트 {loser} 개선 제안"):
        for suggestion in result.get("improvement_for_loser", []):
            st.markdown(f"- {suggestion}")

    # ─── 최적 합성 포스트 ───
    st.subheader("✨ 최적 합성 포스트")
    best = result.get("best_of_both", "")

    add_viral = st.checkbox(
        f"바이럴 태그 추가",
        value=False,
        key="ab_viral",
    )
    if add_viral:
        best = append_viral_tag(best, viral_tag)

    st.code(best, language=None)

    post_url = generate_tweet_intent_url(best)
    st.link_button("𝕏 에 게시", post_url, use_container_width=True)
