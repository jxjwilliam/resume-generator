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
} from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import ThemeCard from "../components/ThemeCard";
import LogStream from "../components/LogStream";
import JdInput from "../components/JdInput";
import YamlSelector from "../components/YamlSelector";
import TagChips from "../components/TagChips";
import { api } from "../api/client";
import type { ThemeInfo, LogLine } from "../types";

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
  const [useLlm, setUseLlm] = useState(true);
  const [allFormats, setAllFormats] = useState(false);
  const [running, setRunning] = useState(false);
  const [logLines, setLogLines] = useState<LogLine[]>([]);
  const [error, setError] = useState("");

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
        all_formats: allFormats,
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
  }, [yamlFile, company, role, selectedTheme, jdText, useLlm, allFormats, onRefreshHistory]);

  return (
    <Box>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Typography variant="subtitle2" gutterBottom>YAML Source</Typography>
      <YamlSelector value={yamlFile} onChange={setYamlFile} />

      <Stack direction="row" spacing={2} sx={{ mt: 2, mb: 2 }}>
        <TextField label="Company" size="small" placeholder="Unknown"
          value={company} onChange={(e) => setCompany(e.target.value)} />
        <TextField label="Role" size="small"
          value={role} onChange={(e) => setRole(e.target.value)} />
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
      <JdInput value={jdText} onChange={setJdText} onKeywords={setKeywords} />
      {keywords.length > 0 && <TagChips keywords={keywords} />}

      <Stack direction="row" spacing={2} sx={{ mt: 2, alignItems: "center" }}>
        <FormControlLabel
          control={<Checkbox checked={useLlm} onChange={(e) => setUseLlm(e.target.checked)} />}
          label="Use LLM"
        />
        <FormControlLabel
          control={<Checkbox checked={allFormats} onChange={(e) => setAllFormats(e.target.checked)} />}
          label="All formats"
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
