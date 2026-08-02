"""Thin async wrapper around the shared history_db module.

This file exists so the WebUI's existing imports (from .db import ...)
continue to work without changes. The actual SQLite logic lives in
src/history_db.py which is shared with resume.py (CLI).
"""

from src.history_db import (
    async_init_db as init_db,
    async_insert_run as insert_run,
    async_update_run as update_run,
    async_get_run as get_run,
    async_list_runs as list_runs,
    scan_output_files,
)
