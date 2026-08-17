"""
Profile / source layering for the resume system.

Two kinds of YAML can live in ``profiles/``:

1. **Sources** - full resume content (identity, summary, experience, skills,
   projects, education, cover letters). Examples: ``career-en.yaml``,
   ``base-zh-cto.yaml``, legacy ``base*.yaml``.

2. **Positioning profiles** - lightweight selection/presentation configs that
   point at a source and re-focus it (headline, summary, ordering, caps).
   Examples: ``na-ai-engineer.yaml``, ``china-cto.yaml``.

``load_effective(path)`` returns the *effective* resume dict for either kind:
a positioning profile is resolved to its source, then the profile's
headline/summary/priorities are layered on top.  The old system only knew
about standalone full-source files, so this module is what lets the four
English profiles replace the old ``base*.yaml`` files without losing context.
"""

from __future__ import annotations

import copy
import re
from pathlib import Path

PROFILES_DIR = "profiles"
DEFAULT_SOURCE = "career-en.yaml"

# How many entries at the top of ``experience_priority`` count as "recent"
# jobs (full bullets).  Jobs ranked at/after this position get
# ``old_experience_max_bullets`` instead.  Profiles can override with
# ``recent_jobs``.
DEFAULT_RECENT_JOBS = 5


def _norm(s: str) -> str:
    """Aggressive normalization for fuzzy name matching (ASCII + CJK)."""
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", str(s).casefold())


def _match_name(candidate: str, wanted: str) -> bool:
    """
    Fuzzy name match used for companies / skills / projects.

    Handles:
    - exact names ("Best IT Consulting Inc.")
    - punctuation / spacing differences ("Python/FastAPI" vs "Python / FastAPI")
    - composite entries ("TypeScript/React/Next.js" matches TypeScript and
      React.js / Next.js)
    - abbreviations ("MLDP" matches "MLDP (Machine Learning Data Pipelines)")
    """
    c = _norm(candidate)
    if not c:
        return False
    wanted = str(wanted)
    whole = _norm(wanted)
    if whole and (whole == c or whole in c or c in whole):
        return True
    segments = [s.strip() for s in wanted.split("/") if s.strip()]
    return any(
        (s and (s == c or s in c or c in s))
        for s in (_norm(seg) for seg in segments)
    )


def reorder_by_priority(items: list, priority: list[str], key) -> list:
    """
    Stable reorder: priority-listed items first (in listed order), then the
    rest in their original relative order.  Unmatched items are never dropped.
    """
    used: set[int] = set()
    ordered: list = []
    for wanted in priority or []:
        for it in items:
            if id(it) in used:
                continue
            if _match_name(str(key(it)), wanted):
                used.add(id(it))
                ordered.append(it)
    ordered.extend(it for it in items if id(it) not in used)
    return ordered


def is_positioning_profile(data: dict) -> bool:
    """True when the YAML is a presentation/selection config, not full content."""
    if not isinstance(data, dict):
        return False
    if data.get("experience_priority") or data.get("skills_priority"):
        return True
    src = data.get("source")
    return isinstance(src, dict) and bool(src.get("career"))


def resolve_source_path(profile_path: str, data: dict) -> str | None:
    """
    Resolve the career source for a positioning profile.

    Prefers an explicit ``source.career`` (relative to the profile file);
    falls back to ``career-en.yaml`` next to the profile.
    """
    profile_file = Path(profile_path).resolve()
    base_dir = profile_file.parent
    src = (data.get("source") or {}).get("career") if isinstance(data.get("source"), dict) else None
    if src:
        return str((base_dir / str(src)).resolve())
    default = base_dir / DEFAULT_SOURCE
    return str(default) if default.exists() else None


def _ranked_experience(
    experience: list,
    priority: list[str],
    recent_jobs: int,
    old_max_bullets: int,
) -> list:
    """Reorder experience by priority, then attach per-job bullet caps."""
    jobs = reorder_by_priority(
        experience, priority or [], key=lambda j: j.get("company", ""),
    )
    for job in jobs:
        company = job.get("company", "")
        rank = next(
            (i for i, c in enumerate(priority or []) if _match_name(company, c)),
            None,
        )
        # Listed-but-older jobs get the reduced cap; unlisted jobs keep default.
        if rank is not None and rank >= recent_jobs:
            job["_max_bullets"] = int(old_max_bullets)
    return jobs


def _ranked_skills(skills: dict, priority: list[str]) -> dict:
    """
    Reorder skill categories + items by profile priority.

    A composite entry like "TypeScript/React/Next.js" can match items in
    multiple categories (TypeScript in languages, React/Next.js in
    frameworks); the earliest matching entry decides the category order.
    """
    if not priority or not skills:
        return skills

    entry_items: dict[int, set] = {}
    for cat, items in skills.items():
        for item in items:
            name = item.get("name", "") if isinstance(item, dict) else str(item)
            for i, entry in enumerate(priority):
                if _match_name(str(name), entry):
                    entry_items.setdefault(i, set()).add(str(name))

    cat_rank: dict[str, int] = {}
    for cat, items in skills.items():
        best = None
        for item in items:
            name = item.get("name", "") if isinstance(item, dict) else str(item)
            for i, names in entry_items.items():
                if str(name) in names:
                    best = i if best is None else min(best, i)
        if best is not None:
            cat_rank[cat] = best

    original_order = {cat: i for i, cat in enumerate(skills.keys())}
    ordered_cats = sorted(
        skills.keys(),
        key=lambda c: (cat_rank.get(c, 10**9), original_order[c]),
    )
    return {
        cat: reorder_by_priority(skills[cat], priority, key=lambda s: s.get("name", "") if isinstance(s, dict) else str(s))
        for cat in ordered_cats
    }


def apply_profile(profile: dict, career: dict, profile_id: str, source_path: str) -> dict:
    """Layer a positioning profile on top of a career source (deep copy)."""
    eff = copy.deepcopy(career)

    meta = dict(eff.get("meta") or {})
    pmeta = profile.get("meta") or {}
    meta["profile"] = {
        "id": profile_id,
        "market": pmeta.get("market"),
        "profile": pmeta.get("profile"),
    }
    meta["source"] = source_path
    eff["meta"] = meta

    if profile.get("headline"):
        eff.setdefault("identity", {})["headline"] = profile["headline"]
    if profile.get("summary"):
        eff["summary"] = profile["summary"]
    for key in ("target_roles", "emphasis"):
        if key in profile:
            eff[key] = profile[key]

    eff["experience_priority"] = profile.get("experience_priority") or []
    eff["skills_priority"] = profile.get("skills_priority") or []
    eff["projects_priority"] = profile.get("projects_priority") or []
    eff["old_experience_max_bullets"] = int(profile.get("old_experience_max_bullets", 1))
    recent_jobs = int(profile.get("recent_jobs", DEFAULT_RECENT_JOBS))

    eff["experience"] = _ranked_experience(
        eff.get("experience") or [],
        eff["experience_priority"],
        recent_jobs,
        eff["old_experience_max_bullets"],
    )
    eff["projects"] = reorder_by_priority(
        eff.get("projects") or [], eff["projects_priority"],
        key=lambda p: p.get("name", ""),
    )
    eff["skills"] = _ranked_skills(eff.get("skills") or {}, eff["skills_priority"])
    return eff


def load_effective(yaml_file: str) -> tuple[dict, dict]:
    """
    Load any YAML under profiles/ as an effective resume dict.

    Returns ``(effective_base, info)`` where ``info`` records the kind
    ("source" | "profile"), the profile id, and the resolved source path so
    callers can keep provenance.
    """
    import yaml

    path = Path(yaml_file)
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    info = {
        "path": str(path),
        "kind": "source",
        "source": str(path),
        "profile": None,
    }
    if not is_positioning_profile(data):
        return data, info

    source_path = resolve_source_path(str(path), data)
    if not source_path or not Path(source_path).exists():
        raise FileNotFoundError(
            f"Positioning profile {path} needs a career source: add "
            f"`source: {{career: ./{DEFAULT_SOURCE}}}` or place {DEFAULT_SOURCE} "
            "next to it."
        )
    with open(source_path, encoding="utf-8") as f:
        career = yaml.safe_load(f) or {}

    profile_id = path.stem
    info.update({
        "kind": "profile",
        "source": source_path,
        "profile": profile_id,
    })
    return apply_profile(data, career, profile_id, source_path), info


def list_profiles(profiles_dir: str = PROFILES_DIR) -> list[dict]:
    """Classify every YAML in profiles/ for CLI + WebUI listings."""
    import yaml

    rows: list[dict] = []
    base = Path(profiles_dir)
    if not base.exists():
        return rows
    for p in sorted(base.glob("*.yaml")):
        if not p.is_file():
            continue
        try:
            with open(p, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except yaml.YAMLError:
            continue
        kind = "profile" if is_positioning_profile(data) else "source"
        meta = data.get("meta") or {}
        rows.append({
            "name": p.name,
            "path": str(p),
            "kind": kind,
            "market": meta.get("market"),
            "focus": meta.get("profile"),
            "source": resolve_source_path(str(p), data) if kind == "profile" else None,
            "target_roles": (data.get("target_roles") or [])[:3],
        })
    return rows
