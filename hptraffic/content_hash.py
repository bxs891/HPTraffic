from __future__ import annotations

import hashlib
import re

_URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", flags=re.IGNORECASE)
_WHITESPACE_PATTERN = re.compile(r"\s+")


def normalize_post_text(title: str, content: str) -> str:
    merged = f"{title}\n{content}".lower()
    without_urls = _URL_PATTERN.sub("", merged)
    return _WHITESPACE_PATTERN.sub("", without_urls)


def build_content_hash(title: str, content: str) -> str:
    normalized_text = normalize_post_text(title=title, content=content)
    return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
