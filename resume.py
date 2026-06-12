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

def load_base(yaml_file: str = BASE_FILE):
    with open(yaml_file) as f:
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


def _font_for_locale(locale: str) -> str:
    """Map a locale to a rendercv font family."""
    return {
        "en": "Source Sans 3",
        "zh-CN": "Noto Sans SC",
    }.get(locale, "Source Sans 3")

def build_variant(base, tags, template, company, role, jd_text=None,
                  headline_override=None, summary_override=None, locale="en"):
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
                "font_family": _font_for_locale(locale),
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


def generate_docx(variant_path: str, slug: str) -> str | None:
    """Generate a .docx file from a variant YAML. Returns output path or None on error."""
    try:
        from docx import Document
        from docx.shared import Pt, Inches, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError:
        print("python-docx not installed. Run: pip install python-docx", file=sys.stderr)
        return None

    with open(variant_path) as f:
        variant = yaml.safe_load(f)

    cv = variant.get("cv", {})
    design = variant.get("design", {})
    doc = Document()

    # Page setup
    section = doc.sections[0]
    page = design.get("page", {})
    margin_str = page.get("left_margin", "0.7in")
    if margin_str.endswith("in"):
        val = float(margin_str.replace("in", ""))
        for attr in ["top_margin", "bottom_margin", "left_margin", "right_margin"]:
            setattr(section, attr, Inches(val))

    theme_color = RGBColor(0, 0x4F, 0x90)

    def _heading(text):
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(12)
        run.font.color.rgb = theme_color
        run.font.name = "Calibri"
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        return p

    def _font(run, name="Calibri", size=Pt(10.5)):
        run.font.name = name
        run.font.size = size

    # Name
    name = cv.get("name", "")
    if name:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(name)
        run.bold = True
        run.font.size = Pt(18)
        run.font.name = "Calibri"
        p.paragraph_format.space_after = Pt(2)

    # Contact line
    parts = [cv.get("email", ""), cv.get("phone", ""), cv.get("location", "")]
    contact = "  |  ".join(p for p in parts if p)
    if contact:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(contact)
        _font(run, size=Pt(10))
        p.paragraph_format.space_after = Pt(2)

    # Headline
    headline = cv.get("headline", "")
    if headline:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(headline)
        run.italic = True
        _font(run, size=Pt(10.5))
        p.paragraph_format.space_after = Pt(6)

    sections_data = cv.get("sections", {})

    # Summary
    summary_list = sections_data.get("Summary", [])
    if summary_list:
        _heading("Summary")
        for text in summary_list:
            p = doc.add_paragraph(text)
            _font(p.runs[0] if p.runs else p.add_run(), size=Pt(10.5))
            p.paragraph_format.space_after = Pt(4)

    # Experience
    exp = sections_data.get("experience", [])
    if exp:
        _heading("Experience")
        for job in exp:
            p = doc.add_paragraph()
            run = p.add_run(job.get("company", ""))
            run.bold = True
            _font(run)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.space_before = Pt(6)

            pos = job.get("position", "")
            dates = job.get("start_date", "")
            if job.get("end_date"):
                dates += f" -- {job['end_date']}"
            if pos or dates:
                p = doc.add_paragraph()
                if pos:
                    run = p.add_run(pos)
                    _font(run)
                    run.font.size = Pt(10)
                if dates:
                    run = p.add_run(f"  ({dates})")
                    run.italic = True
                    _font(run, size=Pt(10))
                p.paragraph_format.space_after = Pt(2)

            loc = job.get("location", "")
            if loc:
                p = doc.add_paragraph()
                run = p.add_run(loc)
                _font(run, size=Pt(10))
                p.paragraph_format.space_after = Pt(2)

            for hl in job.get("highlights", []):
                p = doc.add_paragraph(hl, style="List Bullet")
                for run in p.runs:
                    _font(run, size=Pt(10.5))

    # Skills
    skills = sections_data.get("skills", [])
    if skills:
        _heading("Skills")
        for sg in skills:
            label = sg.get("label", "")
            details = sg.get("details", "")
            if label or details:
                p = doc.add_paragraph()
                if label:
                    run = p.add_run(f"{label}: ")
                    run.bold = True
                    _font(run)
                if details:
                    run = p.add_run(details)
                    _font(run)
                p.paragraph_format.space_after = Pt(2)

    # Projects
    projects = sections_data.get("projects", [])
    if projects:
        _heading("Projects")
        for proj in projects:
            proj_name = proj.get("name", "")
            proj_summary = proj.get("summary", "")
            if proj_name:
                p = doc.add_paragraph()
                run = p.add_run(proj_name)
                run.bold = True
                _font(run)
                p.paragraph_format.space_after = Pt(0)
            if proj_summary:
                p = doc.add_paragraph(proj_summary)
                _font(p.runs[0] if p.runs else p.add_run(), size=Pt(10))
                p.paragraph_format.space_after = Pt(2)
            for hl in proj.get("highlights", []):
                p = doc.add_paragraph(hl, style="List Bullet")
                for run in p.runs:
                    _font(run, size=Pt(10.5))

    # Education
    edu = sections_data.get("education", [])
    if edu:
        _heading("Education")
        for e in edu:
            inst = e.get("institution", "")
            area = e.get("area", "")
            edate = e.get("date", "")
            if inst:
                p = doc.add_paragraph()
                run = p.add_run(inst)
                run.bold = True
                _font(run)
                p.paragraph_format.space_after = Pt(0)
            line = "  |  ".join(p for p in [area, edate] if p)
            if line:
                p = doc.add_paragraph(line)
                _font(p.runs[0] if p.runs else p.add_run(), size=Pt(10))
                p.paragraph_format.space_after = Pt(4)

    output_path = f"{OUTPUT_DIR}/{slug}/resume.docx"
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    print(f"DOCX written: {output_path}")
    return output_path


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
    base = load_base(getattr(args, "yaml", BASE_FILE))

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
    print(f"Locale: {args.locale}")

    variant = build_variant(base, tags, args.template, args.company, role, jd_text,
                            headline_override=headline_override,
                            summary_override=summary_override,
                            locale=args.locale)
    variant_path = write_variant(variant, slug)
    print(f"Variant written: {variant_path}")

    print("Rendering PDF...")
    success = render_variant(variant_path, slug, all_formats=args.all_formats)
    if success:
        print(f"Output: {OUTPUT_DIR}/{slug}/")

    log_application(slug, args.company, role, tags, args.template, args.jd)
    print(f"Logged to {LOG_FILE}")

    # ── Cover letter (optional) ─────────────────────────────────
    if getattr(args, "cover_letter", False):
        print("Generating cover letter...")
        cl_tags = tags or ""
        _generate_cover_letter(base, args.company, role, jd_text, cl_tags, slug,
                                yaml_file=getattr(args, "yaml", BASE_FILE))

    # ── DOCX (optional) ─────────────────────────────────────────
    if getattr(args, "docx", False):
        print("Generating DOCX...")
        generate_docx(variant_path, slug)

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


def _generate_cover_letter(base: dict, company: str, role: str | None,
                           jd_text: str | None, tags: str, slug: str, yaml_file: str = BASE_FILE):
    """Generate a cover letter .txt file in the output directory."""
    from argparse import Namespace
    cl_args = Namespace(
        yaml=yaml_file,
        company=company,
        role=role or "",
        jd=jd_text,
        tags=tags,
        llm=bool(jd_text),
        output=f"{OUTPUT_DIR}/{slug}/cover-letter-{company.lower().replace(' ','-')}.txt",
    )
    try:
        cmd_cover_letter(cl_args)
    except SystemExit:
        pass  # cmd_cover_letter calls exit(1) on error — swallow for batch mode


def cmd_cover_letter(args):
    base = load_base(args.yaml)

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
    build_parser.add_argument("--yaml", default="base.yaml", help="YAML source file (default: base.yaml)")
    build_parser.add_argument("--jd", help="Path to job description text file")
    build_parser.add_argument("--tags", default="", help="Comma-separated tags to filter by")
    build_parser.add_argument("--template", default="classic", help="Template name")
    build_parser.add_argument("--company", required=True, help="Company name")
    build_parser.add_argument("--role", help="Role title (extracted from JD first line if omitted with --llm)")
    build_parser.add_argument("--locale", default="en", choices=["en", "zh-CN"],
                              help="Resume language (en or zh-CN)")
    build_parser.add_argument("--llm", action="store_true", help="Use LLM for JD analysis")
    build_parser.add_argument("--all-formats", action="store_true", help="Generate HTML, Markdown, and PNG in addition to PDF")
    build_parser.add_argument("--cover-letter", action="store_true", help="Also generate a cover letter .txt file")
    build_parser.add_argument("--docx", action="store_true", help="Also generate a .docx Word document")
    build_parser.set_defaults(func=cmd_build)

    tags_parser = subparsers.add_parser("tags", help="List all available tags in base")
    tags_parser.set_defaults(func=cmd_tags)

    log_parser = subparsers.add_parser("log", help="Show application history")
    log_parser.set_defaults(func=cmd_log)

    cl_parser = subparsers.add_parser("cover-letter", help="Generate a cover letter from base.yaml template")
    cl_parser.add_argument("--yaml", default="base.yaml", help="YAML source file (default: base.yaml)")
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
