# Resume Management System

A 3-layer system for maintaining canonical resume sources (YAML), layering
**positioning profiles** on top for job-market focus, composing job-specific
variants, and rendering PDF + HTML via rendercv. Includes a **JD quality
pipeline** for ATS scoring, bullet ranking, and optional LLM tailoring.

## Repo State

**Implemented.** Core system plus full quality pipeline (June 2026):

- `profiles/career-en.yaml` — canonical English career source (variants, metrics, keywords on bullets)
- `profiles/base-zh-cto.yaml`, `profiles/base-zh-partner.yaml` — standalone Chinese resume sources
- `profiles/china-cto.yaml`, `profiles/china-partner.yaml`, `profiles/na-ai-engineer.yaml`, `profiles/na-software-engineer.yaml` — positioning profiles (selection + presentation configs that layer on `career-en.yaml`)
- `src/profiles.py` — profile/source resolver (`load_effective()`, `list_profiles()`)
- `resume.py` — composition CLI (`build`, `analyze`, `score`, `compare`, `interview`, `tags`, `log`, `cover-letter`)
- `src/compose.py` — shared bullet ranking + caps (used by `resume.py`)
- `src/jd_parser.py` — structured JD keyword parsing
- `src/ats.py` — deterministic ATS scoring + multi-JD compare + `score_variant_yaml()`
- `src/llm_pipeline.py` — LLM structured JD parse + hybrid bullet rescoring
- `src/tailor_validation.py` — anti-hallucination for tailor rewrites
- `src/page_budget.py` — one-page line estimator + trim loop
- `src/provenance.py` — `provenance.json` per build
- `ui/` — WebUI (Resume, Transform, Compare, History tabs)

## Architecture (3 Layers + Quality Pipeline)

```
career-en.yaml ← na-ai-engineer.yaml / china-cto.yaml / ... (positioning profiles)
     │
     ↓ src/profiles.py (resolve profile → source, layer priorities)
effective base → src/compose.py (rank + cap) → src/cli.py → rendercv (PDF+HTML)
     ↑
 src/jd_parser.py + src/ats.py + src/llm_pipeline.py (optional LLM: --llm --tailor --boost)
```

- **Layer 1** — canonical sources (`career-en.yaml`, `base-zh-*.yaml`): tagged experience, skills, projects, education, cover letters. Optional `variants[]`, `metrics[]`, `keywords[]` per bullet. Positioning profiles (`source.career` + `experience_priority`, `skills_priority`, `projects_priority`, `headline`, `summary`, `recent_jobs`, `old_experience_max_bullets`) re-focus a source without duplicating it.
- **Layer 2** — `src/cli.py` + `src/compose.py`: filter by tags + status, rank bullets, cap length, senior job filter, page budget, optional LLM tailor/boost.
- **Layer 3** — rendercv / python-docx / rxresu.me: rendering only. Sidebar themes (`classic`) are post-processed by `src/sidebar_layout.py` before the PDF is compiled.

## Key Files

| File | Purpose |
|---|---|
| `profiles/career-en.yaml` | **Canonical English source — manually edited.** |
| `profiles/base-zh-*.yaml` | Standalone Chinese sources (same schema). |
| `profiles/*-engineer.yaml`, `profiles/china-*.yaml` | Positioning profiles → `source.career` + selection priorities. |
| `src/profiles.py` | Resolves any `--yaml` (source or profile) into an effective base. |
| `resume.py` | Composition engine CLI |
| `src/compose.py` | Shared ranking, filtering, skills reorder |
| `src/jd_parser.py` | JD → hard skills, title, domain, seniority |
| `src/ats.py` | ATS score /100 + `compare_jds()` |
| `src/llm_pipeline.py` | LLM JD parse + bullet rescoring |
| `src/tailor_validation.py` | Reject bad tailor rewrites |
| `src/page_budget.py` | `--pages` trim loop |
| `src/sidebar_layout.py` | Two-column sidebar layout for `classic` (rewrites the .typ + compiles with typst) |
| `src/provenance.py` | Build provenance JSON |
| `docs/resume-quality-pipeline.md` | **Quality pipeline reference (read this for JD features)** |
| `docs/resume-system-implementation.md` | Original system design + schema |
| `variants/*.yaml` | Auto-generated per-job YAML |
| `output/` | PDFs, DOCX, `ats-report.json`, `bullet-diff.json`, `provenance.json` (gitignored) |
| `Dockerfile` | Docker image (2-stage: node builds SPA, python runs uvicorn `ui.backend.main:app`) |
| `render.yaml` | Render.com Blueprint — `runtime: docker`, `/api/health`, optional LLM env vars |
| `ui/backend/main.py` | FastAPI app — API + SPA serving (`/api/health`, `/assets`, SPA fallback) |

## CLI Commands

```bash
# Tags + history
python resume.py tags
python resume.py log
python resume.py profiles        # list sources + positioning profiles

# Quality pipeline (no LLM required)
python resume.py analyze --jd jds/target.txt
python resume.py score --jd jds/target.txt --max-bullets 3
python resume.py score --jd jds/target.txt --variant variants/foo.yaml
python resume.py score --jd jds/target.txt --yaml profiles/na-ai-engineer.yaml
python resume.py compare --jds-dir jds/
python resume.py interview --jd jds/target.txt --tags ai,python

# Build — manual tags
python resume.py build --company "BestIT" --role "Senior SWE" \
  --tags backend,python,api --template classic --max-bullets 3 --max-jobs 4 --pages 1

# Build — positioning profile (auto-loads career-en.yaml)
python resume.py build --yaml profiles/na-ai-engineer.yaml --company "BestIT" \
  --role "Senior AI Engineer" --tags ai --template classic --max-bullets 3

# Build — Chinese source
python resume.py build --yaml profiles/base-zh-cto.yaml --company "某公司" \
  --role "CTO" --locale zh-CN --template classic

# Build — full LLM pipeline
python resume.py build --company "BestIT" --jd jds/target.txt \
  --llm --tailor --boost --template auto --pages 1 --target-score 75

```

**Default build outputs 3 files** in `output/{slug}/`:
`William_Jiang-{role}.pdf`, `resume.docx` (Claude-style formatting), and
`cover-letter-{company}.docx`. PNG/HTML are only produced with
`--all-formats`; opt out of DOCX/cover letter with `--no-docx` /
`--no-cover-letter`.

## Build Flags (quality pipeline)

| Flag | Default | Purpose |
|---|---|---|
| `--max-bullets` | 4 | Cap bullets per job |
| `--max-jobs` | 0 | Cap experience entries (0 = unlimited) |
| `--pages` | 2 | Page budget trim (0 = disabled) |
| `--no-projects` | off | Omit projects for shorter resume |
| `--template auto` | — | Pick theme from JD signals |
| `--target-score` | 0 | Re-run with tailor+boost if below threshold |
| `--llm` | off | Tags + headline + summary + JD parse + bullet rescoring |
| `--tailor` | off | LLM bullet rewrite (truth-first + validation) |
| `--boost` | off | Second pass for verified missing skills |
| `--docx` / `--no-docx` | on | Generate `resume.docx` (styled like the PDF/Claude reference) |
| `--cover-letter` / `--no-cover-letter` | on | Generate `cover-letter-{company}.docx` |

## Important Conventions

- **Canonical sources and positioning profiles are the only manually edited files.** Everything else is generated.
- `--yaml` accepts either a full source (`career-en.yaml`, `base-zh-*.yaml`) or a positioning profile (`na-ai-engineer.yaml`, ...). Profiles resolve to their `source.career` and layer headline/summary/ordering/caps on top.
- `recent_jobs` (default 5) = how many `experience_priority` companies keep full bullets; listed-but-older jobs get `old_experience_max_bullets`.
- **Status flags:** `active` / `deprecated` / `conflicted`
- **LLM never fabricates** — only rephrases verified source content
- **ATS scoring is deterministic** — LLM is not used to grade
- Builds with `--jd` write `output/{slug}/ats-report.json` + `provenance.json`
- `--tailor` / `--boost` write `output/{slug}/bullet-diff.json`
- `--pages` writes `output/{slug}/page-budget.json`

## LLM Integration

Set `LLM_PROVIDER` in `.env` to switch between **deepseek**, **kimi**, and **minimax**:

```env
LLM_PROVIDER=kimi   # or deepseek | minimax

DEEPSEEK_API_KEY=...
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash

KIMI_API_KEY=...
KIMI_BASE_URL=https://api.moonshot.cn/v1      # China inland
KIMI_MODEL=kimi-k3

MINIMAX_API_KEY=...
MINIMAX_BASE_URL=https://api.minimaxi.com/v1  # China inland
MINIMAX_MODEL=MiniMax-M3

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
| `classic` | FAANG, large tech, senior — two-column sidebar (profile left, details right) |
| `sb2nov` | Standard SWE, ATS-friendly |
| `moderncv` | Startup, product |
| `engineeringresumes` | Maximally ATS-optimised |

## Git Strategy

- **Commit:** `profiles/career-en.yaml`, `profiles/base-zh-*.yaml`, positioning profiles, `resume.py`, `src/`, `jds/`, `ui/`, `Dockerfile`, `render.yaml`
- **Ignore:** `output/`, `.env`, `__pycache__/`
- **Deploy caveat:** `assets/william-jiang.jpg` (photo, used by rendercv themes) is gitignored but must be in the Docker image → `git add -f` it before deploying.

Full layering reference: [`docs/profile-layering.md`](docs/profile-layering.md)

## User Identity (from `docs/init.md`)

- Name: **William Jiang**
- LinkedIn: `https://www.linkedin.com/in/william-jiang-226a7616/`
- GitHub: `https://williamjxj.github.io/`
