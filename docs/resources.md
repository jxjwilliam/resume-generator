# Resources & Development Setup

What this app needs to **run**.

---

## Run Requirements

| What | Needed? | Why |
|---|---|---|
| Python ≥3.11 | **Yes** | Core runtime |
| `pip install -r requirements.txt` | **Yes** | All Python deps (13 packages, all from PyPI) |
| Virtual environment (venv) | Recommended | Keeps deps isolated; app doesn't care either way |
| `.env` file | Optional | Only for LLM features |
| API keys (DeepSeek / Kimi / MiniMax) | Optional | Only for `--llm` / `--tailor` / `--boost` |
| Node.js + npm | Optional | Only for WebUI frontend dev (Docker builds it for deploy) |
| Internet connection | Optional | Only for LLM API calls |
| Docker | Deploy only | `Dockerfile` + `render.yaml` for Render.com Blueprint deploy; not needed for local dev |
| Render.com account | Deploy only | Blueprint consumes the repo's `render.yaml` |
| Supabase / PostgreSQL / any DB server | **No** | Only local SQLite (`runs.db`, zero config) |
| Redis / Kafka / any message queue | **No** | Not used |

> Deploy profile (Render free tier): ephemeral disk — `runs.db` + `output/` are wiped on
> redeploy. Download deliverables before redeploying.

### What "pip install" Gets You

```
pyyaml          — Parse base.yaml
rendercv[full]  — PDF + HTML rendering (extras add typst + rendercv_fonts,
                  required by the classic sidebar layout)
python-docx     — DOCX generation (--docx)
openai          — LLM API client (--llm / --tailor / --boost)
python-dotenv   — Read .env
fastapi         — WebUI backend
uvicorn         — ASGI server
aiosqlite       — Async SQLite for WebUI
sse-starlette   — SSE log streaming
pypdf           — JD PDF upload parsing
python-multipart — Form parsing
```

No system-level C libs, no compilation step (on normal platforms).

### Database

A single local SQLite file at `runs.db` — auto-created, zero config, no server.

### Docker / Render.com deploy

- `Dockerfile` — 2-stage: `node:22-alpine` builds the React SPA → `ui/frontend/dist`;
  `python:3.12-slim` installs `requirements.txt` and runs
  `python -m uvicorn ui.backend.main:app --port ${PORT:-8000}` (one process serves API + SPA).
- `render.yaml` — Render Blueprint: `runtime: docker`, `healthCheckPath: /api/health`,
  optional LLM env vars (`sync: false` → fill in the Dashboard).
- Requires `assets/william-jiang.jpg` in the image (rendercv theme photo, gitignored —
  commit with `git add -f assets/william-jiang.jpg`).
- No disk persistence on the free tier (note above).

### Venv Quick Ref

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

The app works identically with or without a venv. `ui/start.sh` installs
packages globally regardless. Venv is just good practice.

### .env Quick Ref

Only needed for optional features. Copy the template:

```bash
cp .env.example .env
```

| Key | Needed For |
|---|---|
| `LLM_PROVIDER` | Choosing LLM backend (`deepseek` / `kimi` / `minimax`) |
| `DEEPSEEK_API_KEY` / `KIMI_API_KEY` / `MINIMAX_API_KEY` | `--llm` / `--tailor` / `--boost` |

---

## Development Tooling

### CodeGraph

Pre-computed symbol graph — returns verbatim source + callers + call paths in
one call instead of grep-read loops. Configured globally; `.codegraph/`
holds the auto-generated index (gitignored, do not edit).

### Config Files

| File | Purpose |
|---|---|
| `.claude/CLAUDE.md` | Claude Code project context — architecture, CLI ref, conventions |
| `.codegraph/` | Auto-generated symbol index (gitignored, do not edit) |
| `.vscode/settings.json` | Python type checking config (Pyright) |
