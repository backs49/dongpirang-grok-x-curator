import streamlit as st


def render_curator_tab(grok):
    st.subheader("Personalized Feed Curator")
    st.caption("Grok의 실시간 검색으로 관심사 기반 추천 포스트를 찾습니다")

    interests = st.text_input(
        "관심사 입력",
        placeholder="예: 머신러닝, 웹개발, 한국 테크 뉴스",
        key="curator_interests",
        on_change=lambda: st.session_state.update(run_curator=True),
    )

    if st.button("🔍 실시간 추천", use_container_width=True, type="primary"):
        if not interests.strip():
            st.warning("관심사를 입력해주세요.")
        else:
            with st.spinner("Grok이 X에서 실시간 검색 중..."):
                result = grok.curate_feed(interests)

            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state.curator_result = result

    if "curator_error" in st.session_state:
        st.error(st.session_state.pop("curator_error"))

    if "curator_result" not in st.session_state:
        return

    recs = st.session_state.curator_result.get("recommendations", [])
    for i, rec in enumerate(recs):
        with st.container(border=True):
            st.markdown(f"**추천 #{i + 1}**")
            st.markdown(rec.get("summary", ""))
            st.caption(f"💡 추천 이유: {rec.get('why_recommended', '')}")
            st.caption(f"🤝 {rec.get('engagement_hint', '')}")
