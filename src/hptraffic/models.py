from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Post:
    """Normalized schema for collected posts from any source."""

    source: str
    external_id: str
    subreddit: str
    title: str
    content: str
    url: str
    author: str
    created_utc: float
    raw: dict[str, Any] = field(default_factory=dict)
