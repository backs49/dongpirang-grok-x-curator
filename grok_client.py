import openai
from xalgo_prompts import (
    OPTIMIZER_SYSTEM_PROMPT,
    IDEAS_SYSTEM_PROMPT,
    CURATOR_SYSTEM_PROMPT,
    THREAD_SYSTEM_PROMPT,
    SCHEDULER_SYSTEM_PROMPT,
    AB_COMPARE_SYSTEM_PROMPT,
    RISK_CHECK_SYSTEM_PROMPT,
)
from utils import parse_grok_json, parse_thread_text, contains_hangul
from i18n import get_lang_instruction, get_content_language_pair, get_output_language_name, get_lang


class GrokClient:
    def __init__(self, api_key: str, model: str):
        self.client = openai.OpenAI(
            base_url="https://api.x.ai/v1",
            api_key=api_key,
        )
        self.model = model

    def optimize_post(self, text: str, image_desc: str = "", hashtags: str = "") -> dict:
        user_content = f"포스트 내용:\n{text}"
        if image_desc:
            user_content += f"\n\n이미지 설명: {image_desc}"
        if hashtags:
            user_content += f"\n\n해시태그: {hashtags}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": OPTIMIZER_SYSTEM_PROMPT + get_lang_instruction()},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
            )
            return parse_grok_json(response.choices[0].message.content or "")
        except openai.OpenAIError as e:
            return {"error": f"Grok API 오류: {str(e)}"}

    def generate_ideas(self, keywords: str, length: int = 0) -> dict:
        from datetime import datetime
        # 2026년 4월 3일 현재를 강제로 주입
        current_date_kr = datetime.now().strftime("%Y년 %m월 %d일")

        # 글자수 지시사항 빌드
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

        # placeholder를 실제 값으로 치환
        system_prompt = IDEAS_SYSTEM_PROMPT.format(
            current_date_kr=current_date_kr,
            length_instruction=length_instruction,
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt + get_lang_instruction()},
                    {"role": "user", "content": f"관심사/키워드: {keywords}"},
                ],
                response_format={"type": "json_object"},
            )
            return parse_grok_json(response.choices[0].message.content or "")
        except openai.OpenAIError as e:
            return {"error": f"Grok API 오류: {str(e)}"}

    def curate_feed(self, interests: str) -> dict:
        from datetime import datetime, timedelta
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

        # user 메시지는 한국어 레이블 ("관심사:") 대신 언어 중립적인 영어 레이블 +
        # 명시적 출력 언어 태그를 포함시킨다. 한국어 앵커가 suggested_reply 같은
        # 생성형 필드의 언어 지시(LANG_INSTRUCTION)를 뚫고 한국어로 새는 현상을 방지.
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

            # Responses API에서 텍스트 추출
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
            return {"error": f"Grok API 오류: {str(e)}"}

    def _fix_korean_leakage(self, result: dict) -> None:
        """suggested_reply 가 목표 언어가 아니라 한국어로 새어나온 경우,
        해당 필드만 저비용 번역 호출로 교정한다. grok-4-1-fast-reasoning + 일본어
        조합에서 모델이 종종 한국어로 폴백하는 현상에 대한 안전망."""
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
        """짧은 리플 한 개를 목표 언어로 번역. 실패 시 빈 문자열 반환."""
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

    def optimize_thread(self, thread_text: str) -> dict:
        tweets = parse_thread_text(thread_text)
        if len(tweets) < 2:
            return {"error": "스레드는 최소 2개 이상의 트윗이 필요합니다. --- 또는 빈 줄로 구분하세요."}

        parts = [f"[트윗 {i+1}]\n{t}" for i, t in enumerate(tweets)]
        user_content = f"스레드 분석 요청 (총 {len(tweets)}개 트윗):\n\n" + "\n\n".join(parts)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": THREAD_SYSTEM_PROMPT + get_lang_instruction()},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
            )
            return parse_grok_json(response.choices[0].message.content or "")
        except openai.OpenAIError as e:
            return {"error": f"Grok API 오류: {str(e)}"}

    def plan_schedule(self, posts_info: list) -> dict:
        from datetime import datetime
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

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt + get_lang_instruction()},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
            )
            return parse_grok_json(response.choices[0].message.content or "")
        except openai.OpenAIError as e:
            return {"error": f"Grok API 오류: {str(e)}"}

    def check_risk(self, text: str, image_desc: str = "") -> dict:
        user_content = f"포스트 내용:\n{text}"
        if image_desc:
            user_content += f"\n\n이미지 설명: {image_desc}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": RISK_CHECK_SYSTEM_PROMPT + get_lang_instruction()},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
            )
            return parse_grok_json(response.choices[0].message.content or "")
        except openai.OpenAIError as e:
            return {"error": f"Grok API 오류: {str(e)}"}

    def compare_posts(self, post_a: str, post_b: str) -> dict:
        user_content = f"두 포스트를 비교 분석해주세요:\n\n=== 포스트 A ===\n{post_a}\n\n=== 포스트 B ===\n{post_b}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": AB_COMPARE_SYSTEM_PROMPT + get_lang_instruction()},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
            )
            return parse_grok_json(response.choices[0].message.content or "")
        except openai.OpenAIError as e:
            return {"error": f"Grok API 오류: {str(e)}"}
