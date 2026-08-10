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


class TestPromptV2:
    def test_prompt_version_constant(self):
        from xalgo_prompts import PROMPT_VERSION

        assert PROMPT_VERSION == "2.0"

    def test_ideas_schema_has_new_fields(self):
        assert '"mode"' in IDEAS_SYSTEM_PROMPT
        assert '"suggested_style"' in IDEAS_SYSTEM_PROMPT
        assert '"video_motion"' in IDEAS_SYSTEM_PROMPT

    def test_ideas_image_prompt_is_scene_brief(self):
        # 스타일 결정은 생성 시점 모드 블록의 몫 — 프롬프트에서 그림체 지정 제거
        assert "flat editorial illustration" not in IDEAS_SYSTEM_PROMPT
        assert "장면" in IDEAS_SYSTEM_PROMPT
        assert "4:5" not in IDEAS_SYSTEM_PROMPT

    def test_style_guide_v2_structural_rules(self):
        from xalgo_prompts import NATURAL_STYLE_GUIDE

        assert "교훈" in NATURAL_STYLE_GUIDE          # 교훈 직접 말하기 금지
        assert "문장 길이" in NATURAL_STYLE_GUIDE      # 길이 변주
        # 앵무새 유발 예시 제거 확인
        assert "FSD" not in NATURAL_STYLE_GUIDE
        assert "출퇴근 왕복 1시간" not in NATURAL_STYLE_GUIDE

    def test_draft_prompt_scene_brief(self):
        from xalgo_prompts import DRAFT_FROM_MATERIAL_SYSTEM_PROMPT

        assert "flat editorial illustration" not in DRAFT_FROM_MATERIAL_SYSTEM_PROMPT
        assert "장면" in DRAFT_FROM_MATERIAL_SYSTEM_PROMPT

    def test_voice_analysis_prompt_exists(self):
        from xalgo_prompts import VOICE_ANALYSIS_SYSTEM_PROMPT

        assert "analysis" in VOICE_ANALYSIS_SYSTEM_PROMPT
        assert "JSON" in VOICE_ANALYSIS_SYSTEM_PROMPT
