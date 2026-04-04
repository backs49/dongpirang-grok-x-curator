import streamlit as st
from utils import generate_tweet_intent_url
from i18n import t

RISK_LEVEL_KEYS = {
    "low": {"label": "risk_low", "emoji": "🟢", "msg": "risk_msg_low"},
    "medium": {"label": "risk_medium", "emoji": "🟡", "msg": "risk_msg_medium"},
    "high": {"label": "risk_high", "emoji": "🔴", "msg": "risk_msg_high"},
    "critical": {"label": "risk_critical", "emoji": "🚨", "msg": "risk_msg_critical"},
}

SEVERITY_EMOJI = {
    "low": "🟢",
    "medium": "🟡",
    "high": "🔴",
    "critical": "🚨",
}

CATEGORY_EMOJI = {
    "monetization": "💰",
    "suspension": "🚫",
    "visibility": "👁️",
    "backlash": "💬",
}


def render_risk_check_tab(grok):
    st.subheader(t("risk_subheader"))
    st.caption(t("risk_caption"))

    st.warning(t("risk_warning"))

    # ─── 입력 ───
    post_text = st.text_area(
        t("post_label"),
        height=150,
        placeholder=t("risk_placeholder"),
        key="risk_post_input",
    )

    image_desc = st.text_input(
        t("image_desc_label"),
        placeholder=t("risk_image_placeholder"),
        key="risk_image_desc",
    )

    if st.button(t("risk_analyze_btn"), use_container_width=True, type="primary"):
        if not post_text.strip():
            st.warning(t("enter_post"))
            return

        with st.spinner(t("risk_spinner")):
            result = grok.check_risk(post_text, image_desc)

        if "error" in result:
            st.error(result["error"])
            return

        st.session_state.risk_result = result

    # ─── 결과 표시 ───
    if "risk_result" not in st.session_state:
        return

    result = st.session_state.risk_result
    risk_level = result.get("risk_level", "low")
    risk_score = result.get("risk_score", 0)
    config = RISK_LEVEL_KEYS.get(risk_level, RISK_LEVEL_KEYS["low"])

    st.divider()

    # ─── 전체 위험도 ───
    col_level, col_score = st.columns(2)
    with col_level:
        st.metric(t("risk_level_label"), f"{config['emoji']} {t(config['label'])}")
    with col_score:
        st.metric(t("risk_score_label"), f"{risk_score}/100")

    # 위험도별 메시지
    if risk_level == "low":
        st.success(t(config["msg"]))
    elif risk_level == "medium":
        st.warning(t(config["msg"]))
    else:
        st.error(t(config["msg"]))

    # 요약
    summary = result.get("summary", "")
    if summary:
        st.info(summary)

    # ─── 안전 체크리스트 ───
    checklist = result.get("checklist", [])
    if checklist:
        with st.expander(t("risk_checklist"), expanded=True):
            for item in checklist:
                passed = item.get("passed", True)
                icon = "✅" if passed else "❌"
                note = item.get("note", "")
                st.markdown(f"{icon} **{item.get('item', '')}** — {note}")

    # ─── 위험 항목 상세 ───
    risk_items = result.get("risk_items", [])
    if risk_items:
        st.subheader(t("risk_items_title", n=len(risk_items)))
        for item in risk_items:
            severity = item.get("severity", "low")
            sev_emoji = SEVERITY_EMOJI.get(severity, "⚪")
            cat_emoji = CATEGORY_EMOJI.get(item.get("category", ""), "⚠️")
            cat_label = item.get("category_label", "")

            with st.container(border=True):
                st.markdown(
                    f"{cat_emoji} **{cat_label}** {sev_emoji} `{severity.upper()}`"
                )
                st.markdown(item.get("description", ""))
                phrase = item.get("affected_phrase")
                if phrase:
                    st.code(phrase, language="")

    # ─── 위험 문구 ───
    risky_phrases = result.get("risky_phrases", [])
    if risky_phrases:
        st.subheader(t("risk_phrases_title", n=len(risky_phrases)))
        for rp in risky_phrases:
            with st.container(border=True):
                col_before, col_after = st.columns(2)
                with col_before:
                    st.markdown(f"**{t('risk_phrase_label')}**")
                    st.code(rp.get("phrase", ""), language="")
                    st.caption(rp.get("reason", ""))
                with col_after:
                    st.markdown(f"**{t('risk_safe_alt')}**")
                    st.code(rp.get("suggestion", ""), language="")

    # ─── 안전한 수정 버전 ───
    safe_version = result.get("safe_version", "")
    if safe_version:
        st.divider()
        st.subheader(t("risk_safe_version"))
        st.code(safe_version, language="", wrap_lines=True)

        intent_url = generate_tweet_intent_url(safe_version)
        st.link_button(
            t("risk_post_safe"),
            intent_url,
            use_container_width=True,
        )
