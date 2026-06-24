from __future__ import annotations

from datetime import datetime

from i18n import (
    get_content_language_pair,
    get_lang_instruction,
    get_output_language_name,
)
from providers.xai_api import XaiApiProvider
from utils import parse_thread_text
from xalgo_prompts import (
    AB_COMPARE_SYSTEM_PROMPT,
    CURATOR_SYSTEM_PROMPT,
    IDEAS_SYSTEM_PROMPT,
    OPTIMIZER_SYSTEM_PROMPT,
    RISK_CHECK_SYSTEM_PROMPT,
    SCHEDULER_SYSTEM_PROMPT,
    THREAD_SYSTEM_PROMPT,
)


class GrokClient:
    def __init__(
        self,
        api_key: str = "",
        model: str = "grok-4.1-fast-reasoning",
        provider=None,
    ):
        self.provider = provider or XaiApiProvider(api_key=api_key, model=model)
        self.model = model
        self.client = getattr(self.provider, "client", None)

    def optimize_post(self, text: str, image_desc: str = "", hashtags: str = "") -> dict:
        user_content = f"포스트 내용:\n{text}"
        if image_desc:
            user_content += f"\n\n이미지 설명: {image_desc}"
        if hashtags:
            user_content += f"\n\n해시태그: {hashtags}"

        return self.provider.generate_json(
            OPTIMIZER_SYSTEM_PROMPT + get_lang_instruction(),
            user_content,
        )

    def generate_ideas(self, keywords: str, length: int = 0) -> dict:
        current_date_kr = datetime.now().strftime("%Y년 %m월 %d일")

        if length and length > 0:
            length_instruction = (
                f"**분량: 반드시 정확히 약 {length}자(±10% 이내)**. "
                f"사용자가 직접 지정한 분량이므로 엄격하게 지키세요. "
                f"한두 줄로 끝내지 마세요. 구체적인 예시, 수치, 경험을 포함하여 충실하게 작성하세요."
            )
        else:
            length_instruction = (
                "**분량: 반드시 200~500자**. "
                "한두 줄로 끝내지 마세요. 구체적인 예시, 수치, 경험을 포함하여 충실하게 작성하세요."
            )

        system_prompt = IDEAS_SYSTEM_PROMPT.format(
            current_date_kr=current_date_kr,
            length_instruction=length_instruction,
        )

        return self.provider.generate_json(
            system_prompt + get_lang_instruction(),
            f"관심사/키워드: {keywords}",
        )

    def curate_feed(self, interests: str) -> dict:
        if getattr(self.provider, "supports_curator", False) and hasattr(self.provider, "curate_feed"):
            return self.provider.curate_feed(interests)

        current_date_kr = datetime.now().strftime("%Y년 %m월 %d일")
        system_prompt = CURATOR_SYSTEM_PROMPT.format(
            current_date_kr=current_date_kr,
            language_pair=get_content_language_pair(),
            output_language=get_output_language_name(),
        )
        user_prompt = (
            f"User interests: {interests}\n\n"
            "The current provider cannot access live X search. Generate three manual search "
            "recommendations only. Each recommendation must include summary, why_recommended, "
            "search_keywords, suggested_reply, and engagement_hint. Do not claim these are "
            "real-time X posts."
        )
        return self.provider.generate_json(system_prompt + get_lang_instruction(), user_prompt)

    def optimize_thread(self, thread_text: str) -> dict:
        tweets = parse_thread_text(thread_text)
        if len(tweets) < 2:
            return {"error": "스레드는 최소 2개 이상의 트윗이 필요합니다. --- 또는 빈 줄로 구분하세요."}

        parts = [f"[트윗 {i+1}]\n{t}" for i, t in enumerate(tweets)]
        user_content = f"스레드 분석 요청 (총 {len(tweets)}개 트윗):\n\n" + "\n\n".join(parts)

        return self.provider.generate_json(
            THREAD_SYSTEM_PROMPT + get_lang_instruction(),
            user_content,
        )

    def plan_schedule(self, posts_info: list) -> dict:
        current_date_kr = datetime.now().strftime("%Y년 %m월 %d일")
        system_prompt = SCHEDULER_SYSTEM_PROMPT.format(current_date_kr=current_date_kr)

        parts = []
        for i, info in enumerate(posts_info):
            topic = info.get("topic", "").strip()
            content = info.get("content", "").strip()
            part = f"[포스트 {i+1}]\n주제: {topic or '미정'}"
            if content:
                part += f"\n내용: {content}"
            parts.append(part)

        user_content = f"스케줄 최적화 요청 (총 {len(posts_info)}개 포스트):\n\n" + "\n\n".join(parts)

        return self.provider.generate_json(
            system_prompt + get_lang_instruction(),
            user_content,
        )

    def check_risk(self, text: str, image_desc: str = "") -> dict:
        user_content = f"포스트 내용:\n{text}"
        if image_desc:
            user_content += f"\n\n이미지 설명: {image_desc}"

        return self.provider.generate_json(
            RISK_CHECK_SYSTEM_PROMPT + get_lang_instruction(),
            user_content,
        )

    def compare_posts(self, post_a: str, post_b: str) -> dict:
        user_content = f"두 포스트를 비교 분석해주세요:\n\n=== 포스트 A ===\n{post_a}\n\n=== 포스트 B ===\n{post_b}"

        return self.provider.generate_json(
            AB_COMPARE_SYSTEM_PROMPT + get_lang_instruction(),
            user_content,
        )
