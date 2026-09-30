import streamlit as st

from demo_data import SAMPLE_ANALYTICS_CSV
from i18n import t
from utils import (
    MONETIZATION_IMPRESSIONS_TARGET,
    parse_analytics_csv,
    summarize_performance,
)


def render_performance_tab(grok):
    st.subheader(t("perf_subheader"))
    st.caption(t("perf_caption"))

    with st.expander(t("perf_howto_title")):
        st.markdown(t("perf_howto_body"))
        st.download_button(
            t("perf_sample_download"),
            data=SAMPLE_ANALYTICS_CSV,
            file_name="sample_analytics.csv",
            mime="text/csv",
        )

    uploaded = st.file_uploader(t("perf_upload_label"), type=["csv"], key="perf_csv")
    if uploaded is None:
        st.info(t("perf_upload_hint"))
        return

    posts = parse_analytics_csv(uploaded.getvalue().decode("utf-8-sig"))
    if not posts:
        st.error(t("perf_parse_error"))
        return

    summary = summarize_performance(posts)

    # ─── 핵심 지표 ───
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t("perf_total_posts"), f"{summary['total_posts']:,}")
    col2.metric(t("perf_total_impressions"), f"{summary['total_impressions']:,}")
    col3.metric(t("perf_recent_impressions"), f"{summary['recent_impressions']:,}")
    col4.metric(t("perf_engagement_rate"), f"{summary['avg_engagement_pct']:.2f}%")

    if summary.get("has_detail"):
        st.metric(t("perf_detail_rate"), f"{summary['avg_detail_pct']:.2f}%", help=t("perf_detail_help"))

    if not summary["has_dates"]:
        st.warning(t("perf_no_dates"))

    # ─── 수익화 진행률 ───
    st.subheader(t("perf_monetization_title"))
    pct = summary["monetization_pct"]
    st.progress(min(pct, 100.0) / 100)
    st.markdown(
        t(
            "perf_monetization_progress",
            current=f"{summary['recent_impressions']:,}",
            target=f"{MONETIZATION_IMPRESSIONS_TARGET:,}",
            pct=f"{pct:.2f}",
        )
    )

    est_days = summary["est_days_to_target"]
    if pct >= 100:
        st.success(t("perf_target_reached"))
    elif est_days is not None:
        st.caption(
            t(
                "perf_estimate",
                daily=f"{summary['daily_avg_impressions']:,.0f}",
                days=f"{est_days:,}",
            )
        )

    # 나머지 수익화 요건 체크리스트 (사용자 입력)
    with st.container(border=True):
        st.markdown(f"**{t('perf_checklist_title')}**")
        followers = st.number_input(
            t("perf_followers_input"), min_value=0, step=10, key="perf_followers"
        )
        premium = st.checkbox(t("perf_premium_check"), key="perf_premium")

        rows = [
            (pct >= 100, t("perf_check_impressions")),
            (followers >= 500, t("perf_check_followers")),
            (premium, t("perf_check_premium")),
        ]
        for passed, label in rows:
            st.markdown(f"{'✅' if passed else '⬜'} {label}")

    # ─── 상위 / 하위 포스트 ───
    col_top, col_bottom = st.columns(2)
    for col, key, posts_key in (
        (col_top, "perf_top_posts", "top_posts"),
        (col_bottom, "perf_bottom_posts", "bottom_posts"),
    ):
        with col:
            st.markdown(f"**{t(key)}**")
            for p in summary[posts_key]:
                with st.container(border=True):
                    text = (p["text"] or "—")[:80]
                    st.markdown(text)
                    detail = f" · 🔎 {p['detail_pct']:.2f}%" if "detail_pct" in p else ""
                    st.caption(
                        f"👁 {p['impressions']:,} · 💬 {p['engagement_pct']:.2f}%{detail}"
                    )

    # ─── AI 인사이트 ───
    st.subheader(t("perf_insight_title"))
    if st.button(t("perf_insight_btn"), use_container_width=True, type="primary"):
        if grok is None:
            st.warning(t("demo_key_needed"))
        else:
            with st.spinner(t("perf_insight_spinner")):
                result = grok.analyze_performance(summary)
            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state.perf_insight = result

    insight = st.session_state.get("perf_insight")
    if not insight:
        return

    if insight.get("summary"):
        st.info(insight["summary"])

    for wp in insight.get("working_patterns", []):
        with st.container(border=True):
            st.markdown(f"**🎯 {wp.get('pattern', '')}**")
            st.caption(wp.get("evidence", ""))
            st.markdown(wp.get("how_to_repeat", ""))

    weak_points = insight.get("weak_points", [])
    if weak_points:
        with st.expander(t("perf_weak_points"), expanded=True):
            for w in weak_points:
                st.markdown(f"- {w}")

    action_plan = insight.get("action_plan", [])
    if action_plan:
        st.markdown(f"**{t('perf_action_plan')}**")
        for i, action in enumerate(action_plan, start=1):
            st.markdown(f"{i}. {action}")

    if insight.get("monetization_advice"):
        st.success(insight["monetization_advice"])
