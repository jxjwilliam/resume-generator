import {
  Box,
  Chip,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import type { BulletDiffReport } from "../types";

interface Props {
  diff: BulletDiffReport;
}

const STATUS_COLOR: Record<string, "success" | "warning" | "error" | "default"> = {
  accepted: "success",
  boosted: "success",
  rejected: "error",
  unchanged: "default",
};

export default function BulletDiffView({ diff }: Props) {
  const changed = diff.bullets.filter(
    (b) => b.status === "accepted" || b.status === "boosted" || b.status === "rejected",
  );

  if (changed.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No bullet changes from tailor/boost pass.
      </Typography>
    );
  }

  return (
    <Box>
      {diff.stats && (
        <Stack direction="row" spacing={1} sx={{ mb: 1.5 }} flexWrap="wrap" useFlexGap>
          {diff.stats.accepted ? (
            <Chip label={`${diff.stats.accepted} accepted`} size="small" color="success" variant="outlined" />
          ) : null}
          {diff.stats.boosted ? (
            <Chip label={`${diff.stats.boosted} boosted`} size="small" color="success" variant="outlined" />
          ) : null}
          {diff.stats.rejected ? (
            <Chip label={`${diff.stats.rejected} rejected`} size="small" color="error" variant="outlined" />
          ) : null}
          {diff.stats.unchanged ? (
            <Chip label={`${diff.stats.unchanged} unchanged`} size="small" variant="outlined" />
          ) : null}
        </Stack>
      )}

      <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
        Review tailored bullets below. Rejected rewrites were blocked by validation and the original text was kept in the PDF.
      </Typography>

      <Table size="small" sx={{ bgcolor: "background.paper" }}>
        <TableHead>
          <TableRow>
            <TableCell sx={{ width: 100 }}>Status</TableCell>
            <TableCell sx={{ width: 140 }}>Job</TableCell>
            <TableCell>Original</TableCell>
            <TableCell>Final (in PDF)</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {changed.map((b) => (
            <TableRow key={b.key} hover>
              <TableCell>
                <Chip
                  label={b.status}
                  size="small"
                  color={STATUS_COLOR[b.status] ?? "default"}
                />
                {b.rejection_reason && (
                  <Typography variant="caption" color="error" display="block" sx={{ mt: 0.5 }}>
                    {b.rejection_reason}
                  </Typography>
                )}
              </TableCell>
              <TableCell>
                <Typography variant="body2">{b.job}</Typography>
                {b.pass && b.pass !== "tailor" && (
                  <Typography variant="caption" color="text.secondary">{b.pass}</Typography>
                )}
              </TableCell>
              <TableCell>
                <Typography variant="body2" sx={{ fontSize: "0.8rem" }}>
                  {b.original}
                </Typography>
              </TableCell>
              <TableCell>
                <Typography
                  variant="body2"
                  sx={{
                    fontSize: "0.8rem",
                    fontWeight: b.final !== b.original ? 600 : 400,
                    color: b.status === "rejected" ? "text.secondary" : "text.primary",
                  }}
                >
                  {b.final}
                </Typography>
                {b.rewritten && b.rewritten !== b.final && (
                  <Typography variant="caption" color="error" display="block">
                    LLM: {b.rewritten}
                  </Typography>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Box>
  );
}
