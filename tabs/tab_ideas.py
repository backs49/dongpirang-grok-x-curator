import streamlit as st

from utils import generate_tweet_intent_url
from i18n import t


def render_ideas_tab(grok):
    st.subheader(t("ideas_subheader"))
    st.caption(t("ideas_caption"))

    keywords = st.text_input(
        t("ideas_keyword_label"),
        placeholder=t("ideas_keyword_placeholder"),
        key="keywords_input",
        on_change=lambda: st.session_state.update(run_ideas=True),
    )

    if st.button(t("ideas_generate_btn"), use_container_width=True, type="primary"):
        if not keywords.strip():
            st.warning(t("ideas_enter_keyword"))
        else:
            with st.spinner(t("ideas_spinner")):
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
                content = idea.get("content", "")
                st.code(content, language="", wrap_lines=True)

                intent_url = generate_tweet_intent_url(content)
                st.link_button(t("post_to_x"), intent_url, use_container_width=True)

                detail_col1, detail_col2, detail_col3 = st.columns(3)
                with detail_col1:
                    st.caption(f"📊 {idea.get('engagement_level', '')}")
                with detail_col2:
                    st.caption(f"⏰ {idea.get('best_time', '')}")
                with detail_col3:
                    actions = ", ".join(idea.get("target_actions", []))
                    st.caption(f"🎯 {actions}")

                with st.expander(t("ideas_strategy")):
                    st.markdown(idea.get("strategy", ""))
