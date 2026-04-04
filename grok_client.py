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
from utils import parse_grok_json, parse_thread_text


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
                    {"role": "system", "content": OPTIMIZER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
            )
            return parse_grok_json(response.choices[0].message.content or "")
        except openai.OpenAIError as e:
            return {"error": f"Grok API 오류: {str(e)}"}

    def generate_ideas(self, keywords: str) -> dict:
        from datetime import datetime
        # 2026년 4월 3일 현재를 강제로 주입
        current_date_kr = datetime.now().strftime("%Y년 %m월 %d일")

        # placeholder를 실제 날짜로 치환
        system_prompt = IDEAS_SYSTEM_PROMPT.format(current_date_kr=current_date_kr)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
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
        system_prompt = CURATOR_SYSTEM_PROMPT.format(current_date_kr=current_date_kr)

        today = datetime.now()
        from_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        to_date = today.strftime("%Y-%m-%d")

        try:
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"관심사: {interests}"},
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

            return parse_grok_json(text_content)
        except openai.OpenAIError as e:
            return {"error": f"Grok API 오류: {str(e)}"}

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
                    {"role": "system", "content": THREAD_SYSTEM_PROMPT},
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
                    {"role": "system", "content": system_prompt},
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
                    {"role": "system", "content": RISK_CHECK_SYSTEM_PROMPT},
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
                    {"role": "system", "content": AB_COMPARE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
            )
            return parse_grok_json(response.choices[0].message.content or "")
        except openai.OpenAIError as e:
            return {"error": f"Grok API 오류: {str(e)}"}
