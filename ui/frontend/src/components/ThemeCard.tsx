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

/** Photo placeholder — circle with person silhouette */
function Photo({ cx, cy, r, fill = "#b0c4de" }: { cx: number; cy: number; r: number; fill?: string }) {
  return (
    <>
      <circle cx={cx} cy={cy} r={r} fill={fill} stroke="#fff" strokeWidth={1.5} />
      {/* Head */}
      <circle cx={cx} cy={cy - r * 0.2} r={r * 0.35} fill="#fff" opacity={0.7} />
      {/* Body */}
      <ellipse cx={cx} cy={cy + r * 0.55} rx={r * 0.55} ry={r * 0.45} fill="#fff" opacity={0.7} />
    </>
  );
}

/** Accurate SVG thumbnail for each RenderCV v2 theme */
function ThemePreview({ themeId }: { themeId: string }) {
  const w = 240, h = 175;

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
          <rect x="8" y="8" width="224" height="159" rx="8" fill="url(#ag)" opacity="0.08" />
          <rect x="80" y="60" width="80" height="7" fill="#333" rx="3" />
          <rect x="65" y="74" width="110" height="4" fill="#999" rx="2" />
          <text x="120" y="110" textAnchor="middle" fill="#666" fontSize="13" fontFamily="sans-serif">Auto-select</text>
        </svg>
      );
    case "classic":
      return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
          {/* Left sidebar — dark blue */}
          <rect x="0" y="0" width="70" height={h} fill="#1a3a5c" rx="0" />
          {/* Photo in sidebar */}
          <Photo cx={35} cy={30} r={20} fill="#2a5a8c" />
          {/* Sidebar text */}
          <rect x="10" y="58" width="50" height="4" fill="#4a8bc2" rx="2" />
          <rect x="10" y="66" width="45" height="3" fill="#3a6a9c" rx="1.5" />
          <rect x="10" y="72" width="40" height="3" fill="#3a6a9c" rx="1.5" />
          <rect x="10" y="85" width="50" height="4" fill="#4a8bc2" rx="2" />
          <rect x="10" y="93" width="45" height="3" fill="#3a6a9c" rx="1.5" />
          <rect x="10" y="99" width="35" height="3" fill="#3a6a9c" rx="1.5" />
          <rect x="10" y="112" width="50" height="4" fill="#4a8bc2" rx="2" />
          <rect x="10" y="120" width="45" height="3" fill="#3a6a9c" rx="1.5" />
          {/* Right content */}
          <rect x="85" y="12" width="145" height="6" fill="#222" rx="2" />
          <rect x="85" y="24" width="125" height="3" fill="#888" rx="1.5" />
          <line x1="85" y1="38" x2="235" y2="38" stroke="#ccc" strokeWidth="0.6" />
          <rect x="85" y="46" width="100" height="4" fill="#444" rx="2" />
          <rect x="85" y="56" width="145" height="2.5" fill="#bbb" rx="1" />
          <rect x="85" y="63" width="145" height="2.5" fill="#bbb" rx="1" />
          <rect x="85" y="70" width="120" height="2.5" fill="#bbb" rx="1" />
          <line x1="85" y1="83" x2="235" y2="83" stroke="#ccc" strokeWidth="0.6" />
          <rect x="85" y="91" width="100" height="4" fill="#444" rx="2" />
          <rect x="85" y="101" width="145" height="2.5" fill="#bbb" rx="1" />
          <rect x="85" y="108" width="145" height="2.5" fill="#bbb" rx="1" />
          <rect x="85" y="115" width="110" height="2.5" fill="#bbb" rx="1" />
        </svg>
      );
    case "sb2nov":
      return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
          {/* Centered name — no photo */}
          <rect x="75" y="8" width="90" height="6" fill="#111" rx="2" />
          <rect x="40" y="19" width="160" height="2" fill="#1976d2" rx="1" />
          <rect x="65" y="26" width="110" height="3" fill="#666" rx="1.5" />
          {/* Section with full-width line */}
          <line x1="8" y1="42" x2="232" y2="42" stroke="#1976d2" strokeWidth="0.8" />
          <rect x="8" y="38" width="70" height="4" fill="#222" rx="2" />
          <rect x="8" y="52" width="224" height="2.5" fill="#aaa" rx="1" />
          <rect x="8" y="59" width="224" height="2.5" fill="#aaa" rx="1" />
          <rect x="8" y="66" width="190" height="2.5" fill="#aaa" rx="1" />
          <line x1="8" y1="80" x2="232" y2="80" stroke="#1976d2" strokeWidth="0.8" />
          <rect x="8" y="76" width="70" height="4" fill="#222" rx="2" />
          <rect x="8" y="90" width="224" height="2.5" fill="#aaa" rx="1" />
          <rect x="8" y="97" width="224" height="2.5" fill="#aaa" rx="1" />
          <rect x="8" y="104" width="160" height="2.5" fill="#aaa" rx="1" />
          <line x1="8" y1="118" x2="232" y2="118" stroke="#1976d2" strokeWidth="0.8" />
          <rect x="8" y="114" width="70" height="4" fill="#222" rx="2" />
          <rect x="8" y="128" width="224" height="2.5" fill="#aaa" rx="1" />
          <rect x="8" y="135" width="200" height="2.5" fill="#aaa" rx="1" />
        </svg>
      );
    case "moderncv":
      return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
          {/* Orange accent bar */}
          <rect x="0" y="0" width={w} height="5" fill="#e67e22" />
          {/* Left column — photo + info */}
          <Photo cx={30} cy={28} r={18} fill="#f0dcc8" />
          <rect x="5" y="54" width="50" height="5" fill="#333" rx="2" />
          <circle cx="15" cy="72" r="5" fill="#e67e22" opacity="0.15" />
          <circle cx="15" cy="72" r="2.5" fill="#e67e22" />
          <rect x="26" y="69" width="38" height="3" fill="#888" rx="1.5" />
          <rect x="26" y="75" width="30" height="2.5" fill="#aaa" rx="1" />
          <circle cx="15" cy="92" r="5" fill="#e67e22" opacity="0.15" />
          <circle cx="15" cy="92" r="2.5" fill="#e67e22" />
          <rect x="26" y="89" width="38" height="3" fill="#888" rx="1.5" />
          <rect x="26" y="95" width="30" height="2.5" fill="#aaa" rx="1" />
          {/* Right content — thick orange section lines */}
          <rect x="72" y="12" width="160" height="5" fill="#333" rx="2" />
          <rect x="72" y="23" width="140" height="3" fill="#888" rx="1.5" />
          <rect x="72" y="31" width="110" height="2.5" fill="#aaa" rx="1" />
          <rect x="72" y="42" width="120" height="4" fill="#e67e22" rx="2" />
          <rect x="72" y="53" width="160" height="2.5" fill="#bbb" rx="1" />
          <rect x="72" y="60" width="160" height="2.5" fill="#bbb" rx="1" />
          <rect x="72" y="67" width="120" height="2.5" fill="#bbb" rx="1" />
          <rect x="72" y="80" width="120" height="4" fill="#e67e22" rx="2" />
          <rect x="72" y="91" width="160" height="2.5" fill="#bbb" rx="1" />
          <rect x="72" y="98" width="160" height="2.5" fill="#bbb" rx="1" />
          <rect x="72" y="105" width="100" height="2.5" fill="#bbb" rx="1" />
          <rect x="72" y="118" width="120" height="4" fill="#e67e22" rx="2" />
          <rect x="72" y="129" width="160" height="2.5" fill="#bbb" rx="1" />
          <rect x="72" y="136" width="140" height="2.5" fill="#bbb" rx="1" />
        </svg>
      );
    case "engineeringresumes":
      return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
          {/* Ultra-compact, no photo, everything tight */}
          <rect x="60" y="5" width="120" height="5" fill="#111" rx="1.5" />
          <rect x="20" y="15" width="200" height="0.8" fill="#ccc" />
          <line x1="6" y1="27" x2="234" y2="27" stroke="#ddd" strokeWidth="0.5" />
          <rect x="6" y="22" width="80" height="4" fill="#222" rx="1" />
          {/* ● bullet markers */}
          <circle cx="6" cy="38" r="1.2" fill="#555" />
          <rect x="12" y="36" width="222" height="2" fill="#ccc" rx="0.5" />
          <circle cx="6" cy="46" r="1.2" fill="#555" />
          <rect x="12" y="44" width="222" height="2" fill="#ccc" rx="0.5" />
          <circle cx="6" cy="54" r="1.2" fill="#555" />
          <rect x="12" y="52" width="190" height="2" fill="#ccc" rx="0.5" />
          <line x1="6" y1="66" x2="234" y2="66" stroke="#ddd" strokeWidth="0.5" />
          <rect x="6" y="61" width="80" height="4" fill="#222" rx="1" />
          <circle cx="6" cy="77" r="1.2" fill="#555" />
          <rect x="12" y="75" width="222" height="2" fill="#ccc" rx="0.5" />
          <circle cx="6" cy="85" r="1.2" fill="#555" />
          <rect x="12" y="83" width="222" height="2" fill="#ccc" rx="0.5" />
          <circle cx="6" cy="93" r="1.2" fill="#555" />
          <rect x="12" y="91" width="160" height="2" fill="#ccc" rx="0.5" />
          <line x1="6" y1="105" x2="234" y2="105" stroke="#ddd" strokeWidth="0.5" />
          <rect x="6" y="100" width="80" height="4" fill="#222" rx="1" />
          <circle cx="6" cy="116" r="1.2" fill="#555" />
          <rect x="12" y="114" width="222" height="2" fill="#ccc" rx="0.5" />
          <circle cx="6" cy="124" r="1.2" fill="#555" />
          <rect x="12" y="122" width="200" height="2" fill="#ccc" rx="0.5" />
        </svg>
      );
    case "harvard":
      return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
          {/* Centered name — no photo */}
          <rect x="75" y="8" width="90" height="6" fill="#111" rx="2" />
          <rect x="85" y="19" width="70" height="2.5" fill="#666" rx="1.5" />
          {/* Centered section with partial line */}
          <rect x="80" y="33" width="80" height="1" fill="#333" />
          <rect x="95" y="29" width="50" height="4" fill="#333" rx="2" />
          <rect x="80" y="37" width="80" height="1" fill="#333" />
          <rect x="12" y="48" width="216" height="2.5" fill="#bbb" rx="1" />
          <rect x="12" y="55" width="216" height="2.5" fill="#bbb" rx="1" />
          <rect x="12" y="62" width="170" height="2.5" fill="#bbb" rx="1" />
          <rect x="80" y="76" width="80" height="1" fill="#333" />
          <rect x="95" y="72" width="50" height="4" fill="#333" rx="2" />
          <rect x="80" y="80" width="80" height="1" fill="#333" />
          <rect x="12" y="91" width="216" height="2.5" fill="#bbb" rx="1" />
          <rect x="12" y="98" width="216" height="2.5" fill="#bbb" rx="1" />
          <rect x="12" y="105" width="150" height="2.5" fill="#bbb" rx="1" />
          <rect x="80" y="119" width="80" height="1" fill="#333" />
          <rect x="95" y="115" width="50" height="4" fill="#333" rx="2" />
          <rect x="80" y="123" width="80" height="1" fill="#333" />
          <rect x="12" y="134" width="216" height="2.5" fill="#bbb" rx="1" />
          <rect x="12" y="141" width="190" height="2.5" fill="#bbb" rx="1" />
        </svg>
      );
    case "opal":
      return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
          {/* Centered name — teal, no photo */}
          <rect x="70" y="10" width="100" height="6" fill="#00645a" rx="2" />
          <rect x="80" y="21" width="80" height="2.5" fill="#668884" rx="1.5" />
          {/* Centered section — no line */}
          <rect x="90" y="35" width="60" height="4" fill="#00645a" rx="2" />
          <rect x="12" y="47" width="216" height="2.5" fill="#bbb" rx="1" />
          <rect x="12" y="54" width="216" height="2.5" fill="#bbb" rx="1" />
          <rect x="12" y="61" width="170" height="2.5" fill="#bbb" rx="1" />
          <rect x="90" y="75" width="60" height="4" fill="#00645a" rx="2" />
          <rect x="12" y="87" width="216" height="2.5" fill="#bbb" rx="1" />
          <rect x="12" y="94" width="216" height="2.5" fill="#bbb" rx="1" />
          <rect x="12" y="101" width="140" height="2.5" fill="#bbb" rx="1" />
          <rect x="90" y="115" width="60" height="4" fill="#00645a" rx="2" />
          <rect x="12" y="127" width="216" height="2.5" fill="#bbb" rx="1" />
          <rect x="12" y="134" width="200" height="2.5" fill="#bbb" rx="1" />
        </svg>
      );
    case "ink":
      return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
          {/* Left-aligned name — deep purple, no photo */}
          <rect x="8" y="10" width="110" height="7" fill="#2a1852" rx="2" />
          <rect x="8" y="22" width="140" height="2.5" fill="#46326e" rx="1.5" />
          {/* Section — no line, small caps look */}
          <rect x="8" y="38" width="80" height="4" fill="#2a1852" rx="2" />
          <rect x="8" y="50" width="224" height="2.5" fill="#bbb" rx="1" />
          <rect x="8" y="57" width="224" height="2.5" fill="#bbb" rx="1" />
          <rect x="8" y="64" width="180" height="2.5" fill="#bbb" rx="1" />
          <rect x="8" y="80" width="80" height="4" fill="#2a1852" rx="2" />
          <rect x="8" y="92" width="224" height="2.5" fill="#bbb" rx="1" />
          <rect x="8" y="99" width="224" height="2.5" fill="#bbb" rx="1" />
          <rect x="8" y="106" width="160" height="2.5" fill="#bbb" rx="1" />
          <rect x="8" y="122" width="80" height="4" fill="#2a1852" rx="2" />
          <rect x="8" y="134" width="224" height="2.5" fill="#bbb" rx="1" />
          <rect x="8" y="141" width="200" height="2.5" fill="#bbb" rx="1" />
        </svg>
      );
    case "ember":
      return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
          {/* Centered name — red, no photo */}
          <rect x="70" y="10" width="100" height="7" fill="#9b2319" rx="2" />
          <rect x="80" y="22" width="80" height="2.5" fill="#785048" rx="1.5" />
          {/* Centered section — no line, ◆ diamonds */}
          <rect x="90" y="36" width="60" height="4" fill="#9b2319" rx="2" />
          <rect x="12" y="48" width="216" height="2.5" fill="#ccc" rx="1" />
          <rect x="12" y="55" width="216" height="2.5" fill="#ccc" rx="1" />
          <rect x="12" y="62" width="170" height="2.5" fill="#ccc" rx="1" />
          <rect x="90" y="76" width="60" height="4" fill="#9b2319" rx="2" />
          <rect x="12" y="88" width="216" height="2.5" fill="#ccc" rx="1" />
          <rect x="12" y="95" width="216" height="2.5" fill="#ccc" rx="1" />
          <rect x="12" y="102" width="150" height="2.5" fill="#ccc" rx="1" />
          <rect x="90" y="116" width="60" height="4" fill="#9b2319" rx="2" />
          <rect x="12" y="128" width="216" height="2.5" fill="#ccc" rx="1" />
          <rect x="12" y="135" width="190" height="2.5" fill="#ccc" rx="1" />
        </svg>
      );
    case "engineeringclassic":
      return (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
          {/* Sidebar + compact hybrid */}
          <rect x="0" y="0" width="50" height={h} fill="#1a3a5c" rx="0" />
          {/* Photo in sidebar */}
          <Photo cx={25} cy={22} r={14} fill="#2a5a8c" />
          <rect x="6" y="44" width="38" height="4" fill="#4a8bc2" rx="2" />
          <rect x="6" y="51" width="35" height="3" fill="#3a6a9c" rx="1.5" />
          <rect x="6" y="65" width="38" height="4" fill="#4a8bc2" rx="2" />
          <rect x="6" y="72" width="35" height="3" fill="#3a6a9c" rx="1.5" />
          {/* Right compact content */}
          <rect x="62" y="10" width="170" height="5" fill="#222" rx="1.5" />
          <line x1="62" y1="22" x2="235" y2="22" stroke="#ddd" strokeWidth="0.5" />
          <rect x="62" y="30" width="80" height="4" fill="#444" rx="1" />
          <rect x="62" y="40" width="172" height="2" fill="#ccc" rx="0.5" />
          <rect x="62" y="46" width="172" height="2" fill="#ccc" rx="0.5" />
          <rect x="62" y="52" width="140" height="2" fill="#ccc" rx="0.5" />
          <line x1="62" y1="62" x2="235" y2="62" stroke="#ddd" strokeWidth="0.5" />
          <rect x="62" y="70" width="80" height="4" fill="#444" rx="1" />
          <rect x="62" y="80" width="172" height="2" fill="#ccc" rx="0.5" />
          <rect x="62" y="86" width="172" height="2" fill="#ccc" rx="0.5" />
          <rect x="62" y="92" width="130" height="2" fill="#ccc" rx="0.5" />
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
        width: 255,
        opacity: disabled ? 0.5 : 1,
        border: selected ? "2px solid #1976d2" : "2px solid transparent",
        bgcolor: selected ? "action.selected" : "background.paper",
        transition: "border-color 0.2s, box-shadow 0.2s",
        ...(selected ? { boxShadow: "0 0 10px rgba(25,118,210,0.35)" } : {}),
      }}
    >
      <CardActionArea onClick={disabled ? undefined : onClick} disabled={disabled}>
        <Box
          sx={{
            height: 180,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            bgcolor: "#fafafa",
            borderBottom: "1px solid #eee",
            overflow: "hidden",
            p: 0.5,
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
