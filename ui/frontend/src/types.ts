export interface ThemeInfo {
  id: string;
  name: string;
  description: string;
  best_for: string;
}

export interface RxTemplateInfo {
  id: string;
  name: string;
  description: string;
  best_for: string;
}

export interface YamlInfo {
  name: string;
  path: string;
}

export interface OutputFile {
  name: string;
  type: string;
  slug: string;
  size: number;
}

export interface RunHistoryItem {
  id: string;
  type: "resume" | "transform";
  status: "running" | "success" | "error" | "cancelled";
  company?: string;
  role?: string;
  tags?: string;
  theme?: string;
  jd_snippet?: string;
  use_llm: boolean;
  output_path?: string;
  output_files?: OutputFile[];
  error_log?: string;
  run_duration_seconds?: number;
  ats_score?: number;
  ats_grade?: string;
  ats_before_score?: number;
  pages?: number;
  created_at: string;
  finished_at?: string;
}

export interface ResumeRunRequest {
  yaml_file?: string;
  company: string;
  role?: string;
  tags?: string[];
  theme?: string;
  jd_text?: string;
  use_llm?: boolean;
  tailor?: boolean;
  boost?: boolean;
  max_bullets?: number;
  max_jobs?: number;
  pages?: number;
  no_projects?: boolean;
  all_formats?: boolean;
  locale?: string;
  cover_letter?: boolean;
  docx?: boolean;
}

export interface TransformRunRequest {
  yaml_file?: string;
  jd_text: string;
  tags?: string[];
  template?: string;
  resume_id?: string;
  use_llm?: boolean;
  generate_pdf?: boolean;
}

export interface RunResponse {
  job_id: string;
}

export interface KeywordResult {
  keywords: string[];
}

export interface JdAnalysisResult {
  keywords: string[];
  hard_skills: string[];
  title_keywords?: string[];
  domain_keywords?: string[];
  soft_skills?: string[];
  role_title?: string;
  seniority?: string;
  domain?: string | null;
  matched_skills: string[];
  missing_skills: string[];
  matched_soft_skills?: string[];
  missing_soft_skills?: string[];
  matched_domain_keywords?: string[];
  top_bullets: { job: string; text: string; score: number }[];
}

export interface JdUploadResult {
  text: string;
  keywords: string[];
  hard_skills?: string[];
  title_keywords?: string[];
  domain_keywords?: string[];
  soft_skills?: string[];
  role_title?: string;
  seniority?: string;
  domain?: string | null;
  matched_skills?: string[];
  missing_skills?: string[];
  matched_soft_skills?: string[];
  missing_soft_skills?: string[];
  matched_domain_keywords?: string[];
  top_bullets?: { job: string; text: string; score: number }[];
}

export interface PreviewBullet {
  text: string;
  score: number;
  relevance: string;
  tags: string[];
  included: boolean;
}

export interface PreviewJob {
  company: string;
  title: string;
  job_included: boolean;
  bullets: PreviewBullet[];
}

export interface ComposePreviewResult {
  jobs: PreviewJob[];
  jobs_included: number;
  bullets_included: number;
  bullets_excluded: number;
}

export interface JdCompareRanking {
  label: string;
  total: number;
  grade: string;
  role_title: string;
  seniority?: string;
  matched_skills: string[];
  missing_skills: string[];
  keyword_pct: number;
}

export interface JdCompareResult {
  rankings: JdCompareRanking[];
  recommended: string | null;
  best_score: number;
  count: number;
}

export interface JdCompareItem {
  label: string;
  text: string;
}

export type LogLine = {
  text: string;
  source: "stdout" | "stderr" | "system";
};

export interface AtsScoreBreakdownItem {
  score?: number;
  max?: number;
  pct?: number;
}

export interface AtsReport {
  total: number;
  grade: string;
  breakdown: {
    keyword_match?: AtsScoreBreakdownItem;
    title_alignment?: AtsScoreBreakdownItem;
    completeness?: AtsScoreBreakdownItem;
    formatting?: AtsScoreBreakdownItem;
    conciseness?: AtsScoreBreakdownItem;
  };
  skill_match?: {
    matched_skills?: string[];
    missing_skills?: string[];
    matched_soft_skills?: string[];
    missing_soft_skills?: string[];
  };
  role_title?: string;
  seniority?: string;
  jobs_included?: number;
  bullets_included?: number;
}

export interface BulletDiffEntry {
  key: string;
  job: string;
  title?: string;
  original: string;
  source_used?: string;
  rewritten?: string | null;
  final: string;
  status: "accepted" | "rejected" | "unchanged" | "boosted";
  rejection_reason?: string | null;
  pass?: string;
  approved?: boolean;
}

export interface BulletDiffReport {
  before_ats?: { total: number; grade: string; keyword_pct?: number } | null;
  after_ats?: { total: number; grade: string; keyword_pct?: number } | null;
  delta?: number | null;
  bullets: BulletDiffEntry[];
  stats?: {
    accepted?: number;
    rejected?: number;
    unchanged?: number;
    boosted?: number;
  };
}
