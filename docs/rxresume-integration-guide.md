# Reactive Resume (rxresu.me) Integration Guide

> **Goal:** Sync `base.yaml` → [Reactive Resume](https://rxresu.me) via JSON Patch API for visual editing, PDF export, and shareable links.

---

## Architecture

```
base.yaml → transform.py → JSON Patch ops → PATCH /api/openapi/resumes/{id}
                ↑
         .env (RXRESU_API_KEY)
         optional: DeepSeek LLM (--llm)
```

This is a **second rendering path** alongside `resume.py` → rendercv. Both read the same `base.yaml`; choose based on output needs:

| Path | Tool | Best for |
|---|---|---|
| **ATS PDF** | `resume.py build` → rendercv | Job applications, ATS-friendly PDF/HTML |
| **Visual resume** | `transform.py` → rxresu.me | Designer templates, live editing, share links |

---

## Prerequisites

```bash
pip install -r requirements.txt
```

Required packages: `pyyaml`, `httpx`, `Pillow`, `python-dotenv`.

### API key

1. Sign in at [https://rxresu.me](https://rxresu.me)
2. Go to **Settings → API Keys** → **Create a new API key**
3. Add to `.env`:

```env
RXRESU_API_KEY=your_key_here
```

API base: `https://rxresu.me/api/openapi`  
Auth header: `x-api-key: YOUR_KEY`

Schema reference: `curl https://rxresu.me/schema.json`

---

## Quick start

```bash
# Preview JSON Patch operations (no API call)
python transform.py --dry-run

# Patch an existing resume (ID from dashboard URL)
python transform.py --resume-id <RESUME_ID> --all-skills

# Create a new resume (POST blank shell, then PATCH content)
python transform.py --tags fullstack,ai,react,node,python
```

After sync, open the builder URL printed by the script, pick a template in the UI if needed, and export PDF.

---

## What `transform.py` does

The script maps `base.yaml` to Reactive Resume's data model and sends **RFC 6902 JSON Patch** operations (`replace` on paths like `/basics`, `/sections/experience/items`, `/metadata`).

### Content mapping

| `base.yaml` | RxResume field | Notes |
|---|---|---|
| `identity.name`, `email`, `phone`, `location` | `basics` | |
| `identity.headline` | `basics.headline` | LinkedIn-style title |
| `identity.urls` | `basics.website`, `customFields` | GitHub + LinkedIn |
| `identity.photo` | `picture.url` | Resized JPEG embedded as data URL |
| `summary` | `summary.content` | Resume summary (not cover letter) |
| `experience[]` | `sections.experience.items` | Newest-first, tag-filtered bullets |
| `education[]` | `sections.education.items` | Full date ranges when `start` + `graduation` set |
| `skills` (grouped) | `sections.skills.items` | One row per category, tech as keyword tags |
| `projects[]` | `sections.projects.items` | Tag-filtered |
| `cover_letters[]` | — | Only used with `--use-cover-letter` |

### Layout defaults

Single-column, compact order:

```
Summary → Skills → Experience → Projects → Education
```

- **Profiles section hidden** — GitHub/LinkedIn already appear in the header.
- **Skills grouped** — 4 category rows with keyword tags instead of 36 individual rated rows.
- **Proficiency dots hidden** in grouped mode.
- **Experience reverse-chronological** — Best IT first, not WebMD.

### Tag filtering

When `--tags` is set:

1. A job is included if **any bullet tag** matches, **or** if **job-level tags** match (fallback includes all active bullets for that job).
2. Bullets are ranked by tag overlap + `relevance` (`high` > `medium` > `low`).
3. Capped at `--max-bullets` per job (default: 4).
4. Skills respect tags unless `--all-skills` is passed.

---

## CLI reference

```bash
python transform.py [options]
```

| Flag | Default | Description |
|---|---|---|
| `--yaml` | `base.yaml` | Source file |
| `--tags` | `fullstack,ai,react,node,python` | Comma-separated tag filter |
| `--template` | `kakuna` | RxResume template name |
| `--resume-id` | — | PATCH existing resume instead of creating new |
| `--dry-run` | — | Print JSON Patch ops, don't call API |
| `--skills-mode` | `grouped` | `grouped` (category rows) or `flat` (one row per skill) |
| `--all-skills` | — | Include all active skills, ignore tag filter for skills |
| `--show-skill-levels` | — | Show dot ratings (flat mode only) |
| `--max-bullets` | `4` | Max bullets per job (`0` = unlimited) |
| `--no-projects` | — | Hide projects section (shorter resume) |
| `--use-cover-letter` | — | Use cover letter template for summary instead of `summary` field |
| `--photo` | auto | Profile photo path |
| `--no-photo` | — | Skip headshot |
| `--llm` | — | Use DeepSeek to enhance summary (requires `DEEPSEEK_API_KEY`) |
| `--role` | — | Target role description (used with `--llm`) |

### Common recipes

```bash
# Full skills, compact bullets — good default sync
python transform.py --resume-id <ID> --all-skills --max-bullets 3

# Backend/DevOps variant
python transform.py --tags backend,python,node,api,devops --resume-id <ID>

# Shorter 1–2 page resume
python transform.py --resume-id <ID> --all-skills --max-bullets 3 --no-projects

# AI/fullstack with cover-letter tone in summary
python transform.py --tags fullstack,ai,react --use-cover-letter --resume-id <ID>
```

---

## Profile photo

RxResume has no public file-upload API. `transform.py` handles photos by:

1. Reading `identity.photo` from `base.yaml` (default: `assets/william-jiang.jpg`)
2. Resizing with Pillow (max 400px, JPEG quality 85)
3. Embedding as a `data:image/jpeg;base64,...` URL in the `/picture` patch

**Preferred file:** `assets/william-jiang.jpg` (~859×922, ~1 MB source → ~30 KB embedded).  
**Fallback:** `assets/William-Jiang-1.png` (higher resolution but ~5 MB — only used if JPG missing).

Override with `--photo path/to/image.jpg` or disable with `--no-photo`.

---

## Template selection

| Template | Best for |
|---|---|
| `kakuna` | Compact, high density — **CLI default** |
| `bronzor` | Tech / engineering, minimal |
| `elegant` | Senior / leadership, clean layout |
| `leafish` | Modern with color accents |
| `onyx` | Dark, bold (may be forced on create via API) |

> **API note:** Creating a new resume via POST may force template `onyx`. Metadata (layout, typography, colors) still applies. Switch template in the [rxresu.me builder](https://rxresu.me/dashboard) after sync — the UI respects template changes.

---

## Optional LLM enhancement

With `--llm`, DeepSeek can rewrite the summary from your experience bullets. Configure in `.env`:

```env
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-pro
```

The system works without LLM — `--llm` is additive.

---

## Optional MCP integration

RxResume exposes an MCP endpoint at `https://rxresu.me/mcp` for natural-language edits from Cursor or Claude Desktop.

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

Use MCP for ad-hoc tweaks; use `transform.py` for full rebuilds from `base.yaml`.

---

## Recommended workflow

```
1. Edit base.yaml              (single source of truth)
         ↓
2. python transform.py --dry-run --all-skills
         ↓
3. Review job order, bullet counts, skills groups in output
         ↓
4. python transform.py --resume-id <ID> --all-skills
         ↓
5. Open rxresu.me builder → pick template → export PDF
```

For job applications that need ATS PDFs, also run:

```bash
python resume.py build --company "Acme" --role "Senior SWE" --tags fullstack,ai,python
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| 5-page resume, skills dominate | Old flat skills mode | Re-sync with current `transform.py` (`--skills-mode grouped`) |
| Experience starts with oldest job | Missing reverse sort | Re-sync — jobs are now newest-first |
| Best Buy / job missing | Tag filter too strict | Add tags to job/bullets in `base.yaml`, or widen `--tags` |
| Summary reads like cover letter | Wrong source | Remove `--use-cover-letter`; use `summary` field in `base.yaml` |
| Duplicate Profiles section | Old transform version | Re-sync — profiles section is now hidden |
| Photo missing | File not found | Set `identity.photo` or pass `--photo` |
| Template looks wrong | API forces onyx on create | Change template in dashboard UI after PATCH |

---

## Summary

| Step | What | Tool |
|---|---|---|
| 1 | Edit resume data | `base.yaml` |
| 2 | Map to RxResume schema | `transform.py` |
| 3 | Sync via JSON Patch | `PATCH /api/openapi/resumes/{id}` |
| 4 | Visual polish + PDF | rxresu.me dashboard |
| 5 | ATS PDF (parallel path) | `resume.py build` → rendercv |

> **Key lever:** `--tags` drives role-targeted variants; `--all-skills` keeps the full skill inventory; `--max-bullets` controls page length. Always `--dry-run` first.
