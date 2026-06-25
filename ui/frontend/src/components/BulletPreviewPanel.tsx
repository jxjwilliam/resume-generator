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
import type { ComposePreviewResult } from "../types";

interface Props {
  preview: ComposePreviewResult | null;
  loading?: boolean;
}

export default function BulletPreviewPanel({ preview, loading }: Props) {
  if (loading) {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
        Loading composition preview…
      </Typography>
    );
  }
  if (!preview || preview.jobs.length === 0) return null;

  return (
    <Box sx={{ mt: 2, mb: 2, p: 1.5, bgcolor: "grey.50", borderRadius: 1, border: "1px solid", borderColor: "grey.200" }}>
      <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }} flexWrap="wrap" useFlexGap>
        <Typography variant="subtitle2">Composition Preview</Typography>
        <Chip label={`${preview.jobs_included} jobs`} size="small" variant="outlined" />
        <Chip label={`${preview.bullets_included} included`} size="small" color="success" variant="outlined" />
        {preview.bullets_excluded > 0 && (
          <Chip label={`${preview.bullets_excluded} excluded`} size="small" color="default" variant="outlined" />
        )}
      </Stack>

      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell sx={{ width: 90 }}>Status</TableCell>
            <TableCell sx={{ width: 130 }}>Job</TableCell>
            <TableCell sx={{ width: 50 }}>Score</TableCell>
            <TableCell>Bullet</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {preview.jobs.map((job) =>
            job.bullets.map((b, i) => (
              <TableRow
                key={`${job.company}-${i}`}
                sx={{ opacity: b.included && job.job_included ? 1 : 0.55 }}
              >
                <TableCell>
                  {!job.job_included ? (
                    <Chip label="job cut" size="small" color="warning" variant="outlined" />
                  ) : b.included ? (
                    <Chip label="in" size="small" color="success" variant="outlined" />
                  ) : (
                    <Chip label="out" size="small" variant="outlined" />
                  )}
                </TableCell>
                <TableCell>
                  {i === 0 && (
                    <>
                      <Typography variant="body2">{job.company}</Typography>
                      <Typography variant="caption" color="text.secondary">{job.title}</Typography>
                    </>
                  )}
                </TableCell>
                <TableCell>
                  <Typography variant="caption">{b.score}</Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" sx={{ fontSize: "0.8rem" }}>
                    {b.text.length > 120 ? `${b.text.slice(0, 120)}…` : b.text}
                  </Typography>
                </TableCell>
              </TableRow>
            )),
          )}
        </TableBody>
      </Table>
    </Box>
  );
}
