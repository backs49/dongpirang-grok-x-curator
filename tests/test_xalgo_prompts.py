from xalgo_prompts import (
    OPTIMIZER_SYSTEM_PROMPT,
    IDEAS_SYSTEM_PROMPT,
    CURATOR_SYSTEM_PROMPT,
)


class TestOptimizerPrompt:
    def test_exists_and_nonempty(self):
        assert len(OPTIMIZER_SYSTEM_PROMPT) > 100

    def test_contains_phoenix_scorer(self):
        assert "Phoenix" in OPTIMIZER_SYSTEM_PROMPT

    def test_contains_multi_action(self):
        assert "multi-action" in OPTIMIZER_SYSTEM_PROMPT.lower() or "multi_action" in OPTIMIZER_SYSTEM_PROMPT.lower()

    def test_contains_engagement_types(self):
        for keyword in ["like", "reply", "repost", "quote"]:
            assert keyword.lower() in OPTIMIZER_SYSTEM_PROMPT.lower(), f"Missing: {keyword}"

    def test_contains_author_diversity(self):
        assert "diversity" in OPTIMIZER_SYSTEM_PROMPT.lower()

    def test_contains_json_format(self):
        assert "score" in OPTIMIZER_SYSTEM_PROMPT
        assert "engagement_level" in OPTIMIZER_SYSTEM_PROMPT
        assert "suggestions" in OPTIMIZER_SYSTEM_PROMPT
        assert "optimized_post" in OPTIMIZER_SYSTEM_PROMPT

    def test_contains_out_of_network(self):
        lower = OPTIMIZER_SYSTEM_PROMPT.lower()
        assert "out-of-network" in lower or "oon" in lower


class TestIdeasPrompt:
    def test_exists_and_nonempty(self):
        assert len(IDEAS_SYSTEM_PROMPT) > 50

    def test_contains_algorithm_reference(self):
        lower = IDEAS_SYSTEM_PROMPT.lower()
        assert "algorithm" in lower or "알고리즘" in lower

    def test_contains_five_ideas(self):
        assert "5" in IDEAS_SYSTEM_PROMPT


class TestCuratorPrompt:
    def test_exists_and_nonempty(self):
        assert len(CURATOR_SYSTEM_PROMPT) > 50

    def test_contains_search_reference(self):
        lower = CURATOR_SYSTEM_PROMPT.lower()
        assert "search" in lower or "검색" in lower
