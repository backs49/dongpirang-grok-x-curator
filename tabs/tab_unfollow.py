import streamlit as st
from datetime import datetime
from utils import parse_followers_file, compare_followers


def render_unfollow_tab():
    st.subheader("🔄 언팔 추적")
    st.caption("팔로워 리스트를 비교하여 언팔/신규 팔로워를 추적합니다")

    # ─── 안전한 방법 안내 ───
    st.info(
        "**📋 안전한 방법: X 공식 데이터 아카이브**\n\n"
        "1. [X 설정](https://x.com/settings/download_your_data) → '데이터 아카이브 요청'\n"
        "2. 24~48시간 후 다운로드 링크 이메일 수신\n"
        "3. 압축 해제 후 `data/follower.js` 파일을 여기에 업로드\n\n"
        "이 방법은 X 공식 기능이므로 계정 정지 위험이 **전혀 없습니다**."
    )

    with st.expander("⚡ 더 빠르게 하고 싶다면 (주의)"):
        st.warning(
            "⚠️ **Chrome 확장 프로그램 사용 시 주의사항**\n\n"
            "- 비공식 도구는 X 이용약관 위반으로 **계정 정지** 위험이 있습니다.\n"
            "- 단시간 대량 요청 시 일시/영구 정지될 수 있습니다.\n"
            "- 사용 시 CSV로 내보내기 후 여기에 업로드하세요.\n\n"
            "**권장:** X 공식 아카이브를 이용하세요."
        )

    st.divider()

    # ─── 파일 업로드 ───
    st.subheader("📂 팔로워 리스트 업로드")

    col_followers, col_following = st.columns(2)

    with col_followers:
        followers_file = st.file_uploader(
            "팔로워 파일 (필수)",
            type=["js", "csv"],
            help="follower.js 또는 팔로워 CSV 파일",
            key="followers_upload",
        )

    with col_following:
        following_file = st.file_uploader(
            "팔로잉 파일 (선택 — 맞팔 구분용)",
            type=["js", "csv"],
            help="following.js 또는 팔로잉 CSV 파일",
            key="following_upload",
        )

    if not followers_file:
        return

    followers = parse_followers_file(followers_file)
    following = parse_followers_file(following_file) if following_file else set()

    if not followers:
        st.error("파일에서 팔로워를 찾을 수 없습니다. 파일 형식을 확인해주세요.")
        return

    st.success(f"팔로워 **{len(followers)}**명 감지")
    if following:
        mutual = followers & following
        st.success(f"팔로잉 **{len(following)}**명 감지 (맞팔: **{len(mutual)}**명)")

    # ─── 스냅샷 저장 ───
    if "unfollow_snapshots" not in st.session_state:
        st.session_state.unfollow_snapshots = []

    label = st.text_input(
        "스냅샷 라벨",
        value=datetime.now().strftime("%Y-%m-%d %H:%M"),
        key="snapshot_label",
    )

    if st.button("📸 스냅샷 저장", use_container_width=True, type="primary"):
        snapshot = {
            "label": label,
            "date": datetime.now().isoformat(),
            "followers": followers,
            "following": following,
        }
        snapshots = st.session_state.unfollow_snapshots
        snapshots.insert(0, snapshot)
        st.session_state.unfollow_snapshots = snapshots[:10]
        st.success(f"스냅샷 '{label}' 저장 완료 (팔로워 {len(followers)}명)")
        st.rerun()

    # ─── CSV 다운로드 ───
    csv_lines = ["username_or_id"]
    csv_lines.extend(sorted(followers))
    csv_data = "\n".join(csv_lines)
    st.download_button(
        "📥 팔로워 리스트 CSV 다운로드",
        data=csv_data,
        file_name=f"followers_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.divider()

    # ─── 스냅샷 비교 ───
    st.subheader("📊 스냅샷 비교")

    snapshots = st.session_state.get("unfollow_snapshots", [])

    if len(snapshots) < 2:
        st.info(
            f"현재 저장된 스냅샷: **{len(snapshots)}개**\n\n"
            "비교하려면 **최소 2개의 스냅샷**이 필요합니다.\n"
            "서로 다른 시점의 팔로워 파일을 업로드하고 저장하세요."
        )
        return

    snapshot_labels = [
        f"{s['label']} ({len(s['followers'])}명)" for s in snapshots
    ]

    col_old, col_new = st.columns(2)
    with col_old:
        old_idx = st.selectbox(
            "이전 스냅샷",
            range(len(snapshots)),
            format_func=lambda i: snapshot_labels[i],
            index=min(1, len(snapshots) - 1),
        )
    with col_new:
        new_idx = st.selectbox(
            "현재 스냅샷",
            range(len(snapshots)),
            format_func=lambda i: snapshot_labels[i],
            index=0,
        )

    if old_idx == new_idx:
        st.warning("서로 다른 스냅샷을 선택하세요.")
        return

    if st.button("🔍 비교하기", use_container_width=True, type="primary"):
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
        "😢 언팔",
        f"{len(result['unfollowed'])}명",
        delta=f"-{len(result['unfollowed'])}",
        delta_color="inverse",
    )
    col2.metric(
        "🎉 새 팔로워",
        f"{len(result['new_followers'])}명",
        delta=f"+{len(result['new_followers'])}",
    )
    col3.metric("🤝 유지", f"{len(result['unchanged'])}명")

    unfollowed = result["unfollowed"]

    if unfollowed:
        if old_following:
            mutual_unf = [u for u in unfollowed if u in old_following]
            simple_unf = [u for u in unfollowed if u not in old_following]
        else:
            mutual_unf = []
            simple_unf = unfollowed

        if mutual_unf:
            st.subheader(f"💔 맞팔이었다가 언팔한 사람 ({len(mutual_unf)}명)")
            st.caption("내가 팔로우 중인데 상대가 언팔한 사람들")
            _render_user_table(mutual_unf)

        if simple_unf:
            st.subheader(f"👋 단순 언팔한 사람 ({len(simple_unf)}명)")
            _render_user_table(simple_unf)
    else:
        st.success("🎉 언팔한 사람이 없습니다!")

    new_followers = result["new_followers"]
    if new_followers:
        st.subheader(f"🎉 새로 팔로우한 사람 ({len(new_followers)}명)")
        _render_user_table(new_followers)


def _render_user_table(users: list[str]):
    """Render a compact table of users with X profile links."""
    rows = []
    for u in users:
        if u.isdigit():
            link = f"https://x.com/intent/user?user_id={u}"
            rows.append(f"| `{u}` | [X에서 보기]({link}) |")
        else:
            rows.append(f"| [@{u}](https://x.com/{u}) | [X에서 보기](https://x.com/{u}) |")

    visible = rows[:50]
    table = "| 사용자 | 프로필 |\n|---|---|\n" + "\n".join(visible)
    st.markdown(table)

    if len(rows) > 50:
        with st.expander(f"나머지 {len(rows) - 50}명 더 보기"):
            rest = "| 사용자 | 프로필 |\n|---|---|\n" + "\n".join(rows[50:])
            st.markdown(rest)
