from pydantic import BaseModel
from typing import Optional


class ResumeRunRequest(BaseModel):
    yaml_file: str = "base.yaml"
    company: str
    role: Optional[str] = None
    tags: list[str] = []
    theme: str = "classic"
    jd_text: Optional[str] = None
    use_llm: bool = False
    all_formats: bool = False


class TransformRunRequest(BaseModel):
    yaml_file: str = "base.yaml"
    jd_text: str
    tags: list[str] = []
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
