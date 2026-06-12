import { useRef, useEffect } from "react";
import { Box, IconButton, Paper, Typography } from "@mui/material";
import ClearIcon from "@mui/icons-material/Clear";
import type { LogLine } from "../types";

interface Props {
  lines: LogLine[];
  onClear: () => void;
}

const colorMap: Record<string, string> = {
  stdout: "#fff",
  stderr: "#ff9800",
  system: "#9e9e9e",
};

export default function LogStream({ lines, onClear }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  return (
    <Paper
      variant="outlined"
      sx={{
        fontFamily: '"Cascadia Code", "Fira Code", monospace',
        fontSize: "0.8rem",
        bgcolor: "#1e1e1e",
        color: "#d4d4d4",
        p: 1.5,
        maxHeight: 400,
        overflow: "auto",
        position: "relative",
      }}
    >
      <Box sx={{ position: "sticky", top: 0, textAlign: "right" }}>
        <IconButton size="small" onClick={onClear} sx={{ color: "#888" }}>
          <ClearIcon fontSize="small" />
        </IconButton>
      </Box>
      {lines.length === 0 && (
        <Typography variant="body2" sx={{ color: "#666", fontStyle: "italic" }}>
          Waiting for output...
        </Typography>
      )}
      {lines.map((line, i) => (
        <Box key={i} sx={{ color: colorMap[line.source] || "#fff",
          whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
          {line.text}
        </Box>
      ))}
      <div ref={bottomRef} />
    </Paper>
  );
}
