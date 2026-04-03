import openai
from xalgo_prompts import (
    OPTIMIZER_SYSTEM_PROMPT,
    IDEAS_SYSTEM_PROMPT,
    CURATOR_SYSTEM_PROMPT,
)
from utils import parse_grok_json


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
            return parse_grok_json(response.choices[0].message.content)
        except Exception as e:
            return {"error": f"Grok API 오류: {str(e)}"}

    def generate_ideas(self, keywords: str) -> dict:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": IDEAS_SYSTEM_PROMPT},
                    {"role": "user", "content": f"관심사/키워드: {keywords}"},
                ],
                response_format={"type": "json_object"},
            )
            return parse_grok_json(response.choices[0].message.content)
        except Exception as e:
            return {"error": f"Grok API 오류: {str(e)}"}

    def curate_feed(self, interests: str) -> dict:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": CURATOR_SYSTEM_PROMPT},
                    {"role": "user", "content": f"관심사: {interests}"},
                ],
                response_format={"type": "json_object"},
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "live_search",
                        "description": "Search for live information on X/Twitter",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query",
                                }
                            },
                            "required": ["query"],
                        },
                    },
                }],
            )
            return parse_grok_json(response.choices[0].message.content)
        except Exception as e:
            return {"error": f"Grok API 오류: {str(e)}"}
