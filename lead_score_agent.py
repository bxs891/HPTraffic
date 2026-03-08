from __future__ import annotations

from typing import Any, Dict, List
import re


CATEGORIES = {
    "automation": ["automation", "automate", "workflow", "rpa", "zapier", "make.com"],
    "scraping": ["scrap", "crawl", "crawler", "selenium", "playwright", "数据抓取"],
    "chatbot": ["chatbot", "bot", "llm", "gpt", "assistant", "客服机器人"],
    "marketing": ["marketing", "growth", "ads", "seo", "投放", "营销"],
    "data": ["data", "etl", "pipeline", "dashboard", "bi", "analytics", "分析"],
}

SENSITIVE_KEYWORDS = [
    "adult", "gambling", "weapon", "exploit", "phishing", "fraud", "违法", "黑灰产", "洗钱", "博彩",
]

BUDGET_PATTERN = re.compile(r"\$\s?\d+[kK]?|\d+\s?(usd|dollars|美金|元)", re.IGNORECASE)
TIMELINE_PATTERN = re.compile(r"\b(\d+\s?(day|days|week|weeks|month|months)|asap|urgent|本周|下周|月底)\b", re.IGNORECASE)


def _to_text(post: Dict[str, Any]) -> str:
    parts = [str(post.get("title", "")), str(post.get("content", "")), str(post.get("text", ""))]
    return " ".join(parts).strip().lower()


def _detect_category(text: str, detect: Dict[str, Any]) -> str:
    if detect.get("category") in set(CATEGORIES) | {"other"}:
        return detect["category"]
    for category, words in CATEGORIES.items():
        if any(word in text for word in words):
            return category
    return "other"


def _has_detail_signal(text: str, detect: Dict[str, Any]) -> bool:
    detail_fields = [
        detect.get("tech_stack"),
        detect.get("requirements"),
        detect.get("scope"),
        detect.get("deliverables"),
    ]
    if any(field for field in detail_fields):
        return True
    detail_keywords = ["api", "integration", "backend", "frontend", "postgres", "aws", "docker", "k8s"]
    return sum(1 for k in detail_keywords if k in text) >= 2


def _budget_signal(text: str, detect: Dict[str, Any]) -> int:
    budget = detect.get("budget")
    if isinstance(budget, (int, float)) and budget > 0:
        if budget >= 5000:
            return 9
        if budget >= 2000:
            return 7
        if budget >= 500:
            return 5
        return 3
    if isinstance(budget, str) and budget.strip():
        return 7
    if BUDGET_PATTERN.search(text):
        return 6
    return 2


def _urgency_signal(text: str, detect: Dict[str, Any]) -> int:
    urgency = detect.get("urgency")
    if isinstance(urgency, (int, float)):
        return max(1, min(10, int(urgency)))
    if TIMELINE_PATTERN.search(text):
        return 8
    return 4


def _is_b2b(text: str, detect: Dict[str, Any]) -> bool:
    if isinstance(detect.get("is_b2b"), bool):
        return detect["is_b2b"]
    b2b_keywords = ["saas", "crm", "enterprise", "team", "ops", "客户", "公司", "business"]
    return any(k in text for k in b2b_keywords)


def _risk_penalty(text: str, detect: Dict[str, Any]) -> int:
    risk = detect.get("risk_level")
    if isinstance(risk, (int, float)):
        return int(max(0, min(30, risk * 3)))
    if any(k in text for k in SENSITIVE_KEYWORDS):
        return 25
    return 0


def _estimated_value(score: int, budget_signal: int) -> int:
    value = int(score * 100 + budget_signal * 250)
    return max(0, min(10000, value))


def _priority(score: int) -> str:
    if score >= 80:
        return "P0"
    if score >= 60:
        return "P1"
    return "P2"


def score_lead(post: Dict[str, Any], lead_detect: Dict[str, Any]) -> Dict[str, Any]:
    """Score a potential lead from post content and lead detection output.

    Returns a JSON-serializable dictionary with score, priority, category,
    estimated_value_usd, urgency, budget_signal, and reasoning bullets.
    """

    text = _to_text(post)
    category = _detect_category(text, lead_detect)
    is_b2b = _is_b2b(text, lead_detect)
    budget_signal = _budget_signal(text, lead_detect)
    urgency = _urgency_signal(text, lead_detect)
    detailed = _has_detail_signal(text, lead_detect)

    score = 35
    reasons: List[str] = []

    if is_b2b:
        score += 20
        reasons.append("B2B 场景加分")
    else:
        score -= 5
        reasons.append("偏 B2C，转化价值相对较低")

    if budget_signal >= 6:
        score += 15
        reasons.append("有明确预算信号")
    else:
        score -= 5
        reasons.append("预算信息较模糊")

    if urgency >= 7:
        score += 10
        reasons.append("时间窗口明确且较紧")
    elif urgency <= 3:
        score -= 4
        reasons.append("紧迫度较低")

    if detailed:
        score += 15
        reasons.append("需求/技术栈描述较具体")
    else:
        score -= 8
        reasons.append("需求描述偏泛")

    risk_penalty = _risk_penalty(text, lead_detect)
    if risk_penalty > 0:
        score -= risk_penalty
        reasons.append("存在敏感/高风险内容，降权处理")

    score = max(0, min(100, int(score)))

    return {
        "score": score,
        "priority": _priority(score),
        "category": category,
        "estimated_value_usd": _estimated_value(score, budget_signal),
        "urgency": urgency,
        "budget_signal": budget_signal,
        "reasoning_bullets": reasons,
    }
