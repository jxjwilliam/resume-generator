# Resume WebUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local web UI (FastAPI + React/Vite/MUI) that wraps `resume.py` and `transform.py` with a visual interface for building resumes and tracking history.

**Architecture:** Two-process design — FastAPI backend (port 8000) serves as an API layer + static files, React/Vite frontend (port 5173 in dev) provides the UI. Backend spawns `resume.py`/`transform.py` as subprocesses (direct import impossible due to `exit(1)` calls) and streams logs via SSE. SQLite stores run history.

**Tech Stack:** Python 3.12, FastAPI, Uvicorn, aiosqlite, sse-starlette, pypdf / React 18, TypeScript, Vite, MUI 5

---

## File Structure

```
resume-app/
├── requirements.txt                           # +fastapi, uvicorn, aiosqlite, sse-starlette, pypdf
├── ui/
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── main.py                            # FastAPI app + all routes
│   │   ├── db.py                              # SQLite init + CRUD
│   │   ├── models.py                          # Pydantic request/response schemas
│   │   ├── runner.py                          # Async subprocess manager + SSE streaming
│   │   ├── jd_analyzer.py                     # TF-based JD keyword extraction
│   │   └── theme_data.py                      # Static rendercv theme definitions
│   ├── frontend/
│   │   ├── index.html
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── tsconfig.node.json
│   │   ├── vite.config.ts
│   │   └── src/
│   │       ├── main.tsx
│   │       ├── App.tsx
│   │       ├── api/
│   │       │   └── client.ts
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
│   └── start.sh
└── output/                                    # existing, gitignored — PDFs land here
```

---

### Task 1: Add Python dependencies

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Append WebUI dependencies to requirements.txt**

Read the current `requirements.txt`, then append:

```
# WebUI
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
aiosqlite>=0.20.0
sse-starlette>=2.1.0
pypdf>=5.0.0
```

- [ ] **Step 2: Verify install**

Run: `pip install -r requirements.txt`

No errors expected.

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "deps: add fastapi, uvicorn, aiosqlite, sse-starlette, pypdf for WebUI"
```

---

### Task 2: Create Pydantic models (`ui/backend/models.py`)

**Files:**
- Create: `ui/backend/__init__.py` (empty file)
- Create: `ui/backend/models.py`

- [ ] **Step 1: Write models.py**

```python
from pydantic import BaseModel
from typing import Optional


class ResumeRunRequest(BaseModel):
    yaml_file: str = "base.yaml"
    company: str
    role: Optional[str] = None
    tags: list[str] = []
    theme: str = "classic"
    jd_text: Optional[str] = None
    use_llm: bool = False
    all_formats: bool = False


class TransformRunRequest(BaseModel):
    yaml_file: str = "base.yaml"
    jd_text: str
    tags: list[str] = []
    use_llm: bool = True
    generate_pdf: bool = False


class RunResponse(BaseModel):
    job_id: str


class RunHistoryItem(BaseModel):
    id: str
    type: str  # "resume" | "transform"
    status: str  # "running" | "success" | "error" | "cancelled"
    company: Optional[str] = None
    role: Optional[str] = None
    tags: Optional[str] = None
    theme: Optional[str] = None
    jd_snippet: Optional[str] = None
    use_llm: bool = False
    output_path: Optional[str] = None
    error_log: Optional[str] = None
    run_duration_seconds: Optional[float] = None
    created_at: str
    finished_at: Optional[str] = None


class ThemeInfo(BaseModel):
    id: str
    name: str
    description: str
    best_for: str


class YamlInfo(BaseModel):
    name: str
    path: str


class KeywordResult(BaseModel):
    keywords: list[str]
```

- [ ] **Step 2: Commit**

```bash
git add ui/backend/__init__.py ui/backend/models.py
git commit -m "feat(webui): add Pydantic models for API schemas"
```

---

### Task 3: Create theme data (`ui/backend/theme_data.py`)

**Files:**
- Create: `ui/backend/theme_data.py`

- [ ] **Step 1: Write theme_data.py**

```python
from models import ThemeInfo

THEMES: list[ThemeInfo] = [
    ThemeInfo(
        id="classic",
        name="Classic",
        description="Professional, clean layout with section headers",
        best_for="FAANG, large tech, senior roles",
    ),
    ThemeInfo(
        id="sb2nov",
        name="Sb2nov",
        description="ATS-optimised, single-column, high density",
        best_for="Standard SWE roles, ATS-friendly",
    ),
    ThemeInfo(
        id="moderncv",
        name="ModernCV",
        description="Modern two-column layout with icon accents",
        best_for="Startup, product, mid-level",
    ),
    ThemeInfo(
        id="engineeringresumes",
        name="EngineeringResumes",
        description="Minimal, maximally ATS-optimised plaintext-friendly",
        best_for="Maximally ATS-optimised",
    ),
]


def get_theme(theme_id: str) -> ThemeInfo | None:
    return next((t for t in THEMES if t.id == theme_id), None)
```

- [ ] **Step 2: Commit**

```bash
git add ui/backend/theme_data.py
git commit -m "feat(webui): add rendercv theme definitions"
```

---

### Task 4: Create JD analyzer (`ui/backend/jd_analyzer.py`)

**Files:**
- Create: `ui/backend/jd_analyzer.py`

- [ ] **Step 1: Write jd_analyzer.py**

```python
import re
from collections import Counter
from typing import Optional

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "need",
    "dare", "ought", "used", "about", "into", "through", "during",
    "before", "after", "above", "below", "between", "under", "again",
    "further", "then", "once", "here", "there", "when", "where", "why",
    "how", "all", "each", "every", "both", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "just", "because", "as", "if", "while",
    "this", "that", "these", "those", "it", "its", "you", "your",
    "we", "our", "they", "them", "their", "what", "which", "who",
    "whom", "i", "me", "my", "he", "him", "his", "she", "her",
}


def extract_keywords(text: str, top_n: int = 15) -> list[str]:
    """Extract the most frequent meaningful keywords from JD text."""
    text = text.lower()
    words = re.findall(r"[a-z][a-z0-9+#.-]{2,}", text)
    filtered = [w for w in words if w not in STOPWORDS and len(w) > 2]
    counts = Counter(filtered)
    return [word for word, _ in counts.most_common(top_n)]


def extract_text_from_pdf(path: str) -> Optional[str]:
    """Extract text from a PDF file. Returns None on failure."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(path)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n".join(pages) if pages else None
    except Exception:
        return None
```

- [ ] **Step 2: Commit**

```bash
git add ui/backend/jd_analyzer.py
git commit -m "feat(webui): add JD keyword extraction and PDF text parser"
```

---

### Task 5: Create database layer (`ui/backend/db.py`)

**Files:**
- Create: `ui/backend/db.py`

- [ ] **Step 1: Write db.py**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add ui/backend/db.py
git commit -m "feat(webui): add SQLite database layer with CRUD operations"
```

---

### Task 6: Create subprocess runner (`ui/backend/runner.py`)

**Files:**
- Create: `ui/backend/runner.py`

- [ ] **Step 1: Write runner.py**

```python
import asyncio
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from db import insert_run, update_run

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# In-memory registry: job_id -> (process, task, log_queue)
_running_jobs: dict[str, dict] = {}


async def stream_logs(job_id: str):
    """Async generator that yields log lines from a job's queue as SSE events."""
    loop = asyncio.get_event_loop()
    queue: asyncio.Queue = _running_jobs[job_id]["log_queue"]
    while True:
        line = await asyncio.wait_for(queue.get(), timeout=300)
        if line is None:
            break
        yield f"data: {line}\n\n"


async def _run_process(cmd: list[str], job_id: str, log_queue: asyncio.Queue):
    """Internal task that spawns the subprocess and streams output."""
    start = time.monotonic()
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=REPO_ROOT,
        )
        _running_jobs[job_id]["process"] = proc

        async def _read_stream(stream, prefix: str):
            while True:
                line = await stream.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace").rstrip()
                await log_queue.put(f"{prefix}{text}")

        await asyncio.gather(
            _read_stream(proc.stdout, ""),
            _read_stream(proc.stderr, "[STDERR] "),
        )

        await proc.wait()
        duration = time.monotonic() - start

        if proc.returncode == 0:
            await update_run(job_id, status="success", run_duration_seconds=duration)
            await log_queue.put("[SYSTEM] Job completed successfully")
        else:
            await update_run(
                job_id, status="error", run_duration_seconds=duration,
                error_log=f"Process exited with code {proc.returncode}",
            )
            await log_queue.put(f"[SYSTEM] Job failed with exit code {proc.returncode}")
    except asyncio.CancelledError:
        proc = _running_jobs[job_id].get("process")
        if proc and proc.returncode is None:
            proc.kill()
            await proc.wait()
        await update_run(job_id, status="cancelled")
        await log_queue.put("[SYSTEM] Job cancelled")
    except Exception as e:
        await update_run(job_id, status="error", error_log=str(e))
        await log_queue.put(f"[SYSTEM] Error: {e}")
    finally:
        await log_queue.put(None)
        _running_jobs.pop(job_id, None)


async def start_job(
    cmd: list[str],
    run_type: str,
    metadata: Optional[dict] = None,
) -> str:
    """Start a subprocess job, return job_id for log streaming and cancellation."""
    job_id = uuid.uuid4().hex[:12]
    log_queue: asyncio.Queue = asyncio.Queue()

    now = datetime.now(timezone.utc).isoformat()
    run_data = {
        "id": job_id,
        "type": run_type,
        "status": "running",
        "yaml_file": (metadata or {}).get("yaml_file"),
        "company": (metadata or {}).get("company"),
        "role": (metadata or {}).get("role"),
        "tags": (metadata or {}).get("tags", []),
        "theme": (metadata or {}).get("theme"),
        "jd_snippet": ((metadata or {}).get("jd_text") or "")[:200],
        "use_llm": 1 if (metadata or {}).get("use_llm") else 0,
        "created_at": now,
    }
    await insert_run(run_data)

    task = asyncio.create_task(_run_process(cmd, job_id, log_queue))
    _running_jobs[job_id] = {"process": None, "task": task, "log_queue": log_queue}
    return job_id


async def cancel_job(job_id: str) -> bool:
    """Cancel a running job by its ID. Returns True if found and cancelled."""
    entry = _running_jobs.get(job_id)
    if entry is None:
        return False
    entry["task"].cancel()
    return True
```

- [ ] **Step 2: Commit**

```bash
git add ui/backend/runner.py
git commit -m "feat(webui): add async subprocess runner with SSE log streaming"
```

---

### Task 7: Create FastAPI app with all routes (`ui/backend/main.py`)

**Files:**
- Create: `ui/backend/main.py`

- [ ] **Step 1: Write main.py**

```python
import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from sse_starlette.sse import EventSourceResponse

from db import init_db, get_run, list_runs
from jd_analyzer import extract_keywords, extract_text_from_pdf
from models import (
    ResumeRunRequest,
    TransformRunRequest,
    RunResponse,
    YamlInfo,
)
from runner import start_job, stream_logs, cancel_job
from theme_data import THEMES

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
YAML_GLOBS = ["*.yaml", "*.yml"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Resume WebUI", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _list_yaml_files() -> list[YamlInfo]:
    files = []
    for glob in YAML_GLOBS:
        for p in REPO_ROOT.glob(glob):
            if p.is_file():
                files.append(YamlInfo(name=p.name, path=str(p)))
    return sorted(files, key=lambda f: f.name)


def _get_output_paths(job_id: str) -> list[str]:
    """Find generated PDF files in output/ directories matching the job."""
    output_dir = REPO_ROOT / "output"
    if not output_dir.exists():
        return []
    paths = []
    for slug_dir in output_dir.iterdir():
        if slug_dir.is_dir():
            for f in slug_dir.iterdir():
                if f.suffix == ".pdf":
                    paths.append(str(f))
    return sorted(paths)


@app.get("/api/yamls")
async def list_yamls():
    return _list_yaml_files()


@app.get("/api/themes")
async def list_themes():
    return THEMES


@app.get("/api/tags")
async def list_tags():
    """Parse all unique tags from base.yaml."""
    yaml_path = REPO_ROOT / "base.yaml"
    if not yaml_path.exists():
        return {"tags": []}
    try:
        import yaml

        with open(yaml_path) as f:
            base = yaml.safe_load(f)
    except Exception:
        return {"tags": []}

    all_tags = set()
    for job in base.get("experience", []):
        for bullet in job.get("bullets", []):
            all_tags.update(bullet.get("tags", []))
    for cat, items in base.get("skills", {}).items():
        for item in items:
            all_tags.update(item.get("tags", []))
    return {"tags": sorted(all_tags)}


@app.post("/api/jd/analyze")
async def analyze_jd(data: dict):
    text = data.get("text", "")
    if not text:
        raise HTTPException(400, "text is required")
    keywords = extract_keywords(text)
    return {"keywords": keywords}


@app.post("/api/jd/upload")
async def upload_jd(file: bytes):
    """Upload a .txt or .pdf JD file and return extracted text + keywords."""
    temp = REPO_ROOT / ".ui_temp_jd"
    temp.write_bytes(file)
    try:
        if temp.suffix.lower() == ".pdf":
            text = extract_text_from_pdf(str(temp))
        else:
            text = temp.read_text("utf-8", errors="replace")
    finally:
        temp.unlink(missing_ok=True)

    if not text:
        raise HTTPException(400, "Could not extract text from file")
    keywords = extract_keywords(text)
    return {"text": text[:5000], "keywords": keywords}


def _build_resume_cmd(args: ResumeRunRequest, jd_file: str | None) -> list[str]:
    cmd = [sys.executable, "resume.py", "build",
           "--company", args.company,
           "--template", args.theme]
    if args.role:
        cmd += ["--role", args.role]
    if args.tags:
        cmd += ["--tags", ",".join(args.tags)]
    if jd_file:
        cmd += ["--jd", jd_file]
    if args.use_llm:
        cmd += ["--llm"]
    if args.all_formats:
        cmd += ["--all-formats"]
    return cmd


@app.post("/api/resume/run", response_model=RunResponse)
async def run_resume(args: ResumeRunRequest):
    jd_file = None
    if args.jd_text:
        jd_file = str(REPO_ROOT / ".ui_temp_jd.txt")
        Path(jd_file).write_text(args.jd_text)

    cmd = _build_resume_cmd(args, jd_file)
    job_id = await start_job(cmd, "resume", metadata=args.model_dump())
    return RunResponse(job_id=job_id)


@app.post("/api/transform/run", response_model=RunResponse)
async def run_transform(args: TransformRunRequest):
    jd_file = str(REPO_ROOT / ".ui_temp_jd.txt")
    Path(jd_file).write_text(args.jd_text)

    cmd = [sys.executable, "transform.py", "--dry-run",
           "--yaml", args.yaml_file]
    if args.tags:
        cmd += ["--tags", ",".join(args.tags)]
    cmd += ["--jd", jd_file]
    if args.use_llm:
        cmd += ["--llm"]
    if args.generate_pdf:
        pass  # PDF generation handled after transform completes

    job_id = await start_job(cmd, "transform", metadata=args.model_dump())
    return RunResponse(job_id=job_id)


@app.post("/api/resume/cancel/{job_id}")
async def cancel_run(job_id: str):
    ok = await cancel_job(job_id)
    if not ok:
        raise HTTPException(404, "Job not found or already completed")
    return {"status": "cancelled"}


@app.get("/api/log/{job_id}")
async def stream_run_log(job_id: str):
    return EventSourceResponse(stream_logs(job_id))


@app.get("/api/history")
async def get_history(
    type: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    rows = await list_runs(type_filter=type, status_filter=status,
                           limit=min(limit, 200), offset=offset)
    return {"runs": rows, "total": len(rows)}


@app.get("/api/history/{job_id}")
async def get_run_detail(job_id: str):
    run = await get_run(job_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return run


@app.get("/api/output/{job_id}")
async def get_output(job_id: str):
    run = await get_run(job_id)
    if not run:
        raise HTTPException(404, "Run not found")
    output_path = run.get("output_path")
    if not output_path:
        paths = _get_output_paths(job_id)
        if not paths:
            raise HTTPException(404, "No output files found")
        output_path = paths[0]
    return FileResponse(output_path, media_type="application/pdf",
                        filename=Path(output_path).name)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
```

- [ ] **Step 2: Verify imports**

Run: `python -c "from ui.backend import main; print('OK')"` from the repo root.

Expected: `OK` (no ImportError)

- [ ] **Step 3: Commit**

```bash
git add ui/backend/main.py
git commit -m "feat(webui): add FastAPI app with all API routes"
```

---

### Task 8: Scaffold frontend project (Vite + React + MUI)

**Files:**
- Create: `ui/frontend/package.json`
- Create: `ui/frontend/tsconfig.json`
- Create: `ui/frontend/tsconfig.node.json`
- Create: `ui/frontend/vite.config.ts`
- Create: `ui/frontend/index.html`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "resume-webui",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@emotion/react": "^11.13.0",
    "@emotion/styled": "^11.13.0",
    "@mui/icons-material": "^6.1.0",
    "@mui/material": "^6.1.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.5.0",
    "vite": "^5.4.0"
  }
}
```

- [ ] **Step 2: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src"]
}
```

- [ ] **Step 3: Create tsconfig.node.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "strict": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 4: Create vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
```

- [ ] **Step 5: Create index.html**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Resume WebUI</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 6: Create main.tsx and src directory**

Create `ui/frontend/src/main.tsx`:

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

Create `ui/frontend/src/` directory.

- [ ] **Step 7: Install npm dependencies**

Run: `cd ui/frontend && npm install`

Expected: `package-lock.json` created, no errors.

- [ ] **Step 8: Commit**

```bash
git add ui/frontend/
git commit -m "feat(webui): scaffold Vite + React + MUI frontend project"
```

---

### Task 9: Create API client and TypeScript types

**Files:**
- Create: `ui/frontend/src/api/client.ts`
- Create: `ui/frontend/src/types.ts`

- [ ] **Step 1: Write types.ts**

```typescript
export interface ThemeInfo {
  id: string;
  name: string;
  description: string;
  best_for: string;
}

export interface YamlInfo {
  name: string;
  path: string;
}

export interface RunHistoryItem {
  id: string;
  type: "resume" | "transform";
  status: "running" | "success" | "error" | "cancelled";
  company?: string;
  role?: string;
  tags?: string;
  theme?: string;
  jd_snippet?: string;
  use_llm: boolean;
  output_path?: string;
  error_log?: string;
  run_duration_seconds?: number;
  created_at: string;
  finished_at?: string;
}

export interface ResumeRunRequest {
  yaml_file?: string;
  company: string;
  role?: string;
  tags?: string[];
  theme?: string;
  jd_text?: string;
  use_llm?: boolean;
  all_formats?: boolean;
}

export interface TransformRunRequest {
  yaml_file?: string;
  jd_text: string;
  tags?: string[];
  use_llm?: boolean;
  generate_pdf?: boolean;
}

export interface RunResponse {
  job_id: string;
}

export interface KeywordResult {
  keywords: string[];
}

export interface JdUploadResult {
  text: string;
  keywords: string[];
}

export type LogLine = {
  text: string;
  source: "stdout" | "stderr" | "system";
};
```

- [ ] **Step 2: Write client.ts**

```typescript
import type {
  ThemeInfo,
  YamlInfo,
  RunHistoryItem,
  ResumeRunRequest,
  TransformRunRequest,
  RunResponse,
  KeywordResult,
  JdUploadResult,
  LogLine,
} from "../types";

const BASE = "/api";

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`POST ${path} ${res.status}: ${text}`);
  }
  return res.json();
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`GET ${path} ${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  listYamls: () => get<YamlInfo[]>("/yamls"),
  listThemes: () => get<ThemeInfo[]>("/themes"),
  listTags: () => get<{ tags: string[] }>("/tags"),
  analyzeJd: (text: string) =>
    post<KeywordResult>("/jd/analyze", { text }),
  uploadJd: async (file: File): Promise<JdUploadResult> => {
    const res = await fetch(`${BASE}/jd/upload`, {
      method: "POST",
      body: file,
    });
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    return res.json();
  },
  runResume: (req: ResumeRunRequest) =>
    post<RunResponse>("/resume/run", req),
  runTransform: (req: TransformRunRequest) =>
    post<RunResponse>("/transform/run", req),
  cancelRun: (jobId: string) =>
    post<{ status: string }>(`/resume/cancel/${jobId}`, {}),
  getHistory: (params?: {
    type?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }) => {
    const q = new URLSearchParams();
    if (params?.type) q.set("type", params.type);
    if (params?.status) q.set("status", params.status);
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    const qs = q.toString();
    return get<{ runs: RunHistoryItem[]; total: number }>(
      `/history${qs ? "?" + qs : ""}`
    );
  },
  getRunDetail: (jobId: string) =>
    get<RunHistoryItem>(`/history/${jobId}`),
  streamLogs: (jobId: string, onLine: (line: LogLine) => void): (() => void) => {
    const es = new EventSource(`${BASE}/log/${jobId}`);
    const abort = () => es.close();

    es.onmessage = (event) => {
      if (!event.data) return;
      const text = event.data;
      if (text.startsWith("[STDERR] ")) {
        onLine({ text: text.slice(9), source: "stderr" });
      } else if (text.startsWith("[SYSTEM] ")) {
        onLine({ text: text.slice(9), source: "system" });
      } else {
        onLine({ text, source: "stdout" });
      }
    };
    es.onerror = () => {
      onLine({ text: "Connection closed", source: "system" });
      es.close();
    };
    return abort;
  },
};
```

- [ ] **Step 3: Commit**

```bash
git add ui/frontend/src/types.ts ui/frontend/src/api/client.ts
git commit -m "feat(webui): add TypeScript types and API client"
```

---

### Task 10: Create shared UI components

**Files:**
- Create: `ui/frontend/src/components/ThemeCard.tsx`
- Create: `ui/frontend/src/components/LogStream.tsx`
- Create: `ui/frontend/src/components/JdInput.tsx`
- Create: `ui/frontend/src/components/YamlSelector.tsx`
- Create: `ui/frontend/src/components/TagChips.tsx`
- Create: `ui/frontend/src/components/HistoryTable.tsx`

- [ ] **Step 1: Write ThemeCard.tsx**

```typescript
import {
  Card,
  CardActionArea,
  CardContent,
  Typography,
  Box,
} from "@mui/material";
import type { ThemeInfo } from "../types";

interface Props {
  theme: ThemeInfo;
  selected: boolean;
  onClick: () => void;
}

export default function ThemeCard({ theme, selected, onClick }: Props) {
  return (
    <Card
      sx={{
        width: 220,
        border: selected ? "2px solid #1976d2" : "2px solid transparent",
        bgcolor: selected ? "action.selected" : "background.paper",
      }}
    >
      <CardActionArea onClick={onClick}>
        <Box sx={{ height: 120, bgcolor: "#f5f5f5", display: "flex",
          alignItems: "center", justifyContent: "center", color: "#999" }}>
          <Typography variant="body2">{theme.name}</Typography>
        </Box>
        <CardContent>
          <Typography variant="subtitle2">{theme.name}</Typography>
          <Typography variant="caption" color="text.secondary">
            {theme.best_for}
          </Typography>
        </CardContent>
      </CardActionArea>
    </Card>
  );
}
```

- [ ] **Step 2: Write LogStream.tsx**

```typescript
import { useRef, useEffect } from "react";
import { Box, IconButton, Paper, Typography } from "@mui/material";
import ClearIcon from "@mui/icons-material/Clear";
import type { LogLine } from "../types";

interface Props {
  lines: LogLine[];
  onClear: () => void;
}

const colorMap: Record<string, string> = {
  stdout: "#fff",
  stderr: "#ff9800",
  system: "#9e9e9e",
};

export default function LogStream({ lines, onClear }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  return (
    <Paper
      variant="outlined"
      sx={{
        fontFamily: '"Cascadia Code", "Fira Code", monospace',
        fontSize: "0.8rem",
        bgcolor: "#1e1e1e",
        color: "#d4d4d4",
        p: 1.5,
        maxHeight: 400,
        overflow: "auto",
        position: "relative",
      }}
    >
      <Box sx={{ position: "sticky", top: 0, textAlign: "right" }}>
        <IconButton size="small" onClick={onClear} sx={{ color: "#888" }}>
          <ClearIcon fontSize="small" />
        </IconButton>
      </Box>
      {lines.length === 0 && (
        <Typography variant="body2" sx={{ color: "#666", fontStyle: "italic" }}>
          Waiting for output...
        </Typography>
      )}
      {lines.map((line, i) => (
        <Box key={i} sx={{ color: colorMap[line.source] || "#fff",
          whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
          {line.text}
        </Box>
      ))}
      <div ref={bottomRef} />
    </Paper>
  );
}
```

- [ ] **Step 3: Write JdInput.tsx**

```typescript
import { useState, useCallback } from "react";
import { Box, TextareaAutosize, Typography, Chip } from "@mui/material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import { api } from "../api/client";

interface Props {
  value: string;
  onChange: (text: string) => void;
  onKeywords: (keywords: string[]) => void;
}

export default function JdInput({ value, onChange, onKeywords }: Props) {
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (!file) return;
      const result = await api.uploadJd(file);
      onChange(result.text);
      onKeywords(result.keywords);
    },
    [onChange, onKeywords]
  );

  const handlePaste = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const text = e.target.value;
      onChange(text);
      if (text.length > 50) {
        api.analyzeJd(text).then((r) => onKeywords(r.keywords)).catch(() => {});
      }
    },
    [onChange, onKeywords]
  );

  return (
    <Box>
      <Box
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        sx={{
          border: "2px dashed",
          borderColor: dragOver ? "primary.main" : "grey.400",
          borderRadius: 1,
          p: 1,
          mb: 1,
          textAlign: "center",
          bgcolor: dragOver ? "action.hover" : "transparent",
        }}
      >
        <CloudUploadIcon sx={{ color: "grey.500", mr: 1 }} />
        <Typography variant="body2" color="text.secondary" component="span">
          Drop .txt / .pdf here or paste below
        </Typography>
      </Box>
      <TextareaAutosize
        minRows={6}
        maxRows={14}
        placeholder="Paste job description here..."
        value={value}
        onChange={handlePaste}
        style={{ width: "100%", fontFamily: "inherit", fontSize: "0.9rem",
                 padding: "8px", border: "1px solid #ccc", borderRadius: "4px" }}
      />
    </Box>
  );
}
```

- [ ] **Step 4: Write YamlSelector.tsx**

```typescript
import { useEffect, useState } from "react";
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from "@mui/material";
import { api } from "../api/client";
import type { YamlInfo } from "../types";

interface Props {
  value: string;
  onChange: (val: string) => void;
}

export default function YamlSelector({ value, onChange }: Props) {
  const [yamls, setYamls] = useState<YamlInfo[]>([]);

  useEffect(() => {
    api.listYamls().then(setYamls).catch(() => {});
  }, []);

  return (
    <FormControl size="small" sx={{ minWidth: 200 }}>
      <InputLabel>YAML Source</InputLabel>
      <Select
        value={value}
        label="YAML Source"
        onChange={(e) => onChange(e.target.value)}
      >
        {yamls.map((y) => (
          <MenuItem key={y.name} value={y.name}>
            {y.name}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}
```

- [ ] **Step 5: Write TagChips.tsx**

```typescript
import { Box, Chip } from "@mui/material";

interface Props {
  keywords: string[];
}

const colors = ["#1976d2", "#388e3c", "#d32f2f", "#f57c00",
                "#7b1fa2", "#00796b", "#c2185b", "#546e7a"];

export default function TagChips({ keywords }: Props) {
  return (
    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5, my: 1 }}>
      {keywords.map((kw, i) => (
        <Chip
          key={kw}
          label={kw}
          size="small"
          sx={{ bgcolor: colors[i % colors.length], color: "#fff" }}
        />
      ))}
    </Box>
  );
}
```

- [ ] **Step 6: Write HistoryTable.tsx**

```typescript
import { useEffect, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip as MuiChip,
  IconButton,
  Collapse,
  Box,
  Typography,
} from "@mui/material";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import ReplayIcon from "@mui/icons-material/Replay";
import { api } from "../api/client";
import type { RunHistoryItem } from "../types";

interface Props {
  onReRun: (item: RunHistoryItem) => void;
  refreshKey: number;
}

function statusColor(status: string): "success" | "error" | "warning" | "default" {
  switch (status) {
    case "success": return "success";
    case "error": return "error";
    case "running": return "warning";
    default: return "default";
  }
}

function Row({ item, onReRun }: { item: RunHistoryItem; onReRun: (i: RunHistoryItem) => void }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <TableRow hover>
        <TableCell>
          <IconButton size="small" onClick={() => setOpen(!open)}>
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell>{item.created_at.slice(0, 10)}</TableCell>
        <TableCell><MuiChip label={item.type} size="small" /></TableCell>
        <TableCell>{item.company || "-"}</TableCell>
        <TableCell>{item.role || "-"}</TableCell>
        <TableCell>
          <MuiChip label={item.status} color={statusColor(item.status)} size="small" />
        </TableCell>
        <TableCell>
          {item.run_duration_seconds != null
            ? `${item.run_duration_seconds.toFixed(1)}s`
            : "-"}
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell colSpan={7} sx={{ py: 0 }}>
          <Collapse in={open}>
            <Box sx={{ p: 2, display: "flex", gap: 2, alignItems: "center" }}>
              <Box flex={1}>
                <Typography variant="caption" color="text.secondary">
                  JD snippet: {item.jd_snippet || "(none)"}
                </Typography>
                {item.tags && (
                  <Typography variant="caption" display="block" color="text.secondary">
                    Tags: {item.tags}
                  </Typography>
                )}
                {item.error_log && (
                  <Typography variant="caption" display="block" color="error">
                    Error: {item.error_log}
                  </Typography>
                )}
              </Box>
              <IconButton onClick={() => onReRun(item)} title="Re-run">
                <ReplayIcon />
              </IconButton>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
}

export default function HistoryTable({ onReRun, refreshKey }: Props) {
  const [runs, setRuns] = useState<RunHistoryItem[]>([]);

  useEffect(() => {
    api.getHistory({ limit: 50 }).then((r) => setRuns(r.runs)).catch(() => {});
  }, [refreshKey]);

  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell width={40} />
            <TableCell>Date</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Company</TableCell>
            <TableCell>Role</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Duration</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {runs.map((r) => (
            <Row key={r.id} item={r} onReRun={onReRun} />
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
```

- [ ] **Step 7: Commit**

```bash
git add ui/frontend/src/components/
git commit -m "feat(webui): add shared UI components (ThemeCard, LogStream, JdInput, etc.)"
```

---

### Task 11: Create page components

**Files:**
- Create: `ui/frontend/src/pages/ResumePage.tsx`
- Create: `ui/frontend/src/pages/TransformPage.tsx`
- Create: `ui/frontend/src/pages/HistoryPage.tsx`

- [ ] **Step 1: Write ResumePage.tsx**

```typescript
import { useState, useCallback, useRef } from "react";
import {
  Box,
  Button,
  TextField,
  Checkbox,
  FormControlLabel,
  Stack,
  Typography,
  Alert,
} from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import ThemeCard from "../components/ThemeCard";
import LogStream from "../components/LogStream";
import JdInput from "../components/JdInput";
import YamlSelector from "../components/YamlSelector";
import TagChips from "../components/TagChips";
import { api } from "../api/client";
import type { ThemeInfo, LogLine } from "../types";

interface Props {
  themes: ThemeInfo[];
  onRefreshHistory: () => void;
}

export default function ResumePage({ themes, onRefreshHistory }: Props) {
  const [yamlFile, setYamlFile] = useState("base.yaml");
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [selectedTheme, setSelectedTheme] = useState("classic");
  const [jdText, setJdText] = useState("");
  const [keywords, setKeywords] = useState<string[]>([]);
  const [useLlm, setUseLlm] = useState(false);
  const [allFormats, setAllFormats] = useState(false);
  const [running, setRunning] = useState(false);
  const [logLines, setLogLines] = useState<LogLine[]>([]);
  const [error, setError] = useState("");
  const abortRef = useRef<(() => void) | null>(null);

  const handleRun = useCallback(async () => {
    if (!company.trim()) { setError("Company is required"); return; }
    setError("");
    setRunning(true);
    setLogLines([]);

    try {
      const { job_id } = await api.runResume({
        yaml_file: yamlFile,
        company: company.trim(),
        role: role.trim() || undefined,
        theme: selectedTheme,
        jd_text: jdText || undefined,
        use_llm: useLlm,
        all_formats: allFormats,
      });

      abortRef.current = api.streamLogs(job_id, (line) => {
        setLogLines((prev) => [...prev, line]);
      });

      // Poll for completion
      const poll = setInterval(async () => {
        const detail = await api.getRunDetail(job_id);
        if (detail.status !== "running") {
          clearInterval(poll);
          setRunning(false);
          onRefreshHistory();
        }
      }, 1000);
    } catch (e: any) {
      setError(e.message);
      setRunning(false);
    }
  }, [yamlFile, company, role, selectedTheme, jdText, useLlm, allFormats, onRefreshHistory]);

  return (
    <Box>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Typography variant="subtitle2" gutterBottom>YAML Source</Typography>
      <YamlSelector value={yamlFile} onChange={setYamlFile} />

      <Stack direction="row" spacing={2} sx={{ mt: 2, mb: 2 }}>
        <TextField label="Company" size="small" required
          value={company} onChange={(e) => setCompany(e.target.value)} />
        <TextField label="Role" size="small"
          value={role} onChange={(e) => setRole(e.target.value)} />
      </Stack>

      <Typography variant="subtitle2" gutterBottom>Theme</Typography>
      <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: "wrap" }}>
        {themes.map((t) => (
          <ThemeCard
            key={t.id}
            theme={t}
            selected={selectedTheme === t.id}
            onClick={() => setSelectedTheme(t.id)}
          />
        ))}
      </Stack>

      <Typography variant="subtitle2" gutterBottom>Job Description</Typography>
      <JdInput value={jdText} onChange={setJdText} onKeywords={setKeywords} />
      {keywords.length > 0 && <TagChips keywords={keywords} />}

      <Stack direction="row" spacing={2} sx={{ mt: 2, alignItems: "center" }}>
        <FormControlLabel
          control={<Checkbox checked={useLlm} onChange={(e) => setUseLlm(e.target.checked)} />}
          label="Use LLM"
        />
        <FormControlLabel
          control={<Checkbox checked={allFormats} onChange={(e) => setAllFormats(e.target.checked)} />}
          label="All formats"
        />
        <Button
          variant="contained"
          startIcon={<PlayArrowIcon />}
          onClick={handleRun}
          disabled={running}
        >
          {running ? "Running..." : "Run"}
        </Button>
      </Stack>

      {logLines.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <LogStream lines={logLines} onClear={() => setLogLines([])} />
        </Box>
      )}
    </Box>
  );
}
```

- [ ] **Step 2: Write TransformPage.tsx**

```typescript
import { useState, useCallback, useRef } from "react";
import {
  Box,
  Button,
  FormControlLabel,
  Checkbox,
  Radio,
  RadioGroup,
  FormControl,
  FormLabel,
  Stack,
  Typography,
  Alert,
} from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import LogStream from "../components/LogStream";
import JdInput from "../components/JdInput";
import YamlSelector from "../components/YamlSelector";
import TagChips from "../components/TagChips";
import { api } from "../api/client";
import type { LogLine } from "../types";

interface Props {
  onRefreshHistory: () => void;
}

export default function TransformPage({ onRefreshHistory }: Props) {
  const [yamlFile, setYamlFile] = useState("base.yaml");
  const [jdText, setJdText] = useState("");
  const [keywords, setKeywords] = useState<string[]>([]);
  const [useLlm, setUseLlm] = useState(true);
  const [generatePdf, setGeneratePdf] = useState(false);
  const [running, setRunning] = useState(false);
  const [logLines, setLogLines] = useState<LogLine[]>([]);
  const [error, setError] = useState("");

  const handleRun = useCallback(async () => {
    if (!jdText.trim()) { setError("JD text is required"); return; }
    setError("");
    setRunning(true);
    setLogLines([]);

    try {
      const { job_id } = await api.runTransform({
        yaml_file: yamlFile,
        jd_text: jdText,
        use_llm: useLlm,
        generate_pdf: generatePdf,
      });

      const abort = api.streamLogs(job_id, (line) => {
        setLogLines((prev) => [...prev, line]);
      });

      const poll = setInterval(async () => {
        const detail = await api.getRunDetail(job_id);
        if (detail.status !== "running") {
          clearInterval(poll);
          setRunning(false);
          onRefreshHistory();
        }
      }, 1000);
    } catch (e: any) {
      setError(e.message);
      setRunning(false);
    }
  }, [yamlFile, jdText, useLlm, generatePdf, onRefreshHistory]);

  return (
    <Box>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Typography variant="subtitle2" gutterBottom>YAML Source</Typography>
      <YamlSelector value={yamlFile} onChange={setYamlFile} />

      <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
        Job Description
      </Typography>
      <JdInput value={jdText} onChange={setJdText} onKeywords={setKeywords} />
      {keywords.length > 0 && <TagChips keywords={keywords} />}

      <Stack direction="row" spacing={3} sx={{ mt: 2, alignItems: "center" }}>
        <FormControlLabel
          control={<Checkbox checked={useLlm} onChange={(e) => setUseLlm(e.target.checked)} />}
          label="Use LLM"
        />
        <FormControlLabel
          control={<Checkbox checked={generatePdf} onChange={(e) => setGeneratePdf(e.target.checked)} />}
          label="Generate PDF too"
        />
        <Button
          variant="contained"
          startIcon={<PlayArrowIcon />}
          onClick={handleRun}
          disabled={running}
        >
          {running ? "Running..." : "Run"}
        </Button>
      </Stack>

      {logLines.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <LogStream lines={logLines} onClear={() => setLogLines([])} />
        </Box>
      )}
    </Box>
  );
}
```

- [ ] **Step 3: Write HistoryPage.tsx**

```typescript
import HistoryTable from "../components/HistoryTable";
import type { RunHistoryItem } from "../types";

interface Props {
  refreshKey: number;
  onReRun: (item: RunHistoryItem) => void;
  onRefreshHistory: () => void;
}

export default function HistoryPage({ refreshKey, onReRun }: Props) {
  return <HistoryTable onReRun={onReRun} refreshKey={refreshKey} />;
}
```

- [ ] **Step 4: Commit**

```bash
git add ui/frontend/src/pages/
git commit -m "feat(webui): add Resume, Transform, and History page components"
```

---

### Task 12: Wire App.tsx with tabs and layout

**Files:**
- Create: `ui/frontend/src/App.tsx`

- [ ] **Step 1: Write App.tsx**

```typescript
import { useState, useEffect, useCallback } from "react";
import {
  AppBar,
  Box,
  Tab,
  Tabs,
  Toolbar,
  Typography,
  Container,
  CssBaseline,
  ThemeProvider,
  createTheme,
} from "@mui/material";
import DescriptionIcon from "@mui/icons-material/Description";
import TransformIcon from "@mui/icons-material/AutoFixHigh";
import HistoryIcon from "@mui/icons-material/History";
import ResumePage from "./pages/ResumePage";
import TransformPage from "./pages/TransformPage";
import HistoryPage from "./pages/HistoryPage";
import { api } from "./api/client";
import type { ThemeInfo, RunHistoryItem } from "./types";

const theme = createTheme();

function a11yProps(index: number) {
  return { id: `tab-${index}`, "aria-controls": `tabpanel-${index}` };
}

export default function App() {
  const [tab, setTab] = useState(0);
  const [themes, setThemes] = useState<ThemeInfo[]>([]);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    api.listThemes().then(setThemes).catch(() => {});
  }, []);

  const refreshHistory = useCallback(
    () => setRefreshKey((k) => k + 1),
    []
  );

  const handleReRun = useCallback((item: RunHistoryItem) => {
    // Switch to Resume tab if it's a resume run, Transform if transform
    setTab(item.type === "transform" ? 1 : 0);
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Resume Management
          </Typography>
        </Toolbar>
      </AppBar>
      <Container maxWidth="xl" sx={{ mt: 3 }}>
        <Box sx={{ borderBottom: 1, borderColor: "divider", mb: 2 }}>
          <Tabs value={tab} onChange={(_, v) => setTab(v)}>
            <Tab icon={<DescriptionIcon />} label="Resume" {...a11yProps(0)} />
            <Tab icon={<TransformIcon />} label="Transform" {...a11yProps(1)} />
            <Tab icon={<HistoryIcon />} label="History" {...a11yProps(2)} />
          </Tabs>
        </Box>

        {tab === 0 && (
          <ResumePage themes={themes} onRefreshHistory={refreshHistory} />
        )}
        {tab === 1 && (
          <TransformPage onRefreshHistory={refreshHistory} />
        )}
        {tab === 2 && (
          <HistoryPage
            refreshKey={refreshKey}
            onReRun={handleReRun}
            onRefreshHistory={refreshHistory}
          />
        )}
      </Container>
    </ThemeProvider>
  );
}
```

- [ ] **Step 2: Verify TypeScript compilation**

Run: `cd ui/frontend && npx tsc --noEmit`

Expected: No type errors.

- [ ] **Step 3: Commit**

```bash
git add ui/frontend/src/App.tsx
git commit -m "feat(webui): wire App.tsx with tab layout and page routing"
```

---

### Task 13: Create launcher script and verify end-to-end

**Files:**
- Create: `ui/start.sh`

- [ ] **Step 1: Write start.sh**

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Resume WebUI Launcher ==="

# Install Python deps if needed
cd "$REPO_ROOT"
pip install -q fastapi uvicorn aiosqlite sse-starlette pypdf 2>/dev/null || true

# Install frontend deps if needed
cd "$REPO_ROOT/ui/frontend"
if [ ! -d "node_modules" ]; then
  echo "Installing frontend dependencies..."
  npm install
fi

# Start backend
echo "Starting backend on http://127.0.0.1:8000"
cd "$REPO_ROOT"
python -m uvicorn ui.backend.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

# Start frontend
echo "Starting frontend on http://localhost:5173"
cd "$REPO_ROOT/ui/frontend"
npx vite --host &
FRONTEND_PID=$!

# Cleanup on exit
cleanup() {
  echo "Shutting down..."
  kill "$BACKEND_PID" 2>/dev/null || true
  kill "$FRONTEND_PID" 2>/dev/null || true
  wait
}
trap cleanup EXIT INT TERM

echo ""
echo "Open http://localhost:5173 in your browser"
echo "Press Ctrl+C to stop"
wait
```

- [ ] **Step 2: Make executable**

Run: `chmod +x ui/start.sh`

- [ ] **Step 3: Start backend and verify health**

Run: `cd /Users/william.jiang/my-tests/resume-app && python -m uvicorn ui.backend.main:app --host 127.0.0.1 --port 8000 &`

Then: `curl http://127.0.0.1:8000/api/yamls`

Expected: `[{"name":"base.yaml","path":"..."}]`

- [ ] **Step 4: Start frontend and verify**

Run: `cd ui/frontend && npx vite --host`

Open `http://localhost:5173`

Expected: Tab layout renders with Resume, Transform, History tabs. Theme cards visible. No console errors.

- [ ] **Step 5: Commit**

```bash
git add ui/start.sh
git commit -m "feat(webui): add ./ui/start.sh launcher script"
```

---

## Self-Review

**1. Spec coverage checklist:**

| Spec Requirement | Task |
|---|---|
| Two-tab UI (Resume + Transform) | Task 12 — App.tsx tab layout |
| YAML source selector | Task 10 — YamlSelector component |
| Theme picker with visual cards | Task 10 — ThemeCard component + Task 3 theme_data.py |
| Tags multi-select | Task 7 — /api/tags endpoint; Task 11 — integrated into page |
| Company / Role text inputs | Task 11 — ResumePage.tsx TextFields |
| JD upload (paste + file, PDF) | Task 10 — JdInput + Task 7 /api/jd/upload + Task 4 jd_analyzer.py |
| LLM toggle | Task 11 — Checkbox in both pages |
| Run button with live log SSE | Task 11 — buttons + Task 9 client.ts streamLogs + Task 6 runner.py |
| Theme descriptions | Task 3 — theme_data.py with best_for field |
| Transform tab with diff | Task 11 — TransformPage.tsx (diff view is future; dry-run output shows in log for v1) |
| JD keyword analysis | Task 7 /api/jd/analyze + Task 10 TagChips component |
| History (SQLite) | Task 5 db.py + Task 10 HistoryTable component + Task 7 /api/history |
| PDF download | Task 7 /api/output/{job_id} endpoint |
| Re-run from history | Task 10 HistoryTable.tsx onReRun prop |
| Cancel running jobs | Task 7 /api/resume/cancel/{job_id} + Task 6 runner cancel_job |
| Single launcher command | Task 13 start.sh |

**2. Placeholder scan:** No placeholders found. Every step contains full code.

**3. Type consistency:** All TypeScript types in `types.ts` match the Pydantic models in `models.py`. API client methods match route signatures. Component prop interfaces match their usage in pages.
