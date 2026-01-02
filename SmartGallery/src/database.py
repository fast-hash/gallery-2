"""SQLite data layer for Smart Gallery.

The database is lightweight and mobile-friendly, and uses simple context
managers to keep connections short-lived. Tables are created on first use.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, List, Sequence

from .config import settings


class Database:
    """Thin wrapper around SQLite with helper methods for the app."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or settings.db_path
        self._ensure_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON;")
        return connection

    def _ensure_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    description TEXT DEFAULT '',
                    processed_flag INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                );

                CREATE TABLE IF NOT EXISTS image_tags (
                    image_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    PRIMARY KEY (image_id, tag_id),
                    FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
                );
                """
            )

    def add_image(
        self, path: Path, description: str = "", processed_flag: bool = False
    ) -> int:
        """Insert an image row or return the existing id if already stored."""

        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO images (path, description, processed_flag)
                VALUES (?, ?, ?);
                """,
                (str(path), description, int(processed_flag)),
            )
            if cursor.lastrowid:
                return int(cursor.lastrowid)

            existing = conn.execute(
                "SELECT id FROM images WHERE path = ?;", (str(path),)
            ).fetchone()
            return int(existing["id"]) if existing else 0

    def update_image_metadata(
        self, image_id: int, description: str, processed_flag: bool = True
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE images
                SET description = ?, processed_flag = ?
                WHERE id = ?;
                """,
                (description, int(processed_flag), image_id),
            )

    def upsert_tags(self, names: Sequence[str]) -> List[int]:
        """Ensure tags exist and return their ids."""

        cleaned_names = [name.strip() for name in names if name.strip()]
        if not cleaned_names:
            return []

        tag_ids: list[int] = []
        with self._connect() as conn:
            for name in cleaned_names:
                cursor = conn.execute(
                    "INSERT OR IGNORE INTO tags (name) VALUES (?);", (name,)
                )
                if cursor.lastrowid:
                    tag_ids.append(int(cursor.lastrowid))
                else:
                    row = conn.execute(
                        "SELECT id FROM tags WHERE name = ?;", (name,)
                    ).fetchone()
                    if row:
                        tag_ids.append(int(row["id"]))
        return tag_ids

    def link_tags_to_image(self, image_id: int, tag_ids: Iterable[int]) -> None:
        ids = list(tag_ids)
        if not ids:
            return

        with self._connect() as conn:
            conn.executemany(
                "INSERT OR IGNORE INTO image_tags (image_id, tag_id) VALUES (?, ?);",
                [(image_id, tag_id) for tag_id in ids],
            )

    def get_images(self, limit: int = 100, offset: int = 0) -> List[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, path, description, processed_flag, created_at
                FROM images
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?;
                """,
                (limit, offset),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_tags_for_image(self, image_id: int) -> List[str]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT t.name
                FROM tags t
                JOIN image_tags it ON it.tag_id = t.id
                WHERE it.image_id = ?
                ORDER BY t.name ASC;
                """,
                (image_id,),
            ).fetchall()
        return [row["name"] for row in rows]

    def clear_tags(self, image_id: int) -> None:
        """Remove all tag associations for an image to allow overwriting."""
        with self._connect() as conn:
            conn.execute("DELETE FROM image_tags WHERE image_id = ?;", (image_id,))

    def get_image_details(self, image_id: int) -> dict | None:
        """Return a single image row along with its tags."""
        with self._connect() as conn:
            image_row = conn.execute(
                """
                SELECT id, path, description, processed_flag, created_at
                FROM images
                WHERE id = ?;
                """,
                (image_id,),
            ).fetchone()
            if not image_row:
                return None

            tags = conn.execute(
                """
                SELECT t.name
                FROM tags t
                JOIN image_tags it ON it.tag_id = t.id
                WHERE it.image_id = ?
                ORDER BY t.name ASC;
                """,
                (image_id,),
            ).fetchall()

        details = dict(image_row)
        details["tags"] = [row["name"] for row in tags]
        return details

    def search_images(self, query: str, limit: int = 100, offset: int = 0) -> List[dict]:
        """Search images by description or tag name using a LIKE pattern."""
        pattern = f"%{query.strip()}%"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT i.id, i.path, i.description, i.processed_flag, i.created_at
                FROM images i
                LEFT JOIN image_tags it ON i.id = it.image_id
                LEFT JOIN tags t ON t.id = it.tag_id
                WHERE i.description LIKE ? OR t.name LIKE ?
                ORDER BY i.created_at DESC
                LIMIT ? OFFSET ?;
                """,
                (pattern, pattern, limit, offset),
            ).fetchall()
        return [dict(row) for row in rows]
