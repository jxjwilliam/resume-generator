import {
  Card,
  CardActionArea,
  CardContent,
  Typography,
  Box,
} from "@mui/material";
import type { ThemeInfo } from "../types";

interface Props {
  theme: ThemeInfo;
  selected: boolean;
  onClick: () => void;
  disabled?: boolean;
}

/** Mini SVG layout preview for each rendercv theme */
function ThemePreview({ themeId }: { themeId: string }) {
  const w = 200, h = 110;

  switch (themeId) {
    case "classic":
      return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
          {/* Left sidebar */}
          <rect x="0" y="0" width="65" height={h} fill="#1a3a5c" rx="2" />
          <rect x="10" y="10" width="45" height="6" fill="#4a8bc2" rx="2" />
          <rect x="10" y="22" width="35" height="3" fill="#5a9bd2" rx="1.5" />
          <rect x="10" y="30" width="40" height="2" fill="#3a6a9c" rx="1" />
          <rect x="10" y="36" width="40" height="2" fill="#3a6a9c" rx="1" />
          <rect x="10" y="50" width="45" height="3" fill="#5a9bd2" rx="1.5" />
          <rect x="10" y="58" width="40" height="2" fill="#3a6a9c" rx="1" />
          <rect x="10" y="64" width="40" height="2" fill="#3a6a9c" rx="1" />
          {/* Right content */}
          <rect x="75" y="10" width="110" height="5" fill="#333" rx="2" />
          <rect x="75" y="22" width="100" height="2" fill="#999" rx="1" />
          <rect x="75" y="28" width="100" height="2" fill="#999" rx="1" />
          <rect x="75" y="34" width="100" height="2" fill="#999" rx="1" />
          <rect x="75" y="44" width="90" height="2" fill="#bbb" rx="1" />
          <rect x="75" y="50" width="90" height="2" fill="#bbb" rx="1" />
          <rect x="75" y="60" width="95" height="2" fill="#bbb" rx="1" />
        </svg>
      );
    case "sb2nov":
      return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
          {/* Centered header */}
          <rect x="70" y="8" width="60" height="5" fill="#222" rx="2" />
          <rect x="40" y="16" width="120" height="2" fill="#1976d2" rx="1" />
          <rect x="70" y="22" width="60" height="2" fill="#666" rx="1" />
          {/* Sections */}
          <rect x="10" y="32" width="60" height="3" fill="#333" rx="1.5" />
          <rect x="10" y="40" width="180" height="2" fill="#999" rx="1" />
          <rect x="10" y="46" width="180" height="2" fill="#999" rx="1" />
          <rect x="10" y="52" width="150" height="2" fill="#999" rx="1" />
          <rect x="10" y="62" width="60" height="3" fill="#333" rx="1.5" />
          <rect x="10" y="70" width="180" height="2" fill="#999" rx="1" />
          <rect x="10" y="76" width="180" height="2" fill="#999" rx="1" />
          <rect x="10" y="82" width="120" height="2" fill="#999" rx="1" />
          <rect x="10" y="92" width="50" height="3" fill="#333" rx="1.5" />
          <rect x="10" y="100" width="170" height="2" fill="#999" rx="1" />
        </svg>
      );
    case "moderncv":
      return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
          {/* Color accent bar */}
          <rect x="0" y="0" width={w} height="3" fill="#e67e22" />
          {/* Left column with icon circles */}
          <rect x="8" y="12" width="55" height="4" fill="#333" rx="2" />
          <circle cx="18" cy="28" r="4" fill="#e67e22" />
          <rect x="28" y="26" width="35" height="2" fill="#999" rx="1" />
          <rect x="28" y="32" width="35" height="2" fill="#999" rx="1" />
          <circle cx="18" cy="46" r="4" fill="#e67e22" />
          <rect x="28" y="44" width="35" height="2" fill="#999" rx="1" />
          <rect x="28" y="50" width="35" height="2" fill="#999" rx="1" />
          <circle cx="18" cy="64" r="4" fill="#e67e22" />
          <rect x="28" y="62" width="35" height="2" fill="#999" rx="1" />
          {/* Right content */}
          <rect x="75" y="12" width="110" height="4" fill="#333" rx="2" />
          <rect x="75" y="22" width="100" height="2" fill="#999" rx="1" />
          <rect x="75" y="28" width="100" height="2" fill="#999" rx="1" />
          <rect x="75" y="34" width="90" height="2" fill="#999" rx="1" />
          <rect x="75" y="46" width="110" height="3" fill="#333" rx="1.5" />
          <rect x="75" y="54" width="100" height="2" fill="#bbb" rx="1" />
          <rect x="75" y="60" width="100" height="2" fill="#bbb" rx="1" />
          <rect x="75" y="66" width="80" height="2" fill="#bbb" rx="1" />
          <rect x="75" y="80" width="110" height="3" fill="#333" rx="1.5" />
          <rect x="75" y="88" width="90" height="2" fill="#bbb" rx="1" />
          <rect x="75" y="94" width="90" height="2" fill="#bbb" rx="1" />
          <rect x="75" y="100" width="60" height="2" fill="#bbb" rx="1" />
        </svg>
      );
    case "engineeringresumes":
      return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
          {/* Ultra-minimal layout */}
          <rect x="60" y="6" width="80" height="4" fill="#111" rx="1" />
          <rect x="20" y="14" width="160" height="1" fill="#ccc" />
          <rect x="10" y="22" width="80" height="3" fill="#222" rx="1" />
          <rect x="10" y="30" width="180" height="1.5" fill="#aaa" />
          <rect x="10" y="35" width="180" height="1.5" fill="#aaa" />
          <rect x="10" y="40" width="160" height="1.5" fill="#aaa" />
          <rect x="10" y="52" width="80" height="3" fill="#222" rx="1" />
          <rect x="10" y="60" width="180" height="1.5" fill="#aaa" />
          <rect x="10" y="65" width="180" height="1.5" fill="#aaa" />
          <rect x="10" y="70" width="150" height="1.5" fill="#aaa" />
          <rect x="10" y="82" width="80" height="3" fill="#222" rx="1" />
          <rect x="10" y="90" width="170" height="1.5" fill="#aaa" />
          <rect x="10" y="95" width="120" height="1.5" fill="#aaa" />
          <rect x="10" y="100" width="100" height="1.5" fill="#aaa" />
        </svg>
      );
    default:
      return (
        <Box sx={{ height: h, display: "flex", alignItems: "center", justifyContent: "center", color: "#999" }}>
          <Typography variant="body2">{themeId}</Typography>
        </Box>
      );
  }
}

export default function ThemeCard({ theme, selected, onClick, disabled }: Props) {
  return (
    <Card
      sx={{
        width: 220,
        opacity: disabled ? 0.5 : 1,
        border: selected ? "2px solid #1976d2" : "2px solid transparent",
        bgcolor: selected ? "action.selected" : "background.paper",
        transition: "border-color 0.2s, box-shadow 0.2s",
        ...(selected ? { boxShadow: "0 0 8px rgba(25,118,210,0.3)" } : {}),
      }}
    >
      <CardActionArea onClick={disabled ? undefined : onClick} disabled={disabled}>
        <Box
          sx={{
            height: 110,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            bgcolor: "#fafafa",
            borderBottom: "1px solid #eee",
            overflow: "hidden",
          }}
        >
          <ThemePreview themeId={theme.id} />
        </Box>
        <CardContent sx={{ py: 1.5, "&:last-child": { pb: 1.5 } }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
            {theme.name}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.5 }}>
            {theme.best_for}
          </Typography>
        </CardContent>
      </CardActionArea>
    </Card>
  );
}
