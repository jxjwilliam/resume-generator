"""
Font registry for resume generation.

Each option maps to:
- ``rendercv``: the font family name used by RenderCV/Typst for the PDF
  (one of the families bundled in ``rendercv_fonts``).
- ``docx``: the matching Word font used by python-docx (Calibri matches the
  Claude reference resume).
"""

FONT_OPTIONS: dict[str, dict[str, str]] = {
    "calibri": {
        "label": "Calibri (Claude-style)",
        "rendercv": "Source Sans 3",
        "docx": "Calibri",
    },
    "source-sans": {
        "label": "Source Sans 3",
        "rendercv": "Source Sans 3",
        "docx": "Calibri",
    },
    "lato": {
        "label": "Lato",
        "rendercv": "Lato",
        "docx": "Calibri",
    },
    "open-sans": {
        "label": "Open Sans",
        "rendercv": "Open Sans",
        "docx": "Arial",
    },
    "roboto": {
        "label": "Roboto",
        "rendercv": "Roboto",
        "docx": "Arial",
    },
    "poppins": {
        "label": "Poppins",
        "rendercv": "Poppins",
        "docx": "Aptos",
    },
    "raleway": {
        "label": "Raleway",
        "rendercv": "Raleway",
        "docx": "Aptos",
    },
    "ubuntu": {
        "label": "Ubuntu",
        "rendercv": "Ubuntu",
        "docx": "Arial",
    },
    "mukta": {
        "label": "Mukta",
        "rendercv": "Mukta",
        "docx": "Arial",
    },
    "open-sauce-sans": {
        "label": "Open Sauce Sans",
        "rendercv": "Open Sauce Sans",
        "docx": "Calibri",
    },
    "noto-sans": {
        "label": "Noto Sans (CJK-ready)",
        "rendercv": "Noto Sans",
        "docx": "Arial",
    },
    "charter": {
        "label": "Charter (serif)",
        "rendercv": "XCharter",
        "docx": "Georgia",
    },
    "libertinus": {
        "label": "Libertinus Serif",
        "rendercv": "Libertinus Serif",
        "docx": "Georgia",
    },
    "garamond": {
        "label": "EB Garamond",
        "rendercv": "EB Garamond",
        "docx": "Garamond",
    },
    "gentium": {
        "label": "Gentium Book Plus",
        "rendercv": "Gentium Book Plus",
        "docx": "Book Antiqua",
    },
    "fontin": {
        "label": "Fontin",
        "rendercv": "Fontin",
        "docx": "Palatino Linotype",
    },
}

DEFAULT_FONT = "calibri"
DEFAULT_FONT_ZH = "noto-sans"


def resolve_font(font_key: str | None, locale: str = "en") -> dict[str, str]:
    """Resolve a font key to rendercv + docx font names."""
    key = font_key or (DEFAULT_FONT_ZH if locale == "zh-CN" else DEFAULT_FONT)
    return FONT_OPTIONS.get(key) or FONT_OPTIONS[DEFAULT_FONT]


def font_choices() -> list[dict[str, str]]:
    """List font options for the WebUI dropdown."""
    return [{"id": key, "label": value["label"]} for key, value in FONT_OPTIONS.items()]
