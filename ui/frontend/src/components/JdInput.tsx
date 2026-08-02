import { useState, useCallback, useRef } from "react";
import { Box, TextareaAutosize, Typography, Alert } from "@mui/material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import { api } from "../api/client";
import { DEFAULT_YAML_PATH } from "../types";
import type { JdAnalysisResult } from "../types";

interface Props {
  value: string;
  onChange: (text: string) => void;
  onKeywords: (keywords: string[]) => void;
  onAnalysis?: (analysis: JdAnalysisResult | null) => void;
  yamlFile?: string;
  disabled?: boolean;
}

export default function JdInput({ value, onChange, onKeywords, onAnalysis, yamlFile = DEFAULT_YAML_PATH, disabled }: Props) {
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState("");
  const dragCounter = useRef(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const runAnalysis = useCallback(
    (text: string) => {
      if (text.length <= 50) {
        onAnalysis?.(null);
        return;
      }
      api.analyzeJd(text, yamlFile).then((r) => {
        onKeywords(r.keywords);
        onAnalysis?.(r);
      }).catch(() => onAnalysis?.(null));
    },
    [onKeywords, onAnalysis, yamlFile],
  );

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current++;
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setDragOver(true);
    }
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current--;
    if (dragCounter.current === 0) {
      setDragOver(false);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const processFile = useCallback(
    async (file: File) => {
      setError("");
      const ext = file.name.toLowerCase();
      if (!ext.endsWith(".txt") && !ext.endsWith(".pdf")) {
        setError("Only .txt and .pdf files are supported.");
        return;
      }
      try {
        const result = await api.uploadJd(file);
        onChange(result.text);
        onKeywords(result.keywords);
        onAnalysis?.({
          keywords: result.keywords,
          hard_skills: result.hard_skills || [],
          title_keywords: result.title_keywords,
          domain_keywords: result.domain_keywords,
          soft_skills: result.soft_skills,
          role_title: result.role_title,
          seniority: result.seniority,
          domain: result.domain,
          matched_skills: result.matched_skills || [],
          missing_skills: result.missing_skills || [],
          matched_soft_skills: result.matched_soft_skills,
          missing_soft_skills: result.missing_soft_skills,
          matched_domain_keywords: result.matched_domain_keywords,
          top_bullets: result.top_bullets || [],
        });
      } catch (err: any) {
        setError(err.message || "Upload failed.");
      }
    },
    [onChange, onKeywords, onAnalysis],
  );

  const handleClickUpload = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) processFile(file);
      // clear so same file can be re-selected
      if (fileInputRef.current) fileInputRef.current.value = "";
    },
    [processFile],
  );

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragOver(false);
      dragCounter.current = 0;
      const file = e.dataTransfer.files[0];
      if (file) processFile(file);
    },
    [processFile],
  );

  const handlePaste = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const text = e.target.value;
      onChange(text);
      setError("");
      runAnalysis(text);
    },
    [onChange, runAnalysis],
  );

  const dropProps = {
    onDragEnter: handleDragEnter,
    onDragLeave: handleDragLeave,
    onDragOver: handleDragOver,
    onDrop: handleDrop,
  };

  return (
    <Box {...dropProps}>
      {error && <Alert severity="error" sx={{ mb: 1 }}>{error}</Alert>}

      <input
        ref={fileInputRef}
        type="file"
        accept=".txt,.pdf"
        style={{ display: "none" }}
        onChange={handleFileChange}
      />
      <Box
        {...(disabled ? {} : dropProps)}
        onClick={disabled ? undefined : handleClickUpload}
        sx={{
          border: "2px dashed",
          borderColor: dragOver ? "primary.main" : "grey.400",
          borderRadius: 1,
          p: 1.5,
          mb: 1,
          textAlign: "center",
          bgcolor: dragOver ? "action.hover" : "transparent",
          opacity: disabled ? 0.5 : 1,
          transition: "border-color 0.15s, background-color 0.15s",
          cursor: disabled ? "default" : "pointer",
          "&:hover": disabled ? {} : { borderColor: "primary.light", bgcolor: "action.hover" },
        }}
      >
        <CloudUploadIcon sx={{ color: "grey.500", mr: 1, verticalAlign: "middle" }} />
        <Typography variant="body2" color="text.secondary" component="span">
          Drop .txt / .pdf here, click to browse, or paste below
        </Typography>
      </Box>
      <TextareaAutosize
        minRows={6}
        maxRows={14}
        placeholder="Paste job description here..."
        value={value}
        onChange={handlePaste}
        disabled={disabled}
        style={{ width: "100%", fontFamily: "inherit", fontSize: "0.9rem",
                 padding: "8px", border: "1px solid #ccc", borderRadius: "4px",
                 opacity: disabled ? 0.5 : 1 }}
      />
    </Box>
  );
}
