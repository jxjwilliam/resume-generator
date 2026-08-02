"""Shared history database — used by both resume.py (sync) and ui/backend/ (async).

Single SQLite DB at <repo_root>/runs.db — every build from CLI or WebUI writes
to the same DB and appears in both History tabs.
"""

import json
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── DB location ──────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = str(REPO_ROOT / "runs.db")
OUTPUT_DIR = REPO_ROOT / "output"
VARIANTS_DIR = REPO_ROOT / "output/variants"

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


def read_ats_from_output_dir(slug: str) -> dict | None:
    """Load ATS totals from output/{slug}/ats-report.json and optional bullet-diff."""
    report_path = OUTPUT_DIR / slug / "ats-report.json"
    if not report_path.is_file():
        return None
    try:
        with open(report_path) as f:
            report = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    out = {
        "ats_score": report.get("total"),
        "ats_grade": report.get("grade"),
    }
    diff_path = OUTPUT_DIR / slug / "bullet-diff.json"
    if diff_path.is_file():
        try:
            with open(diff_path) as f:
                diff = json.load(f)
            before = diff.get("before_ats") or {}
            if before.get("total") is not None:
                out["ats_before_score"] = before["total"]
        except (json.JSONDecodeError, OSError):
            pass
    return out


def ats_from_output_files(output_files: list[dict]) -> dict | None:
    """Resolve ATS scores from a list of output file descriptors."""
    for f in output_files:
        if f.get("name") == "ats-report.json" and f.get("slug"):
            return read_ats_from_output_dir(f["slug"])
    return None


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
        for col, col_type in (
            ("output_files", "TEXT"),
            ("variant_file", "TEXT"),
            ("jd_source", "TEXT"),
            ("cover_letter", "TEXT"),
            ("docx", "TEXT"),
            ("max_bullets", "TEXT"),
            ("max_jobs", "TEXT"),
            ("ats_score", "REAL"),
            ("ats_grade", "TEXT"),
            ("ats_before_score", "REAL"),
            ("pages", "INTEGER"),
        ):
            if col not in cols:
                db.execute(f"ALTER TABLE runs ADD COLUMN {col} {col_type}")
                db.commit()
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
    ats_score: Optional[float] = None,
    ats_grade: Optional[str] = None,
    ats_before_score: Optional[float] = None,
    pages: Optional[int] = None,
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
        if ats_score is not None:
            fields.append("ats_score = ?")
            values.append(ats_score)
        if ats_grade is not None:
            fields.append("ats_grade = ?")
            values.append(ats_grade)
        if ats_before_score is not None:
            fields.append("ats_before_score = ?")
            values.append(ats_before_score)
        if pages is not None:
            fields.append("pages = ?")
            values.append(pages)
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
