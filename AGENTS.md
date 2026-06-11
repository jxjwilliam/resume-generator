# Resume Management System

A 3-layer system for maintaining a single source-of-truth resume (YAML), composing job-specific variants, and rendering PDF + HTML via rendercv.

## Repo State

**Implemented.** `base.yaml`, `resume.py`, `transform.py`, and `.gitignore` all exist and are functional. The following were created from scratch:

- `.gitignore` — ignore `output/`, `__pycache__/`, `.env`
- `variants/` and `jds/` directories
- `base.yaml` — single source of truth (schema in `docs/resume-system-implementation.md` Section 2)
- `resume.py` — composition engine CLI (see actual file; spec in Section 3.2 of the implementation doc)
- `transform.py` — RxResume sync for visual resume path

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
| `transform.py` | RxResume sync. `python transform.py --dry-run ...` |
| `docs/resume-system-implementation.md` | Complete system design with schema, code, CLI reference |
| `docs/rxresume-integration-guide.md` | RxResume integration guide for `transform.py` |
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
pip install openai python-dotenv
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
- **Every application creates a named snapshot** with its own variant YAML + output dir + log entry. Output includes PDF, HTML, Markdown, Typst source, and PNG previews.
- The variant YAML uses rendercv's schema (not the base schema). See `docs/resume-system-implementation.md` Section 3.2 `build_variant()` for the mapping.

## Git Strategy

- **Commit:** `base.yaml`, `resume.py`, `applications.json`, `variants/`, `jds/`
- **Ignore:** `output/` (PDFs — regenerate anytime), `.env` (API keys), `__pycache__/`
- Commits exist on `main` — `base.yaml`, `resume.py`, `transform.py`, `variants/`, `jds/`, and `applications.json` are all tracked.

## Rendercv YAML Format

The variant YAML must include a `design` block for theming:

```yaml
cv:
  name: "William Jiang"
  email: "jxjwilliam@gmail.com"
  phone: "+12369923846"
  location: "Vancouver, Canada"
  headline: "Senior Full-Stack & AI Engineer"
  photo: "../assets/william-jiang.jpg"
  social_networks:
    - network: GitHub
      username: williamjxj
    - network: LinkedIn
      username: william-jiang-226a7616
  sections:
    Summary:
      - "Senior Full-Stack Engineer with 20+ years of experience..."
    experience:
      - company: "Best IT Consulting Inc."
        position: "Founder / Full-Stack & AI Engineer"
        start_date: "2024-10"
        end_date: present
        location: "Vancouver, Canada"
        highlights:
          - "Built production-grade React + Node.js applications..."
    skills:
      - label: Languages
        details: "Python, TypeScript, JavaScript, Java, SQL"
    projects:
      - name: "AutoBidder"
        summary: "Automated bidding system..."
        highlights: ["..."]
    education:
      - institution: "Xi'an Jiaotong University"
        area: "Bachelor of Engineering"
        date: "1991-07"
design:
  theme: classic
  page:
    size: us-letter
    top_margin: 0.7in
    bottom_margin: 0.7in
    left_margin: 0.7in
    right_margin: 0.7in
  colors:
    name: rgb(0,79,144)
    headline: rgb(0,79,144)
    connections: rgb(0,79,144)
    section_titles: rgb(0,79,144)
  typography:
    font_family: Source Sans 3
    font_size:
      body: 10pt
      name: 30pt
      headline: 10pt
      connections: 10pt
      section_titles: 1.4em
```

## LLM Integration

- Uses `openai` client with DeepSeek endpoint (`api.deepseek.com`) by default
- All settings configured via `.env` — `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`
- Falls back gracefully if `DEEPSEEK_API_KEY` is not set
- Swap `DEEPSEEK_BASE_URL` to Ollama (`http://localhost:11434/v1`) for local inference — no code changes needed
