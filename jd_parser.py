"""
Structured job description parsing — keyword categories with weights.

Used by jd_analyzer, resume.py analyze/score, and composition ranking.
"""

from __future__ import annotations

import re
from collections import Counter

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "need",
    "this", "that", "these", "those", "it", "its", "you", "your",
    "we", "our", "they", "them", "their", "what", "which", "who",
}


def extract_keywords(text: str, top_n: int = 15) -> list[str]:
    text = text.lower()
    words = re.findall(r"[a-z][a-z0-9+#.-]{2,}", text)
    filtered = [w for w in words if w not in STOPWORDS and len(w) > 2]
    return [word for word, _ in Counter(filtered).most_common(top_n)]

# Common hard-skill tokens (extended at runtime from base.yaml skill names)
COMMON_HARD_SKILLS = {
    "python", "java", "javascript", "typescript", "go", "golang", "rust", "c++", "c#",
    "sql", "postgresql", "mysql", "mongodb", "redis", "kafka", "rabbitmq",
    "react", "vue", "angular", "next.js", "nextjs", "node.js", "nodejs", "django", "flask",
    "fastapi", "spring", "express", "graphql", "rest", "api", "grpc",
    "aws", "gcp", "azure", "docker", "kubernetes", "k8s", "terraform", "ci/cd", "jenkins",
    "git", "linux", "microservices", "serverless", "lambda",
    "machine learning", "ml", "ai", "llm", "nlp", "pytorch", "tensorflow",
    "agile", "scrum", "jira", "figma",
}

TITLE_HINTS = {
    "engineer", "developer", "architect", "manager", "director", "lead", "staff",
    "principal", "senior", "junior", "intern", "consultant", "analyst", "scientist",
    "full-stack", "fullstack", "backend", "frontend", "devops", "sre", "platform",
}

SENIORITY_HINTS = {
    "intern": "intern",
    "junior": "junior",
    "mid-level": "mid",
    "mid level": "mid",
    "senior": "senior",
    "staff": "staff",
    "principal": "principal",
    "lead": "lead",
    "director": "director",
    "manager": "manager",
}

DOMAIN_HINTS = [
    "fintech", "healthcare", "e-commerce", "ecommerce", "saas", "b2b", "b2c",
    "telecom", "gaming", "edtech", "logistics", "supply chain", "retail",
    "enterprise", "startup", "consulting", "banking", "insurance",
]


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    return re.findall(r"[a-z][a-z0-9+#./-]{1,}", text)


def _collect_skill_names(base: dict | None) -> set[str]:
    names: set[str] = set(COMMON_HARD_SKILLS)
    if not base:
        return names
    for items in base.get("skills", {}).values():
        for item in items:
            name = item.get("name", "")
            if name:
                names.add(name.lower())
                for part in re.split(r"[,/&]+", name):
                    part = part.strip().lower()
                    if len(part) > 2:
                        names.add(part)
    return names


def _find_matches(text_lower: str, candidates: set[str]) -> list[str]:
    found = []
    for term in sorted(candidates, key=len, reverse=True):
        if term in text_lower and term not in found:
            # Avoid double-counting substrings
            if not any(term in f and term != f for f in found):
                found.append(term)
    return found


def parse_jd(text: str, base: dict | None = None) -> dict:
    """
    Parse JD into structured categories for scoring and tag suggestion.

    Returns:
        role_title, seniority, domain, hard_skills, title_keywords,
        domain_keywords, all_keywords (flat, weighted order)
    """
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    role_title = lines[0] if lines else ""
    text_lower = text.lower()
    skill_pool = _collect_skill_names(base)

    hard_skills = _find_matches(text_lower, skill_pool)

    title_keywords = []
    for hint in TITLE_HINTS:
        if hint in text_lower:
            title_keywords.append(hint)
    for word in _tokenize(role_title):
        if word in TITLE_HINTS and word not in title_keywords:
            title_keywords.append(word)

    domain_keywords = [d for d in DOMAIN_HINTS if d in text_lower]

    seniority = "unknown"
    for hint, level in SENIORITY_HINTS.items():
        if hint in text_lower or hint in role_title.lower():
            seniority = level
            break

    # Residual keywords via frequency (business context)
    freq = extract_keywords(text, top_n=25)
    hard_set = set(hard_skills)
    title_set = set(title_keywords)
    domain_set = set(domain_keywords)
    business_context = [
        w for w in freq
        if w not in hard_set and w not in title_set and w not in domain_set
        and w not in STOPWORDS
    ]

    # Weighted flat list for bullet scoring (hard skills repeated for weight)
    all_keywords: list[str] = []
    for s in hard_skills:
        all_keywords.extend([s, s])  # 2x weight
    for t in title_keywords:
        all_keywords.extend([t, t])  # 1.5x approximated with duplicate
        all_keywords.append(t)
    all_keywords.extend(domain_keywords)
    all_keywords.extend(business_context[:10])

    return {
        "role_title": role_title,
        "seniority": seniority,
        "domain": domain_keywords[0] if domain_keywords else None,
        "hard_skills": hard_skills,
        "title_keywords": title_keywords,
        "domain_keywords": domain_keywords,
        "business_context": business_context[:10],
        "all_keywords": list(dict.fromkeys(all_keywords)),  # dedupe, preserve order
        "keywords": extract_keywords(text, top_n=15),  # backward compat
    }


def keyword_match_report(parsed: dict, base: dict, tags: list[str] | None = None) -> dict:
    """Compare JD keywords against base.yaml content."""
    from compose import parse_tag_list, rank_bullets_for_jd

    tags_list = parse_tag_list(tags)
    hard_skills = parsed.get("hard_skills", [])
    resume_text_parts: list[str] = []

    for job in base.get("experience", []):
        if job.get("status") != "active":
            continue
        for b in job.get("bullets", []):
            if b.get("status") != "deprecated":
                resume_text_parts.append(b.get("text", "").lower())
    for items in base.get("skills", {}).values():
        for s in items:
            if s.get("status", "active") == "active":
                resume_text_parts.append(s.get("name", "").lower())

    resume_blob = " ".join(resume_text_parts)
    matched = [s for s in hard_skills if s.lower() in resume_blob]
    missing = [s for s in hard_skills if s.lower() not in resume_blob]

    top_bullets = rank_bullets_for_jd(base, tags_list, parsed.get("all_keywords"))

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "top_bullets": top_bullets,
    }
