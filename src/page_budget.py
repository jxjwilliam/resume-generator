"""
Rules-based page length estimation and trim for composed resumes.

Target: ~1 page (52 lines) for senior ATS resumes; 2 pages with --pages 2.
"""

from __future__ import annotations

from src.compose import bullet_relevance_score

DEFAULT_LINES_PER_PAGE = 52
HEADER_LINES = 6
LINES_SUMMARY = 2
LINES_SECTION_HEADER = 1
LINES_JOB_HEADER = 2
LINES_PER_BULLET = 1.5
LINES_SKILL_ROW = 1
LINES_PROJECT = 3
LINES_EDUCATION = 1


def estimate_lines(
    *,
    has_summary: bool,
    jobs: list[tuple[dict, list]],
    skill_rows: int,
    project_count: int,
    education_count: int,
    skills_collapsed: bool = False,
) -> float:
    lines = float(HEADER_LINES)
    if has_summary:
        lines += LINES_SUMMARY
    if jobs:
        lines += LINES_SECTION_HEADER
        for _, bullets in jobs:
            lines += LINES_JOB_HEADER
            lines += len(bullets) * LINES_PER_BULLET
    if skill_rows > 0:
        lines += LINES_SECTION_HEADER
        lines += 1 if skills_collapsed else skill_rows * LINES_SKILL_ROW
    if project_count > 0:
        lines += LINES_SECTION_HEADER + project_count * LINES_PROJECT
    if education_count > 0:
        lines += LINES_SECTION_HEADER + education_count * LINES_EDUCATION
    return lines


def trim_jobs_to_page_budget(
    job_bullet_pairs: list[tuple[dict, list[dict]]],
    *,
    pages: int = 1,
    required_tags: set | None = None,
    jd_keywords: list[str] | None = None,
    has_summary: bool = True,
    skill_rows: int = 3,
    project_count: int = 0,
    education_count: int = 1,
) -> tuple[list[tuple[dict, list[dict]]], dict]:
    """
    Trim lowest-scored bullets/jobs until estimated lines fit page budget.
    Returns (trimmed pairs, report dict).
    """
    if pages <= 0:
        return job_bullet_pairs, {"enabled": False}

    budget = pages * DEFAULT_LINES_PER_PAGE
    jobs: list[tuple[dict, list[dict]]] = [(j, list(bs)) for j, bs in job_bullet_pairs]
    include_projects = project_count > 0
    skills_collapsed = False
    actions: list[str] = []

    def _lines() -> float:
        return estimate_lines(
            has_summary=has_summary,
            jobs=jobs,
            skill_rows=skill_rows,
            project_count=project_count if include_projects else 0,
            education_count=education_count,
            skills_collapsed=skills_collapsed,
        )

    while _lines() > budget and jobs:
        dropped = False

        # Drop lowest-scored bullet (keep ≥1 bullet per included job)
        for ji, (job, bullets) in enumerate(jobs):
            if len(bullets) <= 1:
                continue
            worst_idx = min(
                range(len(bullets)),
                key=lambda i: bullet_relevance_score(bullets[i], required_tags, jd_keywords),
            )
            if worst_idx is not None:
                jobs[ji][1].pop(worst_idx)
                actions.append(f"drop_bullet:{job.get('company', '?')}")
                dropped = True
                break

        if dropped:
            continue

        if include_projects:
            include_projects = False
            actions.append("drop_projects")
            continue

        if not skills_collapsed and skill_rows > 1:
            skills_collapsed = True
            actions.append("collapse_skills")
            continue

        if len(jobs) > 1:
            worst_job = min(
                range(len(jobs)),
                key=lambda i: sum(
                    bullet_relevance_score(b, required_tags, jd_keywords)
                    for b in jobs[i][1]
                ),
            )
            company = jobs[worst_job][0].get("company", "?")
            jobs.pop(worst_job)
            actions.append(f"drop_job:{company}")
            continue

        break

    estimated = _lines()
    return jobs, {
        "enabled": True,
        "pages": pages,
        "budget_lines": budget,
        "estimated_lines": round(estimated, 1),
        "over_budget": estimated > budget,
        "skills_collapsed": skills_collapsed,
        "projects_included": include_projects,
        "jobs_included": len(jobs),
        "bullets_included": sum(len(bs) for _, bs in jobs),
        "actions": actions,
    }
