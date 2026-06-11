# Reactive Resume (rxresu.me) Auto-Fill Integration Guide

> **Goal:** Parse `base.yaml` → transform to rxresume JSON schema → POST via API → auto-populated resume with suitable template.

---

## Architecture Overview

```
base.yaml → transform.py → rxresume_schema.json → POST /api/openapi/resumes
                ↑
         DeepSeek LLM (optional: enhance summaries, select bullets by tag)
```

**Two approaches, in order of reliability:**

1. **Direct API** — parse `base.yaml` → map to rxresume JSON schema → `POST /api/openapi/resumes` (deterministic, no LLM needed)
2. **MCP server** — use rxresume's MCP endpoint with your LLM to patch resumes via natural language (more flexible, slightly less precise)

---

## Step 1 — Understand the rxresume Schema

The schema is publicly available:

```bash
curl https://rxresu.me/schema.json | jq . > rxresume_schema.json
```

It covers all sections: `basics`, `summary`, `experience`, `education`, `projects`, `skills`, and `metadata` (template, layout, typography, colors).

---

## Step 2 — Get Your API Key

1. Sign in at [https://rxresu.me](https://rxresu.me)
2. Go to **Settings → API Keys**
3. Click **Create a new API key**, copy and store it securely (shown only once)
4. Authenticate all requests with header: `x-api-key: YOUR_API_KEY`

API base: `https://rxresu.me/api/openapi`

---

## Step 3 — The Transformer Script

`transform.py` — maps `base.yaml` → rxresume API payload

```python
#!/usr/bin/env python3
"""
base.yaml → Reactive Resume API payload
Usage: python transform.py [--tags fullstack,ai] [--template elegant]
"""
import yaml
import json
import argparse
import httpx
from typing import Optional

API_BASE = "https://rxresu.me/api/openapi"
API_KEY  = "YOUR_RXRESUME_API_KEY"  # or load from env: os.environ["RXRESUME_API_KEY"]

# ── helpers ───────────────────────────────────────────────────────────────────

def iso_to_display(date_str: Optional[str]) -> Optional[str]:
    """'2021-03' → '2021-03-01' (rxresume expects ISO 8601)"""
    if not date_str:
        return None
    parts = date_str.split("-")
    return f"{parts[0]}-{parts[1]}-01" if len(parts) == 2 else date_str

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

def make_id(prefix: str, idx: int) -> str:
    return f"{prefix}-{idx:03d}"

# ── section builders ──────────────────────────────────────────────────────────

def build_basics(identity: dict) -> dict:
    urls = {u["label"].lower(): u["url"] for u in identity.get("urls", [])}
    return {
        "name": identity["name"],
        "email": identity["email"],
        "phone": identity["phone"],
        "location": identity["location"],
        "url": {"href": urls.get("github", ""), "label": "GitHub"},
        "customFields": [
            {
                "id": "cf-linkedin",
                "icon": "linkedin",
                "name": "LinkedIn",
                "value": urls.get("linkedin", "")
            }
        ],
        "picture": {
            "url": "",
            "size": 64,
            "aspectRatio": 1,
            "borderRadius": 0,
            "effects": {"hidden": False, "border": False, "grayscale": False}
        }
    }

def build_summary(data: dict, target_tags: set = None) -> dict:
    cls = data.get("cover_letters", [])
    body = ""
    if target_tags and target_tags.intersection({"ai", "fullstack"}):
        match = next((c for c in cls if c["id"] == "ai-fullstack-focused"), None)
    elif target_tags and target_tags.intersection({"backend", "api"}):
        match = next((c for c in cls if c["id"] == "backend-focused"), None)
    else:
        match = next((c for c in cls if c["id"] == "leadership-focused"), None)
    if match:
        body = match["body"].replace("{opening}", "").replace("{closing}", "").strip()
    return {"content": body, "visible": True}

def build_experience(exp_list: list, required_tags: set = None) -> list:
    active = filter_active(exp_list, required_tags)
    items = []
    for idx, job in enumerate(active):
        bullets = [
            b["text"] for b in job.get("bullets", [])
            if b.get("status") != "deprecated"
            and (not required_tags or required_tags.intersection(set(b.get("tags", []))))
        ]
        items.append({
            "id": make_id("exp", idx),
            "visible": True,
            "company": job["company"],
            "position": job["title"],
            "location": job["location"],
            "date": f"{iso_to_display(job['start'])} – {iso_to_display(job.get('end')) or 'Present'}",
            "summary": "<ul>" + "".join(f"<li>{b}</li>" for b in bullets) + "</ul>",
            "url": {"href": "", "label": ""}
        })
    return items

def build_education(edu_list: list) -> list:
    return [
        {
            "id": make_id("edu", idx),
            "visible": True,
            "institution": e["institution"],
            "studyType": e["degree"],
            "area": "",
            "score": "",
            "date": e.get("graduation", ""),
            "summary": "",
            "url": {"href": "", "label": ""}
        }
        for idx, e in enumerate(filter_active(edu_list))
    ]

def build_skills(skills: dict) -> list:
    result = []
    idx = 0
    for category, items in skills.items():
        for skill in items:
            if skill.get("status") == "deprecated":
                continue
            result.append({
                "id": make_id("skill", idx),
                "visible": True,
                "name": skill["name"],
                "description": skill.get("level", ""),
                "level": {"expert": 5, "advanced": 4, "intermediate": 3}.get(
                    skill.get("level", ""), 3
                ),
                "keywords": skill.get("tags", [])
            })
            idx += 1
    return result

def build_projects(projects: list, required_tags: set = None) -> list:
    active = filter_active(projects, required_tags)
    return [
        {
            "id": make_id("proj", idx),
            "visible": True,
            "name": p["name"],
            "description": p["description"],
            "date": "",
            "summary": "<ul>" + "".join(
                f"<li>{b['text']}</li>"
                for b in p.get("bullets", [])
                if b.get("status") != "deprecated"
            ) + "</ul>",
            "url": {"href": p.get("url", ""), "label": ""},
            "keywords": p.get("tags", [])
        }
        for idx, p in enumerate(active)
    ]

# ── full payload ──────────────────────────────────────────────────────────────

def build_payload(data: dict, target_tags: set = None, template: str = "elegant") -> dict:
    identity = data["identity"]
    return {
        "title": f"William Jiang — {template.title()} Resume",
        "slug": f"william-jiang-{template}",
        "template": template,
        "basics": build_basics(identity),
        "sections": {
            "summary": {
                "id": "summary", "name": "Summary", "type": "basic", "visible": True,
                **build_summary(data, target_tags)
            },
            "experience": {
                "id": "experience", "name": "Experience", "type": "work", "visible": True,
                "items": build_experience(data["experience"], target_tags)
            },
            "education": {
                "id": "education", "name": "Education", "type": "edu", "visible": True,
                "items": build_education(data["education"])
            },
            "skills": {
                "id": "skills", "name": "Skills", "type": "skills", "visible": True,
                "items": build_skills(data["skills"])
            },
            "projects": {
                "id": "projects", "name": "Projects", "type": "proj", "visible": True,
                "items": build_projects(data["projects"], target_tags)
            },
        },
        "metadata": {
            "template": template,
            "layout": [
                [["summary", "experience", "education"]],  # left column
                [["skills", "projects"]]                   # right column
            ],
            "css": {"value": "", "visible": False},
            "page": {
                "margin": 18,
                "format": "Letter",
                "options": {"breakLine": True, "pageNumbers": True}
            },
            "theme": {
                "background": "#ffffff",
                "text": "#000000",
                "primary": "#2563eb"
            },
            "typography": {
                "font": {
                    "family": "IBM Plex Serif",
                    "subset": "latin",
                    "variants": ["regular", "600"],
                    "size": 14
                },
                "lineHeight": 1.5,
                "hideIcons": False,
                "underlineLinks": True
            }
        }
    }

# ── API calls ─────────────────────────────────────────────────────────────────

def create_resume(payload: dict) -> dict:
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    r = httpx.post(f"{API_BASE}/resumes", headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

def patch_resume(resume_id: str, payload: dict) -> dict:
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--yaml",      default="base.yaml")
    parser.add_argument("--tags",      default="fullstack,ai,react,node,python",
                        help="comma-separated tag filter")
    parser.add_argument("--template",  default="elegant",
                        help="rxresume template name")
    parser.add_argument("--dry-run",   action="store_true",
                        help="print JSON payload, don't POST")
    parser.add_argument("--resume-id", help="PATCH existing resume instead of creating")
    args = parser.parse_args()

    with open(args.yaml) as f:
        data = yaml.safe_load(f)

    required_tags = set(args.tags.split(",")) if args.tags else None
    payload = build_payload(data, required_tags, args.template)

    if args.dry_run:
        print(json.dumps(payload, indent=2))
    elif args.resume_id:
        result = patch_resume(args.resume_id, payload)
        print(f"✅ Patched: {result.get('id')} → https://rxresu.me/dashboard/resumes")
    else:
        result = create_resume(payload)
        print(f"✅ Created: {result.get('id')} → https://rxresu.me/dashboard/resumes")
```

---

## Step 4 — Optional LLM Enhancement (DeepSeek)

`llm_enhance.py` — uses DeepSeek (OpenAI-compatible) to improve summaries and select bullets:

```python
# llm_enhance.py
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_DEEPSEEK_KEY",
    base_url="https://api.deepseek.com"  # or your local endpoint
)

def enhance_summary(raw_bullets: list[str], target_role: str) -> str:
    prompt = f"""
You are a senior technical resume writer.
Given these bullet points from a Full-Stack/AI engineer's career, write a 3-sentence professional
summary targeting a {target_role} role. Be specific, quantified where possible.
Return plain text, no markdown.

Bullets:
{chr(10).join(f'- {b}' for b in raw_bullets[:10])}
"""
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )
    return resp.choices[0].message.content.strip()


def select_bullets(bullets: list[dict], target_role: str, max_bullets: int = 4) -> list[str]:
    """LLM picks the most relevant bullets for a given role."""
    import json
    numbered = "\n".join(f"{i}. {b['text']}" for i, b in enumerate(bullets))
    prompt = f"""
Select the {max_bullets} most relevant bullet points for a '{target_role}' role.
Return ONLY a JSON array of indices (0-based). Example: [0, 2, 5, 7]

Bullets:
{numbered}
"""
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=50
    )
    indices = json.loads(resp.choices[0].message.content.strip())
    return [bullets[i]["text"] for i in indices if i < len(bullets)]
```

Integrate into `build_summary()` and `build_experience()` by passing a `--llm` flag and calling these functions before building the payload.

---

## Step 5 — Template Selection Guide

rxresume offers 12 templates. Best fits for William's profile:

| Template   | Best For                         | Recommended Use Case         |
|------------|----------------------------------|------------------------------|
| `elegant`  | Senior / leadership, clean 2-col | ✅ Default                   |
| `bronzor`  | Tech / engineering, minimal      | ✅ AI / backend roles         |
| `leafish`  | Modern with color accents        | Product / startup roles      |
| `kakuna`   | Compact, high density            | Fitting more content on page |
| `onyx`     | Dark, bold, modern               | Creative / startup roles     |

> **⚠️ API limitation:** The rxresume open API currently forces `template: "onyx"` regardless of the value sent in POST or PATCH. All other metadata fields (layout, colors, typography, page format) apply correctly.  
> **Workaround:** Set the desired template in the rxresume dashboard UI after the PATCH fills your data — the visual editor respects template changes even if the API doesn't.

---

## Step 6 — Usage

```bash
# Install dependencies
pip install pyyaml httpx openai

# Dry run — inspect JSON Patch operations before sending
python transform.py --tags fullstack,ai,react --dry-run

# Create new resume (AI/fullstack variant)
python transform.py --tags fullstack,ai,react,node

# Create backend/DevOps variant
python transform.py --tags backend,python,node,api,devops

# Create leadership/architecture variant
python transform.py --tags leadership,architecture,fullstack

# Patch existing resume (get ID from rxresume dashboard URL)
python transform.py --tags fullstack,ai --resume-id <RESUME_ID>

# List existing resumes
python -c "
import httpx, json
r = httpx.get('https://rxresu.me/api/openapi/resumes', headers={'x-api-key': 'YOUR_API_KEY'})
print(json.dumps(r.json(), indent=2))
"
```

---

## Step 7 — Optional MCP Integration

rxresume exposes an MCP endpoint at `https://rxresu.me/mcp`, supporting both OAuth2 and API key auth.
This lets you patch resumes from Claude Desktop, Cursor, or any MCP client using natural language.

**Claude Desktop config** (`~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "rxresume": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://rxresu.me/mcp"],
      "env": {
        "MCP_HEADERS": "{\"x-api-key\": \"YOUR_API_KEY\"}"
      }
    }
  }
}
```

Once connected, you can say things like:
- *"Update my resume's summary to focus on AI and RAG pipelines"*
- *"Add the AutoBidder project to my resume"*
- *"Change the template to bronzor"*

---

## Recommended Workflow

```
1. Edit base.yaml           (single source of truth)
          ↓
2. python transform.py --dry-run    (inspect JSON)
          ↓
3. Fix any mapping issues
          ↓
4. python transform.py --tags <role-specific-tags>   (POST to rxresume)
          ↓
5. Open rxresu.me dashboard → tweak visually if needed
          ↓
6. Export PDF / share link
```

---

## Summary Table

| Step | What                        | Tool / File           |
|------|-----------------------------|-----------------------|
| 1    | Parse `base.yaml`           | `pyyaml`              |
| 2    | Map to rxresume schema      | `transform.py`        |
| 3    | POST / PATCH via REST       | `httpx` → `/api/openapi/resumes` |
| 4    | Enhance summaries           | DeepSeek via `openai` SDK |
| 5    | Template selection          | `--template` CLI arg  |
| 6    | Natural language patching   | MCP endpoint          |

> **Key lever:** The `--tags` filter drives role-targeted variants from a single `base.yaml`.  
> Always `--dry-run` first, inspect the JSON, then POST.
