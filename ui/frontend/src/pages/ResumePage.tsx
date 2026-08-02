import { useState, useCallback, useRef, useEffect } from "react";
import {
  Box,
  Button,
  Chip,
  TextField,
  Checkbox,
  FormControlLabel,
  Stack,
  Typography,
  Alert,
  ToggleButtonGroup,
  ToggleButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import DescriptionIcon from "@mui/icons-material/Description";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";
import TextSnippetIcon from "@mui/icons-material/TextSnippet";
import AssessmentIcon from "@mui/icons-material/Assessment";
import ThemeCard from "../components/ThemeCard";
import LogStream from "../components/LogStream";
import JdInput from "../components/JdInput";
import YamlSelector from "../components/YamlSelector";
import TagChips from "../components/TagChips";
import JdAnalysisPanel from "../components/JdAnalysisPanel";
import AtsScoreWidget from "../components/AtsScoreWidget";
import BulletDiffView from "../components/BulletDiffView";
import BulletPreviewPanel from "../components/BulletPreviewPanel";
import { DEFAULT_YAML_PATH } from "../types";
import { api } from "../api/client";
import type {
  ThemeInfo, OutputFile, LogLine, JdAnalysisResult,
  AtsReport, BulletDiffReport, ComposePreviewResult,
} from "../types";

interface Props {
  themes: ThemeInfo[];
  onRefreshHistory: () => void;
}

function useStoredState<T>(key: string, fallback: T): [T, (v: T) => void] {
  const [value, setValue] = useState<T>(() => {
    try {
      const stored = localStorage.getItem("resume:" + key);
      if (stored !== null) return JSON.parse(stored);
    } catch { /* ignore */ }
    return fallback;
  });
  useEffect(() => {
    try { localStorage.setItem("resume:" + key, JSON.stringify(value)); } catch { /* quota */ }
  }, [key, value]);
  return [value, setValue];
}

export default function ResumePage({ themes, onRefreshHistory }: Props) {
  const [yamlFile, setYamlFile] = useStoredState<string>("yamlFile", DEFAULT_YAML_PATH);
  const [company, setCompany] = useStoredState<string>("company", "");
  const [role, setRole] = useStoredState<string>("role", "");
  const [selectedTheme, setSelectedTheme] = useStoredState<string>("theme", "classic");
  const [jdText, setJdText] = useState("");
  const [keywords, setKeywords] = useState<string[]>([]);
  const [jdAnalysis, setJdAnalysis] = useState<JdAnalysisResult | null>(null);
  const [useLlm, setUseLlm] = useStoredState<boolean>("useLlm", true);
  const [llmProvider, setLlmProvider] = useStoredState<string>("llmProvider", "");
  const [tailor, setTailor] = useStoredState<boolean>("tailor", false);
  const [enhance, setEnhance] = useStoredState<boolean>("enhance", false);
  const [boost, setBoost] = useStoredState<boolean>("boost", false);
  const [maxBullets, setMaxBullets] = useStoredState<number>("maxBullets", 4);
  const [maxJobs, setMaxJobs] = useStoredState<number>("maxJobs", 5);
  const [allFormats, setAllFormats] = useStoredState<boolean>("allFormats", false);
  const [locale, setLocale] = useStoredState<string>("locale", "en");
  const [coverLetter, setCoverLetter] = useStoredState<boolean>("coverLetter", true);
  const [docx, setDocx] = useStoredState<boolean>("docx", true);
  const [running, setRunning] = useState(false);
  const [logLines, setLogLines] = useState<LogLine[]>([]);
  const [error, setError] = useState("");
  const [outputFiles, setOutputFiles] = useState<OutputFile[]>([]);
  const [lastJobId, setLastJobId] = useState<string | null>(null);
  const [atsReport, setAtsReport] = useState<AtsReport | null>(null);
  const [bulletDiff, setBulletDiff] = useState<BulletDiffReport | null>(null);
  const [composePreview, setComposePreview] = useState<ComposePreviewResult | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const themeManualRef = useRef(false);
  const sseCloseRef = useRef<(() => void) | null>(null);
  const runPollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const jobFinishedRef = useRef(false);

  // Accordion states — log auto-expands when running, output auto-expands when done
  const [jdExpanded, setJdExpanded] = useState(true);
  const [analysisExpanded, setAnalysisExpanded] = useState(false);
  const [previewExpanded, setPreviewExpanded] = useState(false);
  const logExpanded = running || logLines.length > 0;
  const outputExpanded = outputFiles.length > 0;

  useEffect(() => () => {
    sseCloseRef.current?.();
    if (runPollRef.current) clearInterval(runPollRef.current);
  }, []);

  // Auto-select theme when JD is pasted
  useEffect(() => {
    if (jdText.trim().length > 50 && !themeManualRef.current) {
      setSelectedTheme("auto");
    }
  }, [jdText]);

  // Debounced composition preview
  useEffect(() => {
    if (jdText.trim().length <= 50) {
      setComposePreview(null);
      return;
    }
    setPreviewLoading(true);
    const t = setTimeout(() => {
      api.previewComposition({
        text: jdText,
        yaml_file: yamlFile,
        max_bullets: maxBullets,
        max_jobs: maxJobs,
      })
        .then(setComposePreview)
        .catch(() => setComposePreview(null))
        .finally(() => setPreviewLoading(false));
    }, 400);
    return () => clearTimeout(t);
  }, [jdText, yamlFile, maxBullets, maxJobs]);

  // Auto-expand analysis when data arrives
  useEffect(() => {
    if (jdAnalysis) setAnalysisExpanded(true);
  }, [jdAnalysis]);

  const handleLocaleChange = (
    _: React.MouseEvent<HTMLElement>,
    newLocale: string | null,
  ) => {
    if (!newLocale) return;
    setLocale(newLocale);
    const prefix = DEFAULT_YAML_PATH.substring(0, DEFAULT_YAML_PATH.lastIndexOf("/") + 1);
    const zhPath = prefix + "base-zh.yaml";
    if (newLocale === "zh-CN" && yamlFile === DEFAULT_YAML_PATH) {
      setYamlFile(zhPath);
    } else if (newLocale === "en" && yamlFile === zhPath) {
      setYamlFile(DEFAULT_YAML_PATH);
    }
  };

  const fileIcon = (type: string) => {
    switch (type) {
      case "pdf": return <PictureAsPdfIcon fontSize="small" />;
      case "cover-letter": return <TextSnippetIcon fontSize="small" />;
      case "ats-report":
      case "bullet-diff": return <AssessmentIcon fontSize="small" />;
      default: return <DescriptionIcon fontSize="small" />;
    }
  };

  const handleJobDone = useCallback(async (job_id: string, success: boolean) => {
    if (jobFinishedRef.current) return;
    jobFinishedRef.current = true;
    if (runPollRef.current) {
      clearInterval(runPollRef.current);
      runPollRef.current = null;
    }
    sseCloseRef.current?.();
    sseCloseRef.current = null;
    setRunning(false);
    setLastJobId(job_id);
    if (success) {
      try {
        const resp = await api.getOutputFiles(job_id);
        setOutputFiles(resp.files);
        const names = new Set(resp.files.map((f: OutputFile) => f.name));
        if (names.has("ats-report.json")) {
          try {
            const report = await api.getOutputContent<AtsReport>(job_id, "ats-report.json");
            setAtsReport(report);
          } catch { /* optional */ }
        }
        if (names.has("bullet-diff.json")) {
          try {
            const diff = await api.getOutputContent<BulletDiffReport>(job_id, "bullet-diff.json");
            setBulletDiff(diff);
          } catch { /* optional */ }
        }
      } catch { /* no output files */ }
    }
    onRefreshHistory();
  }, [onRefreshHistory]);

  const handleRun = useCallback(async (opts?: { tailor?: boolean; boost?: boolean; useLlm?: boolean }) => {
    const runCompany = company.trim() || "Unknown";
    if (!company.trim()) setCompany("Unknown");
    setError("");
    setRunning(true);
    setLogLines([]);
    setOutputFiles([]);
    setLastJobId(null);
    setAtsReport(null);
    setBulletDiff(null);
    jobFinishedRef.current = false;
    sseCloseRef.current?.();
    sseCloseRef.current = null;
    if (runPollRef.current) {
      clearInterval(runPollRef.current);
      runPollRef.current = null;
    }

    const runTailor = opts?.tailor ?? tailor;
    const runBoost = opts?.boost ?? boost;
    const runLlm = opts?.useLlm ?? useLlm;

    try {
      const { job_id } = await api.runResume({
        yaml_file: yamlFile,
        company: runCompany,
        role: role.trim() || undefined,
        theme: selectedTheme,
        jd_text: jdText || undefined,
        use_llm: runLlm,
        llm_provider: llmProvider || undefined,
        tailor: runTailor || undefined,
        enhance: enhance || undefined,
        boost: runBoost || undefined,
        max_bullets: maxBullets,
        max_jobs: maxJobs,
        all_formats: allFormats,
        locale: locale !== "en" ? locale : undefined,
        cover_letter: coverLetter || undefined,
        docx: docx || undefined,
      });

      setLastJobId(job_id);

      const closeStream = api.streamLogs(job_id, (line) => {
        setLogLines((prev) => [...prev, line]);
        if (line.source === "system") {
          if (line.text === "Job completed successfully") {
            handleJobDone(job_id, true);
          } else if (line.text.startsWith("Job failed")) {
            handleJobDone(job_id, false);
          }
        }
      });
      sseCloseRef.current = closeStream;

      runPollRef.current = setInterval(async () => {
        try {
          const detail = await api.getRunDetail(job_id);
          if (detail.status !== "running") {
            handleJobDone(job_id, detail.status === "success");
          }
        } catch { /* keep polling */ }
      }, 1000);
    } catch (e: any) {
      setError(e.message);
      setRunning(false);
    }
  }, [
    yamlFile, company, role, selectedTheme, jdText, useLlm, tailor, boost, enhance,
    maxBullets, maxJobs, allFormats, locale, coverLetter, docx, handleJobDone,
  ]);

  const handleBoostRerun = useCallback(() => {
    setTailor(true);
    setBoost(true);
    setUseLlm(true);
    handleRun({ tailor: true, boost: true, useLlm: true });
  }, [handleRun]);

  return (
    <Box sx={{ maxWidth: 1080, mx: "auto" }}>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {/* ── Build form ── */}
      <Stack direction="row" spacing={1.5} sx={{ mt: 1, mb: 1, alignItems: "center", flexWrap: "wrap" }}>
        <Typography variant="subtitle2">YAML:</Typography>
        <YamlSelector value={yamlFile} onChange={setYamlFile} disabled={running} />
        <Box sx={{ flexGrow: 0, width: 12 }} />
        <Typography variant="body2" color="text.secondary">LLM:</Typography>
        <ToggleButtonGroup value={llmProvider} exclusive
          onChange={(_, v) => v !== null && setLlmProvider(v)} size="small">
          <ToggleButton value="" disabled={running}>default</ToggleButton>
          <ToggleButton value="deepseek" disabled={running}>DeepSeek</ToggleButton>
          <ToggleButton value="kimi" disabled={running}>Kimi</ToggleButton>
          <ToggleButton value="minimax" disabled={running}>MiniMax</ToggleButton>
        </ToggleButtonGroup>
        <FormControlLabel
          control={<Checkbox size="small" checked={enhance} onChange={(e) => setEnhance(e.target.checked)} disabled={running} />}
          label="Enhance" />
        <FormControlLabel
          control={<Checkbox size="small" checked={tailor} onChange={(e) => setTailor(e.target.checked)} disabled={running} />}
          label="Tailor" />
        <FormControlLabel
          control={<Checkbox size="small" checked={boost} onChange={(e) => setBoost(e.target.checked)} disabled={running} />}
          label="Boost" />
        <Box sx={{ flexGrow: 1 }} />
        <Button variant="contained" size="small" startIcon={<PlayArrowIcon />}
          onClick={() => handleRun()} disabled={running}>
          {running ? "Running..." : "Build"}
        </Button>
      </Stack>

      <Stack direction="row" spacing={2} sx={{ mb: 1, alignItems: "center" }}>
        <TextField label="Company" size="small" placeholder="Unknown"
          value={company} onChange={(e) => setCompany(e.target.value)} disabled={running} />
        <TextField label="Role" size="small"
          value={role} onChange={(e) => setRole(e.target.value)} disabled={running} />
        <Box sx={{ flexGrow: 1 }} />
        <Typography variant="body2" color="text.secondary" sx={{ mr: 1 }}>Language:</Typography>
        <ToggleButtonGroup value={locale} exclusive onChange={handleLocaleChange} size="small">
          <ToggleButton value="en" disabled={running}>English</ToggleButton>
          <ToggleButton value="zh-CN" disabled={running}>中文 (简体)</ToggleButton>
        </ToggleButtonGroup>
      </Stack>

      {/* Theme selection */}
      <Typography variant="subtitle2" gutterBottom>Theme</Typography>
      <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: "wrap" }}>
        {themes.map((t) => (
          <ThemeCard key={t.id} theme={t} selected={selectedTheme === t.id} disabled={running}
            onClick={() => { themeManualRef.current = true; setSelectedTheme(t.id); }} />
        ))}
      </Stack>

      {/* Output options */}
      <Stack direction="row" spacing={2} sx={{ mb: 2, alignItems: "center", flexWrap: "wrap" }}>
        <TextField label="Max bullets/job" type="number" size="small" sx={{ width: 130 }}
          value={maxBullets} onChange={(e) => setMaxBullets(Number(e.target.value) || 4)}
          inputProps={{ min: 1, max: 8 }} disabled={running} />
        <TextField label="Max jobs" type="number" size="small" sx={{ width: 110 }}
          value={maxJobs} onChange={(e) => setMaxJobs(Number(e.target.value) || 5)}
          inputProps={{ min: 1, max: 10 }} disabled={running} />
        <FormControlLabel
          control={<Checkbox size="small" checked={useLlm} onChange={(e) => setUseLlm(e.target.checked)} disabled={running} />}
          label="Use LLM" />
        <FormControlLabel
          control={<Checkbox size="small" checked={coverLetter} onChange={(e) => setCoverLetter(e.target.checked)} disabled={running} />}
          label="Cover letter" />
        <FormControlLabel
          control={<Checkbox size="small" checked={docx} onChange={(e) => setDocx(e.target.checked)} disabled={running} />}
          label="Docx" />
        <FormControlLabel
          control={<Checkbox size="small" checked={allFormats} onChange={(e) => setAllFormats(e.target.checked)} disabled={running} />}
          label="HTML/MD/PNG" />
      </Stack>

      {/* ── Job Description ── */}
      <Accordion expanded={jdExpanded || jdText.length > 0} onChange={(_, v) => setJdExpanded(v)}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="subtitle2">
            Job Description
            {jdText.trim() && <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 1 }}>
              ({jdText.length} chars)
            </Typography>}
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <JdInput value={jdText} onChange={setJdText} onKeywords={setKeywords}
            onAnalysis={setJdAnalysis} yamlFile={yamlFile} disabled={running} />
        </AccordionDetails>
      </Accordion>

      {/* ── JD Analysis (auto-expands when data arrives) ── */}
      <Accordion expanded={analysisExpanded && !running} onChange={(_, v) => setAnalysisExpanded(v)}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="subtitle2">
            JD Analysis
            {jdAnalysis && !analysisExpanded && <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 1 }}>
              — {jdAnalysis.matched_skills?.length || 0} skills matched
            </Typography>}
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <JdAnalysisPanel analysis={jdAnalysis} />
          {keywords.length > 0 && <TagChips keywords={keywords} />}
        </AccordionDetails>
      </Accordion>

      {/* ── Bullet Preview ── */}
      <Accordion expanded={previewExpanded && !running && composePreview !== null} onChange={(_, v) => setPreviewExpanded(v)}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="subtitle2">
            Bullet Composition Preview
            {composePreview && !previewExpanded && <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 1 }}>
              — {composePreview.bullets_included} included / {composePreview.bullets_excluded} excluded
            </Typography>}
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <BulletPreviewPanel preview={composePreview} loading={previewLoading} />
        </AccordionDetails>
      </Accordion>

      {/* ── Build Log (auto-expands during build, shows progress bar) ── */}
      <Accordion expanded={logExpanded} sx={{ mt: running ? 1 : 0 }}>
        <AccordionSummary expandIcon={running ? null : <ExpandMoreIcon />}
          sx={{ cursor: running ? "default" : "pointer" }}>
          <Stack direction="row" spacing={1} sx={{ alignItems: "center", width: "100%", mr: 2 }}>
            <Typography variant="subtitle2">
              {running ? "Building..." : "Build Log"}
            </Typography>
            {running && <LinearProgress sx={{ flexGrow: 1, minWidth: 100 }} />}
            {!running && logLines.length > 0 &&
              <Typography variant="body2" color="text.secondary">
                ({logLines.length} lines)
              </Typography>}
          </Stack>
        </AccordionSummary>
        <AccordionDetails>
          <LogStream lines={logLines} onClear={() => setLogLines([])} />
        </AccordionDetails>
      </Accordion>

      {/* ── Output Files (auto-expands on completion) ── */}
      <Accordion expanded={outputExpanded}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="subtitle2">
            Output Files
            {outputFiles.length > 0 &&
              <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                — {outputFiles.length} file{outputFiles.length !== 1 ? "s" : ""}
              </Typography>}
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: (atsReport || bulletDiff) ? 2 : 0 }}>
            {outputFiles.map((f) => {
              const downloadUrl = `/api/output/${lastJobId}/download?name=${encodeURIComponent(f.name)}`;
              const sizeKb = (f.size / 1024).toFixed(1);
              return (
                <Chip key={f.name} icon={fileIcon(f.type)}
                  label={`${f.name} (${sizeKb} KB)`}
                  component="a" href={downloadUrl} target="_blank"
                  clickable variant="outlined"
                  color={f.type === "pdf" ? "error" : f.type === "cover-letter" ? "info" : "default"}
                  sx={{ cursor: "pointer" }} />
              );
            })}
          </Stack>

          {atsReport && (
            <Box sx={{ mb: bulletDiff ? 2 : 0 }}>
              <AtsScoreWidget report={atsReport}
                before={bulletDiff?.before_ats ?? null}
                delta={bulletDiff?.delta ?? null}
                onBoostRerun={jdText.trim() ? handleBoostRerun : undefined}
                boostRunning={running} />
            </Box>
          )}

          {bulletDiff && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>Bullet Changes</Typography>
              <BulletDiffView diff={bulletDiff} />
            </Box>
          )}
        </AccordionDetails>
      </Accordion>
    </Box>
  );
}
