from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PROMPT_TEMPLATE = """你是 LeadDetectAgent。请基于输入的 normalized post 判断是否是商机线索。

请严格输出 JSON，不要输出任何额外文本，字段如下：
{
  "is_lead": boolean,
  "confidence": 0-100,
  "lead_type": "b2b_service"|"b2c_product"|"hiring"|"unknown",
  "need_summary": "一句话概括需求",
  "buyer_signals": ["..."],
  "disqualifiers": ["..."]
}

判定规则：
- 明确在找工具/服务/外包/供应商 = 高优先
- 纯讨论/吐槽/新闻转发 = 低
- 学生作业、无预算、非真实购买意图 = 排除
"""


@dataclass
class LeadDetectionResult:
    is_lead: bool
    confidence: int
    lead_type: str
    need_summary: str
    buyer_signals: list[str]
    disqualifiers: list[str]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "is_lead": self.is_lead,
            "confidence": self.confidence,
            "lead_type": self.lead_type,
            "need_summary": self.need_summary,
            "buyer_signals": self.buyer_signals,
            "disqualifiers": self.disqualifiers,
        }


class LeadDetectAgent:
    """A lightweight service-style lead detector for normalized posts."""

    def __init__(self, prompt_template: str = PROMPT_TEMPLATE):
        self.prompt_template = prompt_template

    def detect(self, normalized_post: str) -> dict[str, Any]:
        text = (normalized_post or "").strip()
        lowered = text.lower()

        buyer_signals: list[str] = []
        disqualifiers: list[str] = []

        lead_type = "unknown"
        confidence = 40

        high_priority_keywords = [
            "looking for",
            "need",
            "seeking",
            "vendor",
            "supplier",
            "outsource",
            "agency",
            "service provider",
            "采购",
            "求推荐",
            "外包",
            "供应商",
            "找",
        ]

        b2b_keywords = [
            "crm",
            "saas",
            "api",
            "automation",
            "analytics",
            "开发团队",
            "企业",
            "服务商",
            "系统",
        ]

        b2c_keywords = [
            "buy",
            "purchase",
            "recommend product",
            "which brand",
            "哪里买",
            "求购",
        ]

        hiring_keywords = ["hiring", "recruit", "招聘", "招人", "headcount"]

        discussion_keywords = [
            "rant",
            "just discussing",
            "thoughts?",
            "news",
            "转发",
            "吐槽",
            "讨论",
            "新闻",
        ]

        exclusion_keywords = [
            "homework",
            "assignment",
            "student project",
            "no budget",
            "just curious",
            "for fun",
            "作业",
            "学生",
            "没预算",
            "无预算",
            "仅讨论",
            "不买",
        ]

        if any(k in lowered for k in high_priority_keywords):
            buyer_signals.append("明确表达在寻找工具/服务/供应商")
            confidence += 30

        if any(k in lowered for k in b2b_keywords):
            lead_type = "b2b_service"
            buyer_signals.append("需求偏企业服务/B2B")
            confidence += 20

        if any(k in lowered for k in b2c_keywords) and lead_type == "unknown":
            lead_type = "b2c_product"
            buyer_signals.append("需求偏消费品购买")
            confidence += 15

        if any(k in lowered for k in hiring_keywords):
            lead_type = "hiring"
            buyer_signals.append("明确存在招聘需求")
            confidence += 10

        if any(k in lowered for k in discussion_keywords):
            disqualifiers.append("内容偏讨论/吐槽/新闻，购买意图弱")
            confidence -= 20

        if any(k in lowered for k in exclusion_keywords):
            disqualifiers.append("存在排除信号（学生作业/无预算/非真实购买意图）")
            confidence -= 60

        confidence = max(0, min(100, confidence))

        is_lead = confidence >= 60 and not any("排除信号" in d for d in disqualifiers)

        if not text:
            need_summary = "无有效需求信息"
            is_lead = False
            confidence = 0
            lead_type = "unknown"
        elif is_lead:
            need_summary = "发布者明确在寻求可执行的采购/服务方案"
        else:
            need_summary = "当前内容购买意图不足或存在排除条件"

        result = LeadDetectionResult(
            is_lead=is_lead,
            confidence=confidence,
            lead_type=lead_type,
            need_summary=need_summary,
            buyer_signals=buyer_signals,
            disqualifiers=disqualifiers,
        )
        return result.to_json_dict()
