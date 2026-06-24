from __future__ import annotations

from datetime import datetime, timedelta

import openai

from i18n import (
    get_content_language_pair,
    get_lang,
    get_lang_instruction,
    get_output_language_name,
)
from providers.base import ProviderStatus
from utils import contains_hangul, parse_grok_json
from xalgo_prompts import CURATOR_SYSTEM_PROMPT


class XaiApiProvider:
    name = "xAI API"
    supports_curator = True

    def __init__(self, api_key: str, model: str):
        self.client = openai.OpenAI(
            base_url="https://api.x.ai/v1",
            api_key=api_key,
        )
        self.model = model

    def is_available(self) -> ProviderStatus:
        return ProviderStatus(bool(self.client), "xAI API configured")

    def generate_json(self, system_prompt: str, user_prompt: str, *, timeout: int = 120) -> dict:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                timeout=timeout,
            )
            return parse_grok_json(response.choices[0].message.content or "")
        except openai.OpenAIError as e:
            return {"error": f"xAI API error: {str(e)}"}

    def generate_text(self, system_prompt: str, user_prompt: str, *, timeout: int = 120) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                timeout=timeout,
            )
            return (response.choices[0].message.content or "").strip()
        except openai.OpenAIError as e:
            return f"xAI API error: {str(e)}"

    def curate_feed(self, interests: str) -> dict:
        current_date_kr = datetime.now().strftime("%Y년 %m월 %d일")
        output_lang_name = get_output_language_name()
        system_prompt = CURATOR_SYSTEM_PROMPT.format(
            current_date_kr=current_date_kr,
            language_pair=get_content_language_pair(),
            output_language=output_lang_name,
        )

        today = datetime.now()
        from_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        to_date = today.strftime("%Y-%m-%d")

        user_content = (
            f"User interests: {interests}\n\n"
            f"Output language for ALL JSON text values: {output_lang_name}. "
            f"This applies to suggested_reply and every other field — do not match "
            f"the source post's language."
        )

        try:
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": system_prompt + get_lang_instruction()},
                    {"role": "user", "content": user_content},
                ],
                tools=[{
                    "type": "x_search",
                    "from_date": from_date,
                    "to_date": to_date,
                }],
                text={"format": {"type": "json_object"}},
            )

            text_content = ""
            for item in response.output:
                if getattr(item, "type", None) == "message":
                    for part in getattr(item, "content", []):
                        if hasattr(part, "text"):
                            text_content = part.text

            result = parse_grok_json(text_content)
            self._fix_korean_leakage(result)
            return result
        except openai.OpenAIError as e:
            return {"error": f"xAI API error: {str(e)}"}

    def _fix_korean_leakage(self, result: dict) -> None:
        if get_lang() == "ko":
            return
        recs = result.get("recommendations")
        if not isinstance(recs, list):
            return
        target_lang = get_output_language_name()
        for rec in recs:
            if not isinstance(rec, dict):
                continue
            reply = rec.get("suggested_reply", "")
            if not isinstance(reply, str) or not contains_hangul(reply):
                continue
            translated = self._translate_reply(reply, target_lang)
            if translated:
                rec["suggested_reply"] = translated

    def _translate_reply(self, text: str, target_lang: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are a translator. Rewrite the user's text in natural, "
                            f"casual {target_lang} suitable for a social media reply. "
                            f"Preserve tone and emojis. Output ONLY the translated text, "
                            f"no quotes, no explanations."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
            )
            return (response.choices[0].message.content or "").strip()
        except openai.OpenAIError:
            return ""
