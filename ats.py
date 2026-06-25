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


def _has_quantification(text: str) -> bool:
    """Check if a bullet contains metrics, percentages, or numeric impact."""
    return bool(re.search(
        r'\d+%|\d+x\b|\$\d+|\d+\s*(?:users|customers|requests|QPS|RPS|GB|TB|ms|seconds|minutes|hours|days)'
        r'|\b(?:reduced|increased|improved|cut|saved|grew|scaled|boosted|lowered|raised)\b.*\d+'
        r'|\d+.*\b(?:reduced|increased|improved|cut|saved|grew|scaled|boosted)',
        text.lower()
    ))


STRONG_VERBS = {
    "architected", "designed", "built", "led", "optimized", "delivered",
    "implemented", "launched", "scaled", "reduced", "increased", "automated",
    "engineered", "developed", "established", "orchestrated", "spearheaded",
    "drove", "created", "deployed", "migrated", "transformed", "integrated",
    "streamlined", "accelerated", "pioneered",
}


def _starts_strong(bullet_text: str) -> bool:
    """Check if bullet starts with a strong action verb."""
    first_word = bullet_text.strip().split()[0] if bullet_text.strip() else ""
    return first_word.lower().rstrip("ed") in STRONG_VERBS or first_word.lower() in STRONG_VERBS


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

    # Build combined text for keyword matching (bullets + skills + headline + summary)
    bullet_texts: list[str] = []
    for _, bullets in jobs:
        for b in bullets:
            bullet_texts.append(b.get("text", ""))
    combined = " ".join(bullet_texts).lower()
    if summary:
        combined += " " + summary.lower()
    if headline:
        combined += " " + headline.lower()
    for items in base.get("skills", {}).values():
        for s in items:
            if isinstance(s, dict) and s.get("status", "active") == "active":
                combined += " " + s.get("name", "").lower()
            elif isinstance(s, str):
                combined += " " + s.lower()

    # --- Keyword match (40%) ---
    soft_skills = parsed.get("soft_skills", [])
    domain_kw = parsed.get("domain_keywords", [])
    soft_domain = soft_skills + domain_kw

    # Sub-score A: Hard skills
    if hard_skills:
        hard_pct = sum(1 for s in hard_skills if s.lower() in combined) / len(hard_skills)
        match_report = {
            "matched_skills": [s for s in hard_skills if s.lower() in combined],
            "missing_skills": [s for s in hard_skills if s.lower() not in combined],
        }
    else:
        hard_pct = 0.5
        match_report = {"matched_skills": [], "missing_skills": []}

    # Sub-score B: Soft skills + domain (40% of keyword weight when present)
    # Soft skills only boost — they never penalize the score
    if soft_domain:
        soft_pct = sum(1 for s in soft_domain if s.lower() in combined) / len(soft_domain)
        match_report["matched_soft_skills"] = [s for s in soft_domain if s.lower() in combined]
        match_report["missing_soft_skills"] = [s for s in soft_domain if s.lower() not in combined]
        # Blend: 75% hard skills, 25% soft/domain — only if soft match exceeds hard
        keyword_pct = hard_pct * 0.75 + soft_pct * 0.25 if soft_pct > hard_pct else hard_pct
    else:
        soft_pct = None
        keyword_pct = hard_pct

    keyword_score = round(keyword_pct * WEIGHT_KEYWORD, 1)

    # --- Title alignment (10%) ---
    headline_text = (headline or base.get("identity", {}).get("headline", "")).lower()
    # Also scan selected job titles (the strongest signal for role fit)
    job_titles_text = " ".join(job.get("title", "") for job, _ in jobs).lower()
    summary_text = (summary or base.get("summary", "")).lower()
    # Combined search space: headline + experience titles + summary
    title_search_space = f"{headline_text} {job_titles_text} {summary_text}"
    role_lower = role_title.lower()
    role_tokens = [w for w in re.findall(r"[a-z]+", role_lower) if len(w) > 3]
    if role_tokens:
        title_hits = sum(1 for t in role_tokens if t in title_search_space)
        title_pct = title_hits / len(role_tokens)
    else:
        title_pct = 0.5
    title_score = round(title_pct * WEIGHT_TITLE, 1)

    # --- Completeness (20%) — 5 checks, each worth 4% ---
    section_checks = [
        bool(summary or base.get("summary")),
        len(jobs) > 0,
        bool(base.get("skills")),
        bool(base.get("projects")),
        bool(base.get("education")),
    ]
    sections_present = sum(1 for c in section_checks if c)
    completeness_score = round((sections_present / len(section_checks)) * WEIGHT_COMPLETENESS, 1)

    # --- Formatting (20%) — rendercv output is ATS-safe by default ---
    formatting_score = WEIGHT_FORMATTING  # full marks for YAML→rendercv path

    # --- Conciseness + Impact (10%) ---
    penalty_points = 0
    total_bullets = 0
    quantified_count = 0
    strong_verb_count = 0
    for _, bullets in jobs:
        if len(bullets) > MAX_BULLETS_PER_JOB:
            penalty_points += len(bullets) - MAX_BULLETS_PER_JOB
        for b in bullets:
            text = b.get("text", "")
            total_bullets += 1
            if _word_count(text) > MAX_WORDS_PER_BULLET:
                penalty_points += 1
            if _has_quantification(text):
                quantified_count += 1
            if _starts_strong(text):
                strong_verb_count += 1

    if total_bullets:
        length_pct = max(0, 1.0 - (penalty_points / total_bullets))
        quant_pct = quantified_count / total_bullets
        verb_pct = strong_verb_count / total_bullets
        # 70% length, 15% quantification, 15% strong verbs
        conciseness_pct = length_pct * 0.7 + quant_pct * 0.15 + verb_pct * 0.15
    else:
        conciseness_pct = 0.0
        length_pct = quant_pct = verb_pct = 0.0
    conciseness_score = round(max(0, conciseness_pct) * WEIGHT_CONCISENESS, 1)

    total = round(keyword_score + title_score + completeness_score + formatting_score + conciseness_score, 1)

    return {
        "total": total,
        "grade": _grade(total),
        "breakdown": {
            "keyword_match": {"score": keyword_score, "max": WEIGHT_KEYWORD, "pct": round(keyword_pct * 100)},
            "keyword_sub": {
                "hard_skills": {"pct": round(hard_pct * 100) if hard_skills else None},
                "soft_skills_domain": {"pct": round(soft_pct * 100) if soft_pct is not None else None},
            },
            "title_alignment": {"score": title_score, "max": WEIGHT_TITLE, "pct": round(title_pct * 100)},
            "completeness": {"score": completeness_score, "max": WEIGHT_COMPLETENESS},
            "formatting": {"score": formatting_score, "max": WEIGHT_FORMATTING},
            "conciseness": {"score": conciseness_score, "max": WEIGHT_CONCISENESS},
            "conciseness_sub": {
                "length": {"pct": round(length_pct * 100)},
                "quantified": {"pct": round(quant_pct * 100), "count": quantified_count},
                "strong_verbs": {"pct": round(verb_pct * 100), "count": strong_verb_count},
            },
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