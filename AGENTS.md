# Resume Management System

A 3-layer system for maintaining a single source-of-truth resume (YAML), composing job-specific variants, and rendering PDF + HTML via rendercv.

## Repo State

**Pre-implementation.** No code exists yet — only the system design (`docs/resume-system-implementation.md`) and raw resume assets (`assets/`). The following need to be created from scratch:

- `base.yaml` — single source of truth (schema in `docs/resume-system-implementation.md` Section 2)
- `resume.py` — composition engine CLI (full script in Section 3.2)
- `.gitignore` — ignore `output/`, `__pycache__/`, `.env`
- `variants/` and `jds/` directories

## Architecture (3 Layers)

```
base.yaml (manual edit) → resume.py (composition) → rendercv (PDF+HTML)
```

- **Layer 1** — `base.yaml`: all experience, skills, projects, education, cover letter templates. Sections and bullets are tagged with keywords + status flags (`active`/`deprecated`/`conflicted`).
- **Layer 2** — `resume.py` CLI: reads `base.yaml`, filters by tags + status, outputs a lean `variants/<slug>.yaml`.
- **Layer 3** — `rendercv`: renders variant YAML → PDF + HTML.

## Key Files

| File | Purpose |
|---|---|
| `base.yaml` | **Single source of truth — manually edited.** All resumes derive from this. |
| `resume.py` | Composition engine CLI. `python resume.py build ...` |
| `docs/resume-system-implementation.md` | Complete system design with schema, code, CLI reference |
| `docs/init.md` | User's actual LinkedIn/GitHub/portfolio URLs, resume builder references |
| `assets/` | Existing resume versions (.docx/.txt) to consolidate into `base.yaml` |
| `applications.json` | Auto-generated application tracking log |
| `variants/*.yaml` | Auto-generated per-job resume variants |
| `output/` | Generated PDFs + HTML (gitignored) |

## User Identity (from `docs/init.md`)

- Name: **William Jiang**
- LinkedIn: `https://www.linkedin.com/in/william-jiang-226a7616/`
- GitHub: `https://williamjxj.github.io/`

## Dependencies

```bash
# Core
pip install pyyaml rendercv

# Optional - LLM tag extraction / cover letter drafting
pip install openai
```

Python 3.12.2 is available. `PyYAML` and `openai` are pre-installed.

## CLI Commands (from spec)

```bash
# See all available tags in base.yaml
python resume.py tags

# Build a variant (manual tags)
python resume.py build --company "BestIT" --role "Senior SWE" --tags backend,python,api --template classic

# Build with JD file and LLM tag suggestion
python resume.py build --company "BestIT" --role "Senior SWE" --jd jds/bestit.txt --llm

# View application history
python resume.py log
```

## Rendercv Themes

| Theme | Best for |
|---|---|
| `classic` | FAANG, large tech, senior roles |
| `sb2nov` | Standard SWE roles, ATS-friendly |
| `moderncv` | Startup, product, mid-level |
| `engineeringresumes` | Maximally ATS-optimised |

## Important Conventions

- **base.yaml is the only manually edited file.** Everything else is generated.
- **Status flags** control inclusion: `active` (include), `deprecated` (skip unless role needs it), `conflicted` (fix before use).
- **Tags** filter bullets/skills for job relevance. Tag granularity is per-bullet.
- **LLM is optional** — the system works without it. LLM is additive for JD tag extraction and cover letter drafting.
- **Every application creates a named snapshot** with its own variant YAML + output dir + log entry.
- The variant YAML uses rendercv's schema (not the base schema). See `docs/resume-system-implementation.md` Section 3.2 `build_variant()` for the mapping.

## Git Strategy

- **Commit:** `base.yaml`, `resume.py`, `applications.json`, `variants/`, `jds/`
- **Ignore:** `output/` (PDFs — regenerate anytime), `.env` (API keys), `__pycache__/`
- Currently no commits exist — first commit should include at minimum `base.yaml` + `resume.py` + `.gitignore`.

## Rendercv YAML Format

The variant YAML must include a `design` block for theming:

```yaml
cv:
  name: "William Jiang"
  email: "..."
  # ...
design:
  theme: classic
  font: Source Sans 3
  font_size: 10pt
  page_size: us-letter
  color: "#2B5EA7"
sections:
  experience: []
  skills: []
  projects: []
  education: []
```

## LLM Integration

- Uses `openai` client with DeepSeek endpoint (`api.deepseek.com`) by default
- Falls back gracefully if `DEEPSEEK_API_KEY` is not set
- Can swap to Ollama (`localhost:11434/v1`) for local inference
