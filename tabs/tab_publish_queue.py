import streamlit as st

from content_queue import (
    QUEUE_PATH,
    add_draft,
    add_material,
    approve_draft,
    load_queue,
    reject_draft,
    remove_draft,
    remove_material,
    save_queue,
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
}


def render_publish_queue_tab(grok):
    st.subheader(t("pq_subheader"))
    st.caption(t("pq_caption"))

    if grok is None:
        st.info(t("demo_banner"))

    data = load_queue(QUEUE_PATH)

    # ─── 1. 소재 인박스 ───
    st.markdown(f"### {t('pq_inbox_title')}")
    st.caption(t("pq_inbox_caption"))

    col_input, col_btn = st.columns([5, 1])
    with col_input:
        material_text = st.text_input(
            t("pq_inbox_placeholder"),
            key="pq_material_input",
            label_visibility="collapsed",
            placeholder=t("pq_inbox_placeholder"),
        )
    with col_btn:
        if st.button(t("pq_inbox_add"), use_container_width=True):
            if add_material(data, material_text):
                save_queue(QUEUE_PATH, data)
                st.rerun()

    materials = unused_materials(data)
    for m in materials:
        col_text, col_gen, col_del = st.columns([6, 2, 1])
        col_text.markdown(f"💡 {m['text']}")
        with col_gen:
            if st.button(t("pq_draft_btn"), key=f"pq_gen_{m['id']}"):
                if grok is None:
                    st.warning(t("demo_key_needed"))
                else:
                    with st.spinner(t("pq_draft_spinner")):
                        result = grok.draft_from_material(m["text"])
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        add_draft(
                            data,
                            text=result.get("post", ""),
                            pillar=result.get("pillar", "build_in_public"),
                            image_prompt=result.get("image_prompt", ""),
                            material_id=m["id"],
                        )
                        save_queue(QUEUE_PATH, data)
                        st.rerun()
        with col_del:
            if st.button("🗑️", key=f"pq_delm_{m['id']}"):
                remove_material(data, m["id"])
                save_queue(QUEUE_PATH, data)
                st.rerun()

    if not materials:
        st.caption(t("pq_inbox_empty"))

    st.divider()

    # ─── 2. 초안 큐 ───
    st.markdown(f"### {t('pq_queue_title')}")

    active = [d for d in data["drafts"] if d["status"] in ("draft", "approved")]
    if not active:
        st.caption(t("pq_queue_empty"))

    for d in active:
        badge = _STATUS_BADGE.get(d["status"], "")
        pillar = t(_PILLAR_LABEL_KEYS.get(d["pillar"], "pq_pillar_bip"))
        with st.container(border=True):
            head = f"{badge} **{pillar}**"
            if d["status"] == "approved" and d.get("slot"):
                slot_txt = d["slot"].replace("T", " ")[:16]
                head += f" · 🕐 {t('pq_slot_label')}: {slot_txt}"
            st.markdown(head)

            edited = st.text_area(
                t("pq_draft_text_label"),
                value=d["text"],
                key=f"pq_text_{d['id']}",
                height=140,
                label_visibility="collapsed",
            )
            if edited != d["text"]:
                update_draft_text(data, d["id"], edited)
                save_queue(QUEUE_PATH, data)

            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                if d["status"] == "draft":
                    if st.button(t("pq_approve"), key=f"pq_ok_{d['id']}",
                                 use_container_width=True, type="primary"):
                        approve_draft(data, d["id"])
                        save_queue(QUEUE_PATH, data)
                        st.rerun()
            with col_b:
                if st.button(t("pq_reject"), key=f"pq_no_{d['id']}",
                             use_container_width=True):
                    reject_draft(data, d["id"])
                    save_queue(QUEUE_PATH, data)
                    st.rerun()
            with col_c:
                if st.button("🗑️", key=f"pq_deld_{d['id']}", use_container_width=True):
                    remove_draft(data, d["id"])
                    save_queue(QUEUE_PATH, data)
                    st.rerun()
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
