import streamlit as st
from utils import append_viral_tag, generate_tweet_intent_url
from i18n import t, get_action_labels


def render_ab_compare_tab(grok, app_url, viral_tag):
    st.subheader(t("ab_subheader"))
    st.caption(t("ab_caption"))

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"### {t('ab_post_a')}")
        post_a = st.text_area(
            t("ab_post_a"),
            height=150,
            key="ab_post_a",
            placeholder=t("ab_placeholder_a"),
            label_visibility="collapsed",
        )
    with col_b:
        st.markdown(f"### {t('ab_post_b')}")
        post_b = st.text_area(
            t("ab_post_b"),
            height=150,
            key="ab_post_b",
            placeholder=t("ab_placeholder_b"),
            label_visibility="collapsed",
        )

    if st.button(t("ab_compare_btn"), use_container_width=True, type="primary"):
        if not post_a.strip() or not post_b.strip():
            st.warning(t("ab_enter_both"))
        else:
            with st.spinner(t("ab_spinner")):
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
    st.success(t("ab_winner", w=winner, d=diff))

    # ─── 좌우 비교 ───
    col_a, col_b = st.columns(2)
    action_labels = get_action_labels()

    for col, label, key in [(col_a, "A", "post_a"), (col_b, "B", "post_b")]:
        with col:
            data = result.get(key, {})
            is_winner = winner == label
            score = data.get("score", 0)

            delta_val = f"+{diff}" if is_winner else f"-{diff}"
            st.metric(t("ab_score_label", l=label), f"{score}/100", delta=delta_val)
            st.caption(f"{t('ab_grade')}: {data.get('engagement_level', 'N/A')}")

            with st.expander(t("ab_strengths")):
                for s in data.get("strengths", []):
                    st.markdown(f"- {s}")

            with st.expander(t("ab_weaknesses")):
                for w in data.get("weaknesses", []):
                    st.markdown(f"- {w}")

    # ─── 행동별 비교 분석 ───
    with st.expander(t("ab_action_compare"), expanded=True):
        comparative = result.get("comparative_analysis", {})
        for action, data in comparative.items():
            col_name, col_adv, col_reason = st.columns([2, 1, 5])
            col_name.markdown(f"**{action_labels.get(action, action)}**")
            col_adv.markdown(f"**{data.get('advantage', '?')}**")
            col_reason.caption(data.get("reason", ""))

    # ─── 패자 개선 제안 ───
    loser = "A" if winner == "B" else "B"
    with st.expander(t("ab_improve", l=loser)):
        for suggestion in result.get("improvement_for_loser", []):
            st.markdown(f"- {suggestion}")

    # ─── 최적 합성 포스트 ───
    st.subheader(t("ab_best_post"))
    best = result.get("best_of_both", "")

    add_viral = st.checkbox(
        t("opt_viral_tag"),
        value=False,
        key="ab_viral",
    )
    if add_viral:
        best = append_viral_tag(best, viral_tag)

    st.code(best, language=None)

    post_url = generate_tweet_intent_url(best)
    st.link_button(t("post_to_x"), post_url, use_container_width=True)
