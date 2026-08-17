# Fonts for generated resumes

Every build produces a **PDF**, a **DOCX**, and a **cover letter**, and all
three use the same chosen font family. This doc explains the font options,
how they flow through the pipeline, and how to extend them.

## How it works

`src/fonts.py` is the single source of truth for font options. Each option
maps to two renderers:

```text
--font <key> ──┬──> rendercv/Typst (PDF)  → design.typography.font_family
               └──> python-docx (DOCX + cover letter) → run/paragraph font
```

- The CLI flag `--font <key>` (default `calibri`) resolves the option via
  `src.fonts.resolve_font()`.
- `build_variant()` writes the rendercv font into the variant YAML as
  `design.typography.font_family.{body,name,headline,connections,section_titles}`,
  which is the schema RenderCV expects for every theme.
- `generate_docx()` and the cover-letter builder apply the matching Word font.
- The WebUI gets the same list from `GET /api/fonts` and sends `--font` on
  every build.

## Available fonts

| Key | PDF (rendercv/Typst) | DOCX (Word) |
|---|---|---|
| `calibri` *(default)* | Source Sans 3 | Calibri |
| `source-sans` | Source Sans 3 | Calibri |
| `lato` | Lato | Calibri |
| `open-sans` | Open Sans | Arial |
| `roboto` | Roboto | Arial |
| `poppins` | Poppins | Aptos |
| `raleway` | Raleway | Aptos |
| `ubuntu` | Ubuntu | Arial |
| `mukta` | Mukta | Arial |
| `open-sauce-sans` | Open Sauce Sans | Calibri |
| `noto-sans` | Noto Sans (+ SC for CJK) | Arial |
| `charter` | XCharter | Georgia |
| `libertinus` | Libertinus Serif | Georgia |
| `garamond` | EB Garamond | Garamond |
| `gentium` | Gentium Book Plus | Book Antiqua |
| `fontin` | Fontin | Palatino Linotype |

Notes:

- RenderCV has no Calibri, so `calibri` uses **Source Sans 3** in the PDF
  (the closest bundled modern sans) and real **Calibri** in Word — matching
  the Claude reference resume (`William.Jiang - Senior FullStack-AI
  Engineer.docx`).
- The PDF font names are the families bundled with RenderCV in
  `venv/lib/python3.12/site-packages/rendercv_fonts/`.

## Defaults

- English builds default to `calibri`.
- Chinese builds (`--locale zh-CN`) default to `noto-sans` automatically so
  CJK glyphs embed correctly in the PDF (`NotoSansSC`). The WebUI mirrors
  this: switching the language toggle to 中文 switches the font selector to
  Noto Sans and back.

## Usage

CLI:

```bash
# Explicit font
python resume.py build --yaml profiles/na-ai-engineer.yaml \
  --company "BestIT" --role "Senior AI Engineer" --font garamond

# Serif / Chinese
python resume.py build --yaml profiles/base-zh-cto.yaml \
  --company "某公司" --role "CTO" --locale zh-CN   # auto: noto-sans

# List choices
python resume.py build --help | grep -- --font
```

WebUI:

1. Open the **Build** tab.
2. In **Style & Options**, pick a font from the **Font** dropdown
   (PDF + DOCX + cover letter all use it).
3. Build as usual.

## Verifying the font actually changed

```bash
# What is embedded in the PDF?
pdffonts "output/<slug>/William_Jiang-<Role>.pdf"

# What does the DOCX use?
venv/bin/python - <<'PY'
import docx
from collections import Counter
d = docx.Document("output/<slug>/resume.docx")
print(Counter(r.font.name for p in d.paragraphs for r in p.runs if r.font.name))
PY
```

Expect e.g. `EBGaramond*` in the PDF and `Garamond` in the DOCX after a
`--font garamond` build, or `NotoSansSC-*` in the PDF of a Chinese build.

## Adding a new font

1. Open `src/fonts.py` and add a key to `FONT_OPTIONS`:

   ```python
   "inter": {
       "label": "Inter",
       "rendercv": "Inter",
       "docx": "Arial",
   },
   ```

2. Make the font available to Typst/RenderCV:
   - If it is a system font, add the `.ttf`/`.otf` to the `rendercv_fonts`
     folder (or install it where Typst can discover it) so the PDF embeds it.
   - Word fonts only need to exist on the machine opening the DOCX.
3. The CLI choice list and the WebUI dropdown pick it up automatically
   (the `--font` choices and `/api/fonts` are both generated from
   `FONT_OPTIONS`).

Full pipeline reference: [`profile-layering.md`](profile-layering.md)
