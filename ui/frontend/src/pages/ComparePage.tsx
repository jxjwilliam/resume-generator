import { useState, useCallback } from "react";
import {
  Box,
  Button,
  TextField,
  Stack,
  Typography,
  Alert,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Chip,
  IconButton,
} from "@mui/material";
import CompareArrowsIcon from "@mui/icons-material/CompareArrows";
import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import { api } from "../api/client";
import type { JdCompareResult } from "../types";

interface JdSlot {
  id: number;
  label: string;
  text: string;
}

let nextId = 1;

export default function ComparePage() {
  const [slots, setSlots] = useState<JdSlot[]>([
    { id: nextId++, label: "Role A", text: "" },
    { id: nextId++, label: "Role B", text: "" },
  ]);
  const [result, setResult] = useState<JdCompareResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const updateSlot = (id: number, field: "label" | "text", value: string) => {
    setSlots((prev) => prev.map((s) => (s.id === id ? { ...s, [field]: value } : s)));
  };

  const addSlot = () => {
    if (slots.length >= 5) return;
    setSlots((prev) => [...prev, { id: nextId++, label: `Role ${String.fromCharCode(65 + prev.length)}`, text: "" }]);
  };

  const removeSlot = (id: number) => {
    if (slots.length <= 2) return;
    setSlots((prev) => prev.filter((s) => s.id !== id));
  };

  const handleCompare = useCallback(async () => {
    setError("");
    setResult(null);
    const filled = slots.filter((s) => s.text.trim().length > 30);
    if (filled.length < 2) {
      setError("Paste at least 2 job descriptions (30+ chars each).");
      return;
    }
    setLoading(true);
    try {
      const data = await api.compareJds(
        filled.map((s) => ({ label: s.label || "JD", text: s.text })),
      );
      setResult(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [slots]);

  return (
    <Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Compare your resume fit against 2–5 roles. Rankings use the same ATS scorer as the build pipeline.
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Stack spacing={2}>
        {slots.map((slot) => (
          <Paper key={slot.id} variant="outlined" sx={{ p: 2 }}>
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
              <TextField
                label="Label"
                size="small"
                value={slot.label}
                onChange={(e) => updateSlot(slot.id, "label", e.target.value)}
                sx={{ width: 160 }}
              />
              {slots.length > 2 && (
                <IconButton size="small" onClick={() => removeSlot(slot.id)} aria-label="Remove">
                  <DeleteIcon fontSize="small" />
                </IconButton>
              )}
            </Stack>
            <TextField
              multiline
              minRows={4}
              maxRows={10}
              fullWidth
              placeholder="Paste job description..."
              value={slot.text}
              onChange={(e) => updateSlot(slot.id, "text", e.target.value)}
              size="small"
            />
          </Paper>
        ))}
      </Stack>

      <Stack direction="row" spacing={2} sx={{ mt: 2, alignItems: "center" }}>
        <Button startIcon={<AddIcon />} onClick={addSlot} disabled={slots.length >= 5}>
          Add JD
        </Button>
        <Button
          variant="contained"
          startIcon={<CompareArrowsIcon />}
          onClick={handleCompare}
          disabled={loading}
        >
          {loading ? "Comparing..." : "Compare Fit"}
        </Button>
      </Stack>

      {result && (
        <Box sx={{ mt: 3 }}>
          <Alert severity="success" sx={{ mb: 2 }}>
            Recommended apply first: <strong>{result.recommended}</strong> (score {result.best_score})
          </Alert>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>#</TableCell>
                <TableCell>Score</TableCell>
                <TableCell>Grade</TableCell>
                <TableCell>Role</TableCell>
                <TableCell>JD</TableCell>
                <TableCell>Missing skills</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {result.rankings.map((row, i) => (
                <TableRow key={row.label} selected={i === 0}>
                  <TableCell>{i + 1}</TableCell>
                  <TableCell><strong>{row.total}</strong></TableCell>
                  <TableCell>{row.grade}</TableCell>
                  <TableCell>{row.role_title?.slice(0, 40) || "—"}</TableCell>
                  <TableCell>{row.label}</TableCell>
                  <TableCell>
                    {row.missing_skills.slice(0, 4).map((s) => (
                      <Chip key={s} label={s} size="small" color="warning" variant="outlined" sx={{ mr: 0.5, mb: 0.5 }} />
                    ))}
                    {row.missing_skills.length === 0 && (
                      <Chip label="full match" size="small" color="success" variant="outlined" />
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Box>
      )}
    </Box>
  );
}
