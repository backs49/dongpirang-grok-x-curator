import json
from collections.abc import MutableMapping
from pathlib import Path

import streamlit as st

import image_modes
import voice_card
import writing_modes
from content_queue import QUEUE_PATH, add_draft, queue_transaction
from idea_job_runner import submit_job
from idea_jobs import get_job
from ideas_history import load_history
from image_client import GENERATED_DIR, MASCOT_PATH
from providers.base import ProviderError
from utils import generate_tweet_intent_url
from xalgo_prompts import PROMPT_VERSION
from i18n import t


def _sync_from_slider():
    st.session_state.post_length = st.session_state.length_slider
    st.session_state.length_input = st.session_state.length_slider


def _sync_from_input():
    st.session_state.post_length = st.session_state.length_input
    st.session_state.length_slider = st.session_state.length_input


def _clear_stale_media_state():
    """이전 아이디어 세트의 생성 이미지/영상·위젯 선택 초기화.

    인덱스 기반 키(f"..._{i}")를 새 아이디어 세트에서도 그대로 재사용하기
    때문에, 초기화하지 않으면 이전 세트에서 고른 이미지 스타일/영상
    길이·해상도가 새 세트의 다른 아이디어에 그대로 새어 들어간다.
    """
    stale_prefixes = (
        "generated_image_",
        "generated_video_",
        "queued_",
        "img_style_",
        "vid_dur_",
        "vid_res_",
    )
    for key in [k for k in st.session_state if str(k).startswith(stale_prefixes)]:
        del st.session_state[key]


def _apply_terminal_job_state(job: dict, state: MutableMapping) -> str | None:
    """완료된 영속 작업을 이번 Streamlit 세션에 한 번만 복원한다."""
    job_id = str(job.get("id") or "")
    if not job_id or state.get("_ideas_terminal_job_id") == job_id:
        return None

    status = job.get("status")
    if status == "completed" and isinstance(job.get("result"), dict):
        state["ideas_result"] = job["result"]
        state["ideas_prompt_version"] = PROMPT_VERSION
        state["_ideas_terminal_job_id"] = job_id
        return "completed"
    if status == "failed":
        state["ideas_error"] = str(job.get("error") or "아이디어 생성에 실패했습니다")
        state["_ideas_terminal_job_id"] = job_id
        return "failed"
    return None


def _active_job_id() -> str:
    value = st.query_params.get("idea_job", "")
    if isinstance(value, list):
        value = value[0] if value else ""
    return str(value or "")


def _restore_active_job() -> tuple[dict | None, str | None]:
    job_id = _active_job_id()
    if not job_id:
        return None, None
    job = get_job(job_id)
    if job is None:
        return None, None
    return job, _apply_terminal_job_state(job, st.session_state)


@st.fragment(run_every=2)
def _watch_active_job(job_id: str):
    """연결된 동안만 짧게 상태를 갱신한다. 생성 자체는 독립 워커가 계속한다."""
    job = get_job(job_id)
    if job is None:
        st.warning(t("ideas_job_missing"))
        return

    status = job.get("status")
    if status in ("queued", "running"):
        st.info(t("ideas_job_running", engine=job.get("engine") or "AI"))
        return

    applied = _apply_terminal_job_state(job, st.session_state)
    if applied == "completed":
        # 프래그먼트 렌더는 기존 위젯 뒤에 올 수 있다. 다음 전체 실행에서
        # 미디어 위젯 상태를 안전하게 초기화한다.
        st.session_state["_ideas_clear_media_after_job"] = job_id
    if applied is not None:
        st.rerun(scope="app")


def _apply_pending_restore():
    """이력에서 요청된 복원을 위젯 인스턴스화 전에 session_state 에 반영한다."""
    restore = st.session_state.pop("_ideas_restore", None)
    if restore is None:
        return
    st.session_state.keywords_input = restore.get("keywords", "")
    st.session_state.ideas_mode = restore.get("mode") or writing_modes.AUTO_MIX
    length = min(max(int(restore.get("length") or 0), 0), 1000)
    st.session_state.post_length = length
    st.session_state.length_slider = length
    st.session_state.length_input = length
    if restore.get("result") is not None:
        st.session_state.ideas_result = restore["result"]
        st.session_state.ideas_prompt_version = restore.get("prompt_version", "")
        _clear_stale_media_state()


def _idea_caption_bits(idea: dict, post_length: int) -> list[str]:
    """카드 캡션 조각: 모드 배지 + 글자 수 + 길이 이탈 경고."""
    bits = []
    mode_lbl = (idea.get("mode") or "").strip()
    if mode_lbl:
        bits.append(f"✍️ {mode_lbl}")
    n = len(idea.get("content", ""))
    bits.append(t("ideas_char_count", n=n))
    if post_length and abs(n - post_length) > post_length * 0.1:
        bits.append(f"⚠️ {t('ideas_len_warn', target=post_length)}")
    return bits


def _resolved_image_style(selected: str | None, idea: dict, idea_index: int) -> str:
    """pills 선택값(None=자동 취급)과 아이디어 제안으로 실제 스타일을 정한다."""
    if selected and selected != image_modes.AUTO:
        return selected
    return image_modes.resolve_auto_style(idea.get("suggested_style"), idea_index)


def _use_v2_image_flow() -> bool:
    """현재 아이디어 세트가 v2(장면 브리프) 스키마인지 — 레거시면 스타일 조립을 우회."""
    return st.session_state.get("ideas_prompt_version") == PROMPT_VERSION


def render_ideas_tab(grok, image_client=None, video_client=None):
    _apply_pending_restore()
    active_job, restored_status = _restore_active_job()
    if restored_status == "completed" or st.session_state.pop(
        "_ideas_clear_media_after_job", None
    ):
        _clear_stale_media_state()
    st.subheader(t("ideas_subheader"))
    st.caption(t("ideas_caption"))

    if grok is None:
        st.info(t("demo_banner"))

    keywords = st.text_input(
        t("ideas_keyword_label"),
        placeholder=t("ideas_keyword_placeholder"),
        key="keywords_input",
    )

    # ─── 포스트 길이 선택 (슬라이더 + 숫자 입력 연동) ───
    if "post_length" not in st.session_state:
        st.session_state.post_length = 0
    if "length_slider" not in st.session_state:
        st.session_state.length_slider = 0
    if "length_input" not in st.session_state:
        st.session_state.length_input = 0

    col_slider, col_input = st.columns([3, 1])
    with col_slider:
        st.slider(
            t("ideas_length_label"),
            min_value=0,
            max_value=1000,
            step=10,
            key="length_slider",
            on_change=_sync_from_slider,
        )
    with col_input:
        st.number_input(
            "자 / chars",
            min_value=0,
            max_value=1000,
            step=10,
            key="length_input",
            on_change=_sync_from_input,
        )
    st.caption(t("ideas_length_help"))

    post_length = st.session_state.post_length

    if "ideas_mode" not in st.session_state:
        st.session_state.ideas_mode = writing_modes.AUTO_MIX
    selected_mode = st.pills(
        t("ideas_mode_label"),
        options=writing_modes.mode_options(),
        format_func=writing_modes.mode_label,
        key="ideas_mode",
    )
    mode = selected_mode or writing_modes.AUTO_MIX

    if st.button(t("ideas_generate_btn"), use_container_width=True, type="primary"):
        if grok is None:
            st.warning(t("demo_key_needed"))
        elif not keywords.strip():
            st.warning(t("ideas_enter_keyword"))
        else:
            engine = getattr(getattr(grok, "provider", None), "name", "")
            active_job = submit_job(keywords, post_length, mode, engine)
            st.query_params["idea_job"] = active_job["id"]
            st.toast(t("ideas_job_submitted"))
            restored_status = _apply_terminal_job_state(active_job, st.session_state)
            if restored_status == "completed":
                _clear_stale_media_state()

    if "ideas_error" in st.session_state:
        st.error(st.session_state.pop("ideas_error"))

    if active_job and active_job.get("status") in ("queued", "running"):
        _watch_active_job(active_job["id"])

    _render_voice_card_section(grok)
    _render_history_section()
    _render_media_history_section()

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

                st.caption(" · ".join(_idea_caption_bits(idea, post_length)))
                lint = idea.get("_lint") or {}
                if lint.get("s1"):
                    st.warning(t("ideas_lint_s1", items=", ".join(lint["s1"])))
                elif lint.get("s2"):
                    st.caption(f"💬 {t('ideas_lint_s2', items=', '.join(lint['s2']))}")

                intent_url = generate_tweet_intent_url(content)
                col_x, col_q = st.columns(2)
                with col_x:
                    st.link_button(t("post_to_x"), intent_url, use_container_width=True)
                with col_q:
                    queued_key = f"queued_{i}"
                    if st.button(
                        t("ideas_to_queue_btn"),
                        key=f"to_queue_{i}",
                        use_container_width=True,
                        disabled=st.session_state.get(queued_key, False) or grok is None,
                    ):
                        try:
                            with queue_transaction(QUEUE_PATH) as data:
                                add_draft(
                                    data,
                                    text=content,
                                    pillar=writing_modes.pillar_for_mode(
                                        writing_modes.label_to_key(idea.get("mode", ""))
                                    ),
                                    image_prompt=idea.get("image_prompt", ""),
                                )
                            st.session_state[queued_key] = True
                            st.toast(t("ideas_queued_toast"))
                            st.rerun()
                        except Exception as exc:
                            st.error(t("ideas_queue_error", err=str(exc)))

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

                # ─── 이미지 장면 브리프 + 생성 ───
                image_prompt = idea.get("image_prompt", "")
                if image_prompt:
                    st.markdown(f"**{t('ideas_image_prompt_title')}**")
                    st.caption(t("ideas_image_prompt_caption"))
                    _render_image_generation(image_client, video_client, idea, i)


def _render_history_section():
    """과거 아이디어 생성 이력 조회 + 재등록/재생성 UI."""
    entries = load_history()
    with st.expander(t("hist_expander")):
        if not entries:
            st.caption(t("hist_empty"))
            return
        st.caption(t("hist_count_caption", n=len(entries)))
        for idx, entry in enumerate(entries):
            n_ideas = len(entry.get("result", {}).get("ideas", []))
            length = entry.get("length") or 0
            col_info, col_load, col_edit = st.columns([6, 2, 3])
            with col_info:
                st.markdown(f"**{entry.get('keywords', '') or '-'}**")
                length_label = f"{length}" if length else "auto"
                st.caption(f"🕐 {entry.get('at', '')} · 💡 {n_ideas} · 📏 {length_label}")
            with col_load:
                if st.button(t("hist_restore_btn"), key=f"hist_load_{idx}"):
                    st.session_state._ideas_restore = entry
                    st.rerun()
            with col_edit:
                if st.button(t("hist_edit_btn"), key=f"hist_edit_{idx}"):
                    st.session_state._ideas_restore = {
                        "keywords": entry.get("keywords", ""),
                        "length": length,
                        "mode": entry.get("mode", ""),
                        "result": None,
                    }
                    st.rerun()


def _media_history_entries():
    """generated_images 폴더의 미디어 파일 목록(최신순)과 gen_log 메타를 돌려준다."""
    if not GENERATED_DIR.is_dir():
        return [], {}
    log = {}
    log_path = GENERATED_DIR / "gen_log.jsonl"
    if log_path.is_file():
        try:
            lines = log_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            lines = []
        for line in lines:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            stem = Path(str(entry.get("file", ""))).stem
            if stem:
                log[stem] = entry
    files = sorted(
        (
            p
            for p in GENERATED_DIR.glob("*")
            if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".mp4")
        ),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return files, log


def _render_media_history_section():
    """과거 생성 이미지·영상 전체 조회 UI (gen_log 메타와 함께)."""
    files, log = _media_history_entries()
    with st.expander(t("media_hist_expander")):
        if not files:
            st.caption(t("media_hist_empty"))
            return
        show_n = st.number_input(
            t("media_hist_count"),
            min_value=1,
            max_value=len(files),
            value=min(6, len(files)),
            step=1,
            key="media_hist_show_n",
        )
        for p in files[: int(show_n)]:
            meta = log.get(p.stem, {})
            is_video = p.suffix.lower() == ".mp4"
            if is_video:
                st.video(str(p))
            else:
                st.image(str(p))
            info_bits = [meta.get("at", ""), meta.get("engine", "")]
            if meta.get("mascot_ref"):
                info_bits.append("🐾")
            st.caption(" · ".join(b for b in info_bits if b) or p.name)
            prompt = (meta.get("prompt") or "").strip()
            if prompt:
                st.caption(prompt[:160] + ("…" if len(prompt) > 160 else ""))
            st.download_button(
                t("vid_download") if is_video else t("img_download"),
                data=p.read_bytes(),
                file_name=p.name,
                mime="video/mp4" if is_video else "image/jpeg",
                key=f"media_hist_dl_{p.name}",
            )


def _render_image_generation(image_client, video_client, idea, idea_index):
    """아이디어 카드 하단의 스타일 모드 선택 + 즉시 이미지 생성 UI."""
    if not _use_v2_image_flow():
        # 레거시(v1) 이력의 image_prompt 는 스타일이 이미 문자열에 박혀 있으므로
        # 스타일 pills·모드 조립·마스코트 참조 없이 원문 그대로 사용한다.
        raw_prompt = idea.get("image_prompt", "")
        st.code(raw_prompt, language="", wrap_lines=True)
        st.caption(t("ideas_legacy_prompt_note"))

        if image_client is None:
            st.caption(t("img_engine_none"))
            return

        st.caption(t("img_engine_note", engine=image_client.name))

        image_key = f"generated_image_{idea_index}"
        if st.button(t("img_generate_btn"), key=f"gen_img_btn_{idea_index}"):
            with st.spinner(t("img_generating", engine=image_client.name)):
                try:
                    st.session_state[image_key] = image_client.generate(raw_prompt)
                except ProviderError as exc:
                    st.error(t("img_error", err=str(exc)))

        image_bytes = st.session_state.get(image_key)
        if image_bytes:
            st.image(image_bytes)
            st.download_button(
                t("img_download"),
                data=image_bytes,
                file_name=f"idea_{idea_index + 1}.jpg",
                mime="image/jpeg",
                key=f"dl_img_{idea_index}",
            )
            _render_video_generation(video_client, raw_prompt, image_bytes, idea_index)
        return

    selected = st.pills(
        t("img_style_label"),
        options=image_modes.style_options(),
        format_func=image_modes.style_label,
        default=image_modes.AUTO,
        key=f"img_style_{idea_index}",
    )
    style = _resolved_image_style(selected, idea, idea_index)
    prompt = image_modes.build_image_prompt(idea.get("image_prompt", ""), style)

    st.caption(f"🎨 {image_modes.style_label(style)}")
    st.code(prompt, language="", wrap_lines=True)

    if image_client is None:
        st.caption(t("img_engine_none"))
        return

    st.caption(t("img_engine_note", engine=image_client.name))

    image_key = f"generated_image_{idea_index}"
    if st.button(t("img_generate_btn"), key=f"gen_img_btn_{idea_index}"):
        reference = MASCOT_PATH if style == "mascot" else None
        with st.spinner(t("img_generating", engine=image_client.name)):
            try:
                st.session_state[image_key] = image_client.generate(
                    prompt, reference=reference, style=style
                )
            except ProviderError as exc:
                st.error(t("img_error", err=str(exc)))

    image_bytes = st.session_state.get(image_key)
    if image_bytes:
        st.image(image_bytes)
        st.download_button(
            t("img_download"),
            data=image_bytes,
            file_name=f"idea_{idea_index + 1}.jpg",
            mime="image/jpeg",
            key=f"dl_img_{idea_index}",
        )
        video_prompt = (idea.get("video_motion") or "").strip() or prompt
        _render_video_generation(video_client, video_prompt, image_bytes, idea_index)


def _render_video_generation(video_client, copy_prompt, image_bytes, idea_index):
    """생성된 이미지를 영상으로 애니메이팅하는 UI (xAI 키 필요)."""
    if video_client is None:
        st.caption(t("vid_need_key"))
        return

    is_grok_cli = video_client.name == "Grok CLI"
    if is_grok_cli:
        # Grok Imagine 은 6초/10초 클립만 지원하고 해상도 제어가 없다.
        duration = st.select_slider(
            t("vid_duration_label"), options=[6, 10], value=6, key=f"vid_dur_{idea_index}"
        )
        resolution = "720p"
        st.caption(t("vid_free_note"))
    else:
        col_dur, col_res = st.columns(2)
        with col_dur:
            duration = st.slider(
                t("vid_duration_label"), 3, 15, 6, key=f"vid_dur_{idea_index}"
            )
        with col_res:
            resolution = st.selectbox(
                t("vid_resolution_label"),
                ["480p", "720p", "1080p"],
                index=1,
                key=f"vid_res_{idea_index}",
            )
        st.caption(t("vid_cost_note"))

    video_key = f"generated_video_{idea_index}"
    if st.button(t("vid_generate_btn"), key=f"gen_vid_btn_{idea_index}"):
        with st.spinner(t("vid_generating")):
            try:
                st.session_state[video_key] = video_client.generate(
                    copy_prompt,
                    image_bytes=image_bytes,
                    duration=duration,
                    resolution=resolution,
                )
            except ProviderError as exc:
                st.error(t("vid_error", err=str(exc)))

    mp4_bytes = st.session_state.get(video_key)
    if mp4_bytes:
        st.video(mp4_bytes)
        st.download_button(
            t("vid_download"),
            data=mp4_bytes,
            file_name=f"idea_{idea_index + 1}.mp4",
            mime="video/mp4",
            key=f"dl_vid_{idea_index}",
        )


def _render_voice_card_section(grok):
    """본인 글 예시 등록 UI — few-shot 보이스 매칭의 시드."""
    with st.expander(t("voice_expander")):
        card = voice_card.load_voice_card()
        if card["examples"]:
            st.caption(t("voice_count", n=len(card["examples"])))
            if card["analysis"]:
                st.caption(card["analysis"])
        raw = st.text_area(
            t("voice_input_label"), key="voice_raw", help=t("voice_help")
        )
        if st.button(t("voice_analyze_btn"), key="voice_save_btn"):
            examples = voice_card.split_examples(raw)
            if not examples:
                st.warning(t("voice_need_input"))
            else:
                analysis = ""
                if grok is not None:
                    res = grok.analyze_voice(examples)
                    if isinstance(res, dict):
                        analysis = str(res.get("analysis", ""))
                voice_card.save_voice_card(examples, analysis)
                st.success(t("voice_saved"))
                st.rerun()
