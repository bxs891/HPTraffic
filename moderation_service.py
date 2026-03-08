from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from openai import OpenAI


@dataclass
class ModerationService:
    """文本审核服务：先规则黑名单，再调用 OpenAI moderation。"""

    model: str = "omni-moderation-latest"
    client: OpenAI = field(default_factory=OpenAI)

    _blacklist: dict[str, set[str]] = field(
        default_factory=lambda: {
            "violence": {
                "杀人",
                "爆炸",
                "砍死",
                "枪击",
                "袭击",
                "恐怖袭击",
            },
            "hate": {
                "种族灭绝",
                "仇恨言论",
                "歧视",
                "纳粹",
                "清洗",
            },
            "sexual": {
                "色情",
                "裸聊",
                "成人视频",
                "约炮",
                "性交易",
            },
            "privacy": {
                "身份证号",
                "银行卡号",
                "手机号",
                "住址",
                "社保号",
                "信用卡cvv",
            },
        }
    )

    _high_risk_categories: set[str] = field(
        default_factory=lambda: {
            "violence",
            "hate",
            "sexual",
            "sexual/minors",
            "harassment/threatening",
            "violence/graphic",
            "self-harm/instructions",
            "self-harm/intent",
            "illicit/violent",
            "privacy",
        }
    )

    def check_text(self, text: str) -> dict[str, Any]:
        """
        返回结构:
        {
          "allowed": bool,
          "categories": {...},
          "needs_review": bool,
        }
        """
        normalized = (text or "").strip().lower()

        categories: dict[str, bool] = {
            "violence": False,
            "hate": False,
            "sexual": False,
            "privacy": False,
        }

        for category, keywords in self._blacklist.items():
            if any(keyword.lower() in normalized for keyword in keywords):
                categories[category] = True

        try:
            response = self.client.moderations.create(model=self.model, input=text)
            result = response.results[0]
            api_categories = result.categories.model_dump()
            flagged = bool(result.flagged)
        except Exception:
            # API 异常时不直接拦截，保守进入人工复核
            api_categories = {}
            flagged = False
            return {
                "allowed": not any(categories.values()),
                "categories": categories,
                "needs_review": True,
            }

        for key, hit in api_categories.items():
            if hit:
                categories[key] = True

        blacklist_hit = any(
            categories.get(name, False)
            for name in ("violence", "hate", "sexual", "privacy")
        )

        high_risk_hit = flagged and any(
            categories.get(name, False) for name in self._high_risk_categories
        )

        allowed = not (blacklist_hit or high_risk_hit)
        needs_review = high_risk_hit or any(
            categories.get(name, False) for name in self._high_risk_categories
        )

        return {
            "allowed": allowed,
            "categories": categories,
            "needs_review": needs_review,
        }
