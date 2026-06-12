import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from .db import init_db, get_run, list_runs
from .jd_analyzer import extract_keywords, extract_text_from_pdf
from .models import (
    ResumeRunRequest,
    TransformRunRequest,
    RunResponse,
    YamlInfo,
)
from .runner import start_job, stream_logs, cancel_job
from .theme_data import THEMES

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


@app.get("/api/yamls")
async def list_yamls():
    return _list_yaml_files()


@app.get("/api/themes")
async def list_themes():
    return THEMES


@app.get("/api/tags")
async def list_tags():
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
        output_dir = REPO_ROOT / "output"
        if output_dir.exists():
            candidates = sorted(output_dir.rglob("*.pdf"))
            if candidates:
                output_path = str(candidates[0])
    if not output_path:
        raise HTTPException(404, "No output files found")
    return FileResponse(output_path, media_type="application/pdf",
                        filename=Path(output_path).name)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ui.backend.main:app", host="127.0.0.1", port=8000, reload=True)
