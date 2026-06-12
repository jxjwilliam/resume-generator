# Plan: LLM-Driven Headline & Summary Generation

**Design:** `docs/superpowers/specs/2026-06-12-llm-headline-summary-design.md`

## Steps

### Step 1: Add `llm_generate_headline()` to `resume.py`

- New function after `llm_extract_tags()`
- Uses DeepSeek client (same pattern as existing LLM functions)
- Prompt: "Write a concise 1-line professional headline (10-15 words) for a resume targeting this job. Include the target role title and core relevant technologies."
- Fallback: returns empty string → caller uses base.yaml headline
- Input: `jd_text: str`
- Output: `str`

### Step 2: Add `llm_generate_summary()` to `resume.py`

- New function after `llm_generate_headline()`
- Collects top 10 active, non-deprecated experience bullets from base
- Prompt: "Write a 3-4 sentence professional summary... Draw from the candidate's actual experience..."
- Fallback: returns empty string → caller uses base.yaml summary
- Input: `jd_text: str, base: dict`
- Output: `str`

### Step 3: Modify `build_variant()` signature

```python
def build_variant(base, tags, template, company, role, jd_text=None,
                  headline_override=None, summary_override=None):
```

- `headline`: `headline_override or base["identity"].get("headline", "")`
- `Summary`: `summary_override or base.get("summary")`

### Step 4: Update argparse — `--role` optional

- Remove `required=True` from `--role`
- Update help text: `"Role title (extracted from JD first line if omitted with --llm)"`

### Step 5: Rewrite `cmd_build()` orchestration

New validation:
- `if args.llm and not args.jd`: error + exit
- `if not args.role and not args.llm`: error + exit

New flow when `--llm`:
1. Extract role from JD first line if `--role` not given
2. Call `llm_extract_tags(jd_text, base)` → tags
3. Call `llm_generate_headline(jd_text)` → headline_override
4. Call `llm_generate_summary(jd_text, base)` → summary_override
5. Pass overrides to `build_variant()`

Without `--llm`:
- Identical to current behavior

### Step 6: Update README.md

- Mark `--role` as `✅*` with footnote about optional-with-llm
- Mark `--jd` as `**` with footnote about required-with-llm
- Update `--llm` description to include headline+summary rewrite
- Update LLM example to show `--role` omitted

### Step 7: Verify

- `lsp_diagnostics` clean on `resume.py`
- `python resume.py build --help` shows correct flags
- Test validation errors fire correctly
- Test non-LLM path still produces correct output

## Files Changed

| File | What |
|---|---|
| `resume.py` | +2 functions, modify `build_variant()`, rewrite `cmd_build()`, argparse change |
| `README.md` | Updated flag table, examples |
| `docs/superpowers/plans/2026-06-12-llm-headline-summary-plan.md` | This file |
