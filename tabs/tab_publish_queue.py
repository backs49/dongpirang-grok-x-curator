import streamlit as st

from content_queue import (
    QUEUE_PATH,
    add_draft,
    add_material,
    approve_draft,
    load_queue,
    queue_transaction,
    reject_draft,
    remove_draft,
    remove_material,
    unused_materials,
    update_draft_text,
)
from i18n import t
from utils import generate_tweet_intent_url

_PILLAR_LABEL_KEYS = {
    "build_in_public": "pq_pillar_bip",
    "retrospective": "pq_pillar_retro",
    "tip": "pq_pillar_tip",
    "curation": "pq_pillar_curation",
}

_STATUS_BADGE = {
    "draft": "📝",
    "approved": "✅",
    "published": "📤",
    "rejected": "🚫",
    "publishing": "🔄",
    "error": "⚠️",
}

# 큐 탭에 노출할 상태 — "publishing"/"error" 도 반드시 포함한다. 감춰버리면
# 크래시 잔재(stale_publishing_needs_review)나 발행 실패가 사람 눈에
# 닿지 못하고 조용히 묻힌다 (9e663b8 리마인더 작업과 같은 실패 패턴).
_VISIBLE_STATUSES = ("draft", "approved", "publishing", "error")


def _visible_drafts(data: dict) -> list[dict]:
    return [d for d in data["drafts"] if d["status"] in _VISIBLE_STATUSES]


def _can_approve(status: str) -> bool:
    """error 초안은 승인 버튼으로 재시도할 수 있게 한다(수동 재발행 경로)."""
    return status in ("draft", "error")


def _is_claim_locked(status: str) -> bool:
    """publish_worker 가 트랜잭션1~2 사이에 클레임 중인 초안 — 읽기전용으로
    보여준다(수정/반려/삭제가 워커의 트랜잭션2 기록과 경합하지 않도록)."""
    return status == "publishing"


# 주의: 이 탭에서는 st.rerun() 을 절대 쓰지 않는다. 명시적 rerun 은
# st.tabs 의 활성 탭 상태를 초기화해 첫 탭으로 튕기는 회귀를 일으킨다
# (0a2f500 스피너 회귀와 같은 계열). 대신 모든 상태 변경은 버튼
# on_click 콜백으로 처리한다 — 콜백은 렌더링 전에 실행되므로 같은
# (자연스러운) rerun 안에서 최신 상태가 그려지고 탭 선택이 유지된다.


def _cb_add_material():
    with queue_transaction(QUEUE_PATH) as data:
        added = add_material(data, st.session_state.get("pq_material_input", ""))
    if added:
        st.session_state.pq_material_input = ""


def _cb_remove_material(material_id: str):
    with queue_transaction(QUEUE_PATH) as data:
        remove_material(data, material_id)


def _cb_request_draft(material_id: str):
    # LLM 호출은 오래 걸려 콜백에서 직접 하지 않는다. 의도만 기록하고
    # 렌더 단계 초입에서 스피너와 함께 처리한다.
    st.session_state.pq_pending_draft = material_id


def _cb_approve(draft_id: str):
    with queue_transaction(QUEUE_PATH) as data:
        approve_draft(data, draft_id)


def _cb_reject(draft_id: str):
    with queue_transaction(QUEUE_PATH) as data:
        reject_draft(data, draft_id)


def _cb_remove_draft(draft_id: str):
    with queue_transaction(QUEUE_PATH) as data:
        remove_draft(data, draft_id)


def _process_pending_draft(grok):
    """초안 만들기 요청을 렌더링 전에 처리한다 (스피너 표시 가능)."""
    material_id = st.session_state.pop("pq_pending_draft", None)
    if not material_id:
        return
    if grok is None:
        st.warning(t("demo_key_needed"))
        return

    data = load_queue(QUEUE_PATH)
    material = next(
        (m for m in unused_materials(data) if m["id"] == material_id), None
    )
    if material is None:
        return

    with st.spinner(t("pq_draft_spinner")):
        result = grok.draft_from_material(material["text"])

    if "error" in result:
        st.error(result["error"])
        return

    with queue_transaction(QUEUE_PATH) as tx_data:
        add_draft(
            tx_data,
            text=result.get("post", ""),
            pillar=result.get("pillar", "build_in_public"),
            image_prompt=result.get("image_prompt", ""),
            material_id=material["id"],
        )


def render_publish_queue_tab(grok):
    st.subheader(t("pq_subheader"))
    st.caption(t("pq_caption"))

    if grok is None:
        st.info(t("demo_banner"))

    _process_pending_draft(grok)
    data = load_queue(QUEUE_PATH)

    # ─── 1. 소재 인박스 ───
    st.markdown(f"### {t('pq_inbox_title')}")
    st.caption(t("pq_inbox_caption"))

    col_input, col_btn = st.columns([5, 1])
    with col_input:
        st.text_input(
            t("pq_inbox_placeholder"),
            key="pq_material_input",
            label_visibility="collapsed",
            placeholder=t("pq_inbox_placeholder"),
        )
    with col_btn:
        st.button(
            t("pq_inbox_add"), use_container_width=True, on_click=_cb_add_material
        )

    materials = unused_materials(data)
    for m in materials:
        col_text, col_gen, col_del = st.columns([6, 2, 1])
        col_text.markdown(f"💡 {m['text']}")
        col_gen.button(
            t("pq_draft_btn"),
            key=f"pq_gen_{m['id']}",
            on_click=_cb_request_draft,
            args=(m["id"],),
        )
        col_del.button(
            "🗑️",
            key=f"pq_delm_{m['id']}",
            on_click=_cb_remove_material,
            args=(m["id"],),
        )

    if not materials:
        st.caption(t("pq_inbox_empty"))

    st.divider()

    # ─── 2. 초안 큐 ───
    st.markdown(f"### {t('pq_queue_title')}")

    active = _visible_drafts(data)
    if not active:
        st.caption(t("pq_queue_empty"))

    for d in active:
        badge = _STATUS_BADGE.get(d["status"], "")
        pillar = t(_PILLAR_LABEL_KEYS.get(d["pillar"], "pq_pillar_bip"))
        locked = _is_claim_locked(d["status"])
        with st.container(border=True):
            head = f"{badge} **{pillar}**"
            if d["status"] == "approved" and d.get("slot"):
                slot_txt = d["slot"].replace("T", " ")[:16]
                head += f" · 🕐 {t('pq_slot_label')}: {slot_txt}"
            st.markdown(head)

            if d["status"] == "error":
                st.caption(t("pq_error_note"))
            elif locked:
                st.caption(t("pq_publishing_note"))

            if locked:
                # 워커가 클레임한 상태 — 읽기전용으로만 보여주고 아래
                # 수정/승인/반려/삭제 컨트롤은 렌더링하지 않는다.
                st.text_area(
                    t("pq_draft_text_label"),
                    value=d["text"],
                    key=f"pq_text_{d['id']}",
                    height=140,
                    label_visibility="collapsed",
                    disabled=True,
                )
                continue

            edited = st.text_area(
                t("pq_draft_text_label"),
                value=d["text"],
                key=f"pq_text_{d['id']}",
                height=140,
                label_visibility="collapsed",
            )
            if edited != d["text"]:
                with queue_transaction(QUEUE_PATH) as tx_data:
                    update_draft_text(tx_data, d["id"], edited)

            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                if _can_approve(d["status"]):
                    st.button(
                        t("pq_approve"),
                        key=f"pq_ok_{d['id']}",
                        use_container_width=True,
                        type="primary",
                        on_click=_cb_approve,
                        args=(d["id"],),
                    )
            col_b.button(
                t("pq_reject"),
                key=f"pq_no_{d['id']}",
                use_container_width=True,
                on_click=_cb_reject,
                args=(d["id"],),
            )
            col_c.button(
                "🗑️",
                key=f"pq_deld_{d['id']}",
                use_container_width=True,
                on_click=_cb_remove_draft,
                args=(d["id"],),
            )
            with col_d:
                st.link_button(
                    t("pq_post_now"),
                    generate_tweet_intent_url(d["text"]),
                    use_container_width=True,
                )

    # ─── 3. 안내 ───
    approved_count = sum(1 for d in data["drafts"] if d["status"] == "approved")
    if approved_count:
        st.info(t("pq_worker_note", n=approved_count))
