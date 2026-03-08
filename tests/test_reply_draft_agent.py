from reply_draft_agent import ReplyDraftAgent


def test_generate_structure_and_tones():
    agent = ReplyDraftAgent()
    lead = {
        "original_post": "我们想做一个小程序，先验证市场。",
        "requirement_summary": "需要从0到1的MVP规划与开发建议",
        "category": "小程序MVP",
        "config": {"service_capability": "MVP范围定义、技术方案和迭代计划"},
    }

    result = agent.generate(lead)

    assert set(result.keys()) == {"reply_variants", "key_questions", "cta"}
    tones = [v["tone"] for v in result["reply_variants"]]
    assert tones == ["concise", "friendly", "professional"]
    assert len(result["key_questions"]) == 3


def test_length_constraints_configurable():
    agent = ReplyDraftAgent()
    lead = {
        "requirement_summary": "需要投放优化",
        "category": "增长",
        "config": {"min_chars": 90, "max_chars": 120},
    }

    result = agent.generate(lead)
    for variant in result["reply_variants"]:
        assert 90 <= len(variant["text"]) <= 120


def test_sensitive_words_filtered():
    agent = ReplyDraftAgent()
    lead = {
        "requirement_summary": "涉及诈骗流程整理",
        "category": "咨询",
        "config": {},
    }

    result = agent.generate(lead)
    all_text = " ".join(v["text"] for v in result["reply_variants"])
    assert "诈骗" not in all_text
    assert "[已过滤]" in all_text
