# Profile Layering (sources + positioning profiles)

The old system kept one monolithic `profiles/base.yaml` (plus `base-v1/v2/v3`
and Chinese copies, all removed in 2026-08), each duplicating the full
resume. The new structure separates **content** from **positioning**:

```text
profiles/career-en.yaml            <- canonical English content (WHAT William has done)
   |-- profiles/na-ai-engineer.yaml     <- HOW to market: NA AI-heavy senior roles
   |-- profiles/na-software-engineer.yaml
   |-- profiles/china-cto.yaml
   +-- profiles/china-partner.yaml

profiles/base-zh-cto.yaml          <- standalone Chinese resume (CTO focus)
profiles/base-zh-partner.yaml      <- standalone Chinese resume (partner focus)
```

## Two kinds of YAML

**Sources** carry the full schema (`identity`, `summary`, `experience`,
`skills`, `projects`, `education`, `cover_letters`):

- `career-en.yaml` - the canonical English source
- `base-zh-cto.yaml`, `base-zh-partner.yaml` - full Chinese resumes
- `base.yaml` - legacy English source (still loadable; `base-v1/v2/v3`,
  `base-zh`, `base-2-zh` were deleted)

**Positioning profiles** carry only presentation/selection config:

```yaml
# profiles/na-ai-engineer.yaml
source:
  career: "./career-en.yaml"

headline: "Senior Software Engineer | Full-Stack & AI/GenAI | ..."
summary: "Senior software engineer with strong hands-on full-stack ..."
target_roles: [Senior Software Engineer, Senior AI Engineer, ...]
emphasis: [fullstack, backend, frontend, ai, architecture, cloud]

experience_priority:
  - Best IT Consulting Inc.
  - Xperi Inc.
  - ...
skills_priority:
  - Python/FastAPI
  - TypeScript/React/Next.js
  - ...
projects_priority:
  - AgentsAI / AgentsCrew
  - ...
recent_jobs: 5                 # top-N priority companies keep full bullets
old_experience_max_bullets: 1  # listed-but-older jobs get this many bullets
```

## How resolution works

`src/profiles.py` decides which kind a YAML is and layers it:

1. Load the requested YAML (`--yaml`, WebUI selector, or default).
2. If it is a positioning profile (has `experience_priority` /
   `skills_priority` / `source.career`), resolve its source:
   - explicit `source.career` (relative to the profile file), or
   - `career-en.yaml` next to it.
3. `apply_profile()` deep-copies the source and applies the profile:
   - `identity.headline` <- `headline`
   - `summary` <- `summary`
   - `experience` reordered by `experience_priority` (reverse-chronological
     within each tier)
   - jobs ranked at/after `recent_jobs` get `old_experience_max_bullets`
     (via per-job `_max_bullets`, respected by compose + ATS)
   - `skills` categories and items reordered by `skills_priority` (composite
     entries like `TypeScript/React/Next.js` match items across categories)
   - `projects` reordered by `projects_priority`
   - `meta.profile` + `meta.source` recorded for provenance
4. Everything downstream (`build`, `analyze`, `score`, `compare`,
   `interview`, `cover-letter`, WebUI JD analysis/preview/build) receives the
   effective base - no other code knows about profiles.

## Usage

```bash
python resume.py profiles                          # list sources + profiles

# Default: canonical English source
python resume.py build --company "BestIT" --role "Senior SWE" --tags backend,python

# English positioning profile (auto-loads career-en.yaml)
python resume.py build --yaml profiles/na-ai-engineer.yaml \
  --company "BestIT" --role "Senior AI Engineer" --tags ai --max-bullets 3

# Chinese source
python resume.py build --yaml profiles/base-zh-cto.yaml \
  --company "某公司" --role "CTO" --locale zh-CN
```

The default source is `profiles/career-en.yaml` (CLI `BASE_FILE`,
`ui/backend/models.py`, and `ui/frontend/src/types.ts`).

## Behavior notes

- **Experience order:** priority companies appear first, in listed order;
  unlisted companies follow, and each tier stays reverse-chronological.
- **Job caps:** only *listed* jobs beyond `recent_jobs` are capped at
  `old_experience_max_bullets`; unlisted jobs keep the CLI cap.
- **Projects:** with a JD present, JD keyword scoring still wins over profile
  order (target relevance beats presentation preference); without a JD the
  profile order is used.
- **Skills:** when a JD is present, JD keyword sorting within a skill row is
  unchanged; the profile controls category/item ordering for JD-free builds
  and LLM context.
- **Legacy files:** `base.yaml` still loads as a source for backwards
  compatibility; `base-v1/v2/v3.yaml` were removed on 2026-08-17. The English
  content now lives in `career-en.yaml`.

## Editing workflow

- Edit content only in canonical sources (`career-en.yaml`,
  `base-zh-*.yaml`).
- Edit positioning only in profile YAMLs - never copy the whole career file
  into a profile.
- If a market needs a new focus, copy an existing profile, change
  `meta.profile` / `headline` / priorities, and keep `source.career`.
