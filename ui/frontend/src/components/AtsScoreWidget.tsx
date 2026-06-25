import { Box, Chip, LinearProgress, Stack, Typography, Button } from "@mui/material";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import type { AtsReport } from "../types";

interface Props {
  report: AtsReport;
  before?: { total: number; grade: string } | null;
  delta?: number | null;
  onBoostRerun?: () => void;
  boostRunning?: boolean;
}

const GRADE_COLOR: Record<string, "success" | "warning" | "error" | "default"> = {
  A: "success",
  B: "success",
  C: "warning",
  D: "warning",
  F: "error",
};

function BreakdownRow({
  label,
  item,
}: {
  label: string;
  item?: { score?: number; max?: number; pct?: number };
}) {
  if (!item?.max) return null;
  const pct = item.max ? ((item.score ?? 0) / item.max) * 100 : 0;
  return (
    <Box sx={{ mb: 1 }}>
      <Stack direction="row" justifyContent="space-between" sx={{ mb: 0.25 }}>
        <Typography variant="caption">{label}</Typography>
        <Typography variant="caption" color="text.secondary">
          {item.score}/{item.max}
          {item.pct != null ? ` (${item.pct}%)` : ""}
        </Typography>
      </Stack>
      <LinearProgress variant="determinate" value={pct} sx={{ height: 6, borderRadius: 1 }} />
    </Box>
  );
}

export default function AtsScoreWidget({ report, before, delta, onBoostRerun, boostRunning }: Props) {
  const missing = report.skill_match?.missing_skills ?? [];
  const matched = report.skill_match?.matched_skills ?? [];

  return (
    <Box sx={{ p: 2, bgcolor: "grey.50", borderRadius: 1, border: "1px solid", borderColor: "grey.200" }}>
      <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 1.5 }}>
        <Typography variant="h4" component="span" sx={{ fontWeight: 700 }}>
          {report.total}
        </Typography>
        <Typography variant="body2" color="text.secondary">/100</Typography>
        <Chip
          label={`Grade ${report.grade}`}
          color={GRADE_COLOR[report.grade] ?? "default"}
          size="small"
        />
        {before && (
          <Typography variant="caption" color="text.secondary">
            was {before.total} ({before.grade})
          </Typography>
        )}
        {delta != null && (
          <Chip
            label={`${delta >= 0 ? "+" : ""}${delta}`}
            size="small"
            color={delta >= 0 ? "success" : "warning"}
            variant="outlined"
          />
        )}
      </Stack>

      {report.role_title && (
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
          vs {report.role_title}
          {report.seniority && report.seniority !== "unknown" ? ` · ${report.seniority}` : ""}
          {report.jobs_included != null ? ` · ${report.jobs_included} jobs, ${report.bullets_included} bullets` : ""}
        </Typography>
      )}

      <BreakdownRow label="Keyword match" item={report.breakdown.keyword_match} />
      <BreakdownRow label="Title alignment" item={report.breakdown.title_alignment} />
      <BreakdownRow label="Completeness" item={report.breakdown.completeness} />
      <BreakdownRow label="Formatting" item={report.breakdown.formatting} />
      <BreakdownRow label="Conciseness" item={report.breakdown.conciseness} />

      {missing.length > 0 && (
        <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap sx={{ mt: 1 }}>
          <Typography variant="caption" color="error" sx={{ alignSelf: "center", mr: 0.5 }}>
            Missing:
          </Typography>
          {missing.map((s) => (
            <Chip key={s} label={s} size="small" color="warning" variant="outlined" />
          ))}
        </Stack>
      )}

      {matched.length > 0 && (
        <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap sx={{ mt: 1 }}>
          <Typography variant="caption" color="text.secondary" sx={{ alignSelf: "center", mr: 0.5 }}>
            Matched:
          </Typography>
          {matched.slice(0, 12).map((s) => (
            <Chip key={s} label={s} size="small" color="primary" variant="outlined" />
          ))}
          {matched.length > 12 && (
            <Typography variant="caption" color="text.secondary">+{matched.length - 12} more</Typography>
          )}
        </Stack>
      )}

      {onBoostRerun && missing.length > 0 && (
        <Box sx={{ mt: 1.5 }}>
          <Button
            size="small"
            variant="outlined"
            color="warning"
            startIcon={<TrendingUpIcon />}
            onClick={onBoostRerun}
            disabled={boostRunning}
          >
            {boostRunning ? "Re-running…" : "Re-run with Tailor + Boost"}
          </Button>
        </Box>
      )}
    </Box>
  );
}
