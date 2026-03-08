from __future__ import annotations

from dataclasses import dataclass, field

from .reddit import RedditCollector
from .repository import PostRepository


def shared_task(*_args, **_kwargs):
    """Small Celery-compatible decorator used in tests when Celery is unavailable."""

    def decorator(func):
        return func

    return decorator


@dataclass(slots=True)
class RedditCollectionConfig:
    subreddits: list[str]
    limit: int = 20
    keywords: list[str] = field(default_factory=list)


@shared_task(name="collect_reddit_posts")
def collect_reddit_posts(
    config: RedditCollectionConfig,
    collector: RedditCollector,
    repository: PostRepository,
) -> int:
    posts = collector.fetch_posts(
        subreddits=config.subreddits,
        limit=config.limit,
        keywords=config.keywords,
    )
    return repository.save_posts(posts)
