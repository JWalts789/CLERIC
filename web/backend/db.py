"""SQLite-backed result store for persisting CLERIC research results."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class ResultStore:
    """Stores and retrieves CLERIC pipeline results in a local SQLite database."""

    def __init__(self, db_path: str = "data/cleric.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Create the results table if it does not already exist."""
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS results (
                    id                TEXT PRIMARY KEY,
                    query             TEXT NOT NULL,
                    status            TEXT NOT NULL DEFAULT 'complete',
                    result_json       TEXT,
                    mermaid_json      TEXT,
                    created_at        TEXT NOT NULL,
                    duration_seconds  REAL,
                    overall_grade     TEXT,
                    total_tokens_in   INTEGER DEFAULT 0,
                    total_tokens_out  INTEGER DEFAULT 0
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save_result(
        self,
        job_id: str,
        query: str,
        result_dict: dict,
        mermaid_dict: dict,
    ) -> None:
        """Persist a completed pipeline result."""
        overall_grade = result_dict.get("overall_grade", "")
        duration = result_dict.get("duration_seconds", 0.0)
        tokens = result_dict.get("total_tokens", {})
        tokens_in = tokens.get("input", 0) if isinstance(tokens, dict) else 0
        tokens_out = tokens.get("output", 0) if isinstance(tokens, dict) else 0
        created_at = result_dict.get(
            "timestamp", datetime.now(timezone.utc).isoformat()
        )

        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO results
                    (id, query, status, result_json, mermaid_json,
                     created_at, duration_seconds, overall_grade,
                     total_tokens_in, total_tokens_out)
                VALUES (?, ?, 'complete', ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    query,
                    json.dumps(result_dict),
                    json.dumps(mermaid_dict),
                    created_at,
                    duration,
                    overall_grade,
                    tokens_in,
                    tokens_out,
                ),
            )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_result(self, job_id: str) -> dict | None:
        """Return the full result with parsed JSON fields, or ``None``."""
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM results WHERE id = ?", (job_id,)
            ).fetchone()

        if row is None:
            return None

        return self._row_to_full_dict(row)

    def list_results(
        self, limit: int = 20, offset: int = 0
    ) -> tuple[list[dict], int]:
        """Return ``(results_list, total_count)`` for pagination.

        Each item is a summary dict (no full JSON blobs).
        Ordered by ``created_at DESC``.
        """
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row

            total: int = conn.execute(
                "SELECT COUNT(*) FROM results"
            ).fetchone()[0]

            rows = conn.execute(
                """
                SELECT id, query, status, overall_grade, created_at,
                       duration_seconds, total_tokens_in, total_tokens_out
                FROM results
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()

        results = [
            {
                "id": r["id"],
                "query": r["query"],
                "status": r["status"],
                "overall_grade": r["overall_grade"],
                "created_at": r["created_at"],
                "duration_seconds": r["duration_seconds"],
                "total_tokens": r["total_tokens_in"] + r["total_tokens_out"],
            }
            for r in rows
        ]

        return results, total

    def search_results(
        self, query_substring: str, limit: int = 20
    ) -> list[dict]:
        """Return results whose query text contains *query_substring*."""
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT id, query, status, overall_grade, created_at,
                       duration_seconds, total_tokens_in, total_tokens_out
                FROM results
                WHERE query LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (f"%{query_substring}%", limit),
            ).fetchall()

        return [
            {
                "id": r["id"],
                "query": r["query"],
                "status": r["status"],
                "overall_grade": r["overall_grade"],
                "created_at": r["created_at"],
                "duration_seconds": r["duration_seconds"],
                "total_tokens": r["total_tokens_in"] + r["total_tokens_out"],
            }
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_result(self, job_id: str) -> bool:
        """Delete a result and return ``True`` if it existed."""
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM results WHERE id = ?", (job_id,)
            )
            return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_full_dict(row: sqlite3.Row) -> dict:
        """Convert a database row to a full result dict with parsed JSON."""
        result_json = row["result_json"]
        mermaid_json = row["mermaid_json"]

        return {
            "id": row["id"],
            "query": row["query"],
            "status": row["status"],
            "result": json.loads(result_json) if result_json else None,
            "mermaid_diagrams": json.loads(mermaid_json) if mermaid_json else {},
            "created_at": row["created_at"],
            "duration_seconds": row["duration_seconds"],
            "overall_grade": row["overall_grade"],
            "total_tokens_in": row["total_tokens_in"],
            "total_tokens_out": row["total_tokens_out"],
        }
