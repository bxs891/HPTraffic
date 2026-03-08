from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, model_validator

from hptraffic.content_hash import build_content_hash


class PostSchema(BaseModel):
    source: str
    source_post_id: str
    url: str
    author: str
    title: str
    content: str
    lang: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    content_hash: str | None = None

    @model_validator(mode="after")
    def ensure_content_hash(self) -> "PostSchema":
        if not self.content_hash:
            self.content_hash = build_content_hash(title=self.title, content=self.content)
        return self
