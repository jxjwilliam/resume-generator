import { useState, useCallback } from "react";
import {
  Box,
  Button,
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
import ThemeCard from "../components/ThemeCard";
import LogStream from "../components/LogStream";
import JdInput from "../components/JdInput";
import YamlSelector from "../components/YamlSelector";
import TagChips from "../components/TagChips";
import JdAnalysisPanel from "../components/JdAnalysisPanel";
import { api } from "../api/client";
import type { ThemeInfo, LogLine, JdAnalysisResult } from "../types";

interface Props {
  themes: ThemeInfo[];
  onRefreshHistory: () => void;
}

export default function ResumePage({ themes, onRefreshHistory }: Props) {
  const [yamlFile, setYamlFile] = useState("base.yaml");
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [selectedTheme, setSelectedTheme] = useState("classic");
  const [jdText, setJdText] = useState("");
  const [keywords, setKeywords] = useState<string[]>([]);
  const [jdAnalysis, setJdAnalysis] = useState<JdAnalysisResult | null>(null);
  const [useLlm, setUseLlm] = useState(true);
  const [tailor, setTailor] = useState(false);
  const [boost, setBoost] = useState(false);
  const [maxBullets, setMaxBullets] = useState(4);
  const [maxJobs, setMaxJobs] = useState(5);
  const [allFormats, setAllFormats] = useState(false);
  const [locale, setLocale] = useState("en");
  const [coverLetter, setCoverLetter] = useState(false);
  const [docx, setDocx] = useState(false);
  const [running, setRunning] = useState(false);
  const [logLines, setLogLines] = useState<LogLine[]>([]);
  const [error, setError] = useState("");

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

  const handleRun = useCallback(async () => {
    if (!company.trim()) { setCompany("Unknown"); }
    setError("");
    setRunning(true);
    setLogLines([]);

    try {
      const { job_id } = await api.runResume({
        yaml_file: yamlFile,
        company: company.trim(),
        role: role.trim() || undefined,
        theme: selectedTheme,
        jd_text: jdText || undefined,
        use_llm: useLlm,
        tailor: tailor || undefined,
        boost: boost || undefined,
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

      const poll = setInterval(async () => {
        const detail = await api.getRunDetail(job_id);
        if (detail.status !== "running") {
          clearInterval(poll);
          setRunning(false);
          onRefreshHistory();
        }
      }, 1000);
    } catch (e: any) {
      setError(e.message);
      setRunning(false);
    }
  }, [yamlFile, company, role, selectedTheme, jdText, useLlm, tailor, boost, maxBullets, maxJobs, allFormats, locale, coverLetter, docx, onRefreshHistory]);

  return (
    <Box>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Typography variant="subtitle2" gutterBottom>YAML Source</Typography>
      <YamlSelector value={yamlFile} onChange={setYamlFile} />

      <Stack direction="row" spacing={2} sx={{ mt: 2, mb: 2, alignItems: "center" }}>
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
            onClick={() => setSelectedTheme(t.id)}
          />
        ))}
      </Stack>

      <Typography variant="subtitle2" gutterBottom>Job Description</Typography>
      <JdInput value={jdText} onChange={setJdText} onKeywords={setKeywords} onAnalysis={setJdAnalysis} />
      <JdAnalysisPanel analysis={jdAnalysis} />
      {keywords.length > 0 && <TagChips keywords={keywords} />}

      <Stack direction="row" spacing={2} sx={{ mt: 2, alignItems: "center", flexWrap: "wrap" }}>
        <TextField label="Max bullets/job" type="number" size="small" sx={{ width: 130 }}
          value={maxBullets} onChange={(e) => setMaxBullets(Number(e.target.value) || 4)}
          inputProps={{ min: 1, max: 8 }} />
        <TextField label="Max jobs" type="number" size="small" sx={{ width: 110 }}
          value={maxJobs} onChange={(e) => setMaxJobs(Number(e.target.value) || 5)}
          inputProps={{ min: 1, max: 10 }} />
        <FormControlLabel
          control={<Checkbox checked={useLlm} onChange={(e) => setUseLlm(e.target.checked)} />}
          label="Use LLM"
        />
        <FormControlLabel
          control={<Checkbox checked={tailor} onChange={(e) => setTailor(e.target.checked)} />}
          label="Tailor bullets"
        />
        <FormControlLabel
          control={<Checkbox checked={boost} onChange={(e) => setBoost(e.target.checked)} />}
          label="Boost ATS"
        />
        <FormControlLabel
          control={<Checkbox checked={allFormats} onChange={(e) => setAllFormats(e.target.checked)} />}
          label="All formats"
        />
        <FormControlLabel
          control={<Checkbox checked={coverLetter} onChange={(e) => setCoverLetter(e.target.checked)} />}
          label="Cover letter"
        />
        <FormControlLabel
          control={<Checkbox checked={docx} onChange={(e) => setDocx(e.target.checked)} />}
          label="Docx"
        />
        <Button
          variant="contained"
          startIcon={<PlayArrowIcon />}
          onClick={handleRun}
          disabled={running}
        >
          {running ? "Running..." : "Run"}
        </Button>
      </Stack>

      {logLines.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <LogStream lines={logLines} onClear={() => setLogLines([])} />
        </Box>
      )}
    </Box>
  );
}
