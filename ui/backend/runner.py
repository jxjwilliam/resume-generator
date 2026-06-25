import asyncio
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .db import insert_run, update_run, scan_output_files

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT_DIR = os.path.join(REPO_ROOT, "output")

_running_jobs: dict[str, dict] = {}


async def stream_logs(job_id: str):
    """Async generator that yields log lines from a job's queue as SSE events."""
    entry = _running_jobs.get(job_id)
    if entry is None:
        return
    queue: asyncio.Queue = entry["log_queue"]
    while True:
        try:
            line = await asyncio.wait_for(queue.get(), timeout=300)
        except asyncio.TimeoutError:
            continue
        if line is None:
            break
        yield f"data: {line}\n\n"


async def _run_process(cmd: list[str], job_id: str, log_queue: asyncio.Queue):
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
            output_files = scan_output_files()
            ats_kwargs = {}
            try:
                from history_db import ats_from_output_files
                ats = ats_from_output_files(output_files)
                if ats:
                    ats_kwargs = ats
            except Exception:
                pass
            await update_run(
                job_id, status="success", run_duration_seconds=duration,
                output_files=output_files,
                **ats_kwargs,
            )
            await log_queue.put("[SYSTEM] Job completed successfully")
            if output_files:
                urls = "\n".join(f"  /api/output/{job_id}/download?name={f['name']}" for f in output_files)
                await log_queue.put(f"[SYSTEM] Output files:\n{urls}")
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
    entry = _running_jobs.get(job_id)
    if entry is None:
        return False
    entry["task"].cancel()
    return True
