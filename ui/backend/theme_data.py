from .models import ThemeInfo

THEMES: list[ThemeInfo] = [
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


def get_theme(theme_id: str) -> ThemeInfo | None:
    return next((t for t in THEMES if t.id == theme_id), None)
