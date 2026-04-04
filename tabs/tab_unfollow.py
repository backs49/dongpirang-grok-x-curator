from __future__ import annotations

import streamlit as st
from datetime import datetime
from utils import parse_followers_file, compare_followers
from i18n import t


def render_unfollow_tab():
    st.subheader(t("unf_subheader"))
    st.caption(t("unf_caption"))

    # ─── 안전한 방법 안내 ───
    st.info(t("unf_safe_info"))

    with st.expander(t("unf_fast_expander")):
        st.warning(t("unf_fast_warning"))

    st.divider()

    # ─── 파일 업로드 ───
    st.subheader(t("unf_upload_title"))

    col_followers, col_following = st.columns(2)

    with col_followers:
        followers_file = st.file_uploader(
            t("unf_followers_file"),
            type=["js", "csv"],
            help=t("unf_followers_help"),
            key="followers_upload",
        )

    with col_following:
        following_file = st.file_uploader(
            t("unf_following_file"),
            type=["js", "csv"],
            help=t("unf_following_help"),
            key="following_upload",
        )

    if not followers_file:
        return

    followers = parse_followers_file(followers_file)
    following = parse_followers_file(following_file) if following_file else set()

    if not followers:
        st.error(t("unf_parse_error"))
        return

    st.success(t("unf_detected", n=len(followers)))
    if following:
        mutual = followers & following
        st.success(t("unf_following_detected", n=len(following), m=len(mutual)))

    # ─── 스냅샷 저장 ───
    if "unfollow_snapshots" not in st.session_state:
        st.session_state.unfollow_snapshots = []

    label = st.text_input(
        t("unf_snapshot_label"),
        value=datetime.now().strftime("%Y-%m-%d %H:%M"),
        key="snapshot_label",
    )

    if st.button(t("unf_save_btn"), use_container_width=True, type="primary"):
        snapshot = {
            "label": label,
            "date": datetime.now().isoformat(),
            "followers": followers,
            "following": following,
        }
        snapshots = st.session_state.unfollow_snapshots
        snapshots.insert(0, snapshot)
        st.session_state.unfollow_snapshots = snapshots[:10]
        st.success(t("unf_saved", label=label, n=len(followers)))
        st.rerun()

    # ─── CSV 다운로드 ───
    csv_lines = ["username_or_id"]
    csv_lines.extend(sorted(followers))
    csv_data = "\n".join(csv_lines)
    st.download_button(
        t("unf_csv_download"),
        data=csv_data,
        file_name=f"followers_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.divider()

    # ─── 스냅샷 비교 ───
    st.subheader(t("unf_compare_title"))

    snapshots = st.session_state.get("unfollow_snapshots", [])

    if len(snapshots) < 2:
        st.info(t("unf_need_snapshots", n=len(snapshots)))
        return

    snapshot_labels = [
        f"{s['label']} ({len(s['followers'])})" for s in snapshots
    ]

    col_old, col_new = st.columns(2)
    with col_old:
        old_idx = st.selectbox(
            t("unf_old_snapshot"),
            range(len(snapshots)),
            format_func=lambda i: snapshot_labels[i],
            index=min(1, len(snapshots) - 1),
        )
    with col_new:
        new_idx = st.selectbox(
            t("unf_new_snapshot"),
            range(len(snapshots)),
            format_func=lambda i: snapshot_labels[i],
            index=0,
        )

    if old_idx == new_idx:
        st.warning(t("unf_diff_warning"))
        return

    if st.button(t("unf_compare_btn"), use_container_width=True, type="primary"):
        old_snap = snapshots[old_idx]
        new_snap = snapshots[new_idx]
        result = compare_followers(old_snap["followers"], new_snap["followers"])
        st.session_state.unfollow_result = {
            "result": result,
            "old_following": old_snap.get("following", set()),
            "old_label": old_snap["label"],
            "new_label": new_snap["label"],
        }

    if "unfollow_result" not in st.session_state:
        return

    data = st.session_state.unfollow_result
    result = data["result"]
    old_following = data["old_following"]

    # ─── 결과 요약 ───
    col1, col2, col3 = st.columns(3)
    col1.metric(
        t("unf_unfollowed"),
        f"{len(result['unfollowed'])}",
        delta=f"-{len(result['unfollowed'])}",
        delta_color="inverse",
    )
    col2.metric(
        t("unf_new_followers"),
        f"{len(result['new_followers'])}",
        delta=f"+{len(result['new_followers'])}",
    )
    col3.metric(t("unf_unchanged"), f"{len(result['unchanged'])}")

    unfollowed = result["unfollowed"]

    if unfollowed:
        if old_following:
            mutual_unf = [u for u in unfollowed if u in old_following]
            simple_unf = [u for u in unfollowed if u not in old_following]
        else:
            mutual_unf = []
            simple_unf = unfollowed

        if mutual_unf:
            st.subheader(t("unf_mutual_unf", n=len(mutual_unf)))
            st.caption(t("unf_mutual_caption"))
            _render_user_table(mutual_unf)

        if simple_unf:
            st.subheader(t("unf_simple_unf", n=len(simple_unf)))
            _render_user_table(simple_unf)
    else:
        st.success(t("unf_no_unfollows"))

    new_followers = result["new_followers"]
    if new_followers:
        st.subheader(t("unf_new_title", n=len(new_followers)))
        _render_user_table(new_followers)


def _render_user_table(users: list[str]):
    """Render a compact table of users with X profile links."""
    rows = []
    for u in users:
        if u.isdigit():
            link = f"https://x.com/intent/user?user_id={u}"
            rows.append(f"| `{u}` | [{t('unf_view_on_x')}]({link}) |")
        else:
            rows.append(f"| [@{u}](https://x.com/{u}) | [{t('unf_view_on_x')}](https://x.com/{u}) |")

    visible = rows[:50]
    table = f"| {t('unf_table_user')} | {t('unf_table_profile')} |\n|---|---|\n" + "\n".join(visible)
    st.markdown(table)

    if len(rows) > 50:
        with st.expander(t("unf_show_more", n=len(rows) - 50)):
            rest = f"| {t('unf_table_user')} | {t('unf_table_profile')} |\n|---|---|\n" + "\n".join(rows[50:])
            st.markdown(rest)
