"""
Build provenance JSON — atomic units + source refs per run (resmatch-style).
"""

from __future__ import annotations

from datetime import datetime, timezone

from src.compose import bullet_key, pick_bullet_text


def build_provenance_report(
    *,
    slug: str,
    company: str,
    role: str | None,
    tags: str | list | None,
    template: str,
    rx_template: str | None,
    base: dict,
    job_bullet_pairs: list[tuple[dict, list[dict]]],
    jd_keywords: list[str] | None,
    tailored_bullets: dict[str, str] | None,
    bullet_diff_entries: list[dict] | None,
    ats_result: dict | None,
    before_ats: dict | None,
    page_budget_report: dict | None,
    llm_scores: dict[str, int] | None,
    parsed_jd: dict | None,
) -> dict:
    """Assemble provenance.json payload."""
    tags_list = tags if isinstance(tags, list) else (
        [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    )
    units = []
    for job, bullets in job_bullet_pairs:
        for b in bullets:
            key = bullet_key(job["company"], b["text"])
            source = pick_bullet_text(b, jd_keywords=jd_keywords)
            final = (tailored_bullets or {}).get(key, source)
            diff_entry = next(
                (e for e in (bullet_diff_entries or []) if e.get("key") == key),
                None,
            )
            units.append({
                "key": key,
                "job": job.get("company"),
                "title": job.get("title"),
                "base_text": b.get("text"),
                "source_used": source,
                "final_text": final,
                "tags": b.get("tags", []),
                "relevance": b.get("relevance"),
                "metrics": b.get("metrics"),
                "keywords": b.get("keywords"),
                "variants": b.get("variants"),
                "deterministic_score": b.get("_score"),
                "llm_score": (llm_scores or {}).get(key),
                "tailor_status": diff_entry.get("status") if diff_entry else None,
            })

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "slug": slug,
        "company": company,
        "role": role,
        "tags": tags_list,
        "template": template,
        "rx_template_suggestion": rx_template,
        "jd": {
            "role_title": (parsed_jd or {}).get("role_title"),
            "seniority": (parsed_jd or {}).get("seniority"),
            "must_have_skills": (parsed_jd or {}).get("must_have_skills"),
            "nice_to_have_skills": (parsed_jd or {}).get("nice_to_have_skills"),
            "llm_parsed": (parsed_jd or {}).get("llm_parsed", False),
        },
        "ats": {
            "before": before_ats.get("total") if before_ats else None,
            "after": ats_result.get("total") if ats_result else None,
            "grade": ats_result.get("grade") if ats_result else None,
        },
        "page_budget": page_budget_report,
        "units": units,
        "unit_count": len(units),
    }
