import streamlit as st
from utils import parse_thread_text, append_viral_tag, generate_tweet_intent_url


def render_thread_tab(grok, app_url, viral_tag):
    st.subheader("🧵 스레드 최적화기")
    st.caption("Author Diversity 감쇠를 고려한 스레드 구조 분석")

    thread_input = st.text_area(
        "스레드 내용",
        height=250,
        placeholder="각 트윗을 --- 또는 빈 줄로 구분하세요...\n\n첫 번째 트윗 내용\n---\n두 번째 트윗 내용\n---\n세 번째 트윗 내용",
    )

    if thread_input.strip():
        tweets = parse_thread_text(thread_input)
        st.caption(f"감지된 트윗 수: {len(tweets)}개")

    if st.button("🧵 스레드 분석", use_container_width=True, type="primary"):
        if not thread_input.strip():
            st.warning("스레드 내용을 입력해주세요.")
        else:
            with st.spinner("Grok이 스레드를 분석 중..."):
                result = grok.optimize_thread(thread_input)

            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state.thread_result = result

    if "thread_result" not in st.session_state:
        return

    result = st.session_state.thread_result

    # ─── 상단 요약 메트릭 ───
    col1, col2, col3 = st.columns(3)
    col1.metric("전체 스레드 점수", f"{result.get('overall_score', 0)}/100")

    thread_flow = result.get("thread_flow", {})
    col2.metric("Hook 품질", thread_flow.get("hook_quality", "N/A"))
    col3.metric("최적 트윗 수", f"{thread_flow.get('optimal_tweet_count', '?')}개")

    # ─── 트윗별 분석 ───
    st.subheader("📊 트윗별 분석")
    for tweet in result.get("tweets", []):
        with st.container(border=True):
            col_pos, col_score, col_decay = st.columns([1, 2, 2])
            with col_pos:
                st.markdown(f"### #{tweet.get('position', '?')}")
            with col_score:
                st.metric("점수", f"{tweet.get('score', 0)}")
            with col_decay:
                decay = tweet.get("decay_multiplier", 1.0)
                effective = tweet.get("effective_score", 0)
                st.metric("노출 배율", f"×{decay:.2f} → {effective}")

            effective_score = tweet.get("effective_score", 0)
            st.progress(min(effective_score, 100) / 100)

            with st.expander("분석 보기"):
                st.markdown(tweet.get("analysis", ""))

    # ─── 스레드 흐름 분석 ───
    with st.expander("📊 스레드 흐름 분석", expanded=True):
        st.markdown(f"**내러티브 아크:** {thread_flow.get('narrative_arc', '')}")
        st.markdown(f"**CTA 분석:** {thread_flow.get('cta_analysis', '')}")

    # ─── 최적화된 스레드 ───
    st.subheader("✨ 최적화된 스레드")
    optimized_thread = result.get("optimized_thread", [])
    total = len(optimized_thread)
    for i, tweet_text in enumerate(optimized_thread):
        st.code(f"[{i+1}/{total}]\n{tweet_text}", language=None)

    # ─── 전략 노트 ───
    with st.expander("💡 전략 노트"):
        for note in result.get("strategy_notes", []):
            st.markdown(f"- {note}")

    # ─── 공유 ───
    overall = result.get("overall_score", 0)
    share_text = f"이 스레드를 동피랑 Grok X 추천기로 분석했더니 점수 {overall}/100! 🧵🔥\n\n{app_url}\n\n@mangodaon"
    share_url = generate_tweet_intent_url(share_text)
    st.link_button("🐦 X에 공유하기", share_url, use_container_width=True)
