import { Box, Chip, Stack, Typography } from "@mui/material";
import type { JdAnalysisResult } from "../types";

interface Props {
  analysis: JdAnalysisResult | null;
}

export default function JdAnalysisPanel({ analysis }: Props) {
  if (!analysis) return null;

  return (
    <Box sx={{ mt: 1, mb: 2, p: 1.5, bgcolor: "grey.50", borderRadius: 1 }}>
      {analysis.role_title && (
        <Typography variant="body2" sx={{ mb: 1 }}>
          <strong>Role:</strong> {analysis.role_title}
          {analysis.seniority && analysis.seniority !== "unknown" && (
            <> · <strong>Level:</strong> {analysis.seniority}</>
          )}
        </Typography>
      )}

      {analysis.hard_skills.length > 0 && (
        <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap sx={{ mb: 1 }}>
          <Typography variant="caption" color="text.secondary" sx={{ mr: 0.5, alignSelf: "center" }}>
            Hard skills:
          </Typography>
          {analysis.hard_skills.map((s) => (
            <Chip key={s} label={s} size="small" color="primary" variant="outlined" />
          ))}
        </Stack>
      )}

      {analysis.missing_skills.length > 0 && (
        <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap sx={{ mb: 1 }}>
          <Typography variant="caption" color="error" sx={{ mr: 0.5, alignSelf: "center" }}>
            Missing:
          </Typography>
          {analysis.missing_skills.map((s) => (
            <Chip key={s} label={s} size="small" color="warning" variant="outlined" />
          ))}
        </Stack>
      )}

      {analysis.top_bullets.length > 0 && (
        <Box>
          <Typography variant="caption" color="text.secondary">Top matching bullets:</Typography>
          {analysis.top_bullets.slice(0, 4).map((b, i) => (
            <Typography key={i} variant="caption" display="block" sx={{ ml: 1 }}>
              [{b.score}] {b.job}: {b.text.slice(0, 80)}{b.text.length > 80 ? "…" : ""}
            </Typography>
          ))}
        </Box>
      )}
    </Box>
  );
}
