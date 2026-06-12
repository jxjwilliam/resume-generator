#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "🧹 Cleaning up all generated data..."
echo ""

# ── Variants ────────────────────────────────────────────────────
if [ -d "$REPO_ROOT/variants" ] && [ "$(ls -A "$REPO_ROOT/variants" 2>/dev/null)" ]; then
    rm -f "$REPO_ROOT/variants/"*.yaml
    echo "  ✗ variants/*.yaml  — removed"
else
    echo "  ✓ variants/ — already clean"
fi

# ── Output (PDFs, HTML, etc.) ────────────────────────────────────
if [ -d "$REPO_ROOT/output" ] && [ "$(ls -A "$REPO_ROOT/output" 2>/dev/null)" ]; then
    rm -rf "$REPO_ROOT/output"/*
    echo "  ✗ output/*         — removed"
else
    echo "  ✓ output/ — already clean"
fi

# ── Application log ──────────────────────────────────────────────
if [ -f "$REPO_ROOT/applications.json" ]; then
    echo '{"applications":[]}' > "$REPO_ROOT/applications.json"
    echo "  ✗ applications.json — reset to empty"
else
    echo "  ✓ applications.json — does not exist"
fi

# ── WebUI SQLite DB ──────────────────────────────────────────────
if [ -f "$REPO_ROOT/ui/backend/runs.db" ]; then
    rm -f "$REPO_ROOT/ui/backend/runs.db"
    echo "  ✗ ui/backend/runs.db — removed"
else
    echo "  ✓ ui/backend/runs.db — does not exist"
fi

# ── Python cache ─────────────────────────────────────────────────
find "$REPO_ROOT" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
echo "  ✗ __pycache__/      — cleaned"

echo ""
echo "Done. All generated data removed — ready for a fresh test."
