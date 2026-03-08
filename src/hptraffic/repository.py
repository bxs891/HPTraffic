from __future__ import annotations

import sqlite3

from .models import Post


class PostRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                external_id TEXT NOT NULL,
                subreddit TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                url TEXT NOT NULL,
                author TEXT NOT NULL,
                created_utc REAL NOT NULL,
                UNIQUE(source, external_id)
            )
            """
        )
        self._connection.commit()

    def save_posts(self, posts: list[Post]) -> int:
        if not posts:
            return 0

        inserted = 0
        cursor = self._connection.cursor()

        for post in posts:
            cursor.execute(
                """
                INSERT OR IGNORE INTO posts (
                    source, external_id, subreddit, title, content, url, author, created_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    post.source,
                    post.external_id,
                    post.subreddit,
                    post.title,
                    post.content,
                    post.url,
                    post.author,
                    post.created_utc,
                ),
            )
            if cursor.rowcount > 0:
                inserted += 1

        self._connection.commit()
        return inserted

    def count_posts(self) -> int:
        row = self._connection.execute("SELECT COUNT(*) FROM posts").fetchone()
        return int(row[0])
