import { useState, useCallback, useRef } from "react";
import { Box, TextareaAutosize, Typography, Alert } from "@mui/material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import { api } from "../api/client";
import type { JdAnalysisResult } from "../types";

interface Props {
  value: string;
  onChange: (text: string) => void;
  onKeywords: (keywords: string[]) => void;
  onAnalysis?: (analysis: JdAnalysisResult | null) => void;
}

export default function JdInput({ value, onChange, onKeywords, onAnalysis }: Props) {
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState("");
  const dragCounter = useRef(0);

  const runAnalysis = useCallback(
    (text: string) => {
      if (text.length <= 50) {
        onAnalysis?.(null);
        return;
      }
      api.analyzeJd(text).then((r) => {
        onKeywords(r.keywords);
        onAnalysis?.(r);
      }).catch(() => onAnalysis?.(null));
    },
    [onKeywords, onAnalysis],
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

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragOver(false);
      dragCounter.current = 0;
      setError("");

      const file = e.dataTransfer.files[0];
      if (!file) return;

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
          matched_skills: result.matched_skills || [],
          missing_skills: result.missing_skills || [],
          top_bullets: result.top_bullets || [],
        });
      } catch (err: any) {
        setError(err.message || "Upload failed.");
      }
    },
    [onChange, onKeywords, onAnalysis]
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

      <Box
        {...dropProps}
        sx={{
          border: "2px dashed",
          borderColor: dragOver ? "primary.main" : "grey.400",
          borderRadius: 1,
          p: 1.5,
          mb: 1,
          textAlign: "center",
          bgcolor: dragOver ? "action.hover" : "transparent",
          transition: "border-color 0.15s, background-color 0.15s",
        }}
      >
        <CloudUploadIcon sx={{ color: "grey.500", mr: 1, verticalAlign: "middle" }} />
        <Typography variant="body2" color="text.secondary" component="span">
          Drop .txt / .pdf here or paste below
        </Typography>
      </Box>
      <TextareaAutosize
        minRows={6}
        maxRows={14}
        placeholder="Paste job description here..."
        value={value}
        onChange={handlePaste}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        style={{ width: "100%", fontFamily: "inherit", fontSize: "0.9rem",
                 padding: "8px", border: "1px solid #ccc", borderRadius: "4px" }}
      />
    </Box>
  );
}
