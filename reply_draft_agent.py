from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
import re


SENSITIVE_PATTERNS = [
    r"违法", r"洗钱", r"诈骗", r"仇恨", r"成人", r"博彩", r"枪支", r"毒品", r"骚扰",
]


@dataclass(frozen=True)
class LengthRange:
    min_chars: int = 80
    max_chars: int = 200

    @classmethod
    def from_config(cls, config: Dict[str, Any] | None) -> "LengthRange":
        if not config:
            return cls()
        min_chars = int(config.get("min_chars", cls.min_chars))
        max_chars = int(config.get("max_chars", cls.max_chars))
        if min_chars < 1:
            min_chars = 1
        if max_chars < min_chars:
            max_chars = min_chars
        return cls(min_chars=min_chars, max_chars=max_chars)


class ReplyDraftAgent:
    """Generate short reply variants and follow-up questions for a lead."""

    def generate(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        requirement = self._clean_text(lead.get("requirement_summary", "").strip())
        category = self._clean_text(lead.get("category", "").strip())
        original_post = self._clean_text(lead.get("original_post", "").strip())
        config = lead.get("config", {}) or {}

        capability = self._clean_text(config.get("service_capability", "").strip())
        length_range = LengthRange.from_config(config)

        context = self._build_context(requirement, category, original_post)
        variants = [
            {"tone": "concise", "text": self._build_reply("concise", context, capability, length_range)},
            {"tone": "friendly", "text": self._build_reply("friendly", context, capability, length_range)},
            {"tone": "professional", "text": self._build_reply("professional", context, capability, length_range)},
        ]

        return {
            "reply_variants": variants,
            "key_questions": self._build_key_questions(requirement, category),
            "cta": self._build_cta(category),
        }

    def _build_context(self, requirement: str, category: str, original_post: str) -> str:
        parts = [p for p in [category, requirement] if p]
        if not parts and original_post:
            parts.append(original_post[:40])
        return "，".join(parts) if parts else "你的需求"

    def _build_reply(self, tone: str, context: str, capability: str, length_range: LengthRange) -> str:
        if tone == "concise":
            text = (
                f"看了你的需求（{context}），方向很清晰。"
                f"我这边可提供{capability or '需求梳理、方案设计与落地支持'}，会先给出可执行的分步方案与预估周期，"
                "确认后再推进实施，过程透明、可随时校准。"
            )
        elif tone == "friendly":
            text = (
                f"这个需求我认真看过啦（{context}），挺有价值。"
                f"如果你愿意，我们可以先快速对齐目标与优先级；我能提供{capability or '从思路到执行的完整支持'}，"
                "先小步试跑，确认效果后再扩大，尽量帮你省时间和试错成本。"
            )
        else:
            text = (
                f"感谢分享需求（{context}）。"
                f"基于当前信息，我可以提供{capability or '结构化评估、执行方案及阶段性交付'}，"
                "并以里程碑方式推进，先明确范围、时间与验收标准，再进入执行，以确保产出可衡量、可复盘。"
            )

        safe = self._clean_text(text)
        return self._fit_length(safe, length_range)

    def _build_key_questions(self, requirement: str, category: str) -> List[str]:
        q1 = f"这次最优先要解决的目标是什么？是否有明确的截止时间？"
        q2 = f"目前已有的素材、数据或系统基础有哪些，可直接复用吗？"
        q3 = f"对于{category or '该项目'}，你更看重速度、预算，还是效果稳定性？"
        return [q1, q2, q3]

    def _build_cta(self, category: str) -> str:
        subject = category or "需求"
        return f"如果方便，先约一个15分钟沟通，我会基于{subject}给你一版可执行的下一步建议。"

    def _fit_length(self, text: str, length_range: LengthRange) -> str:
        text = text.strip()
        if len(text) > length_range.max_chars:
            return text[: length_range.max_chars - 1].rstrip("，、；： ") + "。"

        if len(text) >= length_range.min_chars:
            return text

        fillers = [
            "也欢迎你补充限制条件，我会据此微调方案。",
            "这样你能更快判断是否值得继续投入。",
            "沟通后我可当天给出首版建议。",
        ]
        for filler in fillers:
            if len(text) >= length_range.min_chars:
                break
            candidate = text + filler
            if len(candidate) <= length_range.max_chars:
                text = candidate
        return text

    def _clean_text(self, text: str) -> str:
        compact = re.sub(r"\s+", " ", text)
        for pattern in SENSITIVE_PATTERNS:
            compact = re.sub(pattern, "[已过滤]", compact, flags=re.IGNORECASE)
        # Avoid aggressive marketing expressions
        compact = compact.replace("保证成功", "尽力达成")
        compact = compact.replace("绝对", "尽量")
        return compact.strip()


__all__ = ["ReplyDraftAgent"]
