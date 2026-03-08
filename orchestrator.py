import asyncio
import json
import logging
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents import Agent, Runner, function_tool, handoff, trace

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] trace_id=%(trace_id)s %(message)s",
)


class TraceLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        extra = kwargs.setdefault("extra", {})
        extra.setdefault("trace_id", self.extra.get("trace_id", "-"))
        return msg, kwargs


@dataclass
class WorkflowResult:
    trace_id: str
    topic: str
    posts: list[dict[str, Any]]
    detected: list[dict[str, Any]]
    scored: list[dict[str, Any]]
    notify_result: dict[str, Any]


@function_tool
async def collector_tool(topic: str) -> list[dict[str, Any]]:
    """Collect posts by topic (replace with your real data source)."""
    return [
        {
            "id": "p1",
            "text": f"{topic} 出现了明显拥堵，路况很差。",
            "source": "weibo",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "p2",
            "text": f"{topic} 主路通畅，辅路有轻微排队。",
            "source": "xhs",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    ]


@function_tool
async def detect_tool(posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Detect traffic incident signals from posts."""
    detected: list[dict[str, Any]] = []
    for post in posts:
        text = post.get("text", "")
        level = "low"
        if "拥堵" in text or "路况很差" in text:
            level = "high"
        elif "排队" in text:
            level = "medium"
        detected.append({**post, "incident_level": level})
    return detected


@function_tool
async def score_tool(detected_posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Score detected traffic posts."""
    score_map = {"low": 0.3, "medium": 0.6, "high": 0.9}
    return [
        {
            **post,
            "score": score_map.get(post.get("incident_level", "low"), 0.1),
        }
        for post in detected_posts
    ]


@function_tool
async def notify_tool(scored_posts: list[dict[str, Any]]) -> dict[str, Any]:
    """Notify downstream systems with final scored posts."""
    severe = [p for p in scored_posts if p.get("score", 0) >= 0.8]
    return {
        "status": "sent",
        "message": f"sent {len(scored_posts)} posts, severe={len(severe)}",
    }


agent_score = Agent(
    name="agent_score",
    instructions=(
        "你负责执行打分并通知："
        "1) 调用 score_tool 对 detected_posts 打分；"
        "2) 然后调用 notify_tool 发送通知；"
        "3) 输出 JSON：{scored: [...], notify_result: {...}}。"
    ),
    tools=[score_tool, notify_tool],
)

agent_detect = Agent(
    name="agent_detect",
    instructions=(
        "你负责检测交通事件："
        "1) 调用 detect_tool 处理 posts；"
        "2) handoff 给 agent_score，并把 detected_posts 传下去。"
    ),
    tools=[detect_tool],
    handoffs=[handoff(agent_score)],
)

agent_collect = Agent(
    name="agent_collect",
    instructions=(
        "你负责采集："
        "1) 调用 collector_tool 获取 posts；"
        "2) handoff 给 agent_detect，传递 posts。"
    ),
    tools=[collector_tool],
    handoffs=[handoff(agent_detect)],
)

orchestrator = Agent(
    name="orchestrator",
    instructions=(
        "你是总控 Orchestrator。"
        "从用户 topic 开始，先 handoff 给 agent_collect，"
        "流程必须是 collect -> detect -> score -> notify。"
        "最后返回 JSON，包含 posts、detected、scored、notify_result。"
    ),
    handoffs=[handoff(agent_collect)],
)


def init_db(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS traffic_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                posts_json TEXT NOT NULL,
                detected_json TEXT NOT NULL,
                scored_json TEXT NOT NULL,
                notify_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def persist_result(db_path: Path, result: WorkflowResult) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO traffic_runs (
                trace_id, topic, posts_json, detected_json, scored_json, notify_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.trace_id,
                result.topic,
                json.dumps(result.posts, ensure_ascii=False),
                json.dumps(result.detected, ensure_ascii=False),
                json.dumps(result.scored, ensure_ascii=False),
                json.dumps(result.notify_result, ensure_ascii=False),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


async def run_once(topic: str, db_path: str = "traffic_runs.db") -> WorkflowResult:
    init_db(Path(db_path))

    with trace("hp-traffic-orchestrator") as tr:
        trace_id = getattr(tr, "trace_id", None) or getattr(tr, "id", None) or str(uuid.uuid4())
        logger = TraceLoggerAdapter(logging.getLogger("orchestrator"), {"trace_id": trace_id})
        logger.info("workflow started")

        input_payload = f"topic={topic}"
        run_result = await Runner.run(orchestrator, input=input_payload)

        data = json.loads(run_result.final_output)
        workflow = WorkflowResult(
            trace_id=trace_id,
            topic=topic,
            posts=data["posts"],
            detected=data["detected"],
            scored=data["scored"],
            notify_result=data["notify_result"],
        )

        persist_result(Path(db_path), workflow)
        logger.info("workflow finished and persisted to db")
        return workflow


if __name__ == "__main__":
    result = asyncio.run(run_once(topic="北京朝阳路"))
    print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
