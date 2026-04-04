import streamlit as st
from i18n import t


def render_scheduler_tab(grok):
    st.subheader(t("sch_subheader"))
    st.caption(t("sch_caption"))

    num_posts = st.slider(t("sch_post_count"), 1, 5, 3)

    posts_info = []
    for i in range(num_posts):
        with st.container(border=True):
            st.markdown(f"**#{i+1}**")
            topic = st.text_input(
                t("sch_topic_label"),
                key=f"sched_topic_{i}",
                placeholder=t("sch_topic_placeholder"),
            )
            content = st.text_area(
                t("sch_content_label"),
                key=f"sched_content_{i}",
                height=80,
                placeholder=t("sch_content_placeholder"),
            )
            posts_info.append({"topic": topic, "content": content})

    if st.button(t("sch_generate_btn"), use_container_width=True, type="primary"):
        filled = [p for p in posts_info if p["topic"].strip()]
        if not filled:
            st.warning(t("sch_enter_topic"))
        else:
            with st.spinner(t("sch_spinner")):
                result = grok.plan_schedule(filled)

            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state.schedule_result = result

    if "schedule_result" not in st.session_state:
        return

    result = st.session_state.schedule_result

    # ─── 상단 메트릭 ───
    col1, col2 = st.columns(2)
    col1.metric(t("sch_diversity_score"), f"{result.get('topic_diversity_score', 0)}/100")

    posting_order = result.get("posting_order", [])
    order_str = " → ".join(str(x) for x in posting_order)
    col2.metric(t("sch_posting_order"), order_str)

    # ─── 타임라인 ───
    st.subheader(t("sch_timeline"))
    for item in result.get("schedule", []):
        with st.container(border=True):
            col_time, col_content, col_vis = st.columns([2, 5, 2])
            with col_time:
                st.markdown(f"### {item.get('recommended_time', '')}")
                st.caption(item.get("recommended_day", ""))
            with col_content:
                st.markdown(f"**{item.get('topic_summary', '')}**")
                st.caption(item.get("reason", ""))
            with col_vis:
                st.metric(t("sch_visibility"), item.get("expected_visibility", ""))
                decay = item.get("decay_from_previous", 1.0)
                st.progress(min(float(decay), 1.0))

    # ─── Author Diversity 감쇠 시각화 ───
    st.subheader(t("sch_decay"))
    for entry in result.get("decay_visualization", []):
        col_label, col_bar = st.columns([1, 5])
        post_num = entry.get("post", "?")
        vis_pct = entry.get("visibility_percent", 100)
        col_label.markdown(f"**#{post_num}**")
        col_bar.progress(min(vis_pct, 100) / 100)
        col_bar.caption(t("sch_visibility_pct", pct=vis_pct))

    # ─── 시간 간격 분석 ───
    with st.expander(t("sch_time_gap"), expanded=True):
        st.markdown(result.get("time_gap_analysis", ""))

    # ─── 전체 전략 ───
    with st.expander(t("sch_overall_strategy")):
        st.markdown(result.get("overall_strategy", ""))
