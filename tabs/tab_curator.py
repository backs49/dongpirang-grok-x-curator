import streamlit as st

from utils import generate_search_url
from i18n import t


def render_curator_tab(grok):
    st.subheader(t("cur_subheader"))
    st.caption(t("cur_caption"))

    interests = st.text_input(
        t("cur_interest_label"),
        placeholder=t("cur_interest_placeholder"),
        key="curator_interests",
    )

    if st.button(t("cur_search_btn"), use_container_width=True, type="primary"):
        if not interests.strip():
            st.warning(t("cur_enter_interest"))
        else:
            with st.spinner(t("cur_spinner")):
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
            st.markdown(f"**#{i + 1}**")
            st.markdown(rec.get("summary", ""))

            with st.expander(t("cur_why")):
                st.write(rec.get("why_recommended", ""))

            search_kw = rec.get("search_keywords", "")
            if search_kw:
                st.link_button(
                    t("cur_search_x"),
                    generate_search_url(search_kw),
                    use_container_width=True,
                )

            suggested = rec.get("suggested_reply", "")
            if suggested:
                st.caption(t("cur_reply_caption"))
                st.code(suggested, language="")

            st.caption(f"💡 {rec.get('engagement_hint', '')}")
