from __future__ import annotations

from typing import Any

from moderation_service import ModerationService


class LeadPipeline:
    def __init__(self, moderation_service: ModerationService | None = None) -> None:
        self.moderation_service = moderation_service or ModerationService()

    def process_lead(self, lead: dict[str, Any]) -> dict[str, Any]:
        """在 lead 推送前执行审核和优先级降级。"""
        content = str(lead.get("content", ""))
        moderation = self.moderation_service.check_text(content)

        lead["moderation"] = moderation

        if not moderation["allowed"]:
            lead["status"] = "blocked"
            lead["push"] = False
            return lead

        if moderation["needs_review"]:
            lead["status"] = "pending_manual_review"
            lead["manual_review"] = True
            lead["priority"] = self._downgrade_priority(lead.get("priority", "normal"))
            lead["push"] = True
            return lead

        lead["status"] = "ready"
        lead["manual_review"] = False
        lead["push"] = True
        return lead

    @staticmethod
    def _downgrade_priority(priority: str) -> str:
        levels = ["low", "normal", "high", "urgent"]
        if priority not in levels:
            return "low"

        idx = levels.index(priority)
        return levels[max(0, idx - 1)]
