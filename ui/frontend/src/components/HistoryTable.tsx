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
  Typography,
} from "@mui/material";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import ReplayIcon from "@mui/icons-material/Replay";
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
          {item.run_duration_seconds != null
            ? `${item.run_duration_seconds.toFixed(1)}s`
            : "-"}
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell colSpan={7} sx={{ py: 0 }}>
          <Collapse in={open}>
            <Box sx={{ p: 2, display: "flex", gap: 2, alignItems: "center" }}>
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
              </Box>
              <IconButton onClick={() => onReRun(item)} title="Re-run">
                <ReplayIcon />
              </IconButton>
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
