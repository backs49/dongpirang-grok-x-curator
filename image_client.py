from __future__ import annotations


def build_copy_prompt(post_content: str, image_prompt: str) -> str:
    post_content = post_content.strip()
    image_prompt = image_prompt.strip()
    if post_content:
        return (
            "Create an image for this X post. Do not include readable text, letters, UI captions, "
            "watermarks, or logos unless explicitly requested.\n\n"
            f"Post context:\n{post_content}\n\n"
            f"Image prompt:\n{image_prompt}"
        )
    return (
        "Create an image from this prompt. Do not include readable text, letters, UI captions, "
        "watermarks, or logos unless explicitly requested.\n\n"
        f"Image prompt:\n{image_prompt}"
    )
