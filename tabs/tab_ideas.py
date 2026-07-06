import streamlit as st

from image_client import build_copy_prompt
from providers.base import ProviderError
from utils import generate_tweet_intent_url
from i18n import t


def _sync_from_slider():
    st.session_state.post_length = st.session_state.length_slider
    st.session_state.length_input = st.session_state.length_slider


def _sync_from_input():
    st.session_state.post_length = st.session_state.length_input
    st.session_state.length_slider = st.session_state.length_input


def render_ideas_tab(grok, image_client=None):
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

    if st.button(t("ideas_generate_btn"), use_container_width=True, type="primary"):
        if grok is None:
            st.warning(t("demo_key_needed"))
        elif not keywords.strip():
            st.warning(t("ideas_enter_keyword"))
        else:
            with st.spinner(t("ideas_spinner")):
                result = grok.generate_ideas(keywords, length=post_length)

            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state.ideas_result = result
                # 이전 아이디어 세트에서 생성한 이미지가 새 아이디어에
                # 잘못 매칭되지 않도록 정리한다.
                for key in [k for k in st.session_state if str(k).startswith("generated_image_")]:
                    del st.session_state[key]

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

                # ─── 이미지 프롬프트 ───
                image_prompt = idea.get("image_prompt", "")
                if image_prompt:
                    st.markdown(f"**{t('ideas_image_prompt_title')}**")
                    st.caption(t("ideas_image_prompt_caption"))
                    st.code(image_prompt, language="", wrap_lines=True)

                    copy_prompt = build_copy_prompt(content, image_prompt)
                    st.markdown(f"**{t('ideas_copy_image_prompt_title')}**")
                    st.caption(t("ideas_copy_image_prompt_caption"))
                    st.code(copy_prompt, language="", wrap_lines=True)

                    _render_image_generation(image_client, copy_prompt, i)


def _render_image_generation(image_client, copy_prompt, idea_index):
    """아이디어 카드 하단의 즉시 이미지 생성 UI."""
    if image_client is None:
        st.caption(t("img_engine_none"))
        return

    st.caption(t("img_engine_note", engine=image_client.name))

    image_key = f"generated_image_{idea_index}"
    if st.button(t("img_generate_btn"), key=f"gen_img_btn_{idea_index}"):
        with st.spinner(t("img_generating", engine=image_client.name)):
            try:
                st.session_state[image_key] = image_client.generate(copy_prompt)
            except ProviderError as exc:
                st.error(t("img_error", err=str(exc)))

    png_bytes = st.session_state.get(image_key)
    if png_bytes:
        st.image(png_bytes)
        st.download_button(
            t("img_download"),
            data=png_bytes,
            file_name=f"idea_{idea_index + 1}.png",
            mime="image/png",
            key=f"dl_img_{idea_index}",
        )
