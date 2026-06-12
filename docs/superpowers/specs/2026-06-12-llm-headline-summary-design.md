# LLM-Driven Headline & Summary Generation

**Date:** 2026-06-12
**Status:** Approved design, pending implementation

## Problem

When building a job-specific resume with `resume.py build --llm`, the headline and summary are always hardcoded from `base.yaml`, even when a job description (JD) is provided. The JD text is loaded but never used to tailor these sections.

The user wants the LLM to rewrite both the headline and summary from the JD to maximize resume-JD alignment.

## Solution

Add two new LLM calls that generate a job-specific headline and summary from the JD text, with clean fallback to `base.yaml` values on failure. This is incremental — the existing `llm_extract_tags()` path is unchanged.

## Design

### 1. CLI Changes (`resume.py`)

- `--role` becomes **not required** when `--llm` is used. If omitted, the job title is extracted from the JD's first non-empty line (stripped).
- `--jd` is **required** when `--llm` is used.
- Validation:
  - `if args.llm and not args.jd`: error("--jd required with --llm")
  - `if not args.role and not args.llm`: error("--role required when not using --llm")

### 2. New LLM Functions

All use the same DeepSeek client pattern as the existing `llm_extract_tags()`.

#### `llm_generate_headline(jd_text: str) -> str`

- **Prompt:** "Write a concise 1-line professional headline (10-15 words) for a resume targeting this job. Include the target role title and core relevant technologies. Return ONLY the headline text, nothing else."
- **Fallback:** `base["identity"]["headline"]` on error / empty / exception.

#### `llm_generate_summary(jd_text: str, base: dict) -> str`

- **Prompt:** "Write a 3-4 sentence professional summary for a resume targeting this job. Draw from the candidate's actual experience:\n\n{bullets}\n\nThe summary should highlight relevant skills, years of experience, and achievements that match the job description. Return ONLY the summary text, nothing else."
- `bullets` = top 10 active, non-deprecated experience bullets from `base`.
- **Fallback:** `base["summary"]` on error / empty / exception.

### 3. `build_variant()` Changes

```python
def build_variant(base, tags, template, company, role, jd_text=None,
                  headline_override=None, summary_override=None):
```

- `headline`: `headline_override or base["identity"].get("headline", "")`
- `Summary` section: `summary_override or base["summary"]`
- Existing `jd_text` parameter (previously unused) — unchanged, still accepted.

### 4. `cmd_build()` Orchestration

**With `--llm`:**
1. Load `base.yaml`, load `jd_text` from `--jd`
2. Extract role from JD first line if `--role` omitted
3. Run three LLM calls (any order, independent):
   - `llm_extract_tags(jd_text, base)` → tags (existing)
   - `llm_generate_headline(jd_text)` → headline_override
   - `llm_generate_summary(jd_text, base)` → summary_override
4. `build_variant(..., headline_override=headline, summary_override=summary)`
5. Write variant, render, log (unchanged)

**Without `--llm`:**
- Exactly identical to current behavior. Zero regression risk.

### 5. Error Handling

Each LLM function is independently wrapped in try/except:
- On error: print warning to stderr, return fallback value
- Headline failure → uses base.yaml headline (transparent to user)
- Summary failure → uses base.yaml summary
- Tags failure → uses empty string (no tag filtering, shows all active)
- One failure does NOT block the other calls

### 6. Files Changed

| File | Change |
|---|---|
| `resume.py` | Add 2 new LLM functions, modify `build_variant()`, modify `cmd_build()`, relax `--role` requirement |
| `README.md` | Update `--role` description to note optional-with-LLM |

### 7. Non-Goals

- `transform.py` (Reactive Resume) is NOT changed — this is only for the rendercv ATS PDF path.
- No changes to `base.yaml` schema.
- No changes to `docs/` architecture documents.

## Self-Review

- **Placeholders?** None. All sections defined.
- **Internal consistency?** Yes. `build_variant()` overrides match the existing keys. Fallback chain is linear.
- **Scope?** Focused. Single feature, single file change (`resume.py`).
- **Ambiguity?** No. Each LLM function has a clear prompt and fallback. Headline and summary are independently generated.
