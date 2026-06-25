import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
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
    JdCompareRequest,
    JdCompareResponse,
    JdPreviewRequest,
)
from .runner import start_job, stream_logs, cancel_job
from .theme_data import THEMES, RX_TEMPLATES

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


def _load_yaml(yaml_file: str) -> dict:
    import yaml

    yaml_path = REPO_ROOT / yaml_file
    if not yaml_path.exists():
        return {}
    with open(yaml_path) as f:
        return yaml.safe_load(f) or {}


def _resume_text_blob(base: dict) -> str:
    parts: list[str] = []
    for job in base.get("experience", []):
        for b in job.get("bullets", []):
            if b.get("status") != "deprecated":
                parts.append(b.get("text", "").lower())
    for items in base.get("skills", {}).values():
        for s in items:
            if s.get("status", "active") == "active":
                parts.append(s.get("name", "").lower())
    return " ".join(parts)


def _jd_analysis_payload(text: str, base: dict, tags: str | list | None = None) -> dict:
    import sys
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from jd_parser import parse_jd, keyword_match_report

    parsed = parse_jd(text, base)
    match = keyword_match_report(parsed, base, tags)
    blob = _resume_text_blob(base)
    soft_skills = parsed.get("soft_skills", [])
    domain_kw = parsed.get("domain_keywords", [])
    matched_soft = [s for s in soft_skills if s.lower() in blob]
    missing_soft = [s for s in soft_skills if s.lower() not in blob]
    matched_domain = [d for d in domain_kw if d.lower() in blob]

    return {
        "keywords": parsed.get("keywords", []),
        "hard_skills": parsed.get("hard_skills", []),
        "title_keywords": parsed.get("title_keywords", []),
        "domain_keywords": domain_kw,
        "soft_skills": soft_skills,
        "role_title": parsed.get("role_title", ""),
        "seniority": parsed.get("seniority", "unknown"),
        "domain": parsed.get("domain"),
        "matched_skills": match.get("matched_skills", []),
        "missing_skills": match.get("missing_skills", []),
        "matched_soft_skills": matched_soft,
        "missing_soft_skills": missing_soft,
        "matched_domain_keywords": matched_domain,
        "top_bullets": match.get("top_bullets", []),
    }


@app.get("/api/yamls")
async def list_yamls():
    return _list_yaml_files()


@app.get("/api/themes")
async def list_themes():
    return THEMES


@app.get("/api/rxresume-templates")
async def list_rx_templates():
    return RX_TEMPLATES


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

    yaml_file = data.get("yaml_file", "base.yaml")
    base = _load_yaml(yaml_file)
    tags = data.get("tags")
    if isinstance(tags, list):
        tags = ",".join(tags) if tags else None
    return _jd_analysis_payload(text, base, tags)


@app.post("/api/jd/preview")
async def preview_jd(data: JdPreviewRequest):
    text = data.text.strip()
    if len(text) < 20:
        raise HTTPException(400, "JD text too short for preview")

    import sys
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from jd_parser import parse_jd
    from compose import preview_experience_jobs

    base = _load_yaml(data.yaml_file)
    parsed = parse_jd(text, base)
    tags = ",".join(data.tags) if data.tags else None
    jobs = preview_experience_jobs(
        base.get("experience", []),
        tags=tags,
        max_bullets=data.max_bullets,
        max_jobs=data.max_jobs,
        jd_keywords=parsed.get("all_keywords"),
    )
    included_bullets = sum(
        1 for j in jobs for b in j["bullets"] if b.get("included")
    )
    excluded_bullets = sum(
        1 for j in jobs for b in j["bullets"] if not b.get("included")
    )
    return {
        "jobs": jobs,
        "jobs_included": sum(1 for j in jobs if j.get("job_included")),
        "bullets_included": included_bullets,
        "bullets_excluded": excluded_bullets,
    }


@app.post("/api/jd/upload")
async def upload_jd(file: UploadFile):
    temp = REPO_ROOT / f".ui_temp_jd{Path(file.filename or 'file.txt').suffix}"
    content = await file.read()
    temp.write_bytes(content)
    try:
        if temp.suffix.lower() == ".pdf":
            text = extract_text_from_pdf(str(temp))
        else:
            text = temp.read_text("utf-8", errors="replace")
    finally:
        temp.unlink(missing_ok=True)

    if not text:
        raise HTTPException(400, "Could not extract text from file")

    base = _load_yaml("base.yaml")
    payload = _jd_analysis_payload(text, base, None)
    return {"text": text[:5000], **payload}


@app.post("/api/jd/compare", response_model=JdCompareResponse)
async def compare_jds_api(data: JdCompareRequest):
    if len(data.jds) < 2:
        raise HTTPException(400, "At least 2 JDs required")
    if len(data.jds) > 5:
        raise HTTPException(400, "Maximum 5 JDs")

    import sys
    import yaml
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from ats import compare_jds

    yaml_path = REPO_ROOT / "base.yaml"
    base = {}
    if yaml_path.exists():
        with open(yaml_path) as f:
            base = yaml.safe_load(f)

    entries = [(item.label, item.text) for item in data.jds]
    tags = ",".join(data.tags) if data.tags else None
    result = compare_jds(
        base, entries, tags=tags,
        max_bullets=data.max_bullets,
        max_jobs=data.max_jobs,
    )
    return result


def _build_resume_cmd(args: ResumeRunRequest, jd_file: str | None) -> list[str]:
    cmd = [sys.executable, "resume.py", "build",
           "--yaml", args.yaml_file,
           "--company", args.company,
           "--template", args.theme]
    if args.role:
        cmd += ["--role", args.role]
    if args.tags:
        cmd += ["--tags", ",".join(args.tags)]
    if jd_file:
        cmd += ["--jd", jd_file]
    if not args.use_llm:
        cmd += ["--no-llm"]
    if args.llm_provider:
        cmd += ["--llm-provider", args.llm_provider]
    if args.tailor:
        cmd += ["--tailor"]
    if args.enhance:
        cmd += ["--enhance"]
    if args.boost:
        cmd += ["--boost"]
    if args.max_bullets != 4:
        cmd += ["--max-bullets", str(args.max_bullets)]
    if args.max_jobs:
        cmd += ["--max-jobs", str(args.max_jobs)]
    if args.pages != 2:
        cmd += ["--pages", str(args.pages)]
    if args.max_projects != 4:
        cmd += ["--max-projects", str(args.max_projects)]
    if args.no_projects:
        cmd += ["--no-projects"]
    if args.all_formats:
        cmd += ["--all-formats"]
    if args.locale and args.locale != "en":
        cmd += ["--locale", args.locale]
    if args.cover_letter:
        cmd += ["--cover-letter"]
    if args.docx:
        cmd += ["--docx"]
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

    cmd = [sys.executable, "transform.py",
           "--yaml", args.yaml_file,
           "--template", args.template]
    if args.resume_id:
        cmd += ["--resume-id", args.resume_id]
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


@app.get("/api/output/{job_id}/files")
async def get_output_files(job_id: str):
    """Return list of output files for a completed run."""
    run = await get_run(job_id)
    if not run:
        raise HTTPException(404, "Run not found")
    files = run.get("output_files") or []
    # If DB has no output_files but files exist on disk, scan now
    if not files:
        output_dir = REPO_ROOT / "output"
        if output_dir.exists():
            candidates = sorted(output_dir.rglob("*"))
            # Try to match by slug from run metadata
            if run.get("company") and run.get("role"):
                from .db import scan_output_files
                files = scan_output_files(run.get("slug") or run.get("id") or "")
    return {"files": files}


@app.get("/api/output/{job_id}")
async def get_output(job_id: str, name: str | None = None):
    run = await get_run(job_id)
    if not run:
        raise HTTPException(404, "Run not found")

    if name:
        fpath = await _resolve_output_path(job_id, name, run)
        media_type = _mime_for_file(name)
        return FileResponse(str(fpath), media_type=media_type, filename=name)

    # Legacy: serve first PDF
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


@app.get("/api/output/{job_id}/download")
async def download_output(job_id: str, name: str):
    """Alias for file download (used by WebUI links)."""
    return await get_output(job_id, name=name)


@app.get("/api/output/{job_id}/content")
async def get_output_content(job_id: str, name: str):
    """Return parsed JSON or raw text for an output artifact."""
    run = await get_run(job_id)
    if not run:
        raise HTTPException(404, "Run not found")
    fpath = await _resolve_output_path(job_id, name, run)
    text = fpath.read_text(encoding="utf-8", errors="replace")
    if fpath.suffix.lower() == ".json":
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            raise HTTPException(500, f"Invalid JSON in {name}")
    return {"name": name, "text": text}


def _mime_for_file(name: str) -> str:
    ext = Path(name).suffix.lower()
    return {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".html": "text/html",
        ".txt": "text/plain",
        ".json": "application/json",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".typ": "text/plain",
    }.get(ext, "application/octet-stream")


async def _resolve_output_path(job_id: str, name: str, run: dict) -> Path:
    output_dir = REPO_ROOT / "output"
    if not output_dir.exists():
        raise HTTPException(404, "No output directory")

    if run.get("output_files"):
        for f in run["output_files"]:
            if f["name"] == name:
                fpath = output_dir / f["slug"] / f["name"]
                if fpath.exists():
                    return fpath

    for subdir in sorted(output_dir.iterdir(), reverse=True):
        if subdir.is_dir():
            candidate = subdir / name
            if candidate.exists():
                return candidate

    raise HTTPException(404, f"File '{name}' not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ui.backend.main:app", host="127.0.0.1", port=8000, reload=True)
