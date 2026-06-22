from .models import ThemeInfo, RxTemplateInfo

THEMES: list[ThemeInfo] = [
    ThemeInfo(
        id="auto",
        name="Auto",
        description="Pick theme from JD signals (seniority, company type, ATS)",
        best_for="Recommended when a JD is provided",
    ),
    ThemeInfo(
        id="classic",
        name="Classic",
        description="Professional, clean layout with section headers",
        best_for="FAANG, large tech, senior roles",
    ),
    ThemeInfo(
        id="sb2nov",
        name="Sb2nov",
        description="ATS-optimised, single-column, high density",
        best_for="Standard SWE roles, ATS-friendly",
    ),
    ThemeInfo(
        id="moderncv",
        name="ModernCV",
        description="Modern two-column layout with icon accents",
        best_for="Startup, product, mid-level",
    ),
    ThemeInfo(
        id="engineeringresumes",
        name="EngineeringResumes",
        description="Minimal, maximally ATS-optimised plaintext-friendly",
        best_for="Maximally ATS-optimised",
    ),
]

RX_TEMPLATES: list[RxTemplateInfo] = [
    RxTemplateInfo(
        id="kakuna",
        name="Kakuna",
        description="Compact, high-density single-column layout",
        best_for="Maximizing space, dense resumes (default)",
    ),
    RxTemplateInfo(
        id="bronzor",
        name="Bronzor",
        description="Minimal, clean two-column layout",
        best_for="Tech / engineering roles",
    ),
    RxTemplateInfo(
        id="onyx",
        name="Onyx",
        description="Clean corporate layout with subtle sidebar",
        best_for="Corporate, finance, law, consulting",
    ),
    RxTemplateInfo(
        id="ditto",
        name="Ditto",
        description="Minimalist single-column with ample whitespace",
        best_for="Corporate / traditional roles",
    ),
    RxTemplateInfo(
        id="azurill",
        name="Azurill",
        description="Compact two-column with colored accents",
        best_for="Space-efficient resumes",
    ),
    RxTemplateInfo(
        id="chikorita",
        name="Chikorita",
        description="Modern balanced layout with green accents",
        best_for="Tech / startups, modern roles",
    ),
    RxTemplateInfo(
        id="leafish",
        name="Leafish",
        description="Contemporary design with natural tones",
        best_for="Tech / startups, creative tech",
    ),
    RxTemplateInfo(
        id="gengar",
        name="Gengar",
        description="Bold dark-themed layout with high contrast",
        best_for="Creative fields, design, marketing",
    ),
    RxTemplateInfo(
        id="pikachu",
        name="Pikachu",
        description="Playful layout with vibrant yellow accents",
        best_for="Creative fields, design, marketing",
    ),
    RxTemplateInfo(
        id="lapras",
        name="Lapras",
        description="Elegant single-column with refined spacing",
        best_for="Senior / leadership roles",
    ),
    RxTemplateInfo(
        id="glalie",
        name="Glalie",
        description="Clean, cool-toned two-column layout",
        best_for="Technical roles, engineering",
    ),
    RxTemplateInfo(
        id="rhyhorn",
        name="Rhyhorn",
        description="Robust layout with strong visual hierarchy",
        best_for="Experienced professionals, management",
    ),
    RxTemplateInfo(
        id="meowth",
        name="Meowth",
        description="Playful compact layout with personality",
        best_for="Creative roles, startups",
    ),
    RxTemplateInfo(
        id="scizor",
        name="Scizor",
        description="Sharp, precise layout with clean lines",
        best_for="Engineering, technical leadership",
    ),
    RxTemplateInfo(
        id="ditgar",
        name="Ditgar",
        description="Modern hybrid of Ditto and Gengar aesthetics",
        best_for="Creative tech, design engineering",
    ),
]


def get_theme(theme_id: str) -> ThemeInfo | None:
    return next((t for t in THEMES if t.id == theme_id), None)
