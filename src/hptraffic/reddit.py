from __future__ import annotations

import time
from typing import Callable, Protocol

from .models import Post


class RedditCollectorError(RuntimeError):
    """Raised when collecting from Reddit fails after retries."""


class RedditClientProtocol(Protocol):
    """Abstraction for Reddit API clients."""

    def fetch_new(self, subreddit: str, limit: int) -> list[dict]:
        """Fetch raw posts for a subreddit."""


class RedditCollector:
    def __init__(
        self,
        client: RedditClientProtocol,
        requests_per_second: int = 5,
        max_retries: int = 3,
        backoff_base_seconds: float = 0.5,
        time_provider: Callable[[], float] | None = None,
        sleep_func: Callable[[float], None] | None = None,
    ) -> None:
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")
        if max_retries <= 0:
            raise ValueError("max_retries must be positive")

        self._client = client
        self._requests_per_second = requests_per_second
        self._max_retries = max_retries
        self._backoff_base_seconds = backoff_base_seconds
        self._time = time_provider or time.monotonic
        self._sleep = sleep_func or time.sleep
        self._min_interval = 1.0 / float(requests_per_second)
        self._last_request_at = 0.0

    def fetch_posts(
        self,
        subreddits: list[str],
        limit: int,
        keywords: list[str] | None = None,
    ) -> list[Post]:
        if limit <= 0:
            return []

        normalized_keywords = [k.lower() for k in (keywords or []) if k.strip()]
        posts: list[Post] = []

        for subreddit in subreddits:
            raw_posts = self._fetch_subreddit_with_retry(subreddit, limit)
            for raw in raw_posts:
                post = self._normalize_post(raw, subreddit)
                if self._matches_keywords(post, normalized_keywords):
                    posts.append(post)

        return posts

    def _fetch_subreddit_with_retry(self, subreddit: str, limit: int) -> list[dict]:
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            self._apply_rate_limit()
            try:
                return self._client.fetch_new(subreddit=subreddit, limit=limit)
            except Exception as exc:  # noqa: BLE001 - network/client exceptions vary
                last_error = exc
                if attempt >= self._max_retries:
                    break
                wait_seconds = self._backoff_base_seconds * (2 ** (attempt - 1))
                self._sleep(wait_seconds)

        raise RedditCollectorError(
            f"failed to fetch posts from r/{subreddit} after {self._max_retries} attempts"
        ) from last_error

    def _apply_rate_limit(self) -> None:
        now = self._time()
        elapsed = now - self._last_request_at

        if elapsed < self._min_interval:
            self._sleep(self._min_interval - elapsed)
            now = self._time()

        self._last_request_at = now

    def _matches_keywords(self, post: Post, keywords: list[str]) -> bool:
        if not keywords:
            return True
        haystack = f"{post.title}\n{post.content}".lower()
        return any(keyword in haystack for keyword in keywords)

    def _normalize_post(self, raw: dict, subreddit: str) -> Post:
        return Post(
            source="reddit",
            external_id=str(raw.get("id", "")),
            subreddit=subreddit,
            title=str(raw.get("title", "")),
            content=str(raw.get("selftext", "")),
            url=str(raw.get("url", "")),
            author=str(raw.get("author", "")),
            created_utc=float(raw.get("created_utc", 0.0)),
            raw=raw,
        )
