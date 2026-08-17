import { useEffect, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip as MuiChip,
  IconButton,
  Collapse,
  Box,
  Stack,
  Typography,
} from "@mui/material";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import ReplayIcon from "@mui/icons-material/Replay";
import DescriptionIcon from "@mui/icons-material/Description";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";
import TextSnippetIcon from "@mui/icons-material/TextSnippet";
import AssessmentIcon from "@mui/icons-material/Assessment";
import { api } from "../api/client";
import type { RunHistoryItem } from "../types";

interface Props {
  onReRun: (item: RunHistoryItem) => void;
  refreshKey: number;
}

function statusColor(status: string): "success" | "error" | "warning" | "default" {
  switch (status) {
    case "success": return "success";
    case "error": return "error";
    case "running": return "warning";
    default: return "default";
  }
}

function fileIcon(type: string) {
  switch (type) {
    case "pdf": return <PictureAsPdfIcon fontSize="small" />;
    case "cover-letter": return <TextSnippetIcon fontSize="small" />;
    case "ats-report":
    case "bullet-diff": return <AssessmentIcon fontSize="small" />;
    default: return <DescriptionIcon fontSize="small" />;
  }
}

function Row({ item, onReRun }: { item: RunHistoryItem; onReRun: (i: RunHistoryItem) => void }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <TableRow hover>
        <TableCell>
          <IconButton size="small" onClick={() => setOpen(!open)}>
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell>{item.created_at.slice(0, 10)}</TableCell>
        <TableCell><MuiChip label={item.type} size="small" /></TableCell>
        <TableCell>{item.company || "-"}</TableCell>
        <TableCell>{item.role || "-"}</TableCell>
        <TableCell>
          <MuiChip label={item.status} color={statusColor(item.status)} size="small" />
        </TableCell>
        <TableCell>
          {item.ats_score != null ? (
            <MuiChip
              label={`${item.ats_score} (${item.ats_grade || "?"})`}
              size="small"
              color={item.ats_score >= 75 ? "success" : item.ats_score >= 65 ? "warning" : "default"}
              variant="outlined"
            />
          ) : "-"}
        </TableCell>
        <TableCell>
          {item.run_duration_seconds != null
            ? `${item.run_duration_seconds.toFixed(1)}s`
            : "-"}
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell colSpan={8} sx={{ py: 0 }}>
          <Collapse in={open}>
            <Box sx={{ p: 2 }}>
              <Stack direction="row" spacing={2} alignItems="flex-start">
                <Box flex={1}>
                  <Typography variant="caption" color="text.secondary">
                    JD snippet: {item.jd_snippet || "(none)"}
                  </Typography>
                  {item.tags && (
                    <Typography variant="caption" display="block" color="text.secondary">
                      Tags: {item.tags}
                    </Typography>
                  )}
                  {item.error_log && (
                    <Typography variant="caption" display="block" color="error">
                      Error: {item.error_log}
                    </Typography>
                  )}
                  {item.output_files && item.output_files.length > 0 && (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="caption" display="block" color="text.secondary" sx={{ mb: 0.5 }}>
                        Output files:
                      </Typography>
                      <Stack direction="row" spacing={0.5} flexWrap="wrap">
                        {item.output_files
                          .filter((f) =>
                            ["pdf", "docx", "cover-letter", "ats-report", "bullet-diff"].includes(f.type),
                          )
                          .map((f) => (
                          <MuiChip
                            key={f.name}
                            icon={fileIcon(f.type)}
                            label={`${f.name} (${(f.size / 1024).toFixed(0)} KB)`}
                            component="a"
                            href={`/api/output/${item.id}/download?name=${encodeURIComponent(f.name)}`}
                            target="_blank"
                            clickable
                            size="small"
                            variant="outlined"
                            color={f.type === "pdf" ? "error" : f.type === "cover-letter" ? "info" : "default"}
                            sx={{ cursor: "pointer" }}
                          />
                        ))}
                      </Stack>
                    </Box>
                  )}
                </Box>
                <IconButton onClick={() => onReRun(item)} title="Re-run">
                  <ReplayIcon />
                </IconButton>
              </Stack>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
}

export default function HistoryTable({ onReRun, refreshKey }: Props) {
  const [runs, setRuns] = useState<RunHistoryItem[]>([]);

  useEffect(() => {
    api.getHistory({ limit: 50 }).then((r) => setRuns(r.runs)).catch(() => {});
  }, [refreshKey]);

  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell width={40} />
            <TableCell>Date</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Company</TableCell>
            <TableCell>Role</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>ATS</TableCell>
            <TableCell>Duration</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {runs.map((r) => (
            <Row key={r.id} item={r} onReRun={onReRun} />
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
