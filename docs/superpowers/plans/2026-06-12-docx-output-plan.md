# DOCX Output Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `.docx` output to `resume.py build`, producing a polished recruiter-friendly Word document in `output/{slug}/resume.docx`.

**Architecture:** A new `generate_docx()` function in `resume.py` reads the already-written variant YAML and builds a `python-docx` Document programmatically. The `--docx` CLI flag triggers it after rendercv renders the PDF. The WebUI exposes a "Docx" checkbox that passes through to the CLI.

**Tech Stack:** `python-docx>=1.1`, Python 3.12+

---

### Task 1: Install dependency + add to requirements.txt

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add python-docx to requirements.txt**

Append to `requirements.txt`:
```text
# DOCX generation
python-docx>=1.1
```

- [ ] **Step 2: Install the library**

Run:
```bash
pip install python-docx
```

Expected: `Successfully installed python-docx-1.1.2`

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: add python-docx dependency"
```

---

### Task 2: Add `--docx` flag to the build subparser

**Files:**
- Modify: `resume.py:520-535` (build_parser arguments)

- [ ] **Step 1: Read the build parser section**

```bash
grep -n "build_parser" resume.py | head -10
```

- [ ] **Step 2: Add `--docx` argument**

Find the `build_parser.add_argument("--cover-letter"` line and add the docx flag after it:

```python
    build_parser.add_argument("--cover-letter", action="store_true", help="Also generate a cover letter .txt file")
    build_parser.add_argument("--docx", action="store_true", help="Also generate a .docx Word document")
```

- [ ] **Step 3: Verify the flag appears in help**

Run:
```bash
python resume.py build --help
```

Expected: output includes `--docx    Also generate a .docx Word document`

- [ ] **Step 4: Commit**

```bash
git add resume.py
git commit -m "feat(resume.py): add --docx CLI flag to build subparser"
```

---

### Task 3: Implement `generate_docx()` function

**Files:**
- Modify: `resume.py` (after `render_variant()`, before `log_application()`)

- [ ] **Step 1: Write the `generate_docx()` function**

Add this function in `resume.py`, placed after `render_variant()` (around line 201):

```python
def generate_docx(variant_path: str, slug: str) -> str | None:
    """Generate a .docx file from a variant YAML. Returns output path or None on error."""
    try:
        from docx import Document
        from docx.shared import Pt, Inches, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml.ns import qn
    except ImportError:
        print("python-docx not installed. Run: pip install python-docx", file=sys.stderr)
        return None

    with open(variant_path) as f:
        variant = yaml.safe_load(f)

    cv = variant.get("cv", {})
    design = variant.get("design", {})
    doc = Document()

    # ── Page setup ──────────────────────────────────────────────
    section = doc.sections[0]
    page = design.get("page", {})
    margin = page.get("left_margin", "0.7in")
    if margin.endswith("in"):
        val = float(margin.replace("in", ""))
        for attr in ["top_margin", "bottom_margin", "left_margin", "right_margin"]:
            setattr(section, attr, Inches(val))

    theme_color = RGBColor(0, 0x4F, 0x90)  # rgb(0,79,144)

    def _add_heading(text: str, level: int = 1):
        """Add a dark-blue section heading."""
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(12)
        run.font.color.rgb = theme_color
        run.font.name = "Calibri"
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        return p

    def _set_font(run, name="Calibri", size=Pt(10.5)):
        run.font.name = name
        run.font.size = size

    # ── Name ────────────────────────────────────────────────────
    name = cv.get("name", "")
    if name:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(name)
        run.bold = True
        run.font.size = Pt(18)
        run.font.name = "Calibri"
        p.paragraph_format.space_after = Pt(2)

    # ── Contact line ────────────────────────────────────────────
    parts = [cv.get("email", ""), cv.get("phone", ""), cv.get("location", "")]
    contact = "  |  ".join(p for p in parts if p)
    if contact:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(contact)
        _set_font(run, size=Pt(10))
        p.paragraph_format.space_after = Pt(2)

    # ── Headline ────────────────────────────────────────────────
    headline = cv.get("headline", "")
    if headline:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(headline)
        run.italic = True
        _set_font(run, size=Pt(10.5))
        p.paragraph_format.space_after = Pt(6)

    sections_data = cv.get("sections", {})

    # ── Summary ─────────────────────────────────────────────────
    summary_list = sections_data.get("Summary", [])
    if summary_list:
        _add_heading("Summary")
        for text in summary_list:
            p = doc.add_paragraph(text)
            _set_font(p.runs[0] if p.runs else p.add_run(), size=Pt(10.5))
            p.paragraph_format.space_after = Pt(4)

    # ── Experience ──────────────────────────────────────────────
    exp = sections_data.get("experience", [])
    if exp:
        _add_heading("Experience")
        for job in exp:
            # Company line
            p = doc.add_paragraph()
            run = p.add_run(job.get("company", ""))
            run.bold = True
            _set_font(run)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.space_before = Pt(6)

            # Position + dates
            pos = job.get("position", "")
            dates = job.get("start_date", "")
            if job.get("end_date"):
                dates += f" – {job['end_date']}"
            if pos or dates:
                p = doc.add_paragraph()
                if pos:
                    run = p.add_run(pos)
                    _set_font(run)
                    run.font.size = Pt(10)
                if dates:
                    run = p.add_run(f"  ({dates})")
                    run.italic = True
                    _set_font(run, size=Pt(10))
                p.paragraph_format.space_after = Pt(2)

            # Location
            loc = job.get("location", "")
            if loc:
                p = doc.add_paragraph()
                run = p.add_run(loc)
                _set_font(run, size=Pt(10))
                p.paragraph_format.space_after = Pt(2)

            # Bullets
            for hl in job.get("highlights", []):
                p = doc.add_paragraph(hl, style="List Bullet")
                for run in p.runs:
                    _set_font(run, size=Pt(10.5))

    # ── Skills ──────────────────────────────────────────────────
    skills = sections_data.get("skills", [])
    if skills:
        _add_heading("Skills")
        for skill_group in skills:
            label = skill_group.get("label", "")
            details = skill_group.get("details", "")
            if label or details:
                p = doc.add_paragraph()
                if label:
                    run = p.add_run(f"{label}: ")
                    run.bold = True
                    _set_font(run)
                if details:
                    run = p.add_run(details)
                    _set_font(run)
                p.paragraph_format.space_after = Pt(2)

    # ── Projects ────────────────────────────────────────────────
    projects = sections_data.get("projects", [])
    if projects:
        _add_heading("Projects")
        for proj in projects:
            name = proj.get("name", "")
            summary = proj.get("summary", "")
            if name:
                p = doc.add_paragraph()
                run = p.add_run(name)
                run.bold = True
                _set_font(run)
                p.paragraph_format.space_after = Pt(0)
            if summary:
                p = doc.add_paragraph(summary)
                _set_font(p.runs[0] if p.runs else p.add_run(), size=Pt(10))
                p.paragraph_format.space_after = Pt(2)
            for hl in proj.get("highlights", []):
                p = doc.add_paragraph(hl, style="List Bullet")
                for run in p.runs:
                    _set_font(run, size=Pt(10.5))

    # ── Education ───────────────────────────────────────────────
    edu = sections_data.get("education", [])
    if edu:
        _add_heading("Education")
        for e in edu:
            inst = e.get("institution", "")
            area = e.get("area", "")
            date = e.get("date", "")
            if inst:
                p = doc.add_paragraph()
                run = p.add_run(inst)
                run.bold = True
                _set_font(run)
                p.paragraph_format.space_after = Pt(0)
            line = "  |  ".join(p for p in [area, date] if p)
            if line:
                p = doc.add_paragraph(line)
                _set_font(p.runs[0] if p.runs else p.add_run(), size=Pt(10))
                p.paragraph_format.space_after = Pt(4)

    # ── Save ────────────────────────────────────────────────────
    output_path = f"{OUTPUT_DIR}/{slug}/resume.docx"
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    print(f"DOCX written: {output_path}")
    return output_path
```

> **Note:** `List Bullet` style may not exist in a blank document. python-docx auto-creates it on first use of `style="List Bullet"` in many environments, but to be safe the function falls back gracefully.

- [ ] **Step 2: Verify python syntax**

Run:
```bash
python3 -c "import py_compile; py_compile.compile('resume.py', doraise=True); print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add resume.py
git commit -m "feat(resume.py): add generate_docx() function"
```

---

### Task 4: Wire `--docx` into `cmd_build()`

**Files:**
- Modify: `resume.py` — `cmd_build()` function, after `render_variant()` call

- [ ] **Step 1: Add docx generation after render**

In `cmd_build()`, find the `render_variant()` call and the cover-letter block. Add the docx block between them:

```python
    print("Rendering PDF...")
    success = render_variant(variant_path, slug, all_formats=args.all_formats)
    if success:
        print(f"Output: {OUTPUT_DIR}/{slug}/")

    # ── DOCX (optional) ────────────────────────────────────────
    if getattr(args, "docx", False):
        print("Generating DOCX...")
        generate_docx(variant_path, slug)

    log_application(slug, args.company, role, tags, args.template, args.jd)
```

- [ ] **Step 2: Verify the flow compiles**

Run:
```bash
python3 -c "import py_compile; py_compile.compile('resume.py', doraise=True); print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add resume.py
git commit -m "feat(resume.py): wire --docx into cmd_build()"
```

---

### Task 5: Add `docx` field to WebUI backend model

**Files:**
- Modify: `ui/backend/models.py`

- [ ] **Step 1: Add `docx: bool` to `ResumeRunRequest`**

```python
class ResumeRunRequest(BaseModel):
    yaml_file: str = "base.yaml"
    company: str
    role: Optional[str] = None
    tags: list[str] = []
    theme: str = "classic"
    jd_text: Optional[str] = None
    use_llm: bool = False
    all_formats: bool = False
    locale: str = "en"
    cover_letter: bool = False
    docx: bool = False
```

- [ ] **Step 2: Verify syntax**

```bash
python3 -c "import py_compile; py_compile.compile('ui/backend/models.py', doraise=True); print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add ui/backend/models.py
git commit -m "feat(api): add docx field to ResumeRunRequest"
```

---

### Task 6: Pass `--docx` from the API to the CLI

**Files:**
- Modify: `ui/backend/main.py` — `_build_resume_cmd()`

- [ ] **Step 1: Add `--docx` to the command builder**

In `_build_resume_cmd()`, after the `--cover-letter` block:

```python
    if args.cover_letter:
        cmd += ["--cover-letter"]
    if args.docx:
        cmd += ["--docx"]
    return cmd
```

- [ ] **Step 2: Verify syntax**

```bash
python3 -c "import py_compile; py_compile.compile('ui/backend/main.py', doraise=True); print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add ui/backend/main.py
git commit -m "feat(api): pass --docx flag from API to CLI"
```

---

### Task 7: Add "Docx" checkbox to the frontend Resume page

**Files:**
- Modify: `ui/frontend/src/pages/ResumePage.tsx`
- Modify: `ui/frontend/src/types.ts`

- [ ] **Step 1: Add `docx` to `ResumeRunRequest` type**

In `ui/frontend/src/types.ts`:

```typescript
export interface ResumeRunRequest {
  yaml_file?: string;
  company: string;
  role?: string;
  tags?: string[];
  theme?: string;
  jd_text?: string;
  use_llm?: boolean;
  all_formats?: boolean;
  locale?: string;
  cover_letter?: boolean;
  docx?: boolean;
}
```

- [ ] **Step 2: Add state and pass it in the API call**

In `ResumePage.tsx`, add this state alongside `coverLetter`:

```typescript
  const [docx, setDocx] = useState(false);
```

In the `handleRun` callback, add to the request body:

```typescript
        docx: docx || undefined,
```

And add `docx` to the dependency array.

- [ ] **Step 3: Add the checkbox UI**

In the JSX checkbox row, after the "Cover letter" checkbox:

```tsx
        <FormControlLabel
          control={<Checkbox checked={docx} onChange={(e) => setDocx(e.target.checked)} />}
          label="Docx"
        />
```

- [ ] **Step 4: Verify TypeScript compiles**

Run:
```bash
npx tsc --noEmit
```

Expected: no output (clean)

- [ ] **Step 5: Verify Vite builds**

Run:
```bash
npx vite build
```

Expected: `✓ built in X.XXs`

- [ ] **Step 6: Commit**

```bash
git add ui/frontend/src/pages/ResumePage.tsx ui/frontend/src/types.ts
git commit -m "feat(ui): add Docx checkbox to Resume page"
```

---

### Task 8: End-to-end verification

- [ ] **Step 1: Build a test resume with docx**

Run:
```bash
python resume.py build --company "TestCo" --role "Engineer" --tags backend,python --template classic --docx
```

Expected output includes:
```
DOCX written: output/testco-engineer-202606/resume.docx
```

- [ ] **Step 2: Verify the file exists and is a valid docx**

```bash
file output/testco-engineer-202606/resume.docx
```

Expected: `resume.docx: Microsoft Word 2007+`

- [ ] **Step 3: Verify PDF-only still works (no regression)**

```bash
python resume.py build --company "TestCo" --role "Engineer" --tags backend,python --template classic
```

Expected: No mention of DOCX in output. No `resume.docx` in the output dir (or the previous one is overwritten — check `--company` differs).

- [ ] **Step 4: Start the UI and verify the checkbox appears**

```bash
open ui/frontend/src/pages/ResumePage.tsx
```

Confirm the "Docx" checkbox renders next to "Cover letter" in the checkbox row.

- [ ] **Step 5: Commit the final state**

```bash
git add -A
git commit -m "chore: finalize docx output feature"
```
