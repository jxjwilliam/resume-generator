import { useState, useCallback, useRef, useEffect } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Checkbox,
  Chip,
  CircularProgress,
  Collapse,
  Divider,
  FormControlLabel,
  IconButton,
  LinearProgress,
  MenuItem,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from "@mui/material";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import AssessmentIcon from "@mui/icons-material/Assessment";
import DescriptionIcon from "@mui/icons-material/Description";
import DownloadIcon from "@mui/icons-material/Download";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import TerminalIcon from "@mui/icons-material/Terminal";
import TextSnippetIcon from "@mui/icons-material/TextSnippet";
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
  ThemeInfo,
  OutputFile,
  LogLine,
  JdAnalysisResult,
  AtsReport,
  BulletDiffReport,
  ComposePreviewResult,
} from "../types";

interface Props {
  themes: ThemeInfo[];
  onRefreshHistory: () => void;
}

/** Only recruiter-ready files + score reports are shown in Results. */
const MAIN_FILE_TYPES = new Set(["pdf", "docx", "cover-letter", "ats-report", "bullet-diff"]);

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

function fileIcon(type: string) {
  switch (type) {
    case "pdf":
      return <PictureAsPdfIcon fontSize="small" sx={{ color: "error.main" }} />;
    case "cover-letter":
      return <TextSnippetIcon fontSize="small" sx={{ color: "info.main" }} />;
    case "ats-report":
    case "bullet-diff":
      return <AssessmentIcon fontSize="small" sx={{ color: "warning.main" }} />;
    default:
      return <DescriptionIcon fontSize="small" sx={{ color: "primary.main" }} />;
  }
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
  const [font, setFont] = useStoredState<string>("font", "calibri");
  const [fonts, setFonts] = useState<{ id: string; label: string }[]>([]);
  const [locale, setLocale] = useStoredState<string>("locale", "en");
  const [running, setRunning] = useState(false);
  const [logLines, setLogLines] = useState<LogLine[]>([]);
  const [error, setError] = useState("");
  const [outputFiles, setOutputFiles] = useState<OutputFile[]>([]);
  const [lastJobId, setLastJobId] = useState<string | null>(null);
  const [atsReport, setAtsReport] = useState<AtsReport | null>(null);
  const [bulletDiff, setBulletDiff] = useState<BulletDiffReport | null>(null);
  const [composePreview, setComposePreview] = useState<ComposePreviewResult | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [logOpen, setLogOpen] = useState(false);
  const themeManualRef = useRef(false);
  const sseCloseRef = useRef<(() => void) | null>(null);
  const runPollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const jobFinishedRef = useRef(false);

  useEffect(() => () => {
    sseCloseRef.current?.();
    if (runPollRef.current) clearInterval(runPollRef.current);
  }, []);

  useEffect(() => {
    api.listFonts().then(setFonts).catch(() => {});
  }, []);

  // Auto-select theme when a JD is pasted (until the user picks one manually).
  useEffect(() => {
    if (jdText.trim().length > 50 && !themeManualRef.current) {
      setSelectedTheme("auto");
    }
  }, [jdText]);

  // Debounced composition preview.
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

  const handleLocaleChange = (
    _: React.MouseEvent<HTMLElement>,
    newLocale: string | null,
  ) => {
    if (!newLocale) return;
    setLocale(newLocale);
    const prefix = DEFAULT_YAML_PATH.substring(0, DEFAULT_YAML_PATH.lastIndexOf("/") + 1);
    const zhPath = prefix + "base-zh-cto.yaml";
    if (newLocale === "zh-CN" && yamlFile === DEFAULT_YAML_PATH) {
      setYamlFile(zhPath);
      if (font === "calibri") setFont("noto-sans");
    } else if (newLocale === "en" && (yamlFile === zhPath || yamlFile === prefix + "base-zh-partner.yaml")) {
      setYamlFile(DEFAULT_YAML_PATH);
      if (font === "noto-sans") setFont("calibri");
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
    setLogOpen(true);
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
        locale: locale !== "en" ? locale : undefined,
        font,
        cover_letter: true,
        docx: true,
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
    maxBullets, maxJobs, locale, font, handleJobDone,
  ]);

  const handleBoostRerun = useCallback(() => {
    setTailor(true);
    setBoost(true);
    setUseLlm(true);
    handleRun({ tailor: true, boost: true, useLlm: true });
  }, [handleRun]);

  const recruiterFiles = outputFiles.filter((f) => MAIN_FILE_TYPES.has(f.type));
  const hasJd = jdText.trim().length > 0;
  const mainFiles = recruiterFiles.filter((f) => f.type !== "ats-report" && f.type !== "bullet-diff");

  return (
    <Box>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Box
        sx={{
          display: "flex",
          gap: 3,
          alignItems: "flex-start",
          flexDirection: { xs: "column", lg: "row" },
        }}
      >
        {/* ── Left column: settings ─────────────────────────────────────── */}
        <Box
          sx={{
            width: { xs: "100%", lg: 400 },
            flexShrink: 0,
            position: { lg: "sticky" },
            top: 84,
          }}
        >
          <Card variant="outlined" sx={{ mb: 2 }}>
            <CardHeader
              title="Target & Profile"
              subheader="Who is this resume for, and which source/profile to use."
            />
            <CardContent sx={{ pt: 1 }}>
              <Stack spacing={2}>
                <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>
                  <TextField
                    label="Company"
                    size="small"
                    placeholder="e.g. Best IT Consulting"
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    disabled={running}
                    fullWidth
                  />
                  <TextField
                    label="Role"
                    size="small"
                    placeholder="e.g. Senior AI Engineer"
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    disabled={running}
                    fullWidth
                  />
                </Stack>
                <Stack direction="row" spacing={1.5} alignItems="center" flexWrap="wrap">
                  <Box sx={{ flex: "1 1 180px", minWidth: 0 }}>
                    <YamlSelector value={yamlFile} onChange={setYamlFile} disabled={running} />
                  </Box>
                  <ToggleButtonGroup value={locale} exclusive onChange={handleLocaleChange} size="small">
                    <ToggleButton value="en" disabled={running}>EN</ToggleButton>
                    <ToggleButton value="zh-CN" disabled={running}>中文</ToggleButton>
                  </ToggleButtonGroup>
                </Stack>
              </Stack>
            </CardContent>
          </Card>

          <Card variant="outlined" sx={{ mb: 2 }}>
            <CardHeader
              title="Style & Options"
              subheader="Template, bullet density, and AI-assisted passes."
            />
            <CardContent sx={{ pt: 1 }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                Template
              </Typography>
              <Box
                sx={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
                  gap: 1,
                  mt: 1,
                  mb: 2,
                }}
              >
                {themes.map((t) => (
                  <ThemeCard
                    key={t.id}
                    theme={t}
                    selected={selectedTheme === t.id}
                    disabled={running}
                    compact
                    onClick={() => {
                      themeManualRef.current = true;
                      setSelectedTheme(t.id);
                    }}
                  />
                ))}
              </Box>

              <Stack direction="row" spacing={1.5} sx={{ mb: 2 }}>
                <TextField
                  label="Max bullets / job"
                  type="number"
                  size="small"
                  sx={{ width: 140 }}
                  value={maxBullets}
                  onChange={(e) => setMaxBullets(Number(e.target.value) || 4)}
                  inputProps={{ min: 1, max: 8 }}
                  disabled={running}
                />
                <TextField
                  label="Max jobs"
                  type="number"
                  size="small"
                  sx={{ width: 110 }}
                  value={maxJobs}
                  onChange={(e) => setMaxJobs(Number(e.target.value) || 5)}
                  inputProps={{ min: 1, max: 10 }}
                  disabled={running}
                />
              </Stack>

              <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mb: 2 }}>
                <TextField
                  select
                  label="Font"
                  size="small"
                  sx={{ minWidth: 230 }}
                  value={font}
                  onChange={(e) => setFont(e.target.value)}
                  disabled={running}
                  helperText="Applied to PDF + DOCX"
                >
                  {fonts.map((f) => (
                    <MenuItem key={f.id} value={f.id}>{f.label}</MenuItem>
                  ))}
                </TextField>
              </Stack>

              <Divider sx={{ my: 1.5 }} />
              <Stack spacing={1}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <AutoAwesomeIcon fontSize="small" sx={{ color: "secondary.main" }} />
                  <Typography variant="subtitle2" sx={{ flex: 1 }}>
                    AI-assisted passes
                  </Typography>
                  <FormControlLabel
                    control={<Checkbox size="small" checked={useLlm} onChange={(e) => setUseLlm(e.target.checked)} disabled={running} />}
                    label={<Typography variant="body2">LLM</Typography>}
                    sx={{ m: 0 }}
                  />
                </Stack>
                <ToggleButtonGroup
                  value={llmProvider}
                  exclusive
                  onChange={(_, v) => v !== null && setLlmProvider(v)}
                  size="small"
                  fullWidth
                  disabled={!useLlm || running}
                >
                  <ToggleButton value="">default</ToggleButton>
                  <ToggleButton value="deepseek">DeepSeek</ToggleButton>
                  <ToggleButton value="kimi">Kimi</ToggleButton>
                  <ToggleButton value="minimax">MiniMax</ToggleButton>
                </ToggleButtonGroup>
                <Stack direction="row" spacing={1.5} flexWrap="wrap">
                  <FormControlLabel
                    control={<Checkbox size="small" checked={enhance} onChange={(e) => setEnhance(e.target.checked)} disabled={running} />}
                    label="Enhance"
                    sx={{ m: 0 }}
                  />
                  <FormControlLabel
                    control={<Checkbox size="small" checked={tailor} onChange={(e) => setTailor(e.target.checked)} disabled={running} />}
                    label="Tailor"
                    sx={{ m: 0 }}
                  />
                  <FormControlLabel
                    control={<Checkbox size="small" checked={boost} onChange={(e) => setBoost(e.target.checked)} disabled={running} />}
                    label="Boost"
                    sx={{ m: 0 }}
                  />
                </Stack>
              </Stack>

              <Divider sx={{ my: 1.5 }} />
              <Stack spacing={0.5}>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                  Always generated
                </Typography>
                <Stack direction="row" spacing={0.5} flexWrap="wrap">
                  <Chip size="small" icon={<PictureAsPdfIcon />} label="PDF" variant="outlined" />
                  <Chip size="small" icon={<DescriptionIcon />} label="DOCX" variant="outlined" />
                  <Chip size="small" icon={<TextSnippetIcon />} label="Cover letter" variant="outlined" />
                </Stack>
              </Stack>
            </CardContent>
          </Card>

          <Button
            variant="contained"
            size="large"
            fullWidth
            startIcon={running ? <CircularProgress size={18} color="inherit" /> : <PlayArrowIcon />}
            onClick={() => handleRun()}
            disabled={running}
            sx={{ py: 1.2, boxShadow: "0 6px 18px rgba(31,56,100,0.25)" }}
          >
            {running ? "Building…" : "Build Resume"}
          </Button>
          <Typography variant="caption" color="text.secondary" sx={{ display: "block", textAlign: "center", mt: 1 }}>
            Outputs: PDF · DOCX · Cover letter{hasJd ? " · ATS score" : ""}
          </Typography>
        </Box>

        {/* ── Right column: JD + results ────────────────────────────────── */}
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Card variant="outlined" sx={{ mb: 2 }}>
            <CardHeader
              title="Job Description"
              subheader={
                hasJd
                  ? `${jdText.length.toLocaleString()} chars — analysis & preview update automatically`
                  : "Optional — paste or upload a JD to get ATS analysis and a tailored build."
              }
              action={
                jdAnalysis ? (
                  <Chip
                    size="small"
                    color="success"
                    variant="outlined"
                    label={`${jdAnalysis.matched_skills?.length ?? 0} skills matched`}
                  />
                ) : undefined
              }
            />
            <CardContent sx={{ pt: 1 }}>
              <JdInput
                value={jdText}
                onChange={setJdText}
                onKeywords={setKeywords}
                onAnalysis={setJdAnalysis}
                yamlFile={yamlFile}
                disabled={running}
              />

              {jdAnalysis && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    JD Analysis
                  </Typography>
                  <JdAnalysisPanel analysis={jdAnalysis} />
                  {keywords.length > 0 && <TagChips keywords={keywords} />}
                </Box>
              )}

              {composePreview && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Bullet Composition Preview
                  </Typography>
                  <BulletPreviewPanel preview={composePreview} loading={previewLoading} />
                </Box>
              )}
            </CardContent>
          </Card>

          <Card variant="outlined">
            <CardHeader
              title="Results"
              subheader={
                running
                  ? "Building — this usually takes a few seconds…"
                  : mainFiles.length > 0
                    ? "Recruiter-ready files from the last build"
                    : "Nothing built yet"
              }
              action={
                running ? (
                  <Box sx={{ width: 120 }}>
                    <LinearProgress />
                  </Box>
                ) : undefined
              }
            />
            <CardContent sx={{ pt: 1 }}>
              {mainFiles.length === 0 && !running && (
                <Box
                  sx={{
                    border: "1px dashed #D4DAE4",
                    borderRadius: 2,
                    py: 4,
                    textAlign: "center",
                    color: "text.secondary",
                  }}
                >
                  <DescriptionIcon sx={{ fontSize: 40, opacity: 0.35 }} />
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Your PDF, DOCX, and cover letter will appear here after a build.
                  </Typography>
                </Box>
              )}

              {mainFiles.length > 0 && (
                <Stack spacing={1}>
                  {mainFiles.map((f) => {
                    const downloadUrl =
                      `/api/output/${lastJobId}/download?name=${encodeURIComponent(f.name)}`;
                    return (
                      <Box
                        key={f.name}
                        sx={{
                          display: "flex",
                          alignItems: "center",
                          gap: 1.5,
                          border: "1px solid #E3E8F0",
                          borderRadius: 1.5,
                          px: 1.5,
                          py: 1,
                          bgcolor: "#FAFBFD",
                        }}
                      >
                        {fileIcon(f.type)}
                        <Box sx={{ flex: 1, minWidth: 0 }}>
                          <Typography variant="body2" noWrap sx={{ fontWeight: 600 }}>
                            {f.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {f.type.toUpperCase()} · {(f.size / 1024).toFixed(1)} KB
                          </Typography>
                        </Box>
                        <Tooltip title="Download">
                          <IconButton
                            size="small"
                            component="a"
                            href={downloadUrl}
                            target="_blank"
                            sx={{ border: "1px solid #E3E8F0", bgcolor: "background.paper" }}
                          >
                            <DownloadIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    );
                  })}
                </Stack>
              )}

              {atsReport && (
                <Box sx={{ mt: 2 }}>
                  <AtsScoreWidget
                    report={atsReport}
                    before={bulletDiff?.before_ats ?? null}
                    delta={bulletDiff?.delta ?? null}
                    onBoostRerun={hasJd ? handleBoostRerun : undefined}
                    boostRunning={running}
                  />
                </Box>
              )}

              {bulletDiff && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Bullet Changes
                  </Typography>
                  <BulletDiffView diff={bulletDiff} />
                </Box>
              )}

              <Divider sx={{ my: 2 }} />

              <Stack direction="row" spacing={1} alignItems="center">
                <TerminalIcon fontSize="small" sx={{ color: "text.secondary" }} />
                <Typography variant="subtitle2" sx={{ flex: 1 }}>
                  Build Log
                </Typography>
                {logLines.length > 0 && (
                  <Typography variant="caption" color="text.secondary">
                    {logLines.length} lines
                  </Typography>
                )}
                <Button size="small" onClick={() => setLogOpen((v) => !v)}>
                  {logOpen ? "Hide" : "Show"}
                </Button>
              </Stack>
              <Collapse in={logOpen}>
                <Box sx={{ mt: 1 }}>
                  <LogStream lines={logLines} onClear={() => setLogLines([])} />
                </Box>
              </Collapse>
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Box>
  );
}
