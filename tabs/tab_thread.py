import streamlit as st
from utils import parse_thread_text, append_viral_tag, generate_tweet_intent_url
from i18n import t


def render_thread_tab(grok, app_url, viral_tag):
    st.subheader(t("thr_subheader"))
    st.caption(t("thr_caption"))

    thread_input = st.text_area(
        t("thr_input_label"),
        height=250,
        placeholder=t("thr_input_placeholder"),
    )

    if thread_input.strip():
        tweets = parse_thread_text(thread_input)
        st.caption(t("thr_detected", n=len(tweets)))

    if st.button(t("thr_analyze_btn"), use_container_width=True, type="primary"):
        if not thread_input.strip():
            st.warning(t("thr_enter_content"))
        else:
            with st.spinner(t("thr_spinner")):
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
    col1.metric(t("thr_overall_score"), f"{result.get('overall_score', 0)}/100")

    thread_flow = result.get("thread_flow", {})
    col2.metric(t("thr_hook_quality"), thread_flow.get("hook_quality", "N/A"))
    col3.metric(t("thr_optimal_count"), f"{thread_flow.get('optimal_tweet_count', '?')}")

    # ─── 트윗별 분석 ───
    st.subheader(t("thr_per_tweet"))
    for tweet in result.get("tweets", []):
        with st.container(border=True):
            col_pos, col_score, col_decay = st.columns([1, 2, 2])
            with col_pos:
                st.markdown(f"### #{tweet.get('position', '?')}")
            with col_score:
                st.metric(t("thr_score"), f"{tweet.get('score', 0)}")
            with col_decay:
                decay = tweet.get("decay_multiplier", 1.0)
                effective = tweet.get("effective_score", 0)
                st.metric(t("thr_multiplier"), f"×{decay:.2f} → {effective}")

            effective_score = tweet.get("effective_score", 0)
            st.progress(min(effective_score, 100) / 100)

            with st.expander(t("thr_analysis")):
                st.markdown(tweet.get("analysis", ""))

    # ─── 스레드 흐름 분석 ───
    with st.expander(t("thr_flow"), expanded=True):
        st.markdown(f"**{t('thr_narrative')}:** {thread_flow.get('narrative_arc', '')}")
        st.markdown(f"**{t('thr_cta')}:** {thread_flow.get('cta_analysis', '')}")

    # ─── 최적화된 스레드 ───
    st.subheader(t("thr_optimized"))
    optimized_thread = result.get("optimized_thread", [])
    total = len(optimized_thread)
    for i, tweet_text in enumerate(optimized_thread):
        st.code(f"[{i+1}/{total}]\n{tweet_text}", language=None)

    # ─── 전략 노트 ───
    with st.expander(t("thr_strategy_notes")):
        for note in result.get("strategy_notes", []):
            st.markdown(f"- {note}")

    # ─── 게시 ───
    if optimized_thread:
        first_tweet = optimized_thread[0]
        if add_viral:
            first_tweet = append_viral_tag(first_tweet, viral_tag)
        post_url = generate_tweet_intent_url(first_tweet)
        st.link_button(t("thr_post_first"), post_url, use_container_width=True)
