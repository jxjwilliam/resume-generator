# DOCX Output for Resume Build

**Date**: 2026-06-12
**Status**: Draft

## Goal

Add `.docx` (Microsoft Word) output to `resume.py build`, producing a polished, recruiter-friendly Word document alongside the existing PDF output. The docx must be immediately submittable (no post-editing required) and render correctly in Microsoft Word and Google Docs.

## Background

- `resume.py build` currently produces PDF via rendercv (and optionally HTML/Markdown/PNG)
- A `--cover-letter` flag was recently added to also generate a cover letter `.txt`
- The docx feature follows the same CLI-flag pattern

## Approach

Use `python-docx` to build the document programmatically from the already-written variant YAML. No template files needed — the code creates every element (headings, paragraphs, bullets, styling) directly.

**Rejected alternatives**:
- **docxtpl** — template-based, but per-job content variation (bullet count, optional sections) makes templates fragile
- **pandoc HTML→docx** — inconsistent spacing, no font control, extra system dependency

## CLI

```bash
python resume.py build --company "X" --role "Y" --tags backend,python --docx
```

New flag: `--docx` (store_true, default false)

## Output

- File: `output/{slug}/resume.docx`
- Same directory as the PDF (`output/{slug}/William_Jiang_CV.pdf`)

## Document Layout

| Section | Element | Style |
|---|---|---|
| Name | Heading (centered) | 18pt, bold, centered |
| Contact line | Paragraph | email \| phone \| location, centered, 10pt |
| Headline | Paragraph | Italic, 10.5pt, centered |
| Summary | Paragraph | 10.5pt, spacing after |
| Experience section title | Heading | 12pt, bold, dark blue |
| Per-job: company | Paragraph | 10.5pt, bold |
| Per-job: position + dates | Paragraph | 10.5pt, italic for dates |
| Per-job: highlights | Bullet list | 10.5pt, hanging indent |
| Skills section title | Heading | 12pt, bold, dark blue |
| Per-category: label | Paragraph | 10.5pt, bold |
| Per-category: details | Paragraph | 10.5pt, inline |
| Projects section title | Heading | 12pt, bold, dark blue |
| Per-project: name | Paragraph | 10.5pt, bold |
| Per-project: highlights | Bullet list | 10.5pt |
| Education section title | Heading | 12pt, bold, dark blue |
| Per-ed: institution | Paragraph | 10.5pt, bold |

### Page Setup

- Paper size: US Letter
- Margins: 0.7in all sides
- Default font: Calibri (11pt for body, adjusted per element above)
- Section header color: rgb(0,79,144) — matches PDF theme

## Implementation

All changes in `resume.py`:

1. **New function**: `generate_docx(variant_path: str, slug: str) -> str`
   - Reads variant YAML
   - Builds Document with all sections
   - Saves to `output/{slug}/resume.docx`
   - Returns the output path

2. **Modify `cmd_build()`**: After `render_variant()`, if `--docx`, call `generate_docx()`

3. **Parser**: Add `--docx` flag to the `build` subparser

### WebUI

- **`models.py`**: Add `docx: bool = False` to `ResumeRunRequest`
- **`main.py`**: Pass `--docx` in `_build_resume_cmd()` when `args.docx` is true
- **`ResumePage.tsx`**: Add "Docx" checkbox in the checkbox row (next to "Cover letter")

### Dependencies

Add to `requirements.txt`:
```
python-docx>=1.1
```

## Verification

- Run `python resume.py build --company Test --role Engineer --tags backend --docx`
- `output/test-engineer-202606/resume.docx` exists
- Open in Word / Google Docs — all sections present, fonts correct
- No regressions: `--docx` flag omitted → existing PDF-only behavior unchanged
