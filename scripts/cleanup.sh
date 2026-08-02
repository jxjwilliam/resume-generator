#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "🧹 Cleaning up all generated data..."
echo ""

# ── Output (PDFs, HTML, variants, etc.) ──────────────────────────
if [ -d "$REPO_ROOT/output" ] && [ "$(ls -A "$REPO_ROOT/output" 2>/dev/null)" ]; then
    rm -rf "$REPO_ROOT/output"/*
    echo "  ✗ output/*         — removed"
else
    echo "  ✓ output/ — already clean"
fi

# ── Shared SQLite history DB ─────────────────────────────────────
if [ -f "$REPO_ROOT/runs.db" ]; then
    rm -f "$REPO_ROOT/runs.db"
    echo "  ✗ runs.db — removed"
else
    echo "  ✓ runs.db — does not exist"
fi

# ── Stale databases ──────────────────────────────────────────────
if [ -f "$REPO_ROOT/resume_history.db" ]; then
    rm -f "$REPO_ROOT/resume_history.db"
    echo "  ✗ resume_history.db — removed"
fi

# ── Legacy WebUI SQLite DB ───────────────────────────────────────
if [ -f "$REPO_ROOT/ui/backend/runs.db" ]; then
    rm -f "$REPO_ROOT/ui/backend/runs.db"
    echo "  ✗ ui/backend/runs.db — removed (legacy)"
fi

# ── Python cache ─────────────────────────────────────────────────
find "$REPO_ROOT" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
echo "  ✗ __pycache__/      — cleaned"

echo ""
echo "Done. All generated data removed — ready for a fresh test."
