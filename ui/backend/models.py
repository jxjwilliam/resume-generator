from pydantic import BaseModel
from typing import Optional

DEFAULT_YAML = "profiles/base.yaml"


class ResumeRunRequest(BaseModel):
    yaml_file: str = DEFAULT_YAML
    company: str
    role: Optional[str] = None
    tags: list[str] = []
    theme: str = "classic"
    jd_text: Optional[str] = None
    use_llm: bool = True
    llm_provider: Optional[str] = None
    tailor: bool = False
    enhance: bool = False
    boost: bool = False
    max_bullets: int = 4
    max_jobs: int = 0
    pages: int = 2
    max_projects: int = 4
    no_projects: bool = False
    all_formats: bool = False
    locale: str = "en"
    cover_letter: bool = False
    docx: bool = False


class TransformRunRequest(BaseModel):
    yaml_file: str = DEFAULT_YAML
    jd_text: str
    tags: list[str] = []
    template: str = "kakuna"
    resume_id: Optional[str] = None
    use_llm: bool = True
    generate_pdf: bool = False


class RunResponse(BaseModel):
    job_id: str


class RunHistoryItem(BaseModel):
    id: str
    type: str
    status: str
    company: Optional[str] = None
    role: Optional[str] = None
    tags: Optional[str] = None
    theme: Optional[str] = None
    jd_snippet: Optional[str] = None
    use_llm: bool = False
    output_path: Optional[str] = None
    error_log: Optional[str] = None
    run_duration_seconds: Optional[float] = None
    created_at: str
    finished_at: Optional[str] = None


class ThemeInfo(BaseModel):
    id: str
    name: str
    description: str
    best_for: str


class YamlInfo(BaseModel):
    name: str
    path: str


class KeywordResult(BaseModel):
    keywords: list[str]


class JdCompareItem(BaseModel):
    label: str
    text: str


class JdCompareRequest(BaseModel):
    jds: list[JdCompareItem]
    tags: list[str] = []
    max_bullets: int = 4
    max_jobs: int = 0


class JdCompareRanking(BaseModel):
    label: str
    total: float
    grade: str
    role_title: str = ""
    seniority: Optional[str] = None
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    keyword_pct: float = 0


class JdCompareResponse(BaseModel):
    rankings: list[JdCompareRanking]
    recommended: Optional[str] = None
    best_score: float = 0
    count: int = 0


class RxTemplateInfo(BaseModel):
    id: str
    name: str
    description: str
    best_for: str


class JdPreviewRequest(BaseModel):
    yaml_file: str = DEFAULT_YAML
    text: str
    tags: list[str] = []
    max_bullets: int = 4
    max_jobs: int = 0


class YamlSaveRequest(BaseModel):
    path: str = DEFAULT_YAML
    content: str
