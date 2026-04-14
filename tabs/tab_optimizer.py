import streamlit as st
from utils import generate_tweet_intent_url, append_viral_tag
from i18n import t, get_action_labels


def render_optimizer_tab(grok, app_url, viral_tag):
    st.subheader(t("opt_subheader"))
    st.caption(t("opt_caption"))

    if grok is None:
        st.info(t("demo_banner"))

    post_text = st.text_area(
        t("post_label"),
        height=240,
        placeholder=t("post_placeholder"),
    )

    col1, col2 = st.columns(2)
    with col1:
        image_desc = st.text_input(t("image_desc_label"), placeholder=t("image_desc_placeholder"))
    with col2:
        hashtags = st.text_input(t("opt_hashtag_label"), placeholder=t("opt_hashtag_placeholder"))

    if st.button(t("opt_analyze_btn"), use_container_width=True, type="primary"):
        if grok is None:
            st.warning(t("demo_key_needed"))
        elif not post_text.strip():
            st.warning(t("enter_post"))
        else:
            with st.spinner(t("opt_spinner")):
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
        st.metric(t("opt_score"), f"{score}/100")
    with col_level:
        level = result.get("engagement_level", "Unknown")
        level_colors = {
            "Very High": "🟢", "High": "🔵", "Medium": "🟡", "Low": "🔴"
        }
        st.metric(t("opt_engagement"), f"{level_colors.get(level, '⚪')} {level}")

    # ─── Multi-Action 점수 대시보드 ───
    if "action_breakdown" in result:
        _render_action_dashboard(result["action_breakdown"])

    with st.expander(t("opt_reasons"), expanded=True):
        for reason in result.get("reasons", []):
            st.markdown(f"- {reason}")

    with st.expander(t("opt_suggestions"), expanded=True):
        for suggestion in result.get("suggestions", []):
            st.markdown(f"- {suggestion}")

    st.subheader(t("opt_optimized"))
    optimized = result.get("optimized_post", "")

    add_viral = st.checkbox(
        f"{t('opt_viral_tag')} '{viral_tag}'",
        value=False,
    )

    if add_viral:
        optimized = append_viral_tag(optimized, viral_tag)

    st.code(optimized, language=None)

    post_url = generate_tweet_intent_url(optimized)
    st.link_button(t("post_to_x"), post_url, use_container_width=True)


def _render_action_dashboard(breakdown):
    action_labels = get_action_labels()

    with st.expander(t("opt_action_analysis"), expanded=True):
        st.caption(t("opt_action_caption"))

        sorted_actions = sorted(
            breakdown.items(),
            key=lambda x: x[1].get("contribution", 0),
            reverse=True,
        )

        for action_name, data in sorted_actions:
            label = action_labels.get(action_name, action_name)
            prob = data.get("probability", 0)
            weight = data.get("weight", 0)
            contrib = data.get("contribution", 0)

            col_label, col_bar, col_numbers = st.columns([2, 5, 3])
            with col_label:
                st.markdown(f"**{label}**")
            with col_bar:
                st.progress(min(prob, 100) / 100)
            with col_numbers:
                st.caption(f"{prob}% × {weight} = **{contrib:.1f}**")

        st.divider()

        total = sum(d.get("contribution", 0) for d in breakdown.values())
        top_action = max(breakdown, key=lambda k: breakdown[k].get("contribution", 0))
        weakest_action = min(breakdown, key=lambda k: breakdown[k].get("contribution", 0))

        cols = st.columns(3)
        cols[0].metric(t("opt_total_score"), f"{total:.1f}")
        cols[1].metric(t("opt_strongest"), action_labels.get(top_action, top_action))
        cols[2].metric(t("opt_weakest"), action_labels.get(weakest_action, weakest_action))
