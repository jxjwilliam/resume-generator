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
  error_log?: string;
  run_duration_seconds?: number;
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
  all_formats?: boolean;
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

export interface JdUploadResult {
  text: string;
  keywords: string[];
}

export type LogLine = {
  text: string;
  source: "stdout" | "stderr" | "system";
};
