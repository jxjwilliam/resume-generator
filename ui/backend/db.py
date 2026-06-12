import aiosqlite
import json
import os
from datetime import datetime, timezone
from typing import Optional

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "runs.db")


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'running',
                yaml_file TEXT,
                company TEXT,
                role TEXT,
                tags TEXT,
                theme TEXT,
                jd_snippet TEXT,
                use_llm INTEGER DEFAULT 0,
                output_path TEXT,
                error_log TEXT,
                run_duration_seconds REAL,
                created_at TEXT NOT NULL,
                finished_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_runs_type ON runs(type);
            CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
        """)
        await db.commit()
    finally:
        await db.close()


async def insert_run(run: dict) -> None:
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO runs (id, type, status, yaml_file, company, role,
             tags, theme, jd_snippet, use_llm, created_at)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run["id"], run["type"], run["status"],
                run.get("yaml_file"), run.get("company"), run.get("role"),
                json.dumps(run.get("tags", [])),
                run.get("theme"),
                run.get("jd_snippet"),
                run.get("use_llm", 0),
                run["created_at"],
            ),
        )
        await db.commit()
    finally:
        await db.close()


async def update_run(
    run_id: str,
    status: Optional[str] = None,
    output_path: Optional[str] = None,
    error_log: Optional[str] = None,
    run_duration_seconds: Optional[float] = None,
) -> None:
    db = await get_db()
    try:
        fields = []
        values = []
        if status is not None:
            fields.append("status = ?")
            values.append(status)
        if output_path is not None:
            fields.append("output_path = ?")
            values.append(output_path)
        if error_log is not None:
            fields.append("error_log = ?")
            values.append(error_log)
        if run_duration_seconds is not None:
            fields.append("run_duration_seconds = ?")
            values.append(run_duration_seconds)
        if status in ("success", "error", "cancelled"):
            fields.append("finished_at = ?")
            values.append(datetime.now(timezone.utc).isoformat())
        if fields:
            values.append(run_id)
            await db.execute(
                f"UPDATE runs SET {', '.join(fields)} WHERE id = ?",
                values,
            )
            await db.commit()
    finally:
        await db.close()


async def get_run(run_id: str) -> Optional[dict]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def list_runs(
    type_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    db = await get_db()
    try:
        query = "SELECT * FROM runs WHERE 1=1"
        params = []
        if type_filter:
            query += " AND type = ?"
            params.append(type_filter)
        if status_filter:
            query += " AND status = ?"
            params.append(status_filter)
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()
