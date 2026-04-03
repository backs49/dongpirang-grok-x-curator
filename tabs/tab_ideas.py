import streamlit as st


def render_ideas_tab(grok):
    st.subheader("오늘 올릴 포스트 아이디어 5개")
    st.caption("x-algorithm 최적화된 포스트 아이디어를 생성합니다")

    keywords = st.text_input(
        "관심사 / 키워드",
        placeholder="예: AI, 프로그래밍, 스타트업, 한국 여행",
        key="keywords_input",
        on_change=lambda: st.session_state.update(run_ideas=True),
    )

    if st.button("💡 아이디어 생성", use_container_width=True, type="primary"):
        if not keywords.strip():
            st.warning("관심사나 키워드를 입력해주세요.")
        else:
            with st.spinner("Grok이 x-algorithm 최적화 아이디어 생성 중..."):
                result = grok.generate_ideas(keywords)

            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state.ideas_result = result

    if "ideas_error" in st.session_state:
        st.error(st.session_state.pop("ideas_error"))

    if "ideas_result" not in st.session_state:
        return

    ideas = st.session_state.ideas_result.get("ideas", [])
    for i, idea in enumerate(ideas):
        with st.container(border=True):
            col_num, col_content = st.columns([1, 10])
            with col_num:
                st.markdown(f"### #{i + 1}")
            with col_content:
                st.markdown(f"**{idea.get('title', '')}**")
                st.markdown(idea.get("content", ""))

                detail_col1, detail_col2, detail_col3 = st.columns(3)
                with detail_col1:
                    st.caption(f"📊 {idea.get('engagement_level', '')}")
                with detail_col2:
                    st.caption(f"⏰ {idea.get('best_time', '')}")
                with detail_col3:
                    actions = ", ".join(idea.get("target_actions", []))
                    st.caption(f"🎯 {actions}")

                with st.expander("전략 보기"):
                    st.markdown(idea.get("strategy", ""))
