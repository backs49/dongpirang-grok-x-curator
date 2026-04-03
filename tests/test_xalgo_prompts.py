from xalgo_prompts import (
    OPTIMIZER_SYSTEM_PROMPT,
    IDEAS_SYSTEM_PROMPT,
    CURATOR_SYSTEM_PROMPT,
    THREAD_SYSTEM_PROMPT,
    SCHEDULER_SYSTEM_PROMPT,
    AB_COMPARE_SYSTEM_PROMPT,
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


class TestOptimizerActionBreakdown:
    def test_contains_action_breakdown(self):
        assert "action_breakdown" in OPTIMIZER_SYSTEM_PROMPT

    def test_contains_weight_values(self):
        assert "13.5" in OPTIMIZER_SYSTEM_PROMPT
        assert "11.0" in OPTIMIZER_SYSTEM_PROMPT
        assert "0.5" in OPTIMIZER_SYSTEM_PROMPT


class TestCuratorPrompt:
    def test_exists_and_nonempty(self):
        assert len(CURATOR_SYSTEM_PROMPT) > 50

    def test_contains_search_reference(self):
        lower = CURATOR_SYSTEM_PROMPT.lower()
        assert "search" in lower or "검색" in lower


class TestThreadPrompt:
    def test_exists_and_nonempty(self):
        assert len(THREAD_SYSTEM_PROMPT) > 100

    def test_contains_author_diversity_decay(self):
        assert "decay" in THREAD_SYSTEM_PROMPT.lower()

    def test_contains_thread_keywords(self):
        assert "스레드" in THREAD_SYSTEM_PROMPT

    def test_contains_json_format(self):
        assert "overall_score" in THREAD_SYSTEM_PROMPT
        assert "optimized_thread" in THREAD_SYSTEM_PROMPT


class TestSchedulerPrompt:
    def test_exists_and_nonempty(self):
        assert len(SCHEDULER_SYSTEM_PROMPT) > 100

    def test_contains_time_recommendations(self):
        assert "시간" in SCHEDULER_SYSTEM_PROMPT

    def test_contains_diversity_decay(self):
        assert "decay" in SCHEDULER_SYSTEM_PROMPT.lower() or "감쇠" in SCHEDULER_SYSTEM_PROMPT


class TestABComparePrompt:
    def test_exists_and_nonempty(self):
        assert len(AB_COMPARE_SYSTEM_PROMPT) > 100

    def test_contains_comparison_keywords(self):
        assert "비교" in AB_COMPARE_SYSTEM_PROMPT

    def test_contains_winner(self):
        assert "winner" in AB_COMPARE_SYSTEM_PROMPT
