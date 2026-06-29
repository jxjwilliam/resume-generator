import type {
  ThemeInfo,
  RxTemplateInfo,
  YamlInfo,
  YamlContent,
  YamlSaveResponse,
  RunHistoryItem,
  OutputFile,
  OutputsResponse,
  ResumeRunRequest,
  TransformRunRequest,
  RunResponse,
  JdAnalysisResult,
  JdUploadResult,
  JdCompareResult,
  JdCompareItem,
  LogLine,
  ComposePreviewResult,
} from "../types";
import { DEFAULT_YAML_PATH } from "../types";

const BASE = "/api";

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`POST ${path} ${res.status}: ${text}`);
  }
  return res.json();
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`GET ${path} ${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  listYamls: () => get<YamlInfo[]>("/yamls"),
  getYaml: (path?: string) => {
    const q = path ? `?path=${encodeURIComponent(path)}` : "";
    return get<YamlContent>(`/yaml${q}`);
  },
  saveYaml: (path: string, content: string) =>
    post<YamlSaveResponse>("/yaml", { path, content }),
  listThemes: () => get<ThemeInfo[]>("/themes"),
	  listOutputs: () => get<OutputsResponse>("/outputs"),
	  listRxTemplates: () => get<RxTemplateInfo[]>("/rxresume-templates"),
  listTags: () => get<{ tags: string[] }>("/tags"),
  analyzeJd: (text: string, yamlFile?: string) =>
    post<JdAnalysisResult>("/jd/analyze", { text, yaml_file: yamlFile || DEFAULT_YAML_PATH }),
  previewComposition: (req: {
    text: string;
    yaml_file?: string;
    tags?: string[];
    max_bullets?: number;
    max_jobs?: number;
  }) => post<ComposePreviewResult>("/jd/preview", req),
  compareJds: (jds: JdCompareItem[], tags?: string[]) =>
    post<JdCompareResult>("/jd/compare", { jds, tags: tags || [] }),
  uploadJd: async (file: File): Promise<JdUploadResult> => {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch(`${BASE}/jd/upload`, {
      method: "POST",
      body: fd,
    });
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    return res.json();
  },
  runResume: (req: ResumeRunRequest) =>
    post<RunResponse>("/resume/run", req),
  runTransform: (req: TransformRunRequest) =>
    post<RunResponse>("/transform/run", req),
  cancelRun: (jobId: string) =>
    post<{ status: string }>(`/resume/cancel/${jobId}`, {}),
  getHistory: (params?: {
    type?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }) => {
    const q = new URLSearchParams();
    if (params?.type) q.set("type", params.type);
    if (params?.status) q.set("status", params.status);
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    const qs = q.toString();
    return get<{ runs: RunHistoryItem[]; total: number }>(
      `/history${qs ? "?" + qs : ""}`
    );
  },
  getRunDetail: (jobId: string) =>
    get<RunHistoryItem>(`/history/${jobId}`),
  getOutputFiles: (jobId: string) =>
    get<{ files: OutputFile[] }>(`/output/${jobId}/files`),
  getOutputContent: <T>(jobId: string, name: string) =>
    get<T>(`/output/${jobId}/content?name=${encodeURIComponent(name)}`),
  streamLogs: (jobId: string, onLine: (line: LogLine) => void): (() => void) => {
    const es = new EventSource(`${BASE}/log/${jobId}`);
    const abort = () => es.close();

    es.onmessage = (event) => {
      if (!event.data) return;
      const text = event.data;
      if (text.startsWith("[STDERR] ")) {
        onLine({ text: text.slice(9), source: "stderr" });
      } else if (text.startsWith("[SYSTEM] ")) {
        onLine({ text: text.slice(9), source: "system" });
      } else {
        onLine({ text, source: "stdout" });
      }
    };
    es.onerror = () => {
      onLine({ text: "Connection closed", source: "system" });
      es.close();
    };
    return abort;
  },
};
