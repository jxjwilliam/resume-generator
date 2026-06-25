"""Shared history database — used by both resume.py (sync) and ui/backend/ (async).

Single SQLite DB at <repo_root>/runs.db replaces the old split:
  - applications.json  (CLI-only, flat JSON)
  - ui/backend/runs.db (WebUI-only, SQLite)

Now every build from CLI or WebUI writes to the same DB and appears in both History tabs.
"""

import json
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── DB location ──────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent
DB_PATH = str(REPO_ROOT / "runs.db")
OUTPUT_DIR = REPO_ROOT / "output"
VARIANTS_DIR = REPO_ROOT / "variants"
LOG_FILE = str(REPO_ROOT / "applications.json")

# ── Schema ───────────────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL DEFAULT 'build',
    status TEXT NOT NULL DEFAULT 'running',
    yaml_file TEXT,
    company TEXT,
    role TEXT,
    tags TEXT,
    theme TEXT,
    max_bullets INTEGER,
    max_jobs INTEGER,
    jd_snippet TEXT,
    use_llm INTEGER DEFAULT 0,
    output_path TEXT,
    output_files TEXT,
    variant_file TEXT,
    jd_source TEXT,
    cover_letter INTEGER DEFAULT 0,
    docx INTEGER DEFAULT 0,
    error_log TEXT,
    run_duration_seconds REAL,
    created_at TEXT NOT NULL,
    finished_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_runs_type ON runs(type);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
CREATE INDEX IF NOT EXISTS idx_runs_company ON runs(company);
"""

# ── Output file helpers ─────────────────────────────────────────────────────
# (moved from ui/backend/runner.py so the CLI can also scan and store)

_OUTPUT_EXT_LABELS = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".html": "html",
    ".txt": "cover-letter",
    ".json": "report",
    ".typ": "typst",
    ".jpg": "photo",
    ".png": "photo",
}


def _classify_file(name: str) -> str:
    lower = name.lower()
    if lower.startswith("cover-letter"):
        return "cover-letter"
    if lower.startswith("ats-report"):
        return "ats-report"
    if lower.startswith("bullet-diff"):
        return "bullet-diff"
    return _OUTPUT_EXT_LABELS.get(Path(name).suffix, "other")


def scan_output_files(slug: str | None = None) -> list[dict]:
    """List generated files in an output directory.

    If slug is given, list files in output/{slug}/.
    Otherwise use the most recently modified output subdirectory.
    """
    if not OUTPUT_DIR.is_dir():
        return []
    target_dir = None
    if slug:
        target_dir = OUTPUT_DIR / slug
        if not target_dir.is_dir():
            return []
    else:
        dirs = [
            (d.stat().st_mtime, d)
            for d in sorted(OUTPUT_DIR.iterdir())
            if d.is_dir()
        ]
        if not dirs:
            return []
        dirs.sort(key=lambda x: x[0], reverse=True)
        target_dir = dirs[0][1]
        slug = target_dir.name
    files = []
    for fpath in sorted(target_dir.iterdir()):
        if fpath.is_file() and not fpath.name.startswith("."):
            files.append({
                "name": fpath.name,
                "type": _classify_file(fpath.name),
                "slug": slug,
                "size": fpath.stat().st_size,
            })
    return files


# ── Sync API (for resume.py CLI) ────────────────────────────────────────────


def _conn() -> sqlite3.Connection:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    return db


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    if d.get("output_files"):
        d["output_files"] = json.loads(d["output_files"])
    if d.get("tags"):
        d["tags"] = json.loads(d["tags"])
    return d


def init_db():
    """Create tables + run migrations."""
    db = _conn()
    try:
        db.executescript(SCHEMA_SQL)
        db.commit()
        # Column migrations for DBs created before this merge
        cursor = db.execute("PRAGMA table_info(runs)")
        cols = {c[1] for c in cursor.fetchall()}
        for col in ("output_files", "variant_file", "jd_source", "cover_letter", "docx", "max_bullets", "max_jobs"):
            if col not in cols:
                db.execute(f"ALTER TABLE runs ADD COLUMN {col} TEXT")
                db.commit()
        _migrate_from_applications_json(db)
        _migrate_from_old_webui_db(db)
    finally:
        db.close()


def insert_run(run: dict) -> None:
    db = _conn()
    try:
        db.execute(
            """INSERT INTO runs
               (id, type, status, yaml_file, company, role, tags, theme,
                max_bullets, max_jobs, jd_snippet, use_llm,
                cover_letter, docx, variant_file, jd_source, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run["id"], run.get("type", "build"), run.get("status", "running"),
                run.get("yaml_file"), run.get("company"), run.get("role"),
                json.dumps(run.get("tags", [])),
                run.get("theme"),
                run.get("max_bullets"), run.get("max_jobs"),
                run.get("jd_snippet"),
                1 if run.get("use_llm") else 0,
                1 if run.get("cover_letter") else 0,
                1 if run.get("docx") else 0,
                run.get("variant_file"), run.get("jd_source"),
                run.get("created_at", datetime.now(timezone.utc).isoformat()),
            ),
        )
        db.commit()
    finally:
        db.close()


def update_run(
    run_id: str,
    status: Optional[str] = None,
    output_path: Optional[str] = None,
    output_files: Optional[list[dict]] = None,
    error_log: Optional[str] = None,
    run_duration_seconds: Optional[float] = None,
) -> None:
    db = _conn()
    try:
        fields = []
        values = []
        if status is not None:
            fields.append("status = ?")
            values.append(status)
        if output_path is not None:
            fields.append("output_path = ?")
            values.append(output_path)
        if output_files is not None:
            fields.append("output_files = ?")
            values.append(json.dumps(output_files))
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
            db.execute(
                f"UPDATE runs SET {', '.join(fields)} WHERE id = ?",
                values,
            )
            db.commit()
    finally:
        db.close()


def get_run(run_id: str) -> Optional[dict]:
    db = _conn()
    try:
        cursor = db.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
        row = cursor.fetchone()
        return _row_to_dict(row) if row else None
    finally:
        db.close()


def list_runs(
    type_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    db = _conn()
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
        cursor = db.execute(query, params)
        return [_row_to_dict(r) for r in cursor.fetchall()]
    finally:
        db.close()


# ── Migration from applications.json ─────────────────────────────────────────


def _migrate_from_applications_json(db: sqlite3.Connection):
    """One-time import of existing applications.json entries into SQLite."""
    log_path = Path(LOG_FILE)
    if not log_path.exists():
        return
    existing = db.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    if existing > 0:
        return  # already migrated
    with open(log_path) as f:
        data = json.load(f)
    apps = data.get("applications", [])
    if not apps:
        return
    now = datetime.now(timezone.utc).isoformat()
    for app in apps:
        slug = app.get("id", "")
        db.execute(
            """INSERT OR IGNORE INTO runs
               (id, type, status, company, role, tags, theme,
                jd_source, variant_file, created_at, finished_at)
               VALUES (?, 'build', 'success', ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                slug,
                app.get("company"),
                app.get("role"),
                json.dumps([t.strip() for t in app.get("tags_used", "").split(",") if t.strip()]),
                app.get("template"),
                app.get("jd_source"),
                app.get("variant_file"),
                app.get("date", now[:10]) + "T00:00:00",
                now,
            ),
        )
        # Scan existing output files for this slug
        files = scan_output_files(slug)
        if files:
            db.execute(
                "UPDATE runs SET output_files = ?, output_path = ? WHERE id = ?",
                (json.dumps(files), str(OUTPUT_DIR / slug), slug),
            )
    db.commit()
    print(f"Migrated {len(apps)} entries from applications.json into runs.db")


def _migrate_from_old_webui_db(db: sqlite3.Connection):
    """One-time import of existing ui/backend/runs.db entries (old WebUI DB)."""
    old_path = Path(REPO_ROOT) / "ui" / "backend" / "runs.db"
    if not old_path.exists():
        return
    # Check if old-webui IDs already migrated (use INSERT OR IGNORE to dedup)
    try:
        old_db = sqlite3.connect(str(old_path))
        old_db.row_factory = sqlite3.Row
        old_rows = old_db.execute("SELECT * FROM runs").fetchall()
        old_db.close()
    except Exception:
        return
    if not old_rows:
        return
    now = datetime.now(timezone.utc).isoformat()
    for row in old_rows:
        d = dict(row)
        slug = d.get("id", "")
        tags_raw = d.get("tags") or "[]"
        try:
            tags = json.loads(tags_raw) if isinstance(tags_raw, str) else tags_raw
        except (json.JSONDecodeError, TypeError):
            tags = []
        output_files_raw = d.get("output_files")
        of = None
        if output_files_raw:
            try:
                of = json.loads(output_files_raw) if isinstance(output_files_raw, str) else output_files_raw
            except (json.JSONDecodeError, TypeError):
                of = None
        db.execute(
            """INSERT OR IGNORE INTO runs
               (id, type, status, yaml_file, company, role, tags, theme,
                jd_snippet, use_llm, output_path, output_files,
                error_log, run_duration_seconds,
                created_at, finished_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                slug,
                d.get("type", "resume"),
                d.get("status", "success"),
                d.get("yaml_file"),
                d.get("company"),
                d.get("role"),
                json.dumps(tags),
                d.get("theme"),
                d.get("jd_snippet"),
                1 if d.get("use_llm") else 0,
                d.get("output_path"),
                json.dumps(of) if of else None,
                d.get("error_log"),
                d.get("run_duration_seconds"),
                d.get("created_at", now),
                d.get("finished_at"),
            ),
        )
    db.commit()
    print(f"Migrated {len(old_rows)} entries from old ui/backend/runs.db into new runs.db")


# ── Async wrapper for WebUI (ui/backend/db.py will delegate to this) ────────

import asyncio


async def async_init_db():
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, init_db)


async def async_insert_run(run: dict):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, insert_run, run)


async def async_update_run(run_id, **kwargs):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: update_run(run_id, **kwargs))


async def async_get_run(run_id: str) -> Optional[dict]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, get_run, run_id)


async def async_list_runs(**kwargs) -> list[dict]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: list_runs(**kwargs))
