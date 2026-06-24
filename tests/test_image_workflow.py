from image_client import build_copy_prompt


class TestBuildCopyPrompt:
    def test_combines_post_context_and_image_prompt(self):
        result = build_copy_prompt("Post about weekend writing", "A cozy desk, no text")
        assert "Post about weekend writing" in result
        assert "A cozy desk, no text" in result
        assert "no text" in result

    def test_handles_empty_post_content(self):
        result = build_copy_prompt("", "A cinematic portrait")
        assert result.startswith("Create an image")
        assert "A cinematic portrait" in result
