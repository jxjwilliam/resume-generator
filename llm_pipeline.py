"""
Optional LLM steps for the resume quality pipeline:
  - Structured JD parse (must_have / nice_to_have)
  - Hybrid bullet re-scoring (0–10) for top candidates
"""

from __future__ import annotations

import json
import re
import sys

from compose import bullet_key, bullet_relevance_score, parse_tag_list, rank_bullets_for_jd
from llm_config import LLMNotConfiguredError, get_llm_client, llm_chat_completion


def llm_parse_jd(jd_text: str, base: dict | None = None, llm_provider: str | None = None) -> dict | None:
    """
    LLM structured JD parse. Returns None if LLM unavailable.
    Merges with heuristic parse_jd() output when successful.
    """
    from jd_parser import parse_jd

    heuristic = parse_jd(jd_text, base)
    try:
        client, model, _cfg = get_llm_client(llm_provider)
    except LLMNotConfiguredError as e:
        print(f"LLM JD parse skipped: {e}", file=sys.stderr)
        return heuristic

    prompt = f"""Parse this job description into JSON only (no markdown):

{{
  "role_title": "exact role title",
  "seniority": "intern|junior|mid|senior|staff|principal|director|unknown",
  "domain": "e.g. fintech or null",
  "must_have_skills": ["required hard skills"],
  "nice_to_have_skills": ["optional skills"],
  "must_have_soft": ["leadership, etc if any"]
}}

Job description:
{jd_text[:4000]}
"""
    try:
        raw = llm_chat_completion(
            client, model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
        )
        if not raw:
            return heuristic
        text = raw.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        data = json.loads(text)
    except (json.JSONDecodeError, Exception) as e:
        print(f"LLM JD parse failed ({type(e).__name__}), using heuristic", file=sys.stderr)
        return heuristic

    must = data.get("must_have_skills") or []
    nice = data.get("nice_to_have_skills") or []
    merged_hard = list(dict.fromkeys(must + nice + heuristic.get("hard_skills", [])))

    all_kw: list[str] = []
    for s in must:
        all_kw.extend([s, s])
    for s in nice:
        all_kw.append(s)
    all_kw.extend(heuristic.get("all_keywords", []))

    out = {**heuristic}
    out["role_title"] = data.get("role_title") or heuristic.get("role_title", "")
    out["seniority"] = data.get("seniority") or heuristic.get("seniority", "unknown")
    out["domain"] = data.get("domain") or heuristic.get("domain")
    out["must_have_skills"] = must
    out["nice_to_have_skills"] = nice
    out["hard_skills"] = merged_hard
    out["all_keywords"] = list(dict.fromkeys(all_kw))
    out["llm_parsed"] = True
    return out


def llm_rescore_bullets(
    base: dict,
    jd_text: str,
    tags: str | list | None,
    jd_keywords: list[str] | None,
    limit: int = 20,
    llm_provider: str | None = None,
) -> dict[str, int]:
    """
    LLM re-score top deterministic candidates 0–10.
    Returns {bullet_key: llm_score}.
    """
    candidates = rank_bullets_for_jd(base, tags, jd_keywords, limit=limit)
    if not candidates:
        return {}

    try:
        client, model, _cfg = get_llm_client(llm_provider)
    except LLMNotConfiguredError as e:
        print(f"LLM bullet scoring skipped: {e}", file=sys.stderr)
        return {}

    bullets_block = "\n".join(
        f"{i+1}. [{c['job']}] {c['text'][:200]}"
        for i, c in enumerate(candidates)
    )
    prompt = f"""Score each resume bullet 0-10 for fit to this job (10 = perfect match).
Use ONLY the bullet text — do not invent facts.

Return JSON array only:
[{{"index": 1, "score": 8, "reason": "brief"}}, ...]

Job description:
{jd_text[:2500]}

Bullets:
{bullets_block}
"""
    try:
        raw = llm_chat_completion(
            client, model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
        )
        if not raw:
            return {}
        text = raw.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        scores_list = json.loads(text)
    except (json.JSONDecodeError, Exception) as e:
        print(f"LLM bullet scoring failed ({type(e).__name__})", file=sys.stderr)
        return {}

    out: dict[str, int] = {}
    for item in scores_list:
        idx = int(item.get("index", 0)) - 1
        if 0 <= idx < len(candidates):
            c = candidates[idx]
            key = bullet_key(c["job"], c["text"])
            out[key] = max(0, min(10, int(item.get("score", 0))))
    return out


def combined_bullet_score(
    bullet: dict,
    job_company: str,
    required_tags: set | None,
    jd_keywords: list[str] | None,
    llm_scores: dict[str, int] | None,
) -> float:
    """Deterministic score + LLM 0–10 weight (LLM × 5 added)."""
    det = bullet_relevance_score(bullet, required_tags, jd_keywords)
    key = bullet_key(job_company, bullet.get("text", ""))
    llm = (llm_scores or {}).get(key, 0)
    return det + llm * 5
