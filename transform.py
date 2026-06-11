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
import httpx
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://rxresu.me/api/openapi"
API_KEY = os.environ.get("RXRESU_REACTIVE_RESUME_API_KEY", "")

BASE_FILE = "base.yaml"


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


def make_uuid() -> str:
    import uuid
    return str(uuid.uuid4())


# ── section builders (rxresume schema) ────────────────────────────────────────

def build_basics(identity: dict) -> dict:
    urls = {u["label"].lower(): u["url"] for u in identity.get("urls", [])}
    return {
        "name": identity["name"],
        "headline": "",
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


def build_summary_content(data: dict, target_tags: set = None) -> str:
    cls = data.get("cover_letters", [])
    if target_tags and target_tags.intersection({"ai", "fullstack"}):
        match = next((c for c in cls if c["id"] == "ai-fullstack-focused"), None)
    elif target_tags and target_tags.intersection({"backend", "api"}):
        match = next((c for c in cls if c["id"] == "backend-focused"), None)
    else:
        match = next((c for c in cls if c["id"] == "leadership-focused"), None)
    if match:
        return match["body"].replace("{opening}", "").replace("{closing}", "").strip()
    return ""


def build_experience_items(exp_list: list, required_tags: set = None) -> list:
    active = filter_active(exp_list, required_tags)
    items = []
    for job in active:
        bullets = [
            b["text"] for b in job.get("bullets", [])
            if b.get("status") != "deprecated"
            and (not required_tags or required_tags.intersection(set(b.get("tags", []))))
        ]
        start = iso_to_readable(job['start'])
        end = iso_to_readable(job.get('end')) or "Present"
        period = f"{start} – {end}"
        items.append({
            "id": make_uuid(),
            "hidden": False,
            "company": job["company"],
            "position": job["title"],
            "location": job["location"],
            "period": period,
            "website": {"url": "", "label": ""},
            "description": "\n".join(f"• {b}" for b in bullets),
            "roles": [],
        })
    return items


def build_education_items(edu_list: list) -> list:
    return [
        {
            "id": make_uuid(),
            "hidden": False,
            "school": e["institution"],
            "degree": e["degree"],
            "area": "",
            "grade": "",
            "location": "",
            "period": iso_to_readable(e.get("graduation")),
            "website": {"url": "", "label": ""},
            "description": "",
        }
        for e in filter_active(edu_list)
    ]


def build_skills_items(skills: dict) -> list:
    result = []
    for _category, items in skills.items():
        for skill in items:
            if skill.get("status") == "deprecated":
                continue
            level_num = {"expert": 5, "advanced": 4, "intermediate": 3}.get(
                skill.get("level", ""), 3
            )
            result.append({
                "id": make_uuid(),
                "hidden": False,
                "icon": "",
                "iconColor": "",
                "name": skill["name"],
                "proficiency": skill.get("level", "").title(),
                "level": level_num,
                "keywords": skill.get("tags", []),
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


def build_profiles() -> list:
    return [
        {
            "id": make_uuid(), "hidden": False,
            "icon": "github-logo", "iconColor": "",
            "network": "GitHub", "username": "williamjxj",
            "website": {"url": "https://github.com/williamjxj", "label": "@williamjxj"},
        },
        {
            "id": make_uuid(), "hidden": False,
            "icon": "linkedin-logo", "iconColor": "",
            "network": "LinkedIn", "username": "William Jiang",
            "website": {"url": "https://www.linkedin.com/in/william-jiang-226a7616/", "label": "william-jiang"},
        },
    ]


def build_metadata(template: str) -> dict:
    return {
        "template": template,
        "layout": {
            "sidebarWidth": 35,
            "pages": [
                {
                    "fullWidth": False,
                    "main": ["profiles", "summary", "education", "experience", "projects"],
                    "sidebar": ["skills"],
                }
            ],
        },
        "page": {
            "gapX": 4, "gapY": 6, "marginX": 14, "marginY": 12,
            "format": "letter", "locale": "en-US",
            "hideLinkUnderline": False, "hideIcons": False, "hideSectionIcons": True,
        },
        "design": {
            "level": {"icon": "star", "type": "circle"},
            "colors": {
                "primary": "rgba(37, 99, 235, 1)",
                "text": "rgba(0, 0, 0, 1)",
                "background": "rgba(255, 255, 255, 1)",
            },
        },
        "typography": {
            "body": {"fontFamily": "IBM Plex Serif", "fontWeights": ["400", "500"], "fontSize": 14, "lineHeight": 1.5},
            "heading": {"fontFamily": "IBM Plex Serif", "fontWeights": ["600"], "fontSize": 20, "lineHeight": 1.5},
        },
        "notes": "",
        "styleRules": [],
    }


# ── build patch operations (JSON Patch RFC 6902, paths relative to /data) ────

def build_operations(base: dict, target_tags: set = None, template: str = "elegant") -> list:
    """Convert all resume sections into JSON Patch replace operations."""
    ops = []
    basics = build_basics(base["identity"])
    summary_content = build_summary_content(base, target_tags)
    metadata = build_metadata(template)

    field_map = {
        "/basics": basics,
        "/summary/content": summary_content,
        "/summary/hidden": False,
        "/sections/profiles/items": build_profiles(),
        "/sections/profiles/hidden": False,
        "/sections/experience/items": build_experience_items(base["experience"], target_tags),
        "/sections/education/items": build_education_items(base["education"]),
        "/sections/skills/items": build_skills_items(base["skills"]),
        "/sections/projects/items": build_projects_items(base["projects"], target_tags),
        "/metadata": metadata,
    }

    for path, value in field_map.items():
        ops.append({"op": "replace", "path": path, "value": value})

    return ops


# ── LLM enhancement (optional) ────────────────────────────────────────────────

def llm_enhance_summary(raw_bullets: list[str], target_role: str) -> str:
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=os.environ.get("DEEPSEEK_API_KEY"),
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        )
        model = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")
        prompt = f"""You are a senior technical resume writer.
Given these bullet points from a Full-Stack/AI engineer's career, write a 3-sentence professional
summary targeting a {target_role} role. Be specific, quantified where possible.
Return plain text, no markdown.

Bullets:
{chr(10).join(f'- {b}' for b in raw_bullets[:10])}
"""
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM summary enhancement unavailable ({e})")
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


def list_resumes() -> list:
    headers = {"x-api-key": API_KEY}
    r = httpx.get(f"{API_BASE}/resumes", headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="base.yaml → Reactive Resume API")
    parser.add_argument("--yaml", default=BASE_FILE, help="Path to base.yaml")
    parser.add_argument("--tags", default="fullstack,ai,react,node,python",
                        help="Comma-separated tag filter")
    parser.add_argument("--template", default="elegant",
                        help="rxresume template name (elegant, bronzor, leafish, etc.)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print JSON payload, don't POST")
    parser.add_argument("--resume-id", default=None,
                        help="PATCH existing resume instead of creating new")
    parser.add_argument("--llm", action="store_true",
                        help="Use DeepSeek LLM to enhance summary and select bullets")
    parser.add_argument("--role", default="AI Architect / Full-Stack Engineer",
                        help="Target role description (used with --llm)")
    args = parser.parse_args()

    if not API_KEY:
        print("Error: RXRESU_REACTIVE_RESUME_API_KEY not set in .env")
        exit(1)

    with open(args.yaml) as f:
        base = yaml.safe_load(f)

    required_tags = set(args.tags.split(",")) if args.tags else None

    if args.llm:
        print("Running LLM enhancement...")
        all_bullets = []
        for job in base.get("experience", []):
            if job.get("status") == "deprecated":
                continue
            for b in job.get("bullets", []):
                if b.get("status") != "deprecated":
                    all_bullets.append(b)

        summary_text = llm_enhance_summary([b["text"] for b in all_bullets], args.role)
        if summary_text:
            print(f"LLM summary generated ({len(summary_text)} chars)")

    ops = build_operations(base, required_tags, args.template)
    resume_name = f"william-jiang-{args.template}"

    if args.dry_run:
        print(json.dumps(ops, indent=2))
        print(f"\nTotal operations: {len(ops)}")
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
            "metadata": {"template": "onyx", "layout": {"sidebarWidth": 35, "pages": []}, "page": {}, "design": {}, "typography": {}, "notes": "", "styleRules": []},
        }
        rid = create_resume(resume_name, resume_name, blank_data)
        result = patch_resume(rid, ops)
        print(f"✅ Created & filled resume: https://rxresu.me/builder/{rid}")
