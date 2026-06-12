import { useState, useCallback } from "react";
import { Box, TextareaAutosize, Typography } from "@mui/material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import { api } from "../api/client";

interface Props {
  value: string;
  onChange: (text: string) => void;
  onKeywords: (keywords: string[]) => void;
}

export default function JdInput({ value, onChange, onKeywords }: Props) {
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (!file) return;
      const result = await api.uploadJd(file);
      onChange(result.text);
      onKeywords(result.keywords);
    },
    [onChange, onKeywords]
  );

  const handlePaste = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const text = e.target.value;
      onChange(text);
      if (text.length > 50) {
        api.analyzeJd(text).then((r) => onKeywords(r.keywords)).catch(() => {});
      }
    },
    [onChange, onKeywords]
  );

  return (
    <Box>
      <Box
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        sx={{
          border: "2px dashed",
          borderColor: dragOver ? "primary.main" : "grey.400",
          borderRadius: 1,
          p: 1,
          mb: 1,
          textAlign: "center",
          bgcolor: dragOver ? "action.hover" : "transparent",
        }}
      >
        <CloudUploadIcon sx={{ color: "grey.500", mr: 1 }} />
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
        style={{ width: "100%", fontFamily: "inherit", fontSize: "0.9rem",
                 padding: "8px", border: "1px solid #ccc", borderRadius: "4px" }}
      />
    </Box>
  );
}
