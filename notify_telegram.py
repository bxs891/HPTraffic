import os
from dataclasses import asdict, is_dataclass
from typing import Iterable, Mapping, Any

import requests


class TelegramNotifier:
    """Telegram 通知客户端。"""

    def __init__(self, bot_token: str | None = None, chat_id: str | None = None, timeout: int = 10):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("CHAT_ID")
        if not self.bot_token or not self.chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN 和 CHAT_ID 必须通过环境变量提供")

        self.timeout = timeout
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    @staticmethod
    def _lead_to_dict(lead: Any) -> dict[str, Any]:
        if isinstance(lead, Mapping):
            return dict(lead)
        if is_dataclass(lead):
            return asdict(lead)
        return {
            "source": getattr(lead, "source", ""),
            "title": getattr(lead, "title", ""),
            "summary": getattr(lead, "summary", ""),
            "score": getattr(lead, "score", ""),
            "priority": getattr(lead, "priority", ""),
            "url": getattr(lead, "url", ""),
            "reply_points": getattr(lead, "reply_points", ""),
        }

    @staticmethod
    def _format_reply_points(reply_points: Any) -> str:
        if isinstance(reply_points, (list, tuple)):
            if not reply_points:
                return "暂无"
            return "\n".join(f"- {item}" for item in reply_points)
        if not reply_points:
            return "暂无"
        return str(reply_points)

    def _send_message(self, text: str) -> dict[str, Any]:
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "disable_web_page_preview": True,
        }
        response = requests.post(self.api_url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram API error: {data}")
        return data

    def send_lead(self, lead: Any) -> dict[str, Any]:
        lead_data = self._lead_to_dict(lead)

        title_or_summary = lead_data.get("title") or lead_data.get("summary") or "(无标题)"
        reply_points = self._format_reply_points(
            lead_data.get("reply_points") or lead_data.get("suggested_reply_points")
        )

        message = (
            "📣 高优先级线索提醒\n"
            f"来源：{lead_data.get('source', '未知')}\n"
            f"标题/摘要：{title_or_summary}\n"
            f"Score：{lead_data.get('score', 'N/A')}\n"
            f"Priority：{lead_data.get('priority', 'N/A')}\n"
            f"URL：{lead_data.get('url', 'N/A')}\n"
            f"建议回复要点：\n{reply_points}"
        )
        return self._send_message(message)

    def send_daily_digest(self, leads: Iterable[Any]) -> dict[str, Any]:
        lead_items = [self._lead_to_dict(item) for item in leads]
        if not lead_items:
            return self._send_message("🗓️ 今日线索摘要\n暂无新增线索。")

        lines = ["🗓️ 今日线索摘要"]
        for idx, item in enumerate(lead_items, start=1):
            title_or_summary = item.get("title") or item.get("summary") or "(无标题)"
            lines.append(
                f"{idx}. [{item.get('priority', 'N/A')}] {title_or_summary} "
                f"(score={item.get('score', 'N/A')})"
            )
            if item.get("url"):
                lines.append(f"   {item['url']}")

        return self._send_message("\n".join(lines))
