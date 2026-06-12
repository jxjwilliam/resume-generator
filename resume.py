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
import sys
import traceback
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
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) >= 11:
        return f"+{digits}"
    return phone


def _extract_username(url: str) -> str:
    url = url.rstrip("/")
    return url.rsplit("/", 1)[-1]


def build_variant(base, tags, template, company, role, jd_text=None,
                  headline_override=None, summary_override=None):
    """Assemble a job-specific variant from the base."""
    tags_list = [t.strip() for t in tags.split(",")] if tags else []

    sections = {}

    summary_text = summary_override or base.get("summary")
    if summary_text:
        sections["Summary"] = [summary_text]

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

    all_skills = []
    for category, items in base.get("skills", {}).items():
        filtered = filter_by_tags(items, tags_list)
        if filtered:
            all_skills.append({
                "label": category.title(),
                "details": ", ".join(s["name"] for s in filtered)
            })
    sections["skills"] = all_skills

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
            "headline": headline_override or base["identity"].get("headline", ""),
            "photo": str(Path("..") / base["identity"]["photo"]) if base["identity"].get("photo") else None,
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
    Path(VARIANTS_DIR).mkdir(exist_ok=True)
    path = f"{VARIANTS_DIR}/{slug}.yaml"
    with open(path, "w") as f:
        yaml.dump(variant, f, allow_unicode=True, sort_keys=False)
    return path

def render_variant(variant_path, slug, all_formats=False):
    """Call rendercv to render the variant. PDF-only by default."""
    output_path = str(Path(OUTPUT_DIR).resolve() / slug)
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    cmd = ["rendercv", "render", variant_path, "--output-folder", output_path]
    if not all_formats:
        cmd += ["--dont-generate-markdown", "--dont-generate-html", "--dont-generate-png"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"rendercv error:\n{result.stderr}")
        return False
    return True

def log_application(slug, company, role, tags, template, jd_file):
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

    if args.llm and not args.jd:
        print("Error: --jd is required when using --llm", file=sys.stderr)
        exit(1)
    if not args.role and not args.llm:
        print("Error: --role is required when not using --llm", file=sys.stderr)
        exit(1)

    jd_text = None
    role = args.role
    if args.jd:
        with open(args.jd) as f:
            jd_text = f.read()
        if args.llm and not role:
            role = jd_text.strip().split('\n')[0].strip()
            print(f"Extracted role from JD: {role}")

    slug = f"{args.company.lower().replace(' ','-')}-{role.lower().replace(' ','-')}-{datetime.now().strftime('%Y%m')}"

    tags = args.tags
    headline_override = None
    summary_override = None
    if args.llm and jd_text:
        print("Running LLM JD analysis...")
        tags = llm_extract_tags(jd_text, base)
        print(f"LLM suggested tags: {tags}")

        print("Generating LLM headline...")
        headline_override = llm_generate_headline(jd_text, role)
        if headline_override:
            print(f"LLM headline: {headline_override}")
        else:
            print("LLM headline failed, using base.yaml headline")

        print("Generating LLM summary...")
        summary_override = llm_generate_summary(jd_text, base, role)
        if summary_override:
            print(f"LLM summary: {summary_override[:80]}...")
        else:
            print("LLM summary failed, using base.yaml summary")

    if not headline_override and role:
        base_headline = base["identity"].get("headline", "")
        headline_override = f"{role} | {base_headline}" if base_headline else role
        print(f"Role-based headline: {headline_override}")

    print(f"Building variant: {slug}")
    print(f"Tags: {tags}")
    print(f"Template: {args.template}")

    variant = build_variant(base, tags, args.template, args.company, role, jd_text,
                            headline_override=headline_override, summary_override=summary_override)
    variant_path = write_variant(variant, slug)
    print(f"Variant written: {variant_path}")

    print("Rendering PDF...")
    success = render_variant(variant_path, slug, all_formats=args.all_formats)
    if success:
        print(f"Output: {OUTPUT_DIR}/{slug}/")

    log_application(slug, args.company, role, tags, args.template, args.jd)
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
        raw = response.choices[0].message.content
        if raw is None:
            print(f"LLM returned None content. finish_reason={response.choices[0].finish_reason}", file=sys.stderr)
            return ""
        return raw.strip()
    except Exception as e:
        print(f"LLM error ({type(e).__name__}: {e})", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return ""

def llm_generate_headline(jd_text: str, role: str | None = None) -> str:
    """
    Use LLM to generate a job-specific headline from the JD and target role.
    Falls back to empty string on error (caller uses base.yaml headline).
    """
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=os.environ.get("DEEPSEEK_API_KEY"),
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        )
        model = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")
        role_line = f"The target role is: {role}." if role else ""
        prompt = f"""Write a concise 1-line professional headline (10-15 words) for a resume targeting this job. {role_line} The headline MUST reflect the target role title. Include core relevant technologies. Return ONLY the headline text, nothing else.

Job description:
{jd_text[:3000]}
"""
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100
        )
        raw = response.choices[0].message.content
        if raw is None:
            print("LLM headline returned None", file=sys.stderr)
            return ""
        return raw.strip().strip('"')
    except Exception as e:
        print(f"LLM headline error ({type(e).__name__}: {e})", file=sys.stderr)
        return ""


def llm_generate_summary(jd_text: str, base: dict, role: str | None = None) -> str:
    """
    Use LLM to generate a job-specific summary from the JD + top experience bullets.
    Falls back to empty string on error (caller uses base.yaml summary).
    """
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=os.environ.get("DEEPSEEK_API_KEY"),
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        )
        model = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")

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
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        raw = response.choices[0].message.content
        if raw is None:
            print("LLM summary returned None", file=sys.stderr)
            return ""
        return raw.strip().strip('"')
    except Exception as e:
        print(f"LLM summary error ({type(e).__name__}: {e})", file=sys.stderr)
        return ""


def llm_rewrite_cover_letter(body: str, jd_text: str) -> str:
    """Use LLM to rewrite a cover letter body to better match the JD."""
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=os.environ.get("DEEPSEEK_API_KEY"),
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        )
        model = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")
        prompt = f"""Given this cover letter template and job description, rewrite the body to better match the role. Keep the same professional tone and paragraph structure (3-4 paragraphs). Keep the opening and closing sentences intact. Return ONLY the rewritten body, nothing else.

Cover letter body:
{body}

Job description:
{jd_text[:3000]}
"""
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600
        )
        raw = response.choices[0].message.content
        if raw is None:
            print("LLM cover letter returned None", file=sys.stderr)
            return body
        return raw.strip().strip('"')
    except Exception as e:
        print(f"LLM cover letter error ({type(e).__name__}: {e})", file=sys.stderr)
        return body


def cmd_cover_letter(args):
    base = load_base()

    if not args.company:
        print("Error: --company is required", file=sys.stderr)
        exit(1)

    jd_text = None
    if args.jd:
        with open(args.jd) as f:
            jd_text = f.read()

    role = args.role
    if args.llm and jd_text and not role:
        role = jd_text.strip().split('\n')[0].strip()

    tags_list = [t.strip() for t in args.tags.split(",") if t] if args.tags else None
    target_set = set(tags_list) if tags_list else None

    cls = base.get("cover_letters", [])
    if target_set and target_set.intersection({"ai", "fullstack"}):
        match = next((c for c in cls if c["id"] == "ai-fullstack-focused"), None)
    elif target_set and target_set.intersection({"backend", "api"}):
        match = next((c for c in cls if c["id"] == "backend-focused"), None)
    else:
        match = next((c for c in cls if c["id"] == "leadership-focused"), None)

    if not match:
        print("Error: No cover letter template found in base.yaml", file=sys.stderr)
        exit(1)

    cl_base = base.get("identity", {}).get("cover_letter_base", {})
    opening = cl_base.get("opening", "").replace("{role}", role or "{role}").replace("{company}", args.company)
    closing = cl_base.get("closing", "").replace("{role}", role or "{role}").replace("{company}", args.company)

    body = match["body"].replace("{opening}", opening).replace("{closing}", closing)
    body = body.replace("{role}", role or "{role}").replace("{company}", args.company)

    if args.llm and jd_text:
        print("Rewriting cover letter with LLM...")
        rewritten = llm_rewrite_cover_letter(body, jd_text)
        if rewritten != body:
            print("Cover letter rewritten")
        body = rewritten

    header = f"To the Hiring Team at {args.company},\n\n"
    footer = f"\n\nBest regards,\n{base['identity']['name']}"
    full = header + body + footer

    if args.output:
        with open(args.output, "w") as f:
            f.write(full)
        print(f"Cover letter written to {args.output}")
    else:
        print("\n" + "=" * 50)
        print(f"COVER LETTER — {args.company}")
        print("=" * 50)
        print(full)


def main():
    load_dotenv(override=True)
    parser = argparse.ArgumentParser(description="Resume composition engine")
    subparsers = parser.add_subparsers()

    build_parser = subparsers.add_parser("build", help="Build a job-specific resume variant")
    build_parser.add_argument("--jd", help="Path to job description text file")
    build_parser.add_argument("--tags", default="", help="Comma-separated tags to filter by")
    build_parser.add_argument("--template", default="classic", help="Template name")
    build_parser.add_argument("--company", required=True, help="Company name")
    build_parser.add_argument("--role", help="Role title (extracted from JD first line if omitted with --llm)")
    build_parser.add_argument("--llm", action="store_true", help="Use LLM for JD analysis")
    build_parser.add_argument("--all-formats", action="store_true", help="Generate HTML, Markdown, and PNG in addition to PDF")
    build_parser.set_defaults(func=cmd_build)

    tags_parser = subparsers.add_parser("tags", help="List all available tags in base")
    tags_parser.set_defaults(func=cmd_tags)

    log_parser = subparsers.add_parser("log", help="Show application history")
    log_parser.set_defaults(func=cmd_log)

    cl_parser = subparsers.add_parser("cover-letter", help="Generate a cover letter from base.yaml template")
    cl_parser.add_argument("--company", required=True, help="Target company name")
    cl_parser.add_argument("--role", help="Role title (extracted from JD first line if omitted with --llm)")
    cl_parser.add_argument("--jd", help="Path to job description text file")
    cl_parser.add_argument("--tags", default="", help="Comma-separated tags to select cover letter template")
    cl_parser.add_argument("--llm", action="store_true", help="Use LLM to rewrite cover letter body")
    cl_parser.add_argument("--output", help="Output file path (default: stdout)")
    cl_parser.set_defaults(func=cmd_cover_letter)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
