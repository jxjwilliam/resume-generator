"""
Deterministic ATS compatibility scoring — no LLM required for grading.
"""

from __future__ import annotations

import re

from compose import parse_tag_list, rank_bullets_for_jd, select_experience_jobs

# Weights sum to 100
WEIGHT_KEYWORD = 40
WEIGHT_TITLE = 10
WEIGHT_COMPLETENESS = 20
WEIGHT_FORMATTING = 20
WEIGHT_CONCISENESS = 10

MAX_WORDS_PER_BULLET = 22
MAX_BULLETS_PER_JOB = 4


def _word_count(text: str) -> int:
    return len(text.split())


def score_resume(
    base: dict,
    jd_text: str,
    tags: str | list | None = None,
    headline: str | None = None,
    summary: str | None = None,
    max_bullets: int = 4,
    max_jobs: int = 0,
) -> dict:
    """
    Score a composed resume against a JD. Returns breakdown + total /100.
    """
    from jd_parser import parse_jd

    parsed = parse_jd(jd_text, base)
    tags_list = parse_tag_list(tags)
    jd_keywords = parsed.get("all_keywords", [])
    hard_skills = parsed.get("hard_skills", [])
    role_title = parsed.get("role_title", "")

    jobs = select_experience_jobs(
        base.get("experience", []),
        tags=tags_list,
        max_bullets=max_bullets,
        max_jobs=max_jobs,
        jd_keywords=jd_keywords,
    )

    # --- Keyword match (40%) ---
    resume_tokens: set[str] = set()
    bullet_texts: list[str] = []
    for job, bullets in jobs:
        for b in bullets:
            t = b.get("text", "")
            bullet_texts.append(t)
            resume_tokens.update(re.findall(r"[a-z0-9+#./-]+", t.lower()))
        for item in base.get("skills", {}).values():
            for s in item if isinstance(item, list) else []:
                if s.get("status", "active") == "active":
                    resume_tokens.update(re.findall(r"[a-z0-9+#./-]+", s.get("name", "").lower()))

    if headline:
        resume_tokens.update(re.findall(r"[a-z0-9+#./-]+", headline.lower()))
    if summary:
        resume_tokens.update(re.findall(r"[a-z0-9+#./-]+", summary.lower()))

    if hard_skills:
        combined = " ".join(bullet_texts).lower()
        if summary:
            combined += " " + summary.lower()
        if headline:
            combined += " " + headline.lower()
        for items in base.get("skills", {}).values():
            for s in items:
                if s.get("status", "active") == "active":
                    combined += " " + s.get("name", "").lower()
        matched_count = sum(1 for s in hard_skills if s.lower() in combined)
        keyword_pct = matched_count / len(hard_skills)
        match_report = {
            "matched_skills": [s for s in hard_skills if s.lower() in combined],
            "missing_skills": [s for s in hard_skills if s.lower() not in combined],
        }
    else:
        keyword_pct = 0.5
        combined = ""
        match_report = {"matched_skills": [], "missing_skills": []}

    keyword_score = round(keyword_pct * WEIGHT_KEYWORD, 1)

    # --- Title alignment (10%) ---
    headline_text = (headline or base.get("identity", {}).get("headline", "")).lower()
    role_lower = role_title.lower()
    role_tokens = [w for w in re.findall(r"[a-z]+", role_lower) if len(w) > 3]
    if role_tokens:
        title_hits = sum(1 for t in role_tokens if t in headline_text)
        title_pct = title_hits / len(role_tokens)
    else:
        title_pct = 0.5
    title_score = round(title_pct * WEIGHT_TITLE, 1)

    # --- Completeness (20%) ---
    sections_present = 0
    section_checks = [
        bool(summary or base.get("summary")),
        len(jobs) > 0,
        bool(base.get("skills")),
        bool(base.get("education")),
    ]
    sections_present = sum(1 for c in section_checks if c)
    completeness_score = round((sections_present / len(section_checks)) * WEIGHT_COMPLETENESS, 1)

    # --- Formatting (20%) — rendercv output is ATS-safe by default ---
    formatting_score = WEIGHT_FORMATTING  # full marks for YAML→rendercv path

    # --- Conciseness (10%) ---
    long_bullets = 0
    total_bullets = 0
    for _, bullets in jobs:
        for b in bullets:
            total_bullets += 1
            if _word_count(b.get("text", "")) > MAX_WORDS_PER_BULLET:
                long_bullets += 1
            if len(bullets) > MAX_BULLETS_PER_JOB:
                long_bullets += 1

    if total_bullets:
        conciseness_pct = 1.0 - (long_bullets / max(total_bullets, 1))
    else:
        conciseness_pct = 0.0
    conciseness_score = round(max(0, conciseness_pct) * WEIGHT_CONCISENESS, 1)

    total = round(keyword_score + title_score + completeness_score + formatting_score + conciseness_score, 1)

    return {
        "total": total,
        "grade": _grade(total),
        "breakdown": {
            "keyword_match": {"score": keyword_score, "max": WEIGHT_KEYWORD, "pct": round(keyword_pct * 100)},
            "title_alignment": {"score": title_score, "max": WEIGHT_TITLE, "pct": round(title_pct * 100)},
            "completeness": {"score": completeness_score, "max": WEIGHT_COMPLETENESS},
            "formatting": {"score": formatting_score, "max": WEIGHT_FORMATTING},
            "conciseness": {"score": conciseness_score, "max": WEIGHT_CONCISENESS},
        },
        "hard_skills": hard_skills,
        "role_title": role_title,
        "seniority": parsed.get("seniority"),
        "skill_match": match_report,
        "top_bullets": rank_bullets_for_jd(base, tags_list, jd_keywords, limit=10),
        "jobs_included": len(jobs),
        "bullets_included": sum(len(b) for _, b in jobs),
    }


def _grade(total: float) -> str:
    if total >= 85:
        return "A"
    if total >= 75:
        return "B"
    if total >= 65:
        return "C"
    if total >= 50:
        return "D"
    return "F"


def compare_jds(
    base: dict,
    jd_entries: list[tuple[str, str]],
    tags: str | list | None = None,
    max_bullets: int = 4,
    max_jobs: int = 0,
) -> dict:
    """
    Score the same resume against multiple JDs. Returns ranked fit matrix.

    jd_entries: list of (label, jd_text) — label is usually filename or company name.
    """
    rankings = []
    for label, jd_text in jd_entries:
        result = score_resume(
            base, jd_text, tags=tags,
            max_bullets=max_bullets,
            max_jobs=max_jobs,
        )
        rankings.append({
            "label": label,
            "total": result["total"],
            "grade": result["grade"],
            "role_title": result.get("role_title", ""),
            "seniority": result.get("seniority"),
            "matched_skills": result["skill_match"]["matched_skills"],
            "missing_skills": result["skill_match"]["missing_skills"],
            "keyword_pct": result["breakdown"]["keyword_match"].get("pct", 0),
            "jobs_included": result.get("jobs_included", 0),
            "bullets_included": result.get("bullets_included", 0),
        })

    rankings.sort(key=lambda r: r["total"], reverse=True)

    return {
        "rankings": rankings,
        "recommended": rankings[0]["label"] if rankings else None,
        "best_score": rankings[0]["total"] if rankings else 0,
        "count": len(rankings),
    }
