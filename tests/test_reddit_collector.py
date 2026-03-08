import sqlite3

import pytest

from hptraffic.models import Post
from hptraffic.reddit import RedditCollector, RedditCollectorError
from hptraffic.repository import PostRepository
from hptraffic.tasks import RedditCollectionConfig, collect_reddit_posts


class FakeClient:
    def __init__(self, payloads=None, failures=0):
        self.payloads = payloads or {}
        self.failures = failures
        self.calls = 0

    def fetch_new(self, subreddit: str, limit: int) -> list[dict]:
        self.calls += 1
        if self.failures > 0:
            self.failures -= 1
            raise RuntimeError("temporary failure")
        return self.payloads.get(subreddit, [])[:limit]


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def test_fetch_posts_supports_keyword_filtering_and_schema() -> None:
    client = FakeClient(
        payloads={
            "python": [
                {
                    "id": "1",
                    "title": "Celery retry tips",
                    "selftext": "contains details",
                    "url": "https://example.com/1",
                    "author": "alice",
                    "created_utc": 1700000000,
                },
                {
                    "id": "2",
                    "title": "Unrelated",
                    "selftext": "no match",
                    "url": "https://example.com/2",
                    "author": "bob",
                    "created_utc": 1700000001,
                },
            ]
        }
    )

    collector = RedditCollector(client=client)
    posts = collector.fetch_posts(["python"], limit=10, keywords=["retry"])

    assert len(posts) == 1
    assert isinstance(posts[0], Post)
    assert posts[0].source == "reddit"
    assert posts[0].external_id == "1"


def test_retry_with_exponential_backoff_then_success() -> None:
    clock = FakeClock()
    client = FakeClient(payloads={"python": [{"id": "ok"}]}, failures=2)
    collector = RedditCollector(
        client=client,
        max_retries=3,
        backoff_base_seconds=0.5,
        requests_per_second=100,
        time_provider=clock.time,
        sleep_func=clock.sleep,
    )

    posts = collector.fetch_posts(["python"], limit=1)

    assert len(posts) == 1
    assert client.calls == 3
    assert 0.5 in clock.sleeps
    assert 1.0 in clock.sleeps


def test_retry_raises_after_max_attempts() -> None:
    client = FakeClient(failures=3)
    collector = RedditCollector(client=client, max_retries=3)

    with pytest.raises(RedditCollectorError):
        collector.fetch_posts(["python"], limit=5)


def test_rate_limit_enforces_min_interval() -> None:
    clock = FakeClock()
    client = FakeClient(payloads={"a": [{"id": "1"}], "b": [{"id": "2"}]})
    collector = RedditCollector(
        client=client,
        requests_per_second=1,
        time_provider=clock.time,
        sleep_func=clock.sleep,
    )

    collector.fetch_posts(["a", "b"], limit=1)

    assert any(s >= 1.0 for s in clock.sleeps)


def test_collect_reddit_posts_task_is_idempotent() -> None:
    client = FakeClient(payloads={"python": [{"id": "1", "title": "T"}]})
    collector = RedditCollector(client=client)
    repository = PostRepository(sqlite3.connect(":memory:"))
    config = RedditCollectionConfig(subreddits=["python"], limit=10)

    inserted_first = collect_reddit_posts(config, collector, repository)
    inserted_second = collect_reddit_posts(config, collector, repository)

    assert inserted_first == 1
    assert inserted_second == 0
    assert repository.count_posts() == 1
