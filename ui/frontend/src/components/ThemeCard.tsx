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

/** Accurate SVG thumbnail for each RenderCV v2 theme */
function ThemePreview({ themeId }: { themeId: string }) {
  const w = 200, h = 140;

  switch (themeId) {
    case "auto":
      return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
          <defs>
            <linearGradient id="ag" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#1a3a5c" />
              <stop offset="100%" stopColor="#1976d2" />
            </linearGradient>
          </defs>
          <rect x="10" y="10" width="155" height="100" rx="6" fill="url(#ag)" opacity="0.12" />
          <rect x="60" y="40" width="80" height="6" fill="#333" rx="2" />
          <rect x="50" y="52" width="100" height="3" fill="#999" rx="1.5" />
          <text x="88" y="80" textAnchor="middle" fill="#666" fontSize="10" fontFamily="sans-serif">Auto-select</text>
        </svg>
      );
    case "classic":
      return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
          {/* Left sidebar — dark blue */}
          <rect x="0" y="0" width="55" height={h} fill="#1a3a5c" rx="0" />
          {/* Photo placeholder */}
          <rect x="8" y="8" width="39" height="39" fill="#2a5a8c" rx="4" />
          <rect x="10" y="52" width="35" height="3" fill="#4a8bc2" rx="1.5" />
          <rect x="10" y="58" width="35" height="2" fill="#3a6a9c" rx="1" />
          <rect x="10" y="63" width="30" height="2" fill="#3a6a9c" rx="1" />
          <rect x="10" y="75" width="35" height="3" fill="#4a8bc2" rx="1.5" />
          <rect x="10" y="82" width="35" height="2" fill="#3a6a9c" rx="1" />
          <rect x="10" y="87" width="25" height="2" fill="#3a6a9c" rx="1" />
          {/* Right content — classic serif */}
          <rect x="65" y="10" width="105" height="5" fill="#222" rx="2" />
          <rect x="65" y="20" width="95" height="2" fill="#888" rx="1" />
          <line x1="65" y1="32" x2="170" y2="32" stroke="#bbb" strokeWidth="0.5" />
          <rect x="65" y="38" width="80" height="3" fill="#444" rx="1.5" />
          <rect x="65" y="47" width="105" height="2" fill="#aaa" rx="1" />
          <rect x="65" y="53" width="105" height="2" fill="#aaa" rx="1" />
          <rect x="65" y="59" width="90" height="2" fill="#aaa" rx="1" />
          <line x1="65" y1="70" x2="170" y2="70" stroke="#bbb" strokeWidth="0.5" />
          <rect x="65" y="76" width="80" height="3" fill="#444" rx="1.5" />
          <rect x="65" y="85" width="105" height="2" fill="#aaa" rx="1" />
          <rect x="65" y="91" width="100" height="2" fill="#aaa" rx="1" />
          <rect x="65" y="97" width="80" height="2" fill="#aaa" rx="1" />
        </svg>
      );
    case "sb2nov":
      return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
          {/* Centered name */}
          <rect x="55" y="6" width="65" height="5" fill="#111" rx="2" />
          {/* Blue rule under name */}
          <rect x="30" y="15" width="115" height="1.5" fill="#1976d2" />
          {/* Contact line */}
          <rect x="50" y="21" width="75" height="2" fill="#666" rx="1" />
          {/* Section 1 with full-width line */}
          <line x1="5" y1="34" x2="170" y2="34" stroke="#1976d2" strokeWidth="0.8" />
          <rect x="5" y="31" width="50" height="3" fill="#222" rx="1.5" />
          <rect x="5" y="41" width="165" height="2" fill="#999" rx="1" />
          <rect x="5" y="47" width="165" height="2" fill="#999" rx="1" />
          <rect x="5" y="53" width="140" height="2" fill="#999" rx="1" />
          {/* Section 2 */}
          <line x1="5" y1="64" x2="170" y2="64" stroke="#1976d2" strokeWidth="0.8" />
          <rect x="5" y="61" width="50" height="3" fill="#222" rx="1.5" />
          <rect x="5" y="71" width="165" height="2" fill="#999" rx="1" />
          <rect x="5" y="77" width="165" height="2" fill="#999" rx="1" />
          <rect x="5" y="83" width="120" height="2" fill="#999" rx="1" />
        </svg>
      );
    case "moderncv":
      return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
          {/* Orange accent bar at top */}
          <rect x="0" y="0" width={w} height="4" fill="#e67e22" />
          {/* Left column — info/icons */}
          <rect x="5" y="10" width="50" height="4" fill="#333" rx="2" />
          {/* Icon-style circles with orange accent */}
          <circle cx="12" cy="28" r="4" fill="#e67e22" opacity="0.15" />
          <circle cx="12" cy="28" r="2" fill="#e67e22" />
          <rect x="20" y="26" width="35" height="2" fill="#888" rx="1" />
          <rect x="20" y="31" width="30" height="2" fill="#aaa" rx="1" />
          <circle cx="12" cy="48" r="4" fill="#e67e22" opacity="0.15" />
          <circle cx="12" cy="48" r="2" fill="#e67e22" />
          <rect x="20" y="46" width="35" height="2" fill="#888" rx="1" />
          <rect x="20" y="51" width="30" height="2" fill="#aaa" rx="1" />
          <circle cx="12" cy="68" r="4" fill="#e67e22" opacity="0.15" />
          <circle cx="12" cy="68" r="2" fill="#e67e22" />
          <rect x="20" y="66" width="35" height="2" fill="#888" rx="1" />
          <rect x="20" y="71" width="25" height="2" fill="#aaa" rx="1" />
          {/* Right content — thick orange section lines */}
          <rect x="65" y="10" width="105" height="4" fill="#333" rx="2" />
          <rect x="65" y="19" width="95" height="2" fill="#888" rx="1" />
          <rect x="65" y="25" width="80" height="2" fill="#aaa" rx="1" />
          <rect x="65" y="32" width="90" height="3" fill="#e67e22" rx="1.5" />
          <rect x="65" y="39" width="105" height="2" fill="#aaa" rx="1" />
          <rect x="65" y="45" width="105" height="2" fill="#aaa" rx="1" />
          <rect x="65" y="51" width="80" height="2" fill="#aaa" rx="1" />
          <rect x="65" y="60" width="90" height="3" fill="#e67e22" rx="1.5" />
          <rect x="65" y="67" width="105" height="2" fill="#aaa" rx="1" />
          <rect x="65" y="73" width="95" height="2" fill="#aaa" rx="1" />
          <rect x="65" y="79" width="70" height="2" fill="#aaa" rx="1" />
        </svg>
      );
    case "engineeringresumes":
      return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
          {/* Ultra-compact, minimal spacing, inline layout */}
          <rect x="45" y="4" width="85" height="4" fill="#111" rx="1" />
          <rect x="15" y="12" width="145" height="0.8" fill="#ccc" />
          {/* Section with full line divider */}
          <line x1="5" y1="22" x2="170" y2="22" stroke="#ddd" strokeWidth="0.5" />
          <rect x="5" y="18" width="60" height="3" fill="#222" rx="1" />
          <rect x="5" y="29" width="168" height="1.5" fill="#bbb" rx="0.5" />
          <rect x="5" y="34" width="168" height="1.5" fill="#bbb" rx="0.5" />
          <rect x="5" y="39" width="150" height="1.5" fill="#bbb" rx="0.5" />
          <line x1="5" y1="46" x2="170" y2="46" stroke="#ddd" strokeWidth="0.5" />
          <rect x="5" y="42" width="60" height="3" fill="#222" rx="1" />
          <rect x="5" y="53" width="168" height="1.5" fill="#bbb" rx="0.5" />
          <rect x="5" y="58" width="168" height="1.5" fill="#bbb" rx="0.5" />
          <rect x="5" y="63" width="130" height="1.5" fill="#bbb" rx="0.5" />
          <line x1="5" y1="70" x2="170" y2="70" stroke="#ddd" strokeWidth="0.5" />
          <rect x="5" y="66" width="60" height="3" fill="#222" rx="1" />
          <rect x="5" y="77" width="165" height="1.5" fill="#bbb" rx="0.5" />
          <rect x="5" y="82" width="155" height="1.5" fill="#bbb" rx="0.5" />
          <rect x="5" y="87" width="120" height="1.5" fill="#bbb" rx="0.5" />
          {/* ● bullet markers */}
          <circle cx="5" cy="29.5" r="1" fill="#555" />
          <circle cx="5" cy="34.5" r="1" fill="#555" />
          <circle cx="5" cy="53.5" r="1" fill="#555" />
          <circle cx="5" cy="58.5" r="1" fill="#555" />
        </svg>
      );
    case "harvard":
      return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
          {/* Centered name — traditional academic */}
          <rect x="50" y="6" width="75" height="5" fill="#111" rx="2" />
          <rect x="55" y="15" width="65" height="2" fill="#666" rx="1" />
          {/* Centered section title with partial line */}
          <rect x="55" y="25" width="65" height="1" fill="#222" />
          <rect x="65" y="22" width="45" height="3" fill="#333" rx="1.5" />
          <rect x="55" y="28" width="65" height="1" fill="#222" />
          <rect x="10" y="36" width="155" height="2" fill="#aaa" rx="1" />
          <rect x="10" y="42" width="155" height="2" fill="#aaa" rx="1" />
          <rect x="10" y="48" width="130" height="2" fill="#aaa" rx="1" />
          {/* Second section */}
          <rect x="55" y="58" width="65" height="1" fill="#222" />
          <rect x="65" y="55" width="45" height="3" fill="#333" rx="1.5" />
          <rect x="55" y="61" width="65" height="1" fill="#222" />
          <rect x="10" y="69" width="155" height="2" fill="#aaa" rx="1" />
          <rect x="10" y="75" width="155" height="2" fill="#aaa" rx="1" />
          <rect x="10" y="81" width="110" height="2" fill="#aaa" rx="1" />
          {/* Third section */}
          <rect x="55" y="92" width="65" height="1" fill="#222" />
          <rect x="65" y="89" width="45" height="3" fill="#333" rx="1.5" />
          <rect x="55" y="95" width="65" height="1" fill="#222" />
          <rect x="10" y="103" width="155" height="2" fill="#aaa" rx="1" />
          <rect x="10" y="109" width="140" height="2" fill="#aaa" rx="1" />
          <rect x="10" y="115" width="100" height="2" fill="#aaa" rx="1" />
        </svg>
      );
    case "opal":
      return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
          {/* Centered name — teal color */}
          <rect x="50" y="8" width="75" height="5" fill="#00645a" rx="2" />
          <rect x="55" y="17" width="65" height="2" fill="#668884" rx="1" />
          {/* Centered section title — no line, teal */}
          <rect x="65" y="28" width="45" height="3" fill="#00645a" rx="1.5" />
          <rect x="10" y="37" width="155" height="2" fill="#aaa" rx="1" />
          <rect x="10" y="43" width="155" height="2" fill="#aaa" rx="1" />
          <rect x="10" y="49" width="120" height="2" fill="#aaa" rx="1" />
          <rect x="65" y="58" width="45" height="3" fill="#00645a" rx="1.5" />
          <rect x="10" y="67" width="155" height="2" fill="#aaa" rx="1" />
          <rect x="10" y="73" width="155" height="2" fill="#aaa" rx="1" />
          <rect x="10" y="79" width="100" height="2" fill="#aaa" rx="1" />
          <rect x="65" y="88" width="45" height="3" fill="#00645a" rx="1.5" />
          <rect x="10" y="97" width="155" height="2" fill="#aaa" rx="1" />
          <rect x="10" y="103" width="140" height="2" fill="#aaa" rx="1" />
          <rect x="10" y="109" width="110" height="2" fill="#aaa" rx="1" />
        </svg>
      );
    case "ink":
      return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
          {/* Left-aligned name — deep purple, serif feel */}
          <rect x="5" y="8" width="80" height="6" fill="#2a1852" rx="2" />
          <rect x="5" y="18" width="100" height="2" fill="#46326e" rx="1" />
          {/* Section title — no line, purple, small caps */}
          <rect x="5" y="30" width="60" height="3" fill="#2a1852" rx="1.5" />
          <rect x="5" y="39" width="165" height="2" fill="#aaa" rx="1" />
          <rect x="5" y="45" width="165" height="2" fill="#aaa" rx="1" />
          <rect x="5" y="51" width="140" height="2" fill="#aaa" rx="1" />
          <rect x="5" y="62" width="60" height="3" fill="#2a1852" rx="1.5" />
          <rect x="5" y="71" width="165" height="2" fill="#aaa" rx="1" />
          <rect x="5" y="77" width="165" height="2" fill="#aaa" rx="1" />
          <rect x="5" y="83" width="120" height="2" fill="#aaa" rx="1" />
          <rect x="5" y="94" width="60" height="3" fill="#2a1852" rx="1.5" />
          <rect x="5" y="103" width="165" height="2" fill="#aaa" rx="1" />
          <rect x="5" y="109" width="150" height="2" fill="#aaa" rx="1" />
          <rect x="5" y="115" width="100" height="2" fill="#aaa" rx="1" />
        </svg>
      );
    case "ember":
      return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
          {/* Centered name — red/burgundy */}
          <rect x="45" y="8" width="85" height="6" fill="#9b2319" rx="2" />
          <rect x="55" y="18" width="65" height="2" fill="#785048" rx="1" />
          {/* Centered section title — no line, red */}
          <rect x="65" y="28" width="45" height="3" fill="#9b2319" rx="1.5" />
          <rect x="10" y="37" width="155" height="2" fill="#bbb" rx="1" />
          <rect x="10" y="43" width="155" height="2" fill="#bbb" rx="1" />
          <rect x="10" y="49" width="130" height="2" fill="#bbb" rx="1" />
          <rect x="65" y="60" width="45" height="3" fill="#9b2319" rx="1.5" />
          <rect x="10" y="69" width="155" height="2" fill="#bbb" rx="1" />
          <rect x="10" y="75" width="155" height="2" fill="#bbb" rx="1" />
          <rect x="10" y="81" width="110" height="2" fill="#bbb" rx="1" />
          <rect x="65" y="92" width="45" height="3" fill="#9b2319" rx="1.5" />
          <rect x="10" y="101" width="155" height="2" fill="#bbb" rx="1" />
          <rect x="10" y="107" width="140" height="2" fill="#bbb" rx="1" />
          <rect x="10" y="113" width="100" height="2" fill="#bbb" rx="1" />
        </svg>
      );
    case "engineeringclassic":
      return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
          {/* Hybrid: classic sidebar + engineering compactness */}
          <rect x="0" y="0" width="40" height={h} fill="#1a3a5c" rx="0" />
          <rect x="6" y="8" width="28" height="28" fill="#2a5a8c" rx="3" />
          <rect x="6" y="42" width="28" height="3" fill="#4a8bc2" rx="1.5" />
          <rect x="6" y="48" width="25" height="2" fill="#3a6a9c" rx="1" />
          <rect x="50" y="6" width="120" height="4" fill="#222" rx="1.5" />
          <line x1="50" y1="16" x2="170" y2="16" stroke="#ddd" strokeWidth="0.5" />
          <rect x="50" y="22" width="60" height="3" fill="#444" rx="1" />
          <rect x="50" y="30" width="120" height="1.5" fill="#bbb" rx="0.5" />
          <rect x="50" y="35" width="120" height="1.5" fill="#bbb" rx="0.5" />
          <rect x="50" y="40" width="100" height="1.5" fill="#bbb" rx="0.5" />
          <line x1="50" y1="48" x2="170" y2="48" stroke="#ddd" strokeWidth="0.5" />
          <rect x="50" y="54" width="60" height="3" fill="#444" rx="1" />
          <rect x="50" y="62" width="120" height="1.5" fill="#bbb" rx="0.5" />
          <rect x="50" y="67" width="120" height="1.5" fill="#bbb" rx="0.5" />
          <rect x="50" y="72" width="90" height="1.5" fill="#bbb" rx="0.5" />
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
        width: 210,
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
            height: 145,
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
