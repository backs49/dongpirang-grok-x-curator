"""demo_data 프리셋이 각 탭 렌더러가 읽는 스키마와 일치하는지 검증한다.

렌더러는 .get() 으로 방어적으로 읽지만, 키가 빠지면 데모 화면이
비어 보이므로 필수 키 존재를 테스트로 고정한다.
"""

from demo_data import (
    OPTIMIZER_DEMO,
    IDEAS_DEMO,
    CURATOR_DEMO,
    THREAD_DEMO,
    AB_DEMO,
    SCHEDULER_DEMO,
    RISK_DEMO,
)


class TestExistingDemos:
    def test_optimizer_demo_keys(self):
        for key in ("score", "engagement_level", "action_breakdown",
                    "reasons", "suggestions", "optimized_post"):
            assert key in OPTIMIZER_DEMO
        for action_data in OPTIMIZER_DEMO["action_breakdown"].values():
            assert {"probability", "weight", "contribution"} <= action_data.keys()

    def test_ideas_demo_keys(self):
        assert IDEAS_DEMO["ideas"]
        for idea in IDEAS_DEMO["ideas"]:
            for key in ("title", "content", "engagement_level", "best_time",
                        "target_actions", "strategy", "image_prompt"):
                assert key in idea

    def test_ideas_demo_is_v2_schema(self):
        from demo_data import IDEAS_DEMO
        from image_modes import SUGGESTABLE
        from writing_modes import label_to_key

        for idea in IDEAS_DEMO["ideas"]:
            assert label_to_key(idea["mode"]) != "", idea["mode"]
            assert idea["suggested_style"] in SUGGESTABLE
            assert idea["video_motion"].strip()
            ip = idea["image_prompt"].lower()
            # 장면 브리프에는 스타일·비율 단어가 없어야 한다 (스타일은 모드 블록 몫)
            for banned in ("9:16", "3:4", "4:5", "cinematic", "illustration", "flat", "minimal"):
                assert banned not in ip, f"{banned} in image_prompt"

    def test_curator_demo_keys(self):
        assert CURATOR_DEMO["recommendations"]
        for rec in CURATOR_DEMO["recommendations"]:
            for key in ("summary", "why_recommended", "search_keywords",
                        "suggested_reply", "engagement_hint"):
                assert key in rec

    def test_thread_demo_keys(self):
        for key in ("overall_score", "thread_flow", "tweets",
                    "optimized_thread", "strategy_notes"):
            assert key in THREAD_DEMO
        for tweet in THREAD_DEMO["tweets"]:
            for key in ("position", "score", "decay_multiplier",
                        "effective_score", "analysis"):
                assert key in tweet


class TestAbDemo:
    def test_top_level_keys(self):
        for key in ("winner", "score_difference", "post_a", "post_b",
                    "comparative_analysis", "improvement_for_loser",
                    "best_of_both"):
            assert key in AB_DEMO

    def test_posts_have_renderer_keys(self):
        for side in ("post_a", "post_b"):
            data = AB_DEMO[side]
            for key in ("score", "engagement_level", "strengths", "weaknesses"):
                assert key in data, f"{side} missing {key}"

    def test_winner_consistency(self):
        assert AB_DEMO["winner"] in ("A", "B")
        diff = abs(AB_DEMO["post_a"]["score"] - AB_DEMO["post_b"]["score"])
        assert AB_DEMO["score_difference"] == diff
        expected_winner = (
            "A" if AB_DEMO["post_a"]["score"] >= AB_DEMO["post_b"]["score"] else "B"
        )
        assert AB_DEMO["winner"] == expected_winner

    def test_comparative_analysis_shape(self):
        for action, data in AB_DEMO["comparative_analysis"].items():
            assert data["advantage"] in ("A", "B"), action
            assert data["reason"]


class TestSchedulerDemo:
    def test_top_level_keys(self):
        for key in ("schedule", "posting_order", "topic_diversity_score",
                    "time_gap_analysis", "decay_visualization",
                    "overall_strategy"):
            assert key in SCHEDULER_DEMO

    def test_schedule_items(self):
        assert SCHEDULER_DEMO["schedule"]
        for item in SCHEDULER_DEMO["schedule"]:
            for key in ("position", "topic_summary", "recommended_time",
                        "recommended_day", "reason", "decay_from_previous",
                        "expected_visibility"):
                assert key in item
            # tab_scheduler 는 decay 를 st.progress(min(float(decay), 1.0)) 로 그린다.
            assert 0.0 <= float(item["decay_from_previous"]) <= 1.0

    def test_posting_order_matches_schedule(self):
        positions = {item["position"] for item in SCHEDULER_DEMO["schedule"]}
        assert set(SCHEDULER_DEMO["posting_order"]) == positions

    def test_decay_visualization(self):
        for entry in SCHEDULER_DEMO["decay_visualization"]:
            assert {"post", "visibility_percent"} <= entry.keys()
            assert 0 <= entry["visibility_percent"] <= 100


class TestRiskDemo:
    def test_top_level_keys(self):
        for key in ("risk_level", "risk_score", "summary", "risk_items",
                    "risky_phrases", "safe_version", "checklist"):
            assert key in RISK_DEMO

    def test_risk_level_valid(self):
        assert RISK_DEMO["risk_level"] in ("low", "medium", "high", "critical")
        assert 0 <= RISK_DEMO["risk_score"] <= 100

    def test_risk_items_shape(self):
        assert RISK_DEMO["risk_items"], "데모는 위험 항목이 있어야 UI 가치를 보여준다"
        for item in RISK_DEMO["risk_items"]:
            assert item["category"] in (
                "monetization", "suspension", "visibility", "backlash"
            )
            assert item["severity"] in ("low", "medium", "high", "critical")
            for key in ("category_label", "description"):
                assert key in item

    def test_risky_phrases_shape(self):
        assert RISK_DEMO["risky_phrases"]
        for rp in RISK_DEMO["risky_phrases"]:
            for key in ("phrase", "reason", "suggestion"):
                assert key in rp

    def test_checklist_min_items(self):
        assert len(RISK_DEMO["checklist"]) >= 6
        for entry in RISK_DEMO["checklist"]:
            assert {"item", "passed", "note"} <= entry.keys()
            assert isinstance(entry["passed"], bool)
