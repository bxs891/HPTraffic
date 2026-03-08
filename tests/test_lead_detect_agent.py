from lead_detect_agent import LeadDetectAgent


def test_high_priority_b2b_service_lead():
    agent = LeadDetectAgent()
    result = agent.detect("We are looking for a CRM automation vendor for our sales team, budget approved.")
    assert result["is_lead"] is True
    assert 75 <= result["confidence"] <= 100


def test_b2c_purchase_lead():
    agent = LeadDetectAgent()
    result = agent.detect("求推荐一款适合小户型的空气净化器，准备这周购买。")
    assert result["is_lead"] is True
    assert 60 <= result["confidence"] <= 95


def test_hiring_signal_lead():
    agent = LeadDetectAgent()
    result = agent.detect("We are hiring a freelance UI agency to redesign our app landing page.")
    assert result["is_lead"] is True
    assert 60 <= result["confidence"] <= 100


def test_discussion_not_lead():
    agent = LeadDetectAgent()
    result = agent.detect("Just discussing the latest AI news, thoughts?")
    assert result["is_lead"] is False
    assert 0 <= result["confidence"] <= 45


def test_student_no_budget_disqualified():
    agent = LeadDetectAgent()
    result = agent.detect("学生作业，想了解一下电商运营工具，没预算，只是作业调研。")
    assert result["is_lead"] is False
    assert 0 <= result["confidence"] <= 40
