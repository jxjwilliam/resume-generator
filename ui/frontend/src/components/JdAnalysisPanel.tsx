import { Box, Chip, Stack, Typography } from "@mui/material";
import type { JdAnalysisResult } from "../types";

interface Props {
  analysis: JdAnalysisResult | null;
}

function ChipRow({
  label,
  items,
  color = "default",
}: {
  label: string;
  items: string[];
  color?: "primary" | "warning" | "secondary" | "default";
}) {
  if (items.length === 0) return null;
  return (
    <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap sx={{ mb: 1 }}>
      <Typography variant="caption" color="text.secondary" sx={{ mr: 0.5, alignSelf: "center" }}>
        {label}
      </Typography>
      {items.map((s) => (
        <Chip key={s} label={s} size="small" color={color} variant="outlined" />
      ))}
    </Stack>
  );
}

export default function JdAnalysisPanel({ analysis }: Props) {
  if (!analysis) return null;

  const titleKw = analysis.title_keywords ?? [];
  const domainKw = analysis.domain_keywords ?? [];
  const softSkills = analysis.soft_skills ?? [];
  const matchedSoft = analysis.matched_soft_skills ?? [];
  const missingSoft = analysis.missing_soft_skills ?? [];
  const matchedDomain = analysis.matched_domain_keywords ?? [];

  return (
    <Box sx={{ mt: 1, mb: 2, p: 1.5, bgcolor: "grey.50", borderRadius: 1 }}>
      {analysis.role_title && (
        <Typography variant="body2" sx={{ mb: 1 }}>
          <strong>Role:</strong> {analysis.role_title}
          {analysis.seniority && analysis.seniority !== "unknown" && (
            <> · <strong>Level:</strong> {analysis.seniority}</>
          )}
          {analysis.domain && (
            <> · <strong>Domain:</strong> {analysis.domain}</>
          )}
        </Typography>
      )}

      <ChipRow label="Hard skills:" items={analysis.hard_skills} color="primary" />
      <ChipRow label="Title / role:" items={titleKw} color="secondary" />
      <ChipRow label="Domain:" items={domainKw} color="secondary" />
      {matchedDomain.length > 0 && (
        <ChipRow label="Domain in resume:" items={matchedDomain} color="primary" />
      )}
      <ChipRow label="Soft skills:" items={softSkills} />

      {analysis.missing_skills.length > 0 && (
        <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap sx={{ mb: 1 }}>
          <Typography variant="caption" color="error" sx={{ mr: 0.5, alignSelf: "center" }}>
            Missing hard:
          </Typography>
          {analysis.missing_skills.map((s) => (
            <Chip key={s} label={s} size="small" color="warning" variant="outlined" />
          ))}
        </Stack>
      )}

      {missingSoft.length > 0 && (
        <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap sx={{ mb: 1 }}>
          <Typography variant="caption" color="text.secondary" sx={{ mr: 0.5, alignSelf: "center" }}>
            Missing soft:
          </Typography>
          {missingSoft.map((s) => (
            <Chip key={s} label={s} size="small" variant="outlined" />
          ))}
        </Stack>
      )}

      {matchedSoft.length > 0 && (
        <ChipRow label="Soft in resume:" items={matchedSoft} color="primary" />
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
