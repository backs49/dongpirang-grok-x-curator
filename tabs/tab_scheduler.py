import streamlit as st


def render_scheduler_tab(grok):
    st.subheader("📅 포스팅 스케줄러")
    st.caption("Author Diversity 감쇠를 최소화하는 최적 포스팅 일정")

    num_posts = st.slider("포스트 수", 1, 5, 3)

    posts_info = []
    for i in range(num_posts):
        with st.container(border=True):
            st.markdown(f"**포스트 #{i+1}**")
            topic = st.text_input(
                f"주제/설명",
                key=f"sched_topic_{i}",
                placeholder="예: AI 트렌드 분석",
            )
            content = st.text_area(
                f"내용 (선택)",
                key=f"sched_content_{i}",
                height=80,
                placeholder="이미 작성한 내용이 있으면 입력...",
            )
            posts_info.append({"topic": topic, "content": content})

    if st.button("📅 최적 스케줄 생성", use_container_width=True, type="primary"):
        filled = [p for p in posts_info if p["topic"].strip()]
        if not filled:
            st.warning("최소 1개 포스트의 주제를 입력해주세요.")
        else:
            with st.spinner("Grok이 최적 스케줄을 설계 중..."):
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
    col1.metric("주제 다양성 점수", f"{result.get('topic_diversity_score', 0)}/100")

    posting_order = result.get("posting_order", [])
    order_str = " → ".join(str(x) for x in posting_order)
    col2.metric("추천 포스팅 순서", order_str)

    # ─── 타임라인 ───
    st.subheader("📋 추천 타임라인")
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
                st.metric("노출 예상", item.get("expected_visibility", ""))
                decay = item.get("decay_from_previous", 1.0)
                st.progress(min(float(decay), 1.0))

    # ─── Author Diversity 감쇠 시각화 ───
    st.subheader("📉 Author Diversity 감쇠")
    for entry in result.get("decay_visualization", []):
        col_label, col_bar = st.columns([1, 5])
        post_num = entry.get("post", "?")
        vis_pct = entry.get("visibility_percent", 100)
        col_label.markdown(f"**포스트 #{post_num}**")
        col_bar.progress(min(vis_pct, 100) / 100)
        col_bar.caption(f"노출 {vis_pct}%")

    # ─── 시간 간격 분석 ───
    with st.expander("⏱️ 시간 간격 분석", expanded=True):
        st.markdown(result.get("time_gap_analysis", ""))

    # ─── 전체 전략 ───
    with st.expander("💡 전체 전략"):
        st.markdown(result.get("overall_strategy", ""))
