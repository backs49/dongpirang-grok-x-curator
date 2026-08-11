"""이미지 스타일 모드 — 스타일 규칙의 단일 출처.

xAI Grok Imagine 은 시드·스타일 파라미터·네거티브 프롬프트가 없다.
피드의 비주얼 일관성을 만드는 유일한 수단은 "고정 스타일 블록 문자열"이며,
아이디어의 image_prompt(장면 브리프)에는 스타일을 넣지 않고 생성 시점에
선택된 모드 블록이 스타일을 결정한다.

실사 계열(editorial/cinematic)의 anti-slop 은 양성 표현으로만 구현한다
(카메라+렌즈 명시, 방향광, 필름 그레인, 자연 질감, 비중앙 구도).
라벨(한글)은 LLM 에코 값이 아니므로 자유지만 writing_modes 와 통일성을 위해
모듈에 고정한다.

인물 캐스팅: 독자가 한국인이므로 사람이 나오는 스타일(editorial/cinematic/
retro_anime)은 한국 배경 + 한국인 주인공을 강제한다. 실존 아이돌 이름은
프롬프트에 절대 넣지 않는다 — 초상권 문제에 더해 이미지 모델이 실존 인물
요청을 거부하거나 어긋난 결과를 내기 때문에, 같은 인상을 만드는 묘사
(K-pop 아이돌 룩)로만 표현한다.
"""

from __future__ import annotations

AUTO = "auto"

# LLM 이 suggested_style 로 제안할 수 있는 스타일 (mascot 제외 — 마스코트는
# 사용자가 명시적으로 고를 때만)
SUGGESTABLE = ("comic", "doodle", "editorial", "cinematic", "infographic", "retro_anime")

COMMON_RULES = (
    "Aspect ratio: portrait 3:4. "
    "Do not include readable text, letters, UI captions, watermarks, or logos. "
    "READABILITY (mandatory): a viewer must understand the situation within 3 "
    "seconds without any caption — ONE focal point, a simple background, and a "
    "scene that clearly matches the post's core message. "
    "HOOK (mandatory): the image must freeze a fast-scrolling thumb — the "
    "main subject dominates the frame, using the strongest attention-grab "
    "this style allows: a strong, instantly readable emotion on a face, one "
    "oversized focal element, or one bold light-and-color contrast. "
    "TONE (mandatory): exaggeration stays playful and likable — NEVER gross, "
    "grotesque, disturbing, or body-horror. No slime, goo, vomit, melting "
    "bodies, or distorted anatomy."
)

# 실사 계열 공용 캐스팅 블록 — 한국 배경 + K-pop 아이돌 룩의 한국인 주인공.
# 실존 인물 이름 금지(모듈 독스트링 참조). "mid-twenties" 는 성인임을
# 명시하는 안전 장치이므로 빼지 말 것. 조건부 지시(recast/if-then)는 이미지
# 모델이 절차적으로 수행하지 못하므로 선언형("The ONLY person is...")으로 쓴다.
_KOREAN_CAST = (
    "CAST (mandatory): the scene is set in present-day Seoul, Korea. The "
    "ONLY person in the frame is a strikingly beautiful Korean woman in her "
    "mid-twenties with the polished look of a K-pop idol — luminous flawless "
    "skin, elegant features, glossy dark hair, subtle natural makeup. She is "
    "the one performing whatever action the scene describes, and her "
    "expression carries its emotion. If the scene describes no person, she "
    "appears naturally reacting to its subject, with that subject still "
    "clearly visible. She is dressed modestly for the situation in chic "
    "modern clothing — wholesome and non-suggestive, no revealing outfits, "
    "no sensual posing."
)

IMAGE_MODES: dict[str, dict] = {
    "mascot": {
        "label": "마스코트 3D",
        "style_block": (
            "STYLE: cute 3D mascot character, blind-box vinyl toy style, "
            "C4D and Octane render quality, soft subsurface scattering, soft "
            "studio lighting, 50mm lens look, shallow depth of field, clean "
            "pastel seamless background. "
            "MASCOT (mandatory): the protagonist is the fixed brand mascot — an "
            "adorable chubby brown tabby cat with dark stripes, white chest, "
            "muzzle and paws, big glossy green eyes, a pink nose and pink paw "
            "pads. Its fur markings, colors and proportions must stay identical "
            "in every image so it is recognizably the same character. Replace "
            "any human protagonist in the scene with this cat acting out the "
            "situation — anthropomorphic poses are encouraged (typing, driving, "
            "holding coffee)."
        ),
    },
    "comic": {
        "label": "만화/밈",
        "style_block": (
            "STYLE: crude hand-drawn webcomic style cartoon in the spirit of "
            "Korean instant-toon memes, bold messy linework, flat colors, "
            "simple dot-and-line facial features, exaggerated reaction "
            "expression, quirky proportions, plain background, restrained "
            "palette of 2-3 strong colors; characters and props read as "
            "Korean everyday life (office, subway, one-room apartment)."
        ),
    },
    "doodle": {
        "label": "낙서 두들",
        "style_block": (
            "STYLE: playful notebook doodle sketch, messy stick-figure scene, "
            "black ballpoint pen on white paper, hand-drawn arrows and scribbled "
            "shapes, chaotic humor, intentionally crude but charming."
        ),
    },
    "editorial": {
        "label": "에디토리얼 실사",
        "style_block": (
            "STYLE: editorial photograph for a business-magazine feature "
            "with a fashion-editorial polish on the subject, shot on Nikon "
            "Z9, 50mm f/1.4, soft directional window light from the left, "
            "muted refined palette, Kodak Portra 400 tones, subtle film "
            "grain, natural skin texture, slight asymmetry, candid unposed "
            "moment caught mid-action, lived-in environment with everyday "
            "clutter, off-center rule-of-thirds composition. "
            + _KOREAN_CAST
        ),
    },
    "cinematic": {
        "label": "시네마틱",
        "style_block": (
            "STYLE: cinematic film still like a frame from a prestige Korean "
            "drama, 85mm anamorphic lens, f/1.4, shallow depth of field, "
            "close-up or medium close-up on the protagonist, practical "
            "lighting from screens and lamps inside the scene, volumetric "
            "haze, teal-and-orange grade with cool shadows and warm skin "
            "tones, fine film grain, slightly faded blacks, off-center "
            "composition. "
            + _KOREAN_CAST
        ),
    },
    "infographic": {
        "label": "인포그래픽",
        "style_block": (
            "STYLE: flat vector illustration, minimal tech infographic style, "
            "simple geometric shapes connected by dotted-line arrows, "
            "consistent 2px stroke weight, clean grid layout, limited palette "
            "of three muted colors plus one accent on an off-white background, "
            "generous whitespace, rounded corners, no gradients, no texture, "
            "no photorealism."
        ),
    },
    "retro_anime": {
        "label": "레트로 아니메",
        "style_block": (
            "STYLE: 1990s retro anime style, hand-painted cel shading with "
            "hard cel highlights, thick ink outlines, muted faded film "
            "palette, soft grain and slight VHS softness, light scanlines "
            "only as a subtle finishing layer, nostalgic city-pop mood, "
            "Seoul cityscape backdrops. "
            "CAST (mandatory): the heroine is a beautiful adult Korean woman "
            "in her mid-twenties drawn in 90s anime style — expressive eyes, "
            "soft dark hair, elegant features, stylish adult fashion (never "
            "a school uniform); every character is Korean. She is the one "
            "performing whatever action the scene describes; if the scene "
            "describes no person, she appears naturally reacting to its "
            "subject, with that subject still clearly visible. Wholesome and "
            "non-suggestive."
        ),
    },
}


def style_options() -> list[str]:
    return [AUTO] + list(IMAGE_MODES)


def style_label(key: str) -> str:
    if key == AUTO:
        return "자동"
    mode = IMAGE_MODES.get(key)
    return mode["label"] if mode else key


def resolve_auto_style(suggested: str | None, idea_index: int = 0) -> str:
    """자동 모드에서 실제 스타일을 정한다.

    LLM 의 suggested_style 이 유효하면 그대로, 아니면 아이디어 인덱스로
    순환 배정 — 어떤 경우에도 아이디어마다 다른 스타일이 나오게 한다.
    """
    if suggested in SUGGESTABLE:
        return suggested
    return SUGGESTABLE[idea_index % len(SUGGESTABLE)]


def build_image_prompt(scene_brief: str, mode_key: str) -> str:
    """장면 브리프 + 모드 스타일 블록으로 최종 이미지 프롬프트를 조립한다.

    포스트 원문은 절대 포함하지 않는다 — 이미지 모델이 원문 텍스트를
    이미지에 새기는 사고 방지 + 프롬프트 길이 절감.
    """
    mode = IMAGE_MODES[mode_key]
    return (
        f"Create one image for an X post. {COMMON_RULES}\n\n"
        f"{mode['style_block']}\n\n"
        "SCENE (the subject of the image — depict exactly this):\n"
        f"{scene_brief.strip()}"
    )
