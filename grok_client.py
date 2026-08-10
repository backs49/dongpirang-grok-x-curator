from __future__ import annotations

import logging
from datetime import datetime

import ideas_history
import style_lint
import voice_card
import writing_modes
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
    DRAFT_FROM_MATERIAL_SYSTEM_PROMPT,
    IDEAS_SYSTEM_PROMPT,
    NATURAL_STYLE_GUIDE,
    OPTIMIZER_SYSTEM_PROMPT,
    PERFORMANCE_SYSTEM_PROMPT,
    RISK_CHECK_SYSTEM_PROMPT,
    SCHEDULER_SYSTEM_PROMPT,
    THREAD_SYSTEM_PROMPT,
    VOICE_ANALYSIS_SYSTEM_PROMPT,
)


def _avoid_block(max_sets: int = 3, max_lines: int = 15) -> str:
    """최근 생성 아이디어의 각도·훅을 '겹치지 말 것' 블록으로 만든다."""
    lines: list[str] = []
    for entry in ideas_history.load_history()[:max_sets]:
        for idea in entry.get("result", {}).get("ideas", []):
            title = (idea.get("title") or "").strip()
            first = (idea.get("content") or "").strip().split("\n")[0][:60]
            if title or first:
                lines.append(f"- {title} / {first}")
    if not lines:
        return ""
    return (
        "\n\n# 최근에 이미 생성한 아이디어 (겹치지 말 것)\n"
        "아래 각도·훅·소재와 겹치지 않는 새로운 각도로 쓰세요:\n"
        + "\n".join(lines[:max_lines])
        + "\n"
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
            OPTIMIZER_SYSTEM_PROMPT + NATURAL_STYLE_GUIDE + get_lang_instruction(),
            user_content,
        )

    def generate_ideas(
        self,
        keywords: str,
        length: int = 0,
        mode: str = writing_modes.AUTO_MIX,
    ) -> dict:
        current_date_kr = datetime.now().strftime("%Y년 %m월 %d일")

        if length and length > 0:
            length_instruction = (
                f"**분량: 반드시 정확히 약 {length}자(±10% 이내)**. "
                f"사용자가 직접 지정한 분량이므로 엄격하게 지키세요. "
                f"한두 줄로 끝내지 마세요."
            )
        else:
            length_instruction = "**분량: 반드시 200~500자**. 한두 줄로 끝내지 마세요."

        system_prompt = (
            IDEAS_SYSTEM_PROMPT.format(
                current_date_kr=current_date_kr,
                length_instruction=length_instruction,
            )
            + writing_modes.build_mode_block(mode)
            + NATURAL_STYLE_GUIDE
            + voice_card.build_voice_block()
            + _avoid_block()
            + get_lang_instruction()
        )

        result = self.provider.generate_json(
            system_prompt, f"관심사/키워드: {keywords}"
        )
        if "error" in result or not isinstance(result.get("ideas"), list):
            return result

        self._fill_mode_labels(result, mode)
        self._lint_and_rewrite(result, mode)
        return result

    def _fill_mode_labels(self, result: dict, mode: str) -> None:
        """LLM 이 mode 필드를 빠뜨렸을 때 배정 규칙으로 보정한다."""
        if mode == writing_modes.AUTO_MIX:
            rotation = writing_modes.TONE_ROTATION
            for i, idea in enumerate(result["ideas"]):
                fallback = writing_modes.WRITING_MODES[rotation[i % len(rotation)]]["label"]
                idea["mode"] = (idea.get("mode") or "").strip() or fallback
        else:
            label = writing_modes.WRITING_MODES[mode]["label"]
            for idea in result["ideas"]:
                idea["mode"] = label

    def _lint_and_rewrite(self, result: dict, mode: str) -> None:
        """S1 검출 아이디어를 1회 한정 재작성. 실패해도 흐름을 막지 않는다."""
        def _polite_ok(idea: dict) -> bool:
            key = writing_modes.label_to_key(idea.get("mode", ""))
            return writing_modes.allow_polite(key)

        flagged: list[int] = []
        for i, idea in enumerate(result["ideas"]):
            lr = style_lint.lint(idea.get("content", ""), allow_polite=_polite_ok(idea))
            idea["_lint"] = {"s1": lr.s1_hits, "s2": lr.s2_hits}
            if lr.s1_hits:
                flagged.append(i)
        if not flagged:
            return

        listing = "\n\n".join(
            f"[아이디어 {i + 1} | 모드: {result['ideas'][i].get('mode', '')}]\n"
            f"검출된 AI 상투 표현: {', '.join(result['ideas'][i]['_lint']['s1'])}\n"
            f"원문:\n{result['ideas'][i].get('content', '')}"
            for i in flagged
        )
        rewrite_system = (
            "당신은 X(Twitter) 포스트 윤문 전문가입니다. 아래 포스트들에서 검출된 "
            "AI 상투 표현을 제거하고, 같은 모드·같은 소재·같은 의미를 유지한 채 "
            "다시 씁니다. 분량은 원문과 비슷하게 유지하세요.\n"
            + writing_modes.build_mode_block(mode)
            + NATURAL_STYLE_GUIDE
            + '\n반드시 JSON만 출력: {"rewrites": [{"index": 아이디어_번호_정수, "content": "고친 본문"}]}'
        )
        try:
            retry = self.provider.generate_json(rewrite_system, listing)
            for rw in retry.get("rewrites", []):
                idx = int(rw.get("index", 0)) - 1
                new_content = (rw.get("content") or "").strip()
                if idx in flagged and new_content:
                    idea = result["ideas"][idx]
                    old_s1_count = len(idea["_lint"]["s1"])
                    lr = style_lint.lint(new_content, allow_polite=_polite_ok(idea))
                    # 재작성이 원본보다 S1 검출을 실제로 줄였을 때만 채택한다.
                    # 그렇지 않으면(동률·악화) 원본 콘텐츠와 원본 _lint 를 유지한다.
                    if len(lr.s1_hits) < old_s1_count:
                        idea["content"] = new_content
                        idea["_lint"] = {"s1": lr.s1_hits, "s2": lr.s2_hits}
        except Exception as exc:
            logging.getLogger(__name__).warning("lint rewrite pass failed: %s", exc)
            # 재작성 실패는 원본 유지 — 배지로만 알린다

    def analyze_voice(self, examples: list[str]) -> dict:
        """보이스 카드용 1회성 문체 분석."""
        return self.provider.generate_json(
            VOICE_ANALYSIS_SYSTEM_PROMPT,
            "\n\n---\n\n".join(examples),
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
            THREAD_SYSTEM_PROMPT + NATURAL_STYLE_GUIDE + get_lang_instruction(),
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
            RISK_CHECK_SYSTEM_PROMPT + NATURAL_STYLE_GUIDE + get_lang_instruction(),
            user_content,
        )

    def draft_from_material(self, material_text: str) -> dict:
        return self.provider.generate_json(
            DRAFT_FROM_MATERIAL_SYSTEM_PROMPT
            + NATURAL_STYLE_GUIDE
            + voice_card.build_voice_block()
            + get_lang_instruction(),
            f"소재 메모:\n{material_text}",
        )

    def analyze_performance(self, summary: dict) -> dict:
        def _fmt_posts(posts: list, label: str) -> str:
            lines = [label]
            for p in posts:
                text = (p.get("text") or "").replace("\n", " ")[:140]
                lines.append(
                    f"- 노출 {p.get('impressions', 0):,} · 참여율 {p.get('engagement_pct', 0):.2f}% · \"{text}\""
                )
            return "\n".join(lines)

        est_days = summary.get("est_days_to_target")
        user_content = (
            "실제 X 애널리틱스 데이터 요약:\n\n"
            f"- 총 포스트 수: {summary.get('total_posts', 0)}\n"
            f"- 총 노출: {summary.get('total_impressions', 0):,}\n"
            f"- 최근 90일 노출: {summary.get('recent_impressions', 0):,}\n"
            f"- 평균 참여율: {summary.get('avg_engagement_pct', 0):.2f}%\n"
            f"- 수익화 요건(500만 노출) 진행률: {summary.get('monetization_pct', 0):.2f}%\n"
            f"- 일평균 노출: {summary.get('daily_avg_impressions', 0):,.0f}\n"
            f"- 현재 속도 기준 목표까지 예상 일수: {est_days if est_days is not None else '계산 불가'}\n\n"
            + _fmt_posts(summary.get("top_posts", []), "[상위 포스트]")
            + "\n\n"
            + _fmt_posts(summary.get("bottom_posts", []), "[하위 포스트]")
        )

        return self.provider.generate_json(
            PERFORMANCE_SYSTEM_PROMPT + get_lang_instruction(),
            user_content,
        )

    def compare_posts(self, post_a: str, post_b: str) -> dict:
        user_content = f"두 포스트를 비교 분석해주세요:\n\n=== 포스트 A ===\n{post_a}\n\n=== 포스트 B ===\n{post_b}"

        return self.provider.generate_json(
            AB_COMPARE_SYSTEM_PROMPT + NATURAL_STYLE_GUIDE + get_lang_instruction(),
            user_content,
        )
