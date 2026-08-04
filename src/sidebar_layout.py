"""Two-column sidebar layout for rendercv-generated Typst files.

RenderCV 2.8's built-in themes are all single-column templates: a header
(photo, name, headline, connections) followed by full-width sections.  This
module rewrites the generated ``.typ`` file into a classic two-column layout
(profile sidebar on the left, details on the right) and compiles it with
``typst-py``.

The sidebar is implemented entirely at the Typst level (no changes to the
rendercv package):

* ``page-left-margin`` is widened so the body flows in the right column.
* The header block is removed from the document flow and placed, together
  with a navy background rectangle, in ``page(background:)`` so the full
  sidebar repeats on every page.
* The ``rendercv.with(...)`` name/headline/connection colors are switched to
  light-on-dark values that work against the navy sidebar.

The generated PDF is compiled with the ``typst`` Python package using the
same bundled rendercv Typst package and fonts that ``rendercv render`` uses.
"""

from __future__ import annotations

import atexit
import re
import shutil
import tempfile
from pathlib import Path

#: Themes that render as a two-column sidebar layout.
SIDEBAR_THEMES = ("classic",)

SIDEBAR_WIDTH = "4.7cm"          # width of the left sidebar (also left margin)
SIDEBAR_INNER_WIDTH = "3.8cm"    # sidebar width minus horizontal padding
SIDEBAR_FILL = 'rgb("#1a3a5c")'  # navy, matching the UI "classic" thumbnail
SIDEBAR_NAME_SIZE = "18pt"       # default 30pt is too wide for the sidebar
SIDEBAR_NAME_COLOR = "rgb(255, 255, 255)"
SIDEBAR_HEADLINE_COLOR = "rgb(170, 190, 215)"
SIDEBAR_CONNECTIONS_COLOR = "rgb(200, 215, 235)"
PHOTO_WIDTH = "2.8cm"


def is_sidebar_theme(template: str | None) -> bool:
    """Return True if *template* should render with the sidebar layout."""
    return bool(template) and template in SIDEBAR_THEMES


def patch_typst_for_sidebar(typ_path: Path) -> None:
    """Rewrite a rendercv-generated ``.typ`` file into the sidebar layout."""
    text = typ_path.read_text(encoding="utf-8")
    if "rendercv.with(" not in text:
        raise ValueError(f"Unexpected Typst file (no rendercv.with): {typ_path}")

    # --- Theme the header for a dark sidebar: light text, smaller name. ---
    text = _replace_param(text, "page-left-margin", SIDEBAR_WIDTH)
    text = _replace_param(text, "colors-name", SIDEBAR_NAME_COLOR)
    text = _replace_param(text, "colors-headline", SIDEBAR_HEADLINE_COLOR)
    text = _replace_param(text, "colors-connections", SIDEBAR_CONNECTIONS_COLOR)
    text = _replace_param(text, "typography-font-size-name", SIDEBAR_NAME_SIZE)

    # --- Pull the header (photo + name/headline/connections) out of flow. ---
    header, _rest = _split_header(text)
    photo_match = re.search(r'image\("([^"]+)"', header)
    name_cell = header
    if photo_match:
        name_cell = _extract_name_cell(header)
    profile = _build_profile(
        name_cell,
        photo=photo_match.group(1) if photo_match else None,
    )
    text_without_header = text.replace(header, "", 1)

    # --- Render the sidebar as the page background (repeats every page). ---
    background = _sidebar_background(profile)
    patched = _insert_after_import(text_without_header, background)
    typ_path.write_text(patched, encoding="utf-8")


def compile_sidebar_outputs(
    typ_path: Path,
    output_path: Path,
    all_formats: bool = False,
) -> tuple[Path, list[Path]]:
    """Compile a patched sidebar ``.typ`` into PDF (and PNGs if requested)."""
    compiler = _typst_compiler(output_path)
    pdf_path = output_path / "William_Jiang_CV.pdf"
    compiler.compile(input=typ_path, format="pdf", output=pdf_path)

    png_paths: list[Path] = []
    if all_formats:
        result = compiler.compile(input=typ_path, format="png")
        pages = result if isinstance(result, list) else [result]
        for i, data in enumerate(pages):
            if data is None:
                continue
            png = output_path / f"William_Jiang_CV_{i + 1}.png"
            png.write_bytes(data)
            png_paths.append(png)
    return pdf_path, png_paths


def _typst_compiler(root: Path):
    """Build a typst compiler mirroring rendercv's own setup (fonts + package)."""
    try:
        import rendercv
        import rendercv_fonts
        import typst
    except ImportError as exc:
        raise RuntimeError(
            "The sidebar layout needs the 'typst' package. "
            "Reinstall with: pip install 'rendercv[full]'"
        ) from exc

    bundled = Path(rendercv.__file__).parent / "renderer" / "rendercv_typst"
    toml = bundled / "typst.toml"
    version = None
    for line in toml.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("version"):
            version = stripped.split("=", 1)[1].strip().strip('"')
            break
    if not version:
        raise RuntimeError("Could not determine the bundled rendercv Typst version")

    tmp = Path(tempfile.mkdtemp(prefix="rendercv-pkg-"))
    atexit.register(shutil.rmtree, str(tmp), True)
    package_dir = tmp / "preview" / "rendercv" / version
    package_dir.mkdir(parents=True)
    shutil.copy2(toml, package_dir / "typst.toml")
    shutil.copy2(bundled / "lib.typ", package_dir / "lib.typ")

    return typst.Compiler(
        root=root,
        font_paths=[*rendercv_fonts.paths_to_font_folders],
        package_path=tmp,
    )


def _replace_param(text: str, key: str, value: str) -> str:
    """Replace one ``key: value,`` line in the rendercv.with(...) call."""
    return re.sub(
        rf"^\s*{re.escape(key)}: .*$",
        f"{key}: {value},",
        text,
        flags=re.MULTILINE,
    )


def _find_matching_paren(text: str, start: int) -> int:
    """Return the index of the ``)`` matching the ``(`` at *start*."""
    depth = 0
    i = start
    while i < len(text):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("Unbalanced parentheses in Typst file")


def _split_header(text: str) -> tuple[str, str]:
    """Split the document into (header block, rest).

    The header is the photo grid emitted by rendercv's Header template (or,
    when the CV has no photo, everything between the ``rendercv.with(...)``
    call and the first section heading).
    """
    with_start = text.find("rendercv.with(")
    if with_start == -1:
        raise ValueError("Could not find rendercv.with(...) call")
    with_end = _find_matching_paren(text, with_start + len("rendercv.with"))
    body_start = with_end + 1

    grid_start = text.find("#grid(", body_start)
    if grid_start != -1:
        grid_end = _find_matching_paren(text, grid_start + len("#grid")) + 1
        return text[grid_start:grid_end], text[grid_end:]

    heading = re.search(r"\n== ", text[body_start:])
    if not heading:
        return text[body_start:].strip(), ""
    header_end = body_start + heading.start()
    return text[body_start:header_end].strip(), text[header_end:]


def _extract_name_cell(grid: str) -> str:
    """Extract the name/headline/connections cell from the header grid."""
    marker = "],\n  [\n"
    start = grid.find(marker)
    if start == -1:
        raise ValueError("Could not parse header grid cells")
    start += len(marker)
    end = grid.rfind("\n  ]\n)")
    if end == -1:
        raise ValueError("Could not find end of header grid")
    return grid[start:end]


def _build_profile(name_cell: str, photo: str | None = None) -> str:
    """Rebuild the sidebar profile from the extracted header content."""
    parts: list[str] = []
    if photo:
        parts.append(f'#align(center)[#image("{photo}", width: {PHOTO_WIDTH})]')
        parts.append("#v(0.35cm)")

    name = re.search(r"^= (.+)$", name_cell, re.MULTILINE)
    if name:
        parts.append(f"= {name.group(1).strip()}")

    headline = re.search(r"#headline\(\[(.*?)\]\)", name_cell, re.DOTALL)
    if headline:
        parts.append("")
        parts.append(f"  #headline([{headline.group(1)}])")

    conn_start = name_cell.find("#connections(")
    if conn_start != -1:
        inner_start = conn_start + len("#connections(")
        inner_end = _find_matching_paren(name_cell, conn_start + len("#connections"))
        parts.append("")
        parts.append(f"#connections({name_cell[inner_start:inner_end]})")

    return "\n".join(parts)


def _sidebar_background(profile: str) -> str:
    """Build the repeating sidebar: navy rectangle + profile content."""
    return f"""#set page(background: [
  #place(left + top, [#rect(width: {SIDEBAR_WIDTH}, height: 100%, fill: {SIDEBAR_FILL})])
  #place(left + top, dx: 0.45cm, dy: 0.6cm, [
    #block(width: {SIDEBAR_INNER_WIDTH})[
      {profile}
    ]
  ])
])"""


def _insert_after_import(text: str, block: str) -> str:
    """Insert *block* right after the ``#import`` line at the top."""
    match = re.search(r"^#import .*$", text, re.MULTILINE)
    if not match:
        raise ValueError("Could not find the #import line in Typst file")
    return text[: match.end()] + "\n\n" + block + "\n\n" + text[match.end() :]
