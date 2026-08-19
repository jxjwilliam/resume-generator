"""
Shared resume composition logic for resume.py.

Filters, ranks, and caps experience bullets by tag overlap, relevance,
and optional JD keyword matches.
"""

from __future__ import annotations

from src.profiles import _match_name

DEFAULT_MAX_BULLETS = 4
DEFAULT_MAX_JOBS = 0  # 0 = unlimited

# Rendered section titles. Keys are the visible headings (uppercase).
SEC_SUMMARY = "SUMMARY"
SEC_SKILLS = "CORE SKILLS"
SEC_EXPERIENCE = "EXPERIENCE"
SEC_EARLIER = "EARLIER CAREER"
SEC_PROJECTS = "SELECTED PROJECTS"
SEC_EDUCATION = "EDUCATION"

_SECTION_ALIASES = {
    "summary": (SEC_SUMMARY, "Summary", "summary"),
    "skills": (SEC_SKILLS, "skills", "Skills"),
    "experience": (SEC_EXPERIENCE, "experience", "Experience"),
    "earlier": (SEC_EARLIER, "Earlier Career"),
    "projects": (SEC_PROJECTS, "projects", "Projects"),
    "education": (SEC_EDUCATION, "education", "Education"),
}

SECTION_TITLE_COLOR = "rgb(31,56,100)"  # matches DOCX navy #1F3864


def section_entries(sections: dict, kind: str, default=None):
    """Look up a composed section, accepting current and legacy titles."""
    if default is None:
        default = []
    for key in _SECTION_ALIASES.get(kind, (kind,)):
        if key in sections:
            return sections[key]
    return default

_RELEVANCE = {"high": 3, "medium": 2, "low": 1}


def bullet_key(job_company: str, bullet_text: str) -> str:
    return f"{job_company}::{bullet_text[:40]}"


def parse_tag_list(tags: str | list | None) -> list[str] | None:
    if tags is None:
        return None
    if isinstance(tags, str):
        parsed = [t.strip() for t in tags.split(",") if t.strip()]
        return parsed or None
    parsed = [str(t).strip() for t in tags if str(t).strip()]
    return parsed or None


def filter_bullets(bullets: list, required_tags: set | None = None) -> list:
    """Keep non-deprecated bullets; when tags are set, match on bullet tags."""
    out = []
    for b in bullets:
        if b.get("status") == "deprecated":
            continue
        if required_tags and not required_tags.intersection(set(b.get("tags", []))):
            continue
        out.append(b)
    return out


def sort_jobs_reverse_chronological(jobs: list) -> list:
    def sort_key(job):
        start = job.get("start") or "0000-00"
        end = job.get("end") or "9999-12"
        return (start, end)

    return sorted(jobs, key=sort_key, reverse=True)


_MONTHS = {
    "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
    "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
    "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
}


def _format_month_year(value) -> str:
    if not value:
        return "Present"
    parts = str(value).split("-")
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        return f"{_MONTHS.get(parts[1], parts[1])} {parts[0]}"
    return str(value)


def select_earlier_career_jobs(exp_list: list) -> list[dict]:
    """Jobs with status ``earlier`` — compressed one-liners, newest first.

    ``deprecated`` still means omit. ``earlier`` means keep, but briefly.
    """
    return sort_jobs_reverse_chronological(
        [j for j in exp_list if j.get("status") == "earlier"]
    )


def format_earlier_career_line(job: dict) -> str:
    """Markdown one-liner matching the Earlier Career screenshot.

    **Company** — Title | dates
    """
    company = (job.get("earlier_company") or job.get("company") or "").strip()
    title = (job.get("earlier_title") or job.get("title") or job.get("role") or "").strip()
    dates = (job.get("period") or "").strip()
    if not dates:
        dates = f"{_format_month_year(job.get('start'))} – {_format_month_year(job.get('end'))}"
    body = " | ".join(p for p in (title, dates) if p)
    company_md = f"**{company}**" if company else ""
    if company_md and body:
        return f"{company_md} — {body}"
    return company_md or body


def format_education_institution(entry: dict) -> str:
    """Institution with location: "Xi'an Jiaotong University, China"."""
    inst = (entry.get("institution") or "").strip()
    loc = (entry.get("location") or "").strip()
    if loc and loc.casefold() not in inst.casefold():
        return f"{inst}, {loc}"
    return inst


def reorder_jobs_by_priority(jobs: list, priority: list[str] | None) -> list:
    """
    Priority-listed companies first (in listed order), the rest after.
    Within each priority tier, jobs stay reverse-chronological.
    """
    if not priority:
        return sort_jobs_reverse_chronological(jobs)
    used: set[int] = set()
    groups: list[list] = []
    for wanted in priority:
        group = [
            j for j in jobs
            if id(j) not in used and _match_name(j.get("company", ""), wanted)
        ]
        used.update(id(j) for j in group)
        groups.append(group)
    rest = [j for j in jobs if id(j) not in used]
    ordered: list = []
    for group in groups + [rest]:
        ordered.extend(sort_jobs_reverse_chronological(group))
    return ordered


def bullet_relevance_score(
    bullet: dict,
    required_tags: set | None = None,
    jd_keywords: list[str] | None = None,
) -> int:
    """Higher is better. Tag overlap + relevance tier + JD keyword hits in text."""
    overlap = len(required_tags.intersection(set(bullet.get("tags", [])))) if required_tags else 0
    rel = _RELEVANCE.get(bullet.get("relevance", "medium"), 2)
    score = overlap * 10 + rel

    if jd_keywords:
        text_lower = bullet.get("text", "").lower()
        for kw in jd_keywords:
            if kw.lower() in text_lower:
                score += 5

    extra_kw = bullet.get("keywords") or []
    if extra_kw and jd_keywords:
        jd_lower = [k.lower() for k in jd_keywords]
        for kw in extra_kw:
            kl = kw.lower()
            if kl in jd_lower or any(kl in j or j in kl for j in jd_lower):
                score += 4

    if bullet.get("metrics"):
        score += 2

    return score


def select_experience_jobs(
    exp_list: list,
    tags: str | list | None = None,
    max_bullets: int = DEFAULT_MAX_BULLETS,
    max_jobs: int = DEFAULT_MAX_JOBS,
    jd_keywords: list[str] | None = None,
    seniority: str | None = None,
    llm_scores: dict[str, int] | None = None,
    priority: list[str] | None = None,
) -> list[tuple[dict, list[dict]]]:
    """
    Return (job, selected_bullets) pairs, newest first.

    Jobs must be active. Bullets are tag-filtered, ranked, and capped per job.
    When tags are set but no bullet matches, fall back to all bullets if the
    job-level tags overlap.

    For senior/staff/principal roles, omit jobs with no high-relevance bullets
    and weak JD overlap.
    """
    tags_list = parse_tag_list(tags)
    required_tags = set(tags_list) if tags_list else None
    senior_roles = {"senior", "staff", "principal", "director"}

    def _score(bullet: dict, job_company: str) -> float:
        det = bullet_relevance_score(bullet, required_tags, jd_keywords)
        if llm_scores:
            key = bullet_key(job_company, bullet.get("text", ""))
            det += llm_scores.get(key, 0) * 5
        return det

    active_jobs = reorder_jobs_by_priority(
        [j for j in exp_list if j.get("status") == "active"],
        priority,
    )
    results: list[tuple[dict, list[dict]]] = []

    for job in active_jobs:
        matched = filter_bullets(job.get("bullets", []), required_tags)
        if not matched and required_tags:
            job_tags = set(job.get("tags", []))
            if required_tags.intersection(job_tags):
                matched = filter_bullets(job.get("bullets", []), None)
        if not matched:
            continue

        if seniority in senior_roles:
            has_high = any(b.get("relevance") == "high" for b in matched)
            best = max(_score(b, job["company"]) for b in matched)
            if not has_high and best < 12:
                continue

        matched.sort(key=lambda b: _score(b, job["company"]), reverse=True)
        for b in matched:
            b["_score"] = _score(b, job["company"])
        cap = int(job.get("_max_bullets") or max_bullets)
        if cap > 0:
            matched = matched[:cap]
        results.append((job, matched))

        if max_jobs > 0 and len(results) >= max_jobs:
            break

    return results


def filter_skills_by_tags(
    skills: dict,
    tags_list: list[str] | None,
    jd_hard_skills: list[str] | None = None,
    boost_missing: bool = False,
) -> list[dict]:
    """Return rendercv-style skill rows filtered by tags; optionally boost JD-matched skills."""
    jd_lower = [s.lower() for s in (jd_hard_skills or [])]
    rows = []

    for category, items in skills.items():
        if tags_list:
            filtered = [
                s for s in items
                if s.get("status", "active") == "active"
                and any(t in s.get("tags", []) for t in tags_list)
            ]
        else:
            filtered = [s for s in items if s.get("status", "active") == "active"]

        if boost_missing and jd_lower:
            existing_names = {s["name"].lower() for s in filtered}
            for s in items:
                if s.get("status", "active") != "active":
                    continue
                name_lower = s.get("name", "").lower()
                if name_lower in existing_names:
                    continue
                if any(jd in name_lower or name_lower in jd for jd in jd_lower):
                    filtered.append(s)
                    existing_names.add(name_lower)

        if not filtered:
            continue

        if jd_lower:
            def skill_priority(s):
                name = s.get("name", "").lower()
                for i, jd in enumerate(jd_lower):
                    if jd in name or name in jd:
                        return i
                return len(jd_lower) + 1

            filtered.sort(key=skill_priority)

        rows.append({
            "label": category.replace("_", " ").title(),
            "details": ", ".join(s["name"] for s in filtered),
        })
    return rows


def rank_bullets_for_jd(
    base: dict,
    tags: str | list | None = None,
    jd_keywords: list[str] | None = None,
    limit: int = 20,
) -> list[dict]:
    """Return top-scoring bullets across all jobs for LLM context."""
    tags_list = parse_tag_list(tags)
    required_tags = set(tags_list) if tags_list else None
    scored: list[tuple[int, dict]] = []

    for job in base.get("experience", []):
        if job.get("status") != "active":
            continue
        for bullet in filter_bullets(job.get("bullets", []), required_tags):
            score = bullet_relevance_score(bullet, required_tags, jd_keywords)
            scored.append((score, {"job": job["company"], "text": bullet["text"], "score": score}))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:limit]]


def score_text_for_jd(
    text: str,
    bullet_meta: dict | None = None,
    required_tags: set | None = None,
    jd_keywords: list[str] | None = None,
) -> int:
    """Score arbitrary bullet text (base or variant) against JD signals."""
    pseudo = {"text": text, "tags": (bullet_meta or {}).get("tags", []),
              "relevance": (bullet_meta or {}).get("relevance", "medium")}
    return bullet_relevance_score(pseudo, required_tags, jd_keywords)


def pick_bullet_text(
    bullet: dict,
    jd_keywords: list[str] | None = None,
    required_tags: set | None = None,
) -> str:
    """
    Pick the best phrasing for a bullet: highest-scored variant vs base text.
    Falls back to base text when no variants or JD context.
    """
    variants = bullet.get("variants") or []
    if not variants:
        return bullet["text"]

    tags = required_tags
    candidates = [bullet["text"], *variants]
    if not jd_keywords and not tags:
        return variants[0]

    best = max(
        candidates,
        key=lambda t: score_text_for_jd(t, bullet, tags, jd_keywords),
    )
    return best


def preview_experience_jobs(
    exp_list: list,
    tags: str | list | None = None,
    max_bullets: int = DEFAULT_MAX_BULLETS,
    max_jobs: int = DEFAULT_MAX_JOBS,
    jd_keywords: list[str] | None = None,
    priority: list[str] | None = None,
) -> list[dict]:
    """
    Preview which bullets would be included/excluded per job before build.
    """
    tags_list = parse_tag_list(tags)
    required_tags = set(tags_list) if tags_list else None
    active_jobs = reorder_jobs_by_priority(
        [j for j in exp_list if j.get("status") == "active"],
        priority,
    )
    results: list[dict] = []
    jobs_included = 0

    for job in active_jobs:
        matched = filter_bullets(job.get("bullets", []), required_tags)
        if not matched and required_tags:
            job_tags = set(job.get("tags", []))
            if required_tags.intersection(job_tags):
                matched = filter_bullets(job.get("bullets", []), None)
        if not matched:
            continue

        job_will_include = max_jobs <= 0 or jobs_included < max_jobs
        scored_items = []
        for b in matched:
            score = bullet_relevance_score(b, required_tags, jd_keywords)
            scored_items.append({
                "text": b.get("text", ""),
                "score": score,
                "relevance": b.get("relevance", "medium"),
                "tags": b.get("tags", []),
            })
        scored_items.sort(key=lambda x: x["score"], reverse=True)

        cap = int(job.get("_max_bullets") or max_bullets)
        if cap <= 0:
            cap = len(scored_items)
        for i, item in enumerate(scored_items):
            item["included"] = job_will_include and i < cap

        results.append({
            "company": job.get("company", ""),
            "title": job.get("title", ""),
            "job_included": job_will_include,
            "bullets": scored_items,
        })

        if job_will_include:
            jobs_included += 1
        if max_jobs > 0 and jobs_included >= max_jobs:
            break

    return results
