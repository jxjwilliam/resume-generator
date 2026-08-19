# LLM prompts for resume generation

Reference for every LLM instruction used when building or analyzing a resume.
There is **no system prompt**. Each call is a single `role: user` message via
`llm_chat_completion()` in [`src/llm_config.py`](../src/llm_config.py).

The model never writes the whole resume from scratch. Canonical YAML
(`profiles/career-en.yaml` / `profiles/base-zh-*.yaml`) is the source of truth.
LLM only fills optional stages when `--llm`, `--tailor`, `--boost`, or
`--enhance` is on.

Provider setup: [`llm-providers.md`](llm-providers.md). Pipeline overview:
[`resume-quality-pipeline.md`](resume-quality-pipeline.md).

**Not LLM-generated:** experience selection, Earlier Career, Core Skills,
Education, Selected Projects (JD keyword scoring is deterministic), and ATS
grades.

---

## Call map

| Stage | Flag / command | Function | File |
|---|---|---|---|
| Tag extraction | `--llm` | `llm_extract_tags` | `src/cli.py` |
| Headline | `--llm` | `llm_generate_headline` | `src/cli.py` |
| Summary | `--llm` | `llm_generate_summary` | `src/cli.py` |
| Structured JD parse | `--llm` | `llm_parse_jd` | `src/llm_pipeline.py` |
| Bullet rescoring | `--llm` | `llm_rescore_bullets` | `src/llm_pipeline.py` |
| Tailor bullets | `--tailor` | `llm_tailor_bullets` | `src/cli.py` |
| Boost missing skills | `--boost` | `llm_boost_bullets` | `src/cli.py` |
| Enhance experience | `--enhance` | `llm_enhance_experience` | `src/cli.py` |
| Cover letter rewrite | `--llm` + cover letter | `llm_rewrite_cover_letter` | `src/cli.py` |
| Interview Q&A | `resume.py interview --llm` | `cmd_interview` | `src/cli.py` |

Tailor rewrites are validated by `validate_tailor_rewrite()` in
[`src/tailor_validation.py`](../src/tailor_validation.py) (anti-hallucination).
Boost only weaves skills already present in the YAML.

---

## 1. Tag extraction (`--llm`)

`llm_extract_tags` — pick tags from the YAML inventory that match the JD.

```
Given this job description, select the most relevant tags from the list below.
Return ONLY a comma-separated list of tags, nothing else.

Available tags: {tags from career YAML}

Job description:
{jd[:3000]}
```

---

## 2. Headline (`--llm`)

`llm_generate_headline` — one-line headline for the target role.

```
Write a concise 1-line professional headline (10-15 words) for a resume targeting this job.
{The target role is: {role}.}
The headline MUST reflect the target role title. Include core relevant technologies.
Return ONLY the headline text, nothing else.

Job description:
{jd[:3000]}
```

`{The target role is: {role}.}` is omitted when no role is set.

---

## 3. Summary (`--llm`)

`llm_generate_summary` — two-sentence summary from top-scored bullets + JD.

```
Write a professional summary for a resume targeting this job. Target role: {role}.

Rules:
- EXACTLY 2 sentences, maximum 45 words total
- Use ONLY facts from the candidate bullets below — do not invent employers, dates, or metrics
- Include one quantified achievement if present in the source bullets
- Do NOT use filler phrases: "proven track record", "passionate", "dynamic", "results-driven"
- Return ONLY the summary text, nothing else

Candidate experience:
{top 8 bullets}

Job description:
{jd[:3000]}
```

---

## 4. Structured JD parse (`--llm`)

`llm_parse_jd` — merge LLM JSON with the heuristic `parse_jd()` result.

```
Parse this job description into JSON only (no markdown):

{
  "role_title": "exact role title",
  "seniority": "intern|junior|mid|senior|staff|principal|director|unknown",
  "domain": "e.g. fintech or null",
  "must_have_skills": ["required hard skills"],
  "nice_to_have_skills": ["optional skills"],
  "must_have_soft": ["leadership, etc if any"]
}

Job description:
{jd[:4000]}
```

---

## 5. Bullet rescoring (`--llm`)

`llm_rescore_bullets` — 0–10 fit scores for the top deterministic candidates.
Added to the ranking as `LLM_score × 5`. Not used as the ATS grade.

```
Score each resume bullet 0-10 for fit to this job (10 = perfect match).
Use ONLY the bullet text — do not invent facts.

Return JSON array only:
[{"index": 1, "score": 8, "reason": "brief"}, ...]

Job description:
{jd[:2500]}

Bullets:
1. [Company] ...
```

---

## 6. Tailor bullets (`--tailor`)

`llm_tailor_bullets` — per-bullet rewrite for JD language. Truth-first.

```
Rewrite this resume bullet to better match the job description.

Rules:
- Keep ALL original facts — same employer, project, technologies, and metrics
- Do NOT invent numbers, tools, or achievements not in the source
- Maximum 22 words, one line
- Start with a strong action verb
- Naturally weave in relevant JD keywords if they fit: {first 15 keywords}
- Target role: {role}.
- Return ONLY the rewritten bullet, nothing else

Original bullet:
{source}

Job description excerpt:
{jd[:2000]}
```

---

## 7. Boost missing skills (`--boost`)

`llm_boost_bullets` — second pass. Only skills verified in YAML skills or
experience bullets are eligible.

```
Improve this resume bullet to naturally include these ATS keywords IF already implied by the original facts: {verified missing skills}

Rules:
- Do NOT invent employers, projects, metrics, or tools not in the original
- If a keyword cannot fit truthfully, return the original text unchanged
- Maximum 22 words, one line, strong action verb
- Target role: {role}.
- Return ONLY the bullet text, nothing else

Original:
{current bullet}

Job description excerpt:
{jd[:1500]}
```

---

## 8. Enhance experience (`--enhance`)

`llm_enhance_experience` — rewrite + reorder bullets per job; optional
truthful title tweak. Returns JSON.

```
Review this resume experience section and improve it for the job description below.

Company: {company}
Current title: {title}
Target role: {role}.

Rules:
- Reword each bullet for maximum impact: concise (≤22 words), strong action verb, quantified where possible
- Reorder bullets so the most JD-relevant ones come first
- Optionally suggest a better job title IF the current one doesn't reflect the target role well — keep it truthful to the actual role held
- Do NOT invent employers, projects, numbers, or tools not present in the source bullets
- Return ONLY a JSON object with "title" (string, same as current if unchanged) and "bullets" (array of strings in desired order), nothing else

Source bullets:
1. ...

Job description excerpt:
{jd[:2000]}
```

---

## 9. Cover letter (`--llm` + cover letter)

`llm_rewrite_cover_letter` — rewrite the template body for the target company.

```
Given this cover letter template and job description, rewrite the body to better match the role and company.

Rules:
- Replace any references to other companies or products with the target company or generic equivalents
- Keep the same professional tone and paragraph structure (3-4 paragraphs)
- Weave in 2–3 relevant JD keywords naturally
- Return ONLY the rewritten body, nothing else

Cover letter body:
{template body}

Job description:
{jd[:3000]}
```

---

## 10. Interview prep (`resume.py interview --llm`)

`cmd_interview` — likely questions from JD + gap report. Facts must stay
inside verified bullets.

```
Given this JD and resume gap report, list 5 likely interview questions and brief answer outlines using ONLY verified resume bullets.

Missing skills: {missing}
Top bullets:
{top bullets}

JD excerpt:
{jd[:2000]}
```

---

## Shared rules (all resume-content prompts)

- Truth-first: rephrase verified YAML content; never invent employers, dates,
  metrics, or tools.
- Return only the requested artifact (plain text or JSON) — no markdown fences
  unless the stage asks for JSON.
- ATS scoring remains deterministic; LLM is not used to grade.
