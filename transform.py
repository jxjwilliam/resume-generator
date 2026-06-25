#!/usr/bin/env python3
"""
base.yaml → Reactive Resume (rxresu.me) API payload
Usage:
  python transform.py --tags fullstack,ai --template elegant --dry-run
  python transform.py --tags fullstack,ai --resume-id <UUID>
"""
import yaml
import json
import argparse
import os
import sys
import base64
import io
import httpx
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from compose import DEFAULT_MAX_BULLETS, select_experience_jobs
from llm_config import LLMNotConfiguredError, get_llm_client, llm_chat_completion

load_dotenv()

API_BASE = "https://rxresu.me/api/openapi"
API_KEY = os.environ.get("RXRESU_API_KEY", "")

PROFILES_DIR = "profiles"
BASE_FILE = f"{PROFILES_DIR}/base.yaml"
DEFAULT_MAX_BULLETS = 4
PHOTO_CANDIDATES = [
    "assets/william-jiang.jpg",
    "assets/William-Jiang-1.png",
    "assets/william-jiang-1.png",
]


# ── helpers ───────────────────────────────────────────────────────────────────

MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def iso_to_display(date_str: Optional[str]) -> Optional[str]:
    """'2021-03' → '2021-03-01' (rxresume expects ISO 8601 date)"""
    if not date_str:
        return None
    parts = date_str.split("-")
    if len(parts) == 2:
        return f"{parts[0]}-{parts[1]}-01"
    return date_str

def iso_to_readable(date_str: Optional[str]) -> Optional[str]:
    """"2021-03" → "Mar 2021" """
    if not date_str:
        return None
    parts = date_str.split("-")
    year = parts[0]
    if len(parts) >= 2:
        try:
            month_num = int(parts[1])
            return f"{MONTHS[month_num]} {year}" if 1 <= month_num <= 12 else year
        except (ValueError, IndexError):
            pass
    return year


def filter_active(items: list, required_tags: set = None) -> list:
    out = []
    for item in items:
        if item.get("status") == "deprecated":
            continue
        if required_tags:
            item_tags = set(item.get("tags", []))
            if not required_tags.intersection(item_tags):
                continue
        out.append(item)
    return out


def filter_bullets(bullets: list, required_tags: set = None) -> list:
    """Keep active bullets; when tags are set, match on bullet tags only."""
    out = []
    for b in bullets:
        if b.get("status") == "deprecated":
            continue
        if required_tags:
            if not required_tags.intersection(set(b.get("tags", []))):
                continue
        out.append(b)
    return out


def sort_jobs_reverse_chronological(jobs: list) -> list:
    """Newest roles first (matches standard resume order)."""
    def sort_key(job):
        start = job.get("start") or "0000-00"
        end = job.get("end") or "9999-12"
        return (start, end)
    return sorted(jobs, key=sort_key, reverse=True)


def resolve_photo_path(explicit: Optional[str], identity: dict) -> Optional[Path]:
    """Pick the first existing photo path (jpg preferred — smaller upload)."""
    candidates = []
    if explicit:
        candidates.append(explicit)
    if identity.get("photo"):
        candidates.append(identity["photo"])
    candidates.extend(PHOTO_CANDIDATES)
    for raw in candidates:
        path = Path(raw)
        if path.is_file():
            return path
    return None


def build_picture_data_url(image_path: Path, max_px: int = 400) -> dict:
    """Resize photo and embed as a data URL (rxresu.me accepts this via PATCH)."""
    from PIL import Image

    img = Image.open(image_path).convert("RGB")
    img.thumbnail((max_px, max_px))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    data_url = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"
    aspect = round(img.width / img.height, 2) if img.height else 1.0
    return {
        "hidden": False,
        "url": data_url,
        "size": 100,
        "rotation": 0,
        "aspectRatio": aspect,
        "borderRadius": 50,
        "borderColor": "rgba(0, 0, 0, 0)",
        "borderWidth": 0,
        "shadowColor": "rgba(0, 0, 0, 0.2)",
        "shadowWidth": 2,
    }


SKILL_CATEGORY_LABELS = {
    "languages": "Languages",
    "frameworks": "Frameworks & Libraries",
    "tools": "Tools & Platforms",
    "ai_tools": "AI & Development Tools",
}


def make_uuid() -> str:
    import uuid
    return str(uuid.uuid4())


# ── section builders (rxresume schema) ────────────────────────────────────────

def build_basics(identity: dict, headline_override: str = None) -> dict:
    urls = {u["label"].lower(): u["url"] for u in identity.get("urls", [])}
    return {
        "name": identity["name"],
        "headline": headline_override or identity.get("headline", ""),
        "email": identity["email"],
        "phone": identity["phone"],
        "location": identity["location"],
        "website": {"url": urls.get("github", ""), "label": "GitHub"},
        "customFields": [
            {
                "id": "cf-linkedin",
                "icon": "linkedin",
                "text": "LinkedIn",
                "link": urls.get("linkedin", ""),
            }
        ],
    }


def build_summary_content(data: dict, target_tags: set = None, use_cover_letter: bool = False) -> str:
    if not use_cover_letter and data.get("summary"):
        return data["summary"].strip()
    cls = data.get("cover_letters", [])
    if target_tags and target_tags.intersection({"ai", "fullstack"}):
        match = next((c for c in cls if c["id"] == "ai-fullstack-focused"), None)
    elif target_tags and target_tags.intersection({"backend", "api"}):
        match = next((c for c in cls if c["id"] == "backend-focused"), None)
    else:
        match = next((c for c in cls if c["id"] == "leadership-focused"), None)
    if match:
        return match["body"].replace("{opening}", "").replace("{closing}", "").strip()
    return data.get("summary", "").strip()


def build_experience_items(
    exp_list: list,
    required_tags: set = None,
    max_bullets: int = DEFAULT_MAX_BULLETS,
) -> list:
    """Include jobs when any bullet matches tags; sort newest-first."""
    tags = list(required_tags) if required_tags else None
    items = []
    for job, matched in select_experience_jobs(
        exp_list, tags=tags, max_bullets=max_bullets,
    ):
        start = iso_to_readable(job["start"])
        end = iso_to_readable(job.get("end")) or "Present"
        items.append({
            "id": make_uuid(),
            "hidden": False,
            "company": job["company"],
            "position": job["title"],
            "location": job["location"],
            "period": f"{start} – {end}",
            "website": {"url": "", "label": ""},
            "description": "\n".join(f"• {b['text']}" for b in matched),
            "roles": [],
        })
    return items


def build_education_items(edu_list: list) -> list:
    items = []
    for e in filter_active(edu_list):
        start = iso_to_readable(e.get("start"))
        end = iso_to_readable(e.get("graduation"))
        if start and end:
            period = f"{start} – {end}"
        else:
            period = end or start or ""
        items.append({
            "id": make_uuid(),
            "hidden": False,
            "school": e["institution"],
            "degree": e["degree"],
            "area": e.get("location", ""),
            "grade": "",
            "location": e.get("location", ""),
            "period": period,
            "website": {"url": "", "label": ""},
            "description": "",
        })
    return items


def build_skills_items(
    skills: dict,
    required_tags: set = None,
    mode: str = "grouped",
    show_levels: bool = False,
) -> list:
    """Build skills section items.

    grouped (default): one row per base.yaml category, technologies as keyword tags.
    flat: one row per skill (legacy behaviour); dot ratings hidden unless show_levels.
    """
    if mode == "flat":
        return _build_skills_flat(skills, required_tags, show_levels)
    return _build_skills_grouped(skills, required_tags)


def _build_skills_flat(skills: dict, required_tags: set, show_levels: bool) -> list:
    result = []
    for items in skills.values():
        for skill in filter_active(items, required_tags):
            level_num = {"expert": 5, "advanced": 4, "intermediate": 3}.get(
                skill.get("level", ""), 3
            )
            result.append({
                "id": make_uuid(),
                "hidden": False,
                "icon": "",
                "iconColor": "",
                "name": skill["name"],
                "proficiency": skill.get("level", "").title() if show_levels else "",
                "level": level_num if show_levels else 0,
                "keywords": [],
            })
    return result


def _build_skills_grouped(skills: dict, required_tags: set) -> list:
    result = []
    for category, items in skills.items():
        active = filter_active(items, required_tags)
        if not active:
            continue
        label = SKILL_CATEGORY_LABELS.get(category, category.replace("_", " ").title())
        result.append({
            "id": make_uuid(),
            "hidden": False,
            "icon": "",
            "iconColor": "",
            "name": label,
            "proficiency": "",
            "level": 0,
            "keywords": [s["name"] for s in active],
        })
    return result


def build_projects_items(projects: list, required_tags: set = None) -> list:
    active = filter_active(projects, required_tags)
    return [
        {
            "id": make_uuid(),
            "hidden": False,
            "name": p["name"],
            "period": "",
            "website": {"url": p.get("url", ""), "label": ""},
            "description": "<ul>" + "".join(
                f"<li>{b['text']}</li>"
                for b in p.get("bullets", [])
                if b.get("status") != "deprecated"
            ) + "</ul>",
        }
        for p in active
    ]


def build_metadata(template: str, skills_mode: str = "grouped", include_projects: bool = True) -> dict:
    main_sections = ["summary", "skills", "experience"]
    if include_projects:
        main_sections.append("projects")
    main_sections.append("education")
    return {
        "template": template,
        "layout": {
            "sidebarWidth": 35,
            "pages": [
                {
                    "fullWidth": True,
                    "main": main_sections,
                    "sidebar": [],
                }
            ],
        },
        "page": {
            "gapX": 4, "gapY": 3, "marginX": 12, "marginY": 10,
            "format": "letter", "locale": "en-US",
            "hideLinkUnderline": False, "hideIcons": False, "hideSectionIcons": True,
        },
        "design": {
            "level": {"icon": "star", "type": "hidden" if skills_mode == "grouped" else "circle"},
            "colors": {
                "primary": "rgba(37, 99, 235, 1)",
                "text": "rgba(0, 0, 0, 1)",
                "background": "rgba(255, 255, 255, 1)",
            },
        },
        "typography": {
            "body": {"fontFamily": "IBM Plex Sans", "fontWeights": ["400", "500"], "fontSize": 10, "lineHeight": 1.35},
            "heading": {"fontFamily": "IBM Plex Sans", "fontWeights": ["600"], "fontSize": 17, "lineHeight": 1.25},
        },
        "notes": "",
        "styleRules": [],
    }


# ── build patch operations (JSON Patch RFC 6902, paths relative to /data) ────

def build_operations(
    base: dict,
    target_tags: set = None,
    template: str = "elegant",
    skills_mode: str = "grouped",
    all_skills: bool = False,
    show_skill_levels: bool = False,
    max_bullets: int = DEFAULT_MAX_BULLETS,
    use_cover_letter: bool = False,
    include_projects: bool = True,
    photo_path: Optional[Path] = None,
    include_photo: bool = True,
    headline_override: str = None,
    summary_override: str = None,
) -> list:
    """Convert all resume sections into JSON Patch replace operations."""
    basics = build_basics(base["identity"], headline_override)
    summary_content = summary_override or build_summary_content(base, target_tags, use_cover_letter)
    metadata = build_metadata(template, skills_mode, include_projects)
    skill_tags = None if all_skills else target_tags
    skills_columns = 2 if skills_mode == "grouped" else 1

    field_map = {
        "/basics": basics,
        "/summary/content": summary_content,
        "/summary/hidden": False,
        "/sections/profiles/items": [],
        "/sections/profiles/hidden": True,
        "/sections/experience/items": build_experience_items(
            base["experience"], target_tags, max_bullets
        ),
        "/sections/education/items": build_education_items(base["education"]),
        "/sections/skills/items": build_skills_items(
            base["skills"], skill_tags, skills_mode, show_skill_levels
        ),
        "/sections/skills/columns": skills_columns,
        "/sections/skills/hidden": False,
        "/sections/projects/items": build_projects_items(base["projects"], target_tags),
        "/sections/projects/hidden": not include_projects,
        "/metadata": metadata,
    }

    if include_photo and photo_path:
        field_map["/picture"] = build_picture_data_url(photo_path)

    return [{"op": "replace", "path": path, "value": value} for path, value in field_map.items()]


# ── LLM enhancement (optional) ────────────────────────────────────────────────

def llm_generate_headline(jd_text: str, role: str | None = None, llm_provider=None) -> str:
    """Use LLM to generate a job-specific headline from the JD and target role. Falls back to empty string."""
    try:
        client, model, _cfg = get_llm_client(llm_provider)
        role_line = f"The target role is: {role}." if role else ""
        prompt = f"""Write a concise 1-line professional headline (10-15 words) for a resume targeting this job. {role_line} The headline MUST reflect the target role title. Include core relevant technologies. Return ONLY the headline text, nothing else.

Job description:
{jd_text[:3000]}
"""
        raw = llm_chat_completion(
            client, model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
        )
        return raw.strip().strip('"')
    except LLMNotConfiguredError as e:
        print(f"LLM not configured: {e}", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"LLM headline error ({type(e).__name__}: {e})", file=sys.stderr)
        return ""


def llm_generate_summary(jd_text: str, base: dict, role: str | None = None, llm_provider=None) -> str:
    """Use LLM to generate a job-specific summary from the JD + top experience bullets."""
    try:
        client, model, _cfg = get_llm_client(llm_provider)
        active_bullets = []
        for job in base.get("experience", []):
            if job.get("status") != "active":
                continue
            for b in job.get("bullets", []):
                if b.get("status") != "deprecated":
                    active_bullets.append(b["text"])
        bullets_text = "\n".join(f"- {b}" for b in active_bullets[:10])
        role_line = f" Target role: {role}." if role else ""
        prompt = f"""Write a 3-4 sentence professional summary for a resume targeting this job.{role_line} The summary MUST reflect the target role level and focus on experience relevant to that role. Draw from the candidate's actual experience:

{bullets_text}

The summary should highlight relevant skills, years of experience, and achievements that match the job description. Return ONLY the summary text, nothing else.

Job description:
{jd_text[:3000]}
"""
        raw = llm_chat_completion(
            client, model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
        )
        return raw.strip().strip('"')
    except LLMNotConfiguredError as e:
        print(f"LLM not configured: {e}", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"LLM summary error ({type(e).__name__}: {e})", file=sys.stderr)
        return ""


# ── API calls ─────────────────────────────────────────────────────────────────

def create_resume(name: str, slug: str, data: dict) -> str:
    """Create a blank resume, returns its ID as a plain string."""
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    payload = {"name": name, "slug": slug, "tags": [], "data": data}
    r = httpx.post(f"{API_BASE}/resumes", headers=headers, json=payload, timeout=30)
    if r.status_code == 200:
        return r.json()
    r.raise_for_status()


def patch_resume(resume_id: str, operations: list) -> dict:
    """Apply JSON Patch operations to an existing resume."""
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    payload = {"id": resume_id, "operations": operations}
    r = httpx.patch(f"{API_BASE}/resumes/{resume_id}", headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def list_resumes() -> list:
    headers = {"x-api-key": API_KEY}
    r = httpx.get(f"{API_BASE}/resumes", headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=f"{BASE_FILE} → Reactive Resume API")
    parser.add_argument("--yaml", default=BASE_FILE, help=f"Path to {BASE_FILE}")
    parser.add_argument("--tags", default="fullstack,ai,react,node,python",
                        help="Comma-separated tag filter")
    parser.add_argument("--template", default="kakuna",
                        help="rxresume template (kakuna, bronzor, elegant, or auto from --jd)")
    parser.add_argument("--skills-mode", choices=["grouped", "flat"], default="grouped",
                        help="grouped: one row per category with keyword tags (default); flat: one row per skill")
    parser.add_argument("--all-skills", action="store_true",
                        help="Include all active skills, ignore --tags filter for skills only")
    parser.add_argument("--show-skill-levels", action="store_true",
                        help="Show proficiency dots (flat mode only; grouped always hides levels)")
    parser.add_argument("--max-bullets", type=int, default=DEFAULT_MAX_BULLETS,
                        help="Max bullets per job (0 = unlimited)")
    parser.add_argument("--no-projects", action="store_true",
                        help="Omit projects section (reduces page length)")
    parser.add_argument("--use-cover-letter", action="store_true",
                        help=f"Use cover letter template for summary instead of {BASE_FILE} summary")
    parser.add_argument("--photo", default=None,
                        help="Profile photo path (default: identity.photo or assets/william-jiang.jpg)")
    parser.add_argument("--no-photo", action="store_true",
                        help="Do not embed profile photo")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print JSON payload, don't POST")
    parser.add_argument("--resume-id", default=None,
                        help="PATCH existing resume instead of creating new")
    parser.add_argument("--jd", default=None,
                        help="Path to job description text file (required with --llm)")
    parser.add_argument("--llm", action="store_true",
                        help="Use LLM to rewrite headline + summary from JD")
    parser.add_argument("--llm-provider", choices=["deepseek", "kimi", "minimax"],
                        help="LLM provider override (default: LLM_PROVIDER in .env)")
    parser.add_argument("--role", default=None,
                        help="Target role (extracted from JD first line if omitted with --llm)")
    args = parser.parse_args()

    if not args.dry_run and not API_KEY:
        print("Error: RXRESU_API_KEY not set in .env")
        exit(1)

    with open(args.yaml) as f:
        base = yaml.safe_load(f)

    required_tags = set(t for t in args.tags.split(",") if t) if args.tags else None
    photo_path = None if args.no_photo else resolve_photo_path(args.photo, base.get("identity", {}))

    jd_text = None
    if args.jd:
        with open(args.jd) as f:
            jd_text = f.read()

    if args.llm and not jd_text:
        print("Error: --jd is required when using --llm", file=sys.stderr)
        exit(1)

    role = args.role
    headline_override = None
    summary_override = None
    if args.llm and jd_text:
        from llm_config import resolve_llm_config
        llm_provider = getattr(args, "llm_provider", None)
        cfg = resolve_llm_config(llm_provider)
        print(f"LLM provider: {cfg['label']} ({cfg['model']} @ {cfg['base_url']})")
        print("Running LLM enhancement...")
        if not role:
            role = jd_text.strip().split('\n')[0].strip()
            print(f"Extracted role from JD: {role}")

        print("Generating LLM headline...")
        headline_override = llm_generate_headline(jd_text, role, llm_provider=llm_provider)
        if headline_override:
            print(f"LLM headline: {headline_override}")
        else:
            print(f"LLM headline failed, using {BASE_FILE} headline")

        print("Generating LLM summary...")
        summary_override = llm_generate_summary(jd_text, base, role, llm_provider=llm_provider)
        if summary_override:
            print(f"LLM summary: {summary_override[:80]}...")
        else:
            print(f"LLM summary failed, using {BASE_FILE} summary")

    if not headline_override and role:
        base_headline = base["identity"].get("headline", "")
        headline_override = f"{role} | {base_headline}" if base_headline else role

    rx_template = args.template
    if rx_template == "auto":
        if jd_text:
            from resume import select_rx_template_auto
            rx_template = select_rx_template_auto(jd_text)
            print(f"Auto-selected RxResume template: {rx_template}")
        else:
            rx_template = "kakuna"
            print("No JD for auto template — using kakuna")

    ops = build_operations(
        base, required_tags, rx_template,
        skills_mode=args.skills_mode,
        all_skills=args.all_skills,
        show_skill_levels=args.show_skill_levels,
        max_bullets=args.max_bullets,
        use_cover_letter=args.use_cover_letter,
        include_projects=not args.no_projects,
        photo_path=photo_path,
        include_photo=not args.no_photo,
        headline_override=headline_override,
        summary_override=summary_override,
    )
    resume_name = f"william-jiang-{rx_template}"

    if args.dry_run:
        exp_op = next(o for o in ops if o["path"] == "/sections/experience/items")
        skills_op = next(o for o in ops if o["path"] == "/sections/skills/items")
        summary_op = next(o for o in ops if o["path"] == "/summary/content")
        print(json.dumps(ops, indent=2))
        print(f"\nTotal operations: {len(ops)}")
        print(f"Summary: {len(summary_op['value'])} chars")
        print(f"Experience: {len(exp_op['value'])} jobs (newest first)")
        for item in exp_op["value"]:
            n = len([l for l in item.get("description", "").split("\n") if l.strip()])
            print(f"  • {item['company']} | {item['period']} | {n} bullets")
        print(f"Skills: {len(skills_op['value'])} groups ({args.skills_mode} mode)")
        if photo_path:
            print(f"Photo: {photo_path} ({'embedded' if any(o['path']=='/picture' for o in ops) else 'skipped'})")
        elif not args.no_photo:
            print(f"Photo: not found (use --photo or add identity.photo in {BASE_FILE})")
    elif args.resume_id:
        result = patch_resume(args.resume_id, ops)
        rid = result.get("id", args.resume_id)
        print(f"✅ Patched resume: https://rxresu.me/builder/{rid}")
    else:
        # POST first to get a resume ID, then PATCH
        blank_data = {
            "picture": {"hidden": False, "url": "", "size": 80},
            "basics": {"name": "William Jiang", "headline": "", "email": "", "phone": "", "location": "", "website": {"url": "", "label": ""}, "customFields": []},
            "summary": {"title": "", "icon": "article", "columns": 1, "hidden": False, "content": ""},
            "sections": {},
            "customSections": [],
            "metadata": {"template": rx_template, "layout": {"sidebarWidth": 35, "pages": []}, "page": {}, "design": {}, "typography": {}, "notes": "", "styleRules": []},
        }
        created = create_resume(resume_name, resume_name, blank_data)
        rid = created.get("id") if isinstance(created, dict) else created
        result = patch_resume(rid, ops)
        print(f"✅ Created & filled resume: https://rxresu.me/builder/{rid}")
