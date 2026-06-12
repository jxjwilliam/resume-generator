import { useState, useCallback, useEffect } from "react";
import {
  Box,
  Button,
  FormControlLabel,
  Checkbox,
  TextField,
  Stack,
  Typography,
  Alert,
} from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import LogStream from "../components/LogStream";
import JdInput from "../components/JdInput";
import YamlSelector from "../components/YamlSelector";
import TagChips from "../components/TagChips";
import RxTemplateCard from "../components/RxTemplateCard";
import { api } from "../api/client";
import type { LogLine, RxTemplateInfo } from "../types";

interface Props {
  onRefreshHistory: () => void;
}

export default function TransformPage({ onRefreshHistory }: Props) {
  const [yamlFile, setYamlFile] = useState("base.yaml");
  const [jdText, setJdText] = useState("");
  const [keywords, setKeywords] = useState<string[]>([]);
  const [templates, setTemplates] = useState<RxTemplateInfo[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState("kakuna");
  const [resumeId, setResumeId] = useState("");
  const [useLlm, setUseLlm] = useState(true);
  const [generatePdf, setGeneratePdf] = useState(false);
  const [running, setRunning] = useState(false);
  const [logLines, setLogLines] = useState<LogLine[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.listRxTemplates().then(setTemplates).catch(() => {});
  }, []);

  const handleRun = useCallback(async () => {
    if (!jdText.trim()) { setError("JD text is required"); return; }
    setError("");
    setRunning(true);
    setLogLines([]);

    try {
      const { job_id } = await api.runTransform({
        yaml_file: yamlFile,
        jd_text: jdText,
        tags: keywords,
        template: selectedTemplate,
        resume_id: resumeId.trim() || undefined,
        use_llm: useLlm,
        generate_pdf: generatePdf,
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
  }, [yamlFile, jdText, keywords, selectedTemplate, resumeId, useLlm, generatePdf, onRefreshHistory]);

  return (
    <Box>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Typography variant="subtitle2" gutterBottom>YAML Source</Typography>
      <YamlSelector value={yamlFile} onChange={setYamlFile} />

      <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
        RxResume Template
      </Typography>
      <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: "wrap" }}>
        {templates.map((t) => (
          <RxTemplateCard
            key={t.id}
            template={t}
            selected={selectedTemplate === t.id}
            onClick={() => setSelectedTemplate(t.id)}
          />
        ))}
      </Stack>

      <Stack direction="row" spacing={2} sx={{ mt: 2, mb: 2 }} alignItems="center">
        <TextField label="RxResume Resume ID (optional)" size="small"
          placeholder="Leave empty to create new"
          value={resumeId} onChange={(e) => setResumeId(e.target.value)}
          sx={{ minWidth: 300 }}
        />
      </Stack>

      <Typography variant="subtitle2" gutterBottom>
        Job Description
      </Typography>
      <JdInput value={jdText} onChange={setJdText} onKeywords={setKeywords} />
      {keywords.length > 0 && <TagChips keywords={keywords} />}

      <Stack direction="row" spacing={3} sx={{ mt: 2, alignItems: "center" }}>
        <FormControlLabel
          control={<Checkbox checked={useLlm} onChange={(e) => setUseLlm(e.target.checked)} />}
          label="Use LLM"
        />
        <FormControlLabel
          control={<Checkbox checked={generatePdf} onChange={(e) => setGeneratePdf(e.target.checked)} />}
          label="Generate PDF too"
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
