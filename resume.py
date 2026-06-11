#!/usr/bin/env python3
"""
Resume Composition Engine
Usage: python resume.py build --jd <file> --tags <tags> --template <name>
"""

import yaml
import json
import argparse
import subprocess
import os
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

BASE_FILE = "base.yaml"
LOG_FILE = "applications.json"
OUTPUT_DIR = "output"
VARIANTS_DIR = "variants"

def load_base():
    with open(BASE_FILE) as f:
        return yaml.safe_load(f)

def load_log():
    if Path(LOG_FILE).exists():
        with open(LOG_FILE) as f:
            return json.load(f)
    return {"applications": []}

def save_log(log):
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

def filter_by_tags(items, tags, status_filter=["active"]):
    """Filter a list of items by tags and status."""
    if not tags:
        return [i for i in items if i.get("status", "active") in status_filter]
    return [
        i for i in items
        if i.get("status", "active") in status_filter
        and any(t in i.get("tags", []) for t in tags)
    ]

def _parse_phone(phone: str) -> str:
    """Normalize a phone number to E.164 format (+1XXXXXXXXXX)."""
    digits = re.sub(r"[^\d]", "", phone)
    # If it's 10 digits (NA), assume +1
    if len(digits) == 10:
        return f"+1{digits}"
    # If it already has country code
    if len(digits) >= 11:
        return f"+{digits}"
    return phone


def _extract_username(url: str) -> str:
    """Extract the username portion from a social network URL."""
    # Strip trailing slash
    url = url.rstrip("/")
    # Take the last path segment
    return url.rsplit("/", 1)[-1]


def build_variant(base, tags, template, company, role, jd_text=None):
    """Assemble a job-specific variant from the base."""
    tags_list = [t.strip() for t in tags.split(",")] if tags else []

    sections = {}

    # Experience — filter bullets by tags
    exp_section = []
    for job in base.get("experience", []):
        if job.get("status") != "active":
            continue
        filtered_bullets = filter_by_tags(job.get("bullets", []), tags_list)
        if not filtered_bullets:
            continue
        exp_section.append({
            "company": job["company"],
            "position": job["title"],
            "location": job["location"],
            "start_date": job["start"],
            "end_date": job.get("end") or "present",
            "highlights": [b["text"] for b in filtered_bullets]
        })
    exp_section.sort(key=lambda e: e["start_date"], reverse=True)
    sections["experience"] = exp_section

    # Skills — filter by tags
    all_skills = []
    for category, items in base.get("skills", {}).items():
        filtered = filter_by_tags(items, tags_list)
        if filtered:
            all_skills.append({
                "label": category.title(),
                "details": ", ".join(s["name"] for s in filtered)
            })
    sections["skills"] = all_skills

    # Projects
    sections["projects"] = [
        {
            "name": p["name"],
            "summary": p["description"],
            "highlights": [b["text"] for b in p.get("bullets", []) if b.get("status") == "active"]
        }
        for p in base.get("projects", [])
        if p.get("status") == "active"
        and (not tags_list or any(t in p.get("tags", []) for t in tags_list))
    ]

    # Education
    sections["education"] = [
        {
            "institution": e["institution"],
            "area": e["degree"],
            "degree": "",
            "date": e["graduation"]
        }
        for e in base.get("education", [])
        if e.get("status") == "active"
    ]

    variant = {
        "cv": {
            "name": base["identity"]["name"],
            "email": base["identity"]["email"],
            "phone": _parse_phone(base["identity"]["phone"]),
            "location": base["identity"]["location"],
            "social_networks": [
                {"network": u["label"], "username": _extract_username(u["url"])}
                for u in base["identity"]["urls"]
                if u["status"] == "active"
            ],
            "sections": sections,
        },
        "design": {
            "theme": template,
            "page": {
                "size": "us-letter",
                "top_margin": "0.7in",
                "bottom_margin": "0.7in",
                "left_margin": "0.7in",
                "right_margin": "0.7in",
            },
            "colors": {
                "name": "rgb(0,79,144)",
                "headline": "rgb(0,79,144)",
                "connections": "rgb(0,79,144)",
                "section_titles": "rgb(0,79,144)",
                "links": "rgb(0,79,144)",
            },
            "typography": {
                "font_family": "Source Sans 3",
                "font_size": {
                    "body": "10pt",
                    "name": "30pt",
                    "headline": "10pt",
                    "connections": "10pt",
                    "section_titles": "1.4em",
                },
            },
            "header": {
                "alignment": "center",
            },
            "links": {
                "show_external_link_icon": False,
            },
        },
    }

    return variant

def write_variant(variant, slug):
    """Write the variant YAML to disk."""
    Path(VARIANTS_DIR).mkdir(exist_ok=True)
    path = f"{VARIANTS_DIR}/{slug}.yaml"
    with open(path, "w") as f:
        yaml.dump(variant, f, allow_unicode=True, sort_keys=False)
    return path

def render_variant(variant_path, slug):
    """Call rendercv to render the variant to PDF + HTML."""
    output_path = str(Path(OUTPUT_DIR).resolve() / slug)
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    result = subprocess.run(
        ["rendercv", "render", variant_path, "--output-folder", output_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"rendercv error:\n{result.stderr}")
        return False
    return True

def log_application(slug, company, role, tags, template, jd_file):
    """Record this application in the tracking log."""
    log = load_log()
    log["applications"].append({
        "id": slug,
        "company": company,
        "role": role,
        "date": datetime.now().isoformat()[:10],
        "tags_used": tags,
        "template": template,
        "jd_source": jd_file,
        "variant_file": f"{VARIANTS_DIR}/{slug}.yaml",
        "output_dir": f"{OUTPUT_DIR}/{slug}"
    })
    save_log(log)

def cmd_build(args):
    base = load_base()
    slug = f"{args.company.lower().replace(' ','-')}-{args.role.lower().replace(' ','-')}-{datetime.now().strftime('%Y%m')}"

    jd_text = None
    if args.jd:
        with open(args.jd) as f:
            jd_text = f.read()

    # Optional LLM step
    tags = args.tags
    if args.llm and jd_text:
        print("Running LLM JD analysis...")
        tags = llm_extract_tags(jd_text, base)
        print(f"LLM suggested tags: {tags}")

    print(f"Building variant: {slug}")
    print(f"Tags: {tags}")
    print(f"Template: {args.template}")

    variant = build_variant(base, tags, args.template, args.company, args.role, jd_text)
    variant_path = write_variant(variant, slug)
    print(f"Variant written: {variant_path}")

    print("Rendering PDF + HTML...")
    success = render_variant(variant_path, slug)
    if success:
        print(f"Output: {OUTPUT_DIR}/{slug}/")

    log_application(slug, args.company, args.role, tags, args.template, args.jd)
    print(f"Logged to {LOG_FILE}")

def cmd_tags(args):
    base = load_base()
    all_tags = set()
    for job in base.get("experience", []):
        for bullet in job.get("bullets", []):
            all_tags.update(bullet.get("tags", []))
    for cat, items in base.get("skills", {}).items():
        for item in items:
            all_tags.update(item.get("tags", []))
    print("Available tags:\n" + "\n".join(sorted(all_tags)))

def cmd_log(args):
    log = load_log()
    apps = log.get("applications", [])
    if not apps:
        print("No applications logged yet.")
        return
    for a in apps:
        print(f"\n{a['date']} — {a['company']} / {a['role']}")
        print(f"  ID:       {a['id']}")
        print(f"  Tags:     {a['tags_used']}")
        print(f"  Template: {a['template']}")
        print(f"  Output:   {a['output_dir']}")

def llm_extract_tags(jd_text, base):
    """
    Optional: call an LLM to extract relevant tags from the JD.
    Falls back to empty string if no LLM configured.
    """
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=os.environ.get("DEEPSEEK_API_KEY"),
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        )

        all_tags = set()
        for job in base.get("experience", []):
            for b in job.get("bullets", []):
                all_tags.update(b.get("tags", []))
        for cat, items in base.get("skills", {}).items():
            for item in items:
                all_tags.update(item.get("tags", []))

        model = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")
        prompt = f"""Given this job description, select the most relevant tags from the list below.
Return ONLY a comma-separated list of tags, nothing else.

Available tags: {', '.join(sorted(all_tags))}

Job description:
{jd_text[:3000]}
"""
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM not available ({e}), skipping tag extraction")
        return ""

def main():
    load_dotenv()  # Load .env file for DEEPSEEK_API_KEY
    parser = argparse.ArgumentParser(description="Resume composition engine")
    subparsers = parser.add_subparsers()

    # build command
    build_parser = subparsers.add_parser("build", help="Build a job-specific resume variant")
    build_parser.add_argument("--jd", help="Path to job description text file")
    build_parser.add_argument("--tags", default="", help="Comma-separated tags to filter by")
    build_parser.add_argument("--template", default="classic", help="Template name")
    build_parser.add_argument("--company", required=True, help="Company name")
    build_parser.add_argument("--role", required=True, help="Role title")
    build_parser.add_argument("--llm", action="store_true", help="Use LLM for JD analysis")
    build_parser.set_defaults(func=cmd_build)

    # tags command
    tags_parser = subparsers.add_parser("tags", help="List all available tags in base")
    tags_parser.set_defaults(func=cmd_tags)

    # log command
    log_parser = subparsers.add_parser("log", help="Show application history")
    log_parser.set_defaults(func=cmd_log)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
