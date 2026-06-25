"""
Truth-first validation for LLM-tailored resume bullets.

Rejects rewrites that introduce numbers, years, or tool tokens not present in source.
"""

from __future__ import annotations

import re

from jd_parser import COMMON_HARD_SKILLS

STRONG_VERBS = {
    "architected", "designed", "built", "led", "optimized", "delivered",
    "implemented", "launched", "scaled", "reduced", "increased", "automated",
    "engineered", "developed", "established", "orchestrated", "spearheaded",
    "drove", "created", "deployed", "migrated", "transformed", "integrated",
    "streamlined", "accelerated", "pioneered", "mentored", "shipped",
}

MAX_BULLET_WORDS = 30

_NUMBER_PATTERNS = (
    r"\d+\.?\d*%",
    r"\$[\d,.]+[kmb]?",
    r"\d+[kmb]\+?",
    r"\d+\.?\d*x\b",
    r"\b\d+\.?\d*\b",
)


def extract_numbers(text: str) -> set[str]:
    """Normalized numeric tokens from bullet text."""
    found: set[str] = set()
    for pat in _NUMBER_PATTERNS:
        for m in re.finditer(pat, text, re.I):
            found.add(_normalize_token(m.group()))
    return found


def extract_years(text: str) -> set[str]:
    return set(re.findall(r"\b(?:19|20)\d{2}\b", text))


def _normalize_token(s: str) -> str:
    return s.lower().replace(",", "").strip()


def _number_allowed(new_num: str, source: str, source_nums: set[str]) -> bool:
    if new_num in source_nums:
        return True
    src_flat = _normalize_token(source)
    if new_num in src_flat:
        return True
    for sn in source_nums:
        if new_num in sn or sn in new_num:
            return True
    return False


def extract_skill_tokens(text: str) -> set[str]:
    """Hard-skill and capitalized tool-like tokens present in text."""
    text_l = text.lower()
    found: set[str] = set()
    for skill in COMMON_HARD_SKILLS:
        if skill in text_l:
            found.add(skill)

    words = text.split()
    for i, word in enumerate(words):
        # Strip punctuation from both ends but keep internal dots/slashes/hyphens
        clean = re.sub(r"[^\w+#./-]", "", word).strip(".,;:!?\"'()[]{}")
        if not clean or len(clean) < 3:
            continue
        if not clean[0].isupper():
            continue
        low = clean.lower()
        if i == 0 and (low in STRONG_VERBS or low.rstrip("ed") in STRONG_VERBS):
            continue
        # For slash-separated tokens (e.g. "React/TypeScript"), check each part
        if "/" in clean:
            for part in clean.split("/"):
                part_low = part.strip().lower()
                if len(part_low) >= 3:
                    found.add(part_low)
        found.add(low)
    return found


def validate_tailor_rewrite(source: str, rewritten: str) -> tuple[bool, str | None]:
    """
    Return (ok, rejection_reason). Rejects hallucinated numbers, years, or tools.
    """
    if not rewritten or not rewritten.strip():
        return False, "empty_rewrite"

    if len(rewritten.split()) > MAX_BULLET_WORDS:
        return False, "too_long"

    src_nums = extract_numbers(source)
    for num in extract_numbers(rewritten):
        if not _number_allowed(num, source, src_nums):
            return False, f"new_number:{num}"

    src_years = extract_years(source)
    new_years = extract_years(rewritten) - src_years
    if new_years:
        return False, f"new_year:{','.join(sorted(new_years))}"

    src_skills = extract_skill_tokens(source)
    new_skills = extract_skill_tokens(rewritten) - src_skills
    if new_skills:
        return False, f"new_tool:{','.join(sorted(new_skills))}"

    return True, None


def entries_to_tailored_map(entries: list[dict]) -> dict[str, str]:
    """Map accepted/boosted finals to keys for build_variant()."""
    out: dict[str, str] = {}
    for e in entries:
        if e.get("final") and e["final"] != e.get("original"):
            out[e["key"]] = e["final"]
    return out


def build_bullet_diff_report(
    entries: list[dict],
    before_ats: dict | None = None,
    after_ats: dict | None = None,
) -> dict:
    """Structured bullet-diff.json payload."""
    stats = {"accepted": 0, "rejected": 0, "unchanged": 0, "boosted": 0}
    for e in entries:
        status = e.get("status", "unchanged")
        if status in stats:
            stats[status] += 1

    def _ats_summary(result: dict | None) -> dict | None:
        if not result:
            return None
        return {
            "total": result.get("total"),
            "grade": result.get("grade"),
            "keyword_pct": result.get("breakdown", {})
            .get("keyword_match", {})
            .get("pct"),
        }

    return {
        "before_ats": _ats_summary(before_ats),
        "after_ats": _ats_summary(after_ats),
        "delta": (
            round(after_ats["total"] - before_ats["total"], 1)
            if before_ats and after_ats
            else None
        ),
        "bullets": entries,
        "stats": stats,
    }
