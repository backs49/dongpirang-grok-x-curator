import streamlit as st
from utils import generate_tweet_intent_url

RISK_LEVEL_CONFIG = {
    "low": {"label": "낮음", "color": "green", "emoji": "🟢", "msg": "안전한 포스트입니다!"},
    "medium": {"label": "중간", "color": "orange", "emoji": "🟡", "msg": "일부 주의가 필요합니다."},
    "high": {"label": "높음", "color": "red", "emoji": "🔴", "msg": "수정을 강력히 권장합니다."},
    "critical": {"label": "매우 높음", "color": "red", "emoji": "🚨", "msg": "게시하면 안 됩니다!"},
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
    st.subheader("⚠️ 리스크 체크")
    st.caption("수익 중지 · 계정 정지 · 노출 제한 위험을 사전 분석합니다")

    st.warning(
        "요즘 X가 수익 중지와 계정 정지를 자주 하고 있습니다. "
        "올리기 전에 미리 체크해보세요."
    )

    # ─── 입력 ───
    post_text = st.text_area(
        "포스트 내용",
        height=150,
        placeholder="리스크를 체크할 포스트 내용을 입력하세요...",
        key="risk_post_input",
    )

    image_desc = st.text_input(
        "🖼️ 이미지 설명 (선택)",
        placeholder="예: 정치인 합성 사진, 폭력적 장면 등",
        key="risk_image_desc",
    )

    if st.button("⚠️ 리스크 분석하기", use_container_width=True, type="primary"):
        if not post_text.strip():
            st.warning("포스트 내용을 입력해주세요.")
            return

        with st.spinner("Grok이 리스크를 분석하고 있습니다..."):
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
    config = RISK_LEVEL_CONFIG.get(risk_level, RISK_LEVEL_CONFIG["low"])

    st.divider()

    # ─── 전체 위험도 ───
    col_level, col_score = st.columns(2)
    with col_level:
        st.metric("전체 위험도", f"{config['emoji']} {config['label']}")
    with col_score:
        st.metric("위험 점수", f"{risk_score}/100")

    # 위험도별 메시지
    if risk_level == "low":
        st.success(config["msg"])
    elif risk_level == "medium":
        st.warning(config["msg"])
    else:
        st.error(config["msg"])

    # 요약
    summary = result.get("summary", "")
    if summary:
        st.info(summary)

    # ─── 안전 체크리스트 ───
    checklist = result.get("checklist", [])
    if checklist:
        with st.expander("📋 안전 체크리스트", expanded=True):
            for item in checklist:
                passed = item.get("passed", True)
                icon = "✅" if passed else "❌"
                note = item.get("note", "")
                st.markdown(f"{icon} **{item.get('item', '')}** — {note}")

    # ─── 위험 항목 상세 ───
    risk_items = result.get("risk_items", [])
    if risk_items:
        st.subheader(f"🔍 위험 항목 ({len(risk_items)}건)")
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
        st.subheader(f"📍 위험 문구 ({len(risky_phrases)}건)")
        for rp in risky_phrases:
            with st.container(border=True):
                col_before, col_after = st.columns(2)
                with col_before:
                    st.markdown("**위험 문구:**")
                    st.code(rp.get("phrase", ""), language="")
                    st.caption(rp.get("reason", ""))
                with col_after:
                    st.markdown("**안전한 대체:**")
                    st.code(rp.get("suggestion", ""), language="")

    # ─── 안전한 수정 버전 ───
    safe_version = result.get("safe_version", "")
    if safe_version:
        st.divider()
        st.subheader("✅ 안전하게 수정된 포스트")
        st.code(safe_version, language="", wrap_lines=True)

        intent_url = generate_tweet_intent_url(safe_version)
        st.link_button(
            "𝕏 에 안전한 버전으로 게시",
            intent_url,
            use_container_width=True,
        )
