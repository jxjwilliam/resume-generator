# Resume WebUI — Design

**Date:** 2026-06-12
**Status:** Draft design

## Problem

The resume management system currently has two CLI tools (`resume.py` and `transform.py`) that require terminal interaction. There is no graphical interface for:
- Selecting YAML sources, themes, and tags visually
- Monitoring build progress in real-time
- Viewing a history of past runs with results
- Uploading/pasting job descriptions with visual feedback
- Triggering LLM rewrites with a single click

The user wants a local web UI that wraps both tools, running on localhost with no auth, no cloud deployment.

## Solution

A two-process local web application:

```
williamresume/
├── resume.py              # existing — unchanged
├── transform.py            # existing — unchanged
├── ui/
│   ├── backend/
│   │   ├── main.py         # FastAPI server (port 8000)
│   │   ├── db.py           # SQLite schema + queries
│   │   ├── models.py       # Pydantic request/response models
│   │   ├── runner.py       # Subprocess runner with SSE log streaming
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── App.tsx     # Tabs + layout
│   │   │   ├── pages/
│   │   │   │   ├── ResumePage.tsx
│   │   │   │   ├── TransformPage.tsx
│   │   │   │   └── HistoryPage.tsx
│   │   │   └── components/
│   │   │       ├── ThemeCard.tsx
│   │   │       ├── LogStream.tsx
│   │   │       ├── JdInput.tsx
│   │   │       └── YamlSelector.tsx
│   │   └── package.json
│   └── README.md
├── output/                 # PDFs (existing, gitignored)
└── variants/               # Generated YAMLs (existing, tracked)
```

### Key Architectural Decisions

| Decision | Choice | Why |
|---|---|---|
| **Backend** | FastAPI | Python-native, async, built-in SSE support via StreamingResponse |
| **Frontend** | React + Vite + MUI (TypeScript) | Modern, fast HMR, MUI gives polished UI with minimal custom CSS |
| **Process model** | Subprocess (asyncio.create_subprocess_exec) | Both resume.py and transform.py call exit(1) — direct import would kill the server. Subprocess is safer and requires zero refactoring of existing tools. |
| **Log streaming** | SSE (Server-Sent Events) | FastAPI StreamingResponse streaming subprocess stdout/stderr. Simpler than WebSocket for one-directional log output. |
| **Data store** | SQLite (aiosqlite + sqlite3) | Zero setup, no external DB process, sufficient for local single-user history |
| **rendercv integration** | Subprocess `rendercv render <variant>` | rendercv has minimal Python API surface; CLI is the supported interface |
| **UI startup** | Single shell script | `./ui/start.sh` — installs deps if needed, starts both backend + frontend in parallel |

## Two Primary Tabs

### Tab 1 — Resume (wraps `resume.py`)

**Purpose:** Build a job-specific resume variant → render to PDF.

**Controls:**
- **YAML selector** — dropdown listing `*.yaml` files in the repo root (currently only `base.yaml`; extensible if user adds more)
- **Theme picker** — visual card grid showing rendercv's 4 built-in themes: `classic`, `sb2nov`, `moderncv`, `engineeringresumes`. Each card shows a small thumbnail preview.
- **Tags** — multi-select chip input populated from a `/api/tags` endpoint that parses the YAML
- **Company / Role** — text inputs matching `resume.py build --company --role`
- **JD upload** — drag-and-drop file upload (`.txt`/`.pdf`) or paste text into a textarea
- **LLM toggle** — checkbox to enable `--llm` mode (requires JD)
- **All formats toggle** — checkbox for `--all-formats`
- **Run button** — triggers build

**Behavior:**
1. POST `/api/resume/run` with form data
2. Backend generates a job ID (UUID), writes a log entry with `status=running`
3. Backend spawns `asyncio.create_subprocess_exec("python3", "resume.py", "build", ...)` in a background task
4. stdout/stderr streams via SSE at `GET /api/log/{job_id}`
5. On completion: backend polls for the output PDF, updates log entry to `status=success` or `status=error`, stores `output_path` and `error_log`
6. Frontend shows: live log panel (color-coded) + "Download PDF" button + link to output folder

### Tab 2 — Transform (wraps `transform.py`)

**Purpose:** Rewrite resume content to match a JD, then optionally produce PDF.

**Controls:**
- **YAML selector** — same dropdown as Tab 1
- **JD input** — textarea (paste) or file upload (`.txt`/`.pdf`) with extracted text preview
- **JD keyword analysis** — before running, show top 10-15 extracted keywords from the JD as colored tag chips. Helps the user verify the LLM understood the right priorities.
- **Tag filter** — multi-select for which sections to emphasize (skills, experience, projects)
- **LLM toggle** — enabled by default when JD is provided
- **Output mode** — radio: "Preview only" (dry-run) / "Generate PDF too"
- **Run button**

**Behavior:**
1. POST `/api/transform/run` with form data
2. Same subprocess + SSE pattern as Tab 1
3. On completion: show diff view (original YAML vs rewritten YAML), then if "Generate PDF too" selected, auto-trigger `resume.py build` and show the PDF

## API Surface

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/api/yamls` | List available YAML source files in repo root |
| GET | `/api/themes` | List rendercv themes with names + descriptions |
| GET | `/api/tags` | Parse selected YAML, return all unique tags |
| POST | `/api/resume/run` | Run resume.py build, returns `{job_id}` |
| POST | `/api/transform/run` | Run transform.py, returns `{job_id}` |
| POST | `/api/resume/cancel/{job_id}` | Kill running subprocess |
| GET | `/api/log/{job_id}` | SSE stream of stdout/stderr |
| GET | `/api/history` | List all past runs (paginated, filterable) |
| GET | `/api/history/{job_id}` | Single run detail + output paths |
| GET | `/api/output/{job_id}` | Serve generated PDF file |
| POST | `/api/jd/analyze` | Extract keywords from JD text, return tag cloud |

### Request Schemas

**POST /api/resume/run**
```json
{
  "yaml_file": "base.yaml",
  "company": "Ideon Technologies",
  "role": "Principal Software Developer",
  "tags": ["ai", "fullstack"],
  "theme": "classic",
  "jd_text": "...",
  "use_llm": true,
  "all_formats": false
}
```

**POST /api/transform/run**
```json
{
  "yaml_file": "base.yaml",
  "jd_text": "...",
  "tags": ["ai", "fullstack"],
  "use_llm": true,
  "generate_pdf": false
}
```

## Database Schema (SQLite)

```sql
CREATE TABLE runs (
    id TEXT PRIMARY KEY,            -- UUID
    type TEXT NOT NULL,              -- 'resume' | 'transform'
    status TEXT NOT NULL DEFAULT 'running',  -- running | success | error | cancelled
    yaml_file TEXT,
    company TEXT,
    role TEXT,
    tags TEXT,                       -- JSON array
    theme TEXT,
    jd_snippet TEXT,                 -- first 200 chars of JD
    use_llm INTEGER DEFAULT 0,
    output_path TEXT,                -- path to PDF/YAML output
    error_log TEXT,
    run_duration_seconds REAL,
    created_at TEXT NOT NULL,        -- ISO 8601
    finished_at TEXT
);

CREATE INDEX idx_runs_created ON runs(created_at DESC);
CREATE INDEX idx_runs_type ON runs(type);
CREATE INDEX idx_runs_status ON runs(status);
```

## Subprocess Runner

A dedicated `runner.py` module handles subprocess lifecycle:

```python
class ProcessRunner:
    """Spawn, monitor, stream logs for CLI subprocesses."""

    async def run(self, cmd: list[str], job_id: str) -> AsyncGenerator[str, None]:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=REPO_ROOT
        )
        # Read stdout/stderr concurrently, yield lines as SSE events
        async with aiofiles for streaming...
```

- Each job is stored in an in-memory `dict[str, asyncio.Task]` for cancellation support
- On completion, task cleans itself up and updates SQLite record
- Live log endpoints read from an `asyncio.Queue` per job

## UI Component Details

### Theme Gallery
- Theme data is static (4 built-in rendercv themes) with descriptions from `docs/resume-system-implementation.md`
- Each theme shown as a Material-UI Card with:
  - A small thumbnail (pre-generated or placeholder SVG)
  - Theme name
  - "Best for" tag line (e.g., "FAANG, large tech, senior roles")
- Click to select (highlighted border), selected theme passed to run request

### Log Stream Panel
- MUI Paper with monospace font
- Color-coded lines: stdout (white), stderr (orange), system messages (gray)
- Auto-scroll to bottom with "scroll to bottom" button
- Clear button
- Shows elapsed timer while running

### History Table
- MUI Table with columns: Date, Type, Company, Role, Status, Duration
- Click row to expand details (JD snippet, tags, output path)
- Filter by type (resume/transform) and status (success/error)
- "Re-run" button in expanded row that pre-fills the form with that run's parameters

### JD Input
- Drag-and-drop zone for `.txt` and `.pdf` files
- Textarea for manual paste (auto-detects which was used)
- PDF text extraction via `pypdf` or `pdfplumber` on the backend
- After upload/paste, auto-trigger JD keyword analysis

### JD Keyword Analysis
- Backend: simple TF-based keyword extraction (skip common stopwords, take top 15 by frequency)
- Frontend: colored MUI Chip components in a tag cloud layout
- Helps user verify JD was parsed correctly before running

## Project Structure (Detailed)

```
williamresume/
├── resume.py                   # existing — unchanged
├── transform.py                # existing — unchanged
├── base.yaml                   # existing
├── requirements.txt            # existing + add: fastapi, uvicorn, aiosqlite, sse-starlette, pypdf
├── ui/
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI app, route definitions
│   │   ├── db.py               # SQLite init, CRUD operations
│   │   ├── models.py           # Pydantic schemas
│   │   ├── runner.py           # Subprocess runner with streaming
│   │   ├── jd_analyzer.py      # Keyword extraction from JD text
│   │   └── theme_data.py       # Static theme definitions + thumbnails
│   ├── frontend/
│   │   ├── index.html
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── vite.config.ts
│   │   └── src/
│   │       ├── main.tsx         # React entry point
│   │       ├── App.tsx          # Tab layout, theme provider
│   │       ├── api/
│   │       │   └── client.ts   # Fetch wrapper + SSE helpers
│   │       ├── pages/
│   │       │   ├── ResumePage.tsx
│   │       │   ├── TransformPage.tsx
│   │       │   └── HistoryPage.tsx
│   │       └── components/
│   │           ├── ThemeCard.tsx
│   │           ├── LogStream.tsx
│   │           ├── JdInput.tsx
│   │           ├── YamlSelector.tsx
│   │           ├── TagChips.tsx
│   │           └── HistoryTable.tsx
│   └── start.sh                 # One-command launcher
├── output/                      # existing — PDFs (gitignored)
└── variants/                    # existing — generated YAMLs (tracked)
```

## What's In Scope

- Two-tab UI (Resume + Transform) with live log streaming
- Theme picker with visual cards and descriptions
- JD upload (paste + file, PDF text extraction)
- JD keyword analysis (tag cloud preview)
- Full run history with SQLite persistence
- PDF download from history
- Re-run from history (pre-fill form)
- Cancel running jobs
- Single `./ui/start.sh` command to launch everything

## What's Out of Scope (v1)

- **No auth** — localhost only
- **No YAML editor** — edit `base.yaml` in your regular editor; UI reads it
- **No RxResume live preview** — `transform.py` triggers the sync; UI just runs it
- **No user accounts or multi-tenancy** — single-user local tool
- **No Docker** — bare-metal Python + Node is simpler for a local dev tool
- **No dark mode toggle** — MUI dark mode is trivial to add later; default to light

## Self-Review

1. **Placeholders?** None. All sections defined with concrete types, schemas, and file paths.
2. **Internal consistency?** Yes. Subprocess runner is the single pattern for all CLI invocation. SSE is the single pattern for log streaming. SQLite is the single store.
3. **Scope?** Focused on wrapping existing CLI tools. No new resume functionality — just UI automation of what's already there.
4. **Ambiguity?** No. Every feature maps to a specific endpoint + component. The database schema is concrete. The subprocess runner's cancellation model is explicit.

## Files Changed / Created

| File | Action |
|------|--------|
| `requirements.txt` | Add `fastapi`, `uvicorn`, `aiosqlite`, `sse-starlette`, `pypdf` |
| `ui/backend/main.py` | Create — FastAPI app |
| `ui/backend/db.py` | Create — SQLite schema + CRUD |
| `ui/backend/models.py` | Create — Pydantic schemas |
| `ui/backend/runner.py` | Create — async subprocess runner |
| `ui/backend/jd_analyzer.py` | Create — JD keyword extraction |
| `ui/backend/theme_data.py` | Create — static theme definitions |
| `ui/frontend/` | Create — Vite + React + MUI project |
| `ui/start.sh` | Create — dev launcher script |
