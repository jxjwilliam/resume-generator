from .models import ThemeInfo

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
        description="Professional, clean single-column layout",
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
        description="Two-column layout with icon accents",
        best_for="Startup, product, mid-level",
    ),
    ThemeInfo(
        id="engineeringresumes",
        name="EngineeringResumes",
        description="Ultra-compact, maximally ATS-optimised",
        best_for="Maximally ATS-optimised",
    ),
    ThemeInfo(
        id="harvard",
        name="Harvard",
        description="Traditional academic/professional style",
        best_for="Academic, research, formal roles",
    ),
    ThemeInfo(
        id="opal",
        name="Opal",
        description="Clean modern layout with subtle color",
        best_for="Tech, consulting, modern roles",
    ),
    ThemeInfo(
        id="engineeringclassic",
        name="EngineeringClassic",
        description="Classic sidebar + engineering compactness",
        best_for="Balanced professional + ATS",
    ),
    ThemeInfo(
        id="ember",
        name="Ember",
        description="Warm red-accented modern layout",
        best_for="Standout applications, creative tech",
    ),
    ThemeInfo(
        id="ink",
        name="Ink",
        description="Deep purple serif, editorial style",
        best_for="Creative, design, standout applications",
    ),
]


def get_theme(theme_id: str) -> ThemeInfo | None:
    return next((t for t in THEMES if t.id == theme_id), None)
