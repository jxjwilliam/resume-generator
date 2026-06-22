# Resume Management System

A 3-layer system for maintaining a single source-of-truth resume (YAML), composing job-specific variants, and rendering PDF + HTML via rendercv. Includes a **JD quality pipeline** for ATS scoring, bullet ranking, and optional LLM tailoring.

## Repo State

**Implemented.** Core system plus quality pipeline (June 2026):

- `base.yaml` — single source of truth
- `resume.py` — composition CLI (`build`, `analyze`, `score`, `compare`, `tags`, `log`, `cover-letter`)
- `compose.py` — shared bullet ranking + caps (used by `resume.py` and `transform.py`)
- `jd_parser.py` — structured JD keyword parsing
- `ats.py` — deterministic ATS scoring + multi-JD compare
- `transform.py` — RxResume sync
- `ui/` — WebUI (Resume, Transform, **Compare**, History tabs)

## Architecture (3 Layers + Quality Pipeline)

```
base.yaml → compose.py (rank + cap) → resume.py → rendercv (PDF+HTML)
                ↑
         jd_parser.py + ats.py (optional LLM: --llm --tailor --boost)
```

- **Layer 1** — `base.yaml`: tagged experience, skills, projects, education, cover letters. Optional `variants[]` per bullet.
- **Layer 2** — `resume.py` + `compose.py`: filter by tags + status, rank bullets, cap length, optional LLM tailor/boost.
- **Layer 3** — rendercv / python-docx / rxresu.me: rendering only.

## Key Files

| File | Purpose |
|---|---|
| `base.yaml` | **Single source of truth — manually edited.** |
| `resume.py` | Composition engine CLI |
| `compose.py` | Shared ranking, filtering, skills reorder |
| `jd_parser.py` | JD → hard skills, title, domain, seniority |
| `ats.py` | ATS score /100 + `compare_jds()` |
| `transform.py` | RxResume sync |
| `docs/resume-quality-pipeline.md` | **Quality pipeline reference (read this for JD features)** |
| `docs/resume-system-implementation.md` | Original system design + schema |
| `docs/rxresume-integration-guide.md` | RxResume sync guide |
| `variants/*.yaml` | Auto-generated per-job YAML |
| `output/` | PDFs, DOCX, `ats-report.json`, `bullet-diff.json` (gitignored) |

## CLI Commands

```bash
# Tags + history
python resume.py tags
python resume.py log

# Quality pipeline (no LLM required)
python resume.py analyze --jd jds/target.txt
python resume.py score --jd jds/target.txt --max-bullets 3
python resume.py compare --jds-dir jds/

# Build — manual tags
python resume.py build --company "BestIT" --role "Senior SWE" \
  --tags backend,python,api --template classic --max-bullets 3 --max-jobs 4

# Build — full LLM pipeline
python resume.py build --company "BestIT" --jd jds/target.txt \
  --llm --tailor --boost --template auto --docx

# RxResume
python transform.py --dry-run --all-skills
python transform.py --resume-id <ID> --all-skills --max-bullets 3
```

## Build Flags (quality pipeline)

| Flag | Default | Purpose |
|---|---|---|
| `--max-bullets` | 4 | Cap bullets per job |
| `--max-jobs` | 0 | Cap experience entries (0 = unlimited) |
| `--template auto` | — | Pick theme from JD signals |
| `--llm` | off | Tags + headline + summary from JD |
| `--tailor` | off | LLM bullet rewrite (truth-first) |
| `--boost` | off | Second pass for verified missing skills |

## Important Conventions

- **base.yaml is the only manually edited file.** Everything else is generated.
- **Status flags:** `active` / `deprecated` / `conflicted`
- **LLM never fabricates** — only rephrases verified `base.yaml` content
- **ATS scoring is deterministic** — LLM is not used to grade
- Builds with `--jd` write `output/{slug}/ats-report.json`
- `--tailor` / `--boost` write `output/{slug}/bullet-diff.json`

## LLM Integration

Set `LLM_PROVIDER` in `.env` to switch between **deepseek**, **kimi**, and **minimax**:

```env
LLM_PROVIDER=kimi   # or deepseek | minimax

DEEPSEEK_API_KEY=...
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-pro

KIMI_API_KEY=...
KIMI_BASE_URL=https://api.moonshot.cn/v1      # China inland
KIMI_MODEL=kimi-k2.5

MINIMAX_API_KEY=...
MINIMAX_BASE_URL=https://api.minimaxi.com/v1  # China inland
MINIMAX_MODEL=MiniMax-M2.5

RXRESU_API_KEY=...   # transform.py only
```

```bash
python resume.py llm-providers                          # list providers + models
python resume.py build ... --llm --llm-provider kimi     # per-command override
```

Full reference: [`docs/llm-providers.md`](docs/llm-providers.md)

Swap any provider's base URL to Ollama (`http://localhost:11434/v1`) for local inference.

## Rendercv Themes

| Theme | Best for |
|---|---|
| `auto` | Pick from JD (WebUI + CLI) |
| `classic` | FAANG, large tech, senior |
| `sb2nov` | Standard SWE, ATS-friendly |
| `moderncv` | Startup, product |
| `engineeringresumes` | Maximally ATS-optimised |

## Git Strategy

- **Commit:** `base.yaml`, `resume.py`, `compose.py`, `jd_parser.py`, `ats.py`, `transform.py`, `applications.json`, `variants/`, `jds/`, `ui/`
- **Ignore:** `output/`, `.env`, `__pycache__/`

## User Identity (from `docs/init.md`)

- Name: **William Jiang**
- LinkedIn: `https://www.linkedin.com/in/william-jiang-226a7616/`
- GitHub: `https://williamjxj.github.io/`
