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
} from "@mui/material";
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
import { api } from "../api/client";
import type {
  ThemeInfo, OutputFile, LogLine, JdAnalysisResult,
  AtsReport, BulletDiffReport, ComposePreviewResult,
} from "../types";

interface Props {
  themes: ThemeInfo[];
  onRefreshHistory: () => void;
}

// Sync form state with localStorage so user preferences survive reloads
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
  const [yamlFile, setYamlFile] = useStoredState<string>("yamlFile", "base.yaml");
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
  const runPollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Auto-select theme when JD is pasted (until user picks manually)
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

  const handleLocaleChange = (
    _: React.MouseEvent<HTMLElement>,
    newLocale: string | null,
  ) => {
    if (!newLocale) return;
    setLocale(newLocale);
    // Auto-switch YAML file when language changes
    if (newLocale === "zh-CN" && yamlFile === "base.yaml") {
      setYamlFile("base_zh.yaml");
    } else if (newLocale === "en" && yamlFile === "base_zh.yaml") {
      setYamlFile("base.yaml");
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

  const pollRunCompletion = useCallback((job_id: string) => {
    if (runPollRef.current) clearInterval(runPollRef.current);
    runPollRef.current = setInterval(async () => {
      const detail = await api.getRunDetail(job_id);
      if (detail.status !== "running") {
        if (runPollRef.current) clearInterval(runPollRef.current);
        runPollRef.current = null;
        setRunning(false);
        setLastJobId(job_id);
        if (detail.status === "success") {
          try {
            const resp = await api.getOutputFiles(job_id);
            setOutputFiles(resp.files);
            const names = new Set(resp.files.map((f) => f.name));
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
      }
    }, 1000);
  }, [onRefreshHistory]);

  const handleRun = useCallback(async (opts?: { tailor?: boolean; boost?: boolean; useLlm?: boolean }) => {
    if (!company.trim()) { setCompany("Unknown"); }
    setError("");
    setRunning(true);
    setLogLines([]);
    setOutputFiles([]);
    setLastJobId(null);
    setAtsReport(null);
    setBulletDiff(null);

    const runTailor = opts?.tailor ?? tailor;
    const runBoost = opts?.boost ?? boost;
    const runLlm = opts?.useLlm ?? useLlm;

    try {
      const { job_id } = await api.runResume({
        yaml_file: yamlFile,
        company: company.trim(),
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

      api.streamLogs(job_id, (line) => {
        setLogLines((prev) => [...prev, line]);
      });

      pollRunCompletion(job_id);
    } catch (e: any) {
      setError(e.message);
      setRunning(false);
    }
  }, [
    yamlFile, company, role, selectedTheme, jdText, useLlm, tailor, boost,
    maxBullets, maxJobs, allFormats, locale, coverLetter, docx, pollRunCompletion,
  ]);

  const handleBoostRerun = useCallback(() => {
    setTailor(true);
    setBoost(true);
    setUseLlm(true);
    handleRun({ tailor: true, boost: true, useLlm: true });
  }, [handleRun]);

  return (
    <Box>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Stack direction="row" spacing={1.5} sx={{ mt: 1, mb: 2, alignItems: "center", flexWrap: "wrap" }}>
        <Typography variant="subtitle2">YAML:</Typography>
        <YamlSelector value={yamlFile} onChange={setYamlFile} />
        <Box sx={{ flexGrow: 0, width: 16 }} />
        <Typography variant="body2" color="text.secondary">LLM:</Typography>
        <ToggleButtonGroup
          value={llmProvider}
          exclusive
          onChange={(_, v) => v !== null && setLlmProvider(v)}
          size="small"
        >
          <ToggleButton value="">default</ToggleButton>
          <ToggleButton value="deepseek">DeepSeek</ToggleButton>
          <ToggleButton value="kimi">Kimi</ToggleButton>
          <ToggleButton value="minimax">MiniMax</ToggleButton>
        </ToggleButtonGroup>
        <FormControlLabel
          control={<Checkbox size="small" checked={enhance} onChange={(e) => setEnhance(e.target.checked)} />}
          label="Enhance"
        />
        <FormControlLabel
          control={<Checkbox size="small" checked={tailor} onChange={(e) => setTailor(e.target.checked)} />}
          label="Tailor"
        />
        <FormControlLabel
          control={<Checkbox size="small" checked={boost} onChange={(e) => setBoost(e.target.checked)} />}
          label="Boost"
        />
        <Box sx={{ flexGrow: 1 }} />
        <Button
          variant="contained"
          size="small"
          startIcon={<PlayArrowIcon />}
          onClick={() => handleRun()}
          disabled={running}
        >
          {running ? "Running..." : "Build"}
        </Button>
      </Stack>

      <Stack direction="row" spacing={2} sx={{ mb: 2, alignItems: "center" }}>
        <TextField label="Company" size="small" placeholder="Unknown"
          value={company} onChange={(e) => setCompany(e.target.value)} />
        <TextField label="Role" size="small"
          value={role} onChange={(e) => setRole(e.target.value)} />
        <Box sx={{ flexGrow: 1 }} />
        <Typography variant="body2" color="text.secondary" sx={{ mr: 1 }}>Language:</Typography>
        <ToggleButtonGroup
          value={locale}
          exclusive
          onChange={handleLocaleChange}
          size="small"
        >
          <ToggleButton value="en">English</ToggleButton>
          <ToggleButton value="zh-CN">中文 (简体)</ToggleButton>
        </ToggleButtonGroup>
      </Stack>

      <Typography variant="subtitle2" gutterBottom>Theme</Typography>
      <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: "wrap" }}>
        {themes.map((t) => (
          <ThemeCard
            key={t.id}
            theme={t}
            selected={selectedTheme === t.id}
            onClick={() => {
              themeManualRef.current = true;
              setSelectedTheme(t.id);
            }}
          />
        ))}
      </Stack>

      <Typography variant="subtitle2" gutterBottom>Job Description</Typography>
      <JdInput
        value={jdText}
        onChange={setJdText}
        onKeywords={setKeywords}
        onAnalysis={setJdAnalysis}
        yamlFile={yamlFile}
      />
      <JdAnalysisPanel analysis={jdAnalysis} />
      <BulletPreviewPanel preview={composePreview} loading={previewLoading} />
      {keywords.length > 0 && <TagChips keywords={keywords} />}

      <Stack direction="row" spacing={2} sx={{ mt: 2, alignItems: "center", flexWrap: "wrap" }}>
        <TextField label="Max bullets/job" type="number" size="small" sx={{ width: 130 }}
          value={maxBullets} onChange={(e) => setMaxBullets(Number(e.target.value) || 4)}
          inputProps={{ min: 1, max: 8 }} />
        <TextField label="Max jobs" type="number" size="small" sx={{ width: 110 }}
          value={maxJobs} onChange={(e) => setMaxJobs(Number(e.target.value) || 5)}
          inputProps={{ min: 1, max: 10 }} />
        <FormControlLabel
          control={<Checkbox size="small" checked={useLlm} onChange={(e) => setUseLlm(e.target.checked)} />}
          label="Use LLM"
        />
        <FormControlLabel
          control={<Checkbox size="small" checked={allFormats} onChange={(e) => setAllFormats(e.target.checked)} />}
          label="All formats"
        />
        <FormControlLabel
          control={<Checkbox size="small" checked={coverLetter} onChange={(e) => setCoverLetter(e.target.checked)} />}
          label="Cover letter"
        />
        <FormControlLabel
          control={<Checkbox size="small" checked={docx} onChange={(e) => setDocx(e.target.checked)} />}
          label="Docx"
        />
      </Stack>

      {logLines.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <LogStream lines={logLines} onClear={() => setLogLines([])} />
        </Box>
      )}

      {outputFiles.length > 0 && (
        <Box sx={{ mt: 2, p: 2, bgcolor: "success.50", borderRadius: 1, border: "1px solid", borderColor: "success.200" }}>
          <Typography variant="subtitle2" gutterBottom sx={{ color: "success.700" }}>
            Generated Output Files
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: atsReport || bulletDiff ? 2 : 0 }}>
            {outputFiles.map((f) => {
              const downloadUrl = `/api/output/${lastJobId}/download?name=${encodeURIComponent(f.name)}`;
              const sizeKb = (f.size / 1024).toFixed(1);
              return (
                <Chip
                  key={f.name}
                  icon={fileIcon(f.type)}
                  label={`${f.name} (${sizeKb} KB)`}
                  component="a"
                  href={downloadUrl}
                  target="_blank"
                  clickable
                  variant="outlined"
                  color={f.type === "pdf" ? "error" : f.type === "cover-letter" ? "info" : "default"}
                  sx={{ cursor: "pointer" }}
                />
              );
            })}
          </Stack>

          {atsReport && (
            <Box sx={{ mb: bulletDiff ? 2 : 0 }}>
              <Typography variant="subtitle2" gutterBottom>ATS Score</Typography>
              <AtsScoreWidget
                report={atsReport}
                before={bulletDiff?.before_ats ?? null}
                delta={bulletDiff?.delta ?? null}
                onBoostRerun={jdText.trim() ? handleBoostRerun : undefined}
                boostRunning={running}
              />
            </Box>
          )}

          {bulletDiff && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>Bullet Changes</Typography>
              <BulletDiffView diff={bulletDiff} />
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
}
