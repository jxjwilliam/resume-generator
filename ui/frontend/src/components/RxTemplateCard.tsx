import { Card, CardActionArea, CardContent, Typography, Box } from "@mui/material";
import type { RxTemplateInfo } from "../types";

interface Props {
  template: RxTemplateInfo;
  selected: boolean;
  onClick: () => void;
}

const w = 200, h = 110;

/** Colored accent dot for sidebar-based templates */
function SidebarPreview({ color, leftPct = 30 }: { color: string; leftPct?: number }) {
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
      <rect x="0" y="0" width={leftPct} height={h} fill={color} rx="2" />
      <rect x={leftPct + 5} y="10" width={w - leftPct - 10} height="4" fill="#333" rx="2" />
      <rect x={leftPct + 5} y="20" width={w - leftPct - 15} height="2" fill="#999" rx="1" />
      <rect x={leftPct + 5} y="26" width={w - leftPct - 15} height="2" fill="#999" rx="1" />
      <rect x={leftPct + 5} y="32" width={w - leftPct - 25} height="2" fill="#999" rx="1" />
      <rect x={leftPct + 5} y="46" width={w - leftPct - 15} height="3" fill="#333" rx="1.5" />
      <rect x={leftPct + 5} y="54" width={w - leftPct - 15} height="2" fill="#bbb" rx="1" />
      <rect x={leftPct + 5} y="60" width={w - leftPct - 15} height="2" fill="#bbb" rx="1" />
      <rect x={leftPct + 5} y="66" width={w - leftPct - 25} height="2" fill="#bbb" rx="1" />
      <rect x={leftPct + 5} y="80" width={w - leftPct - 15} height="3" fill="#333" rx="1.5" />
      <rect x={leftPct + 5} y="88" width={w - leftPct - 20} height="2" fill="#bbb" rx="1" />
      <rect x={leftPct + 5} y="94" width={w - leftPct - 30} height="2" fill="#bbb" rx="1" />
    </svg>
  );
}

function SingleColumnPreview({ accentColor, density = "medium" }: { accentColor: string; density?: "compact" | "medium" | "spacious" }) {
  const yOff = density === "compact" ? 0 : density === "spacious" ? 6 : 3;
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
      <rect x="50" y={6 + yOff} width="100" height="4" fill="#222" rx="2" />
      <rect x={20 + yOff} y={14 + yOff} width={w - 40 - 2 * yOff} height="1.5" fill={accentColor} rx="0.75" />
      <rect x={10 + yOff} y={24 + yOff} width="60" height="3" fill="#333" rx="1.5" />
      <rect x={10 + yOff} y={32 + yOff} width={w - 20 - 2 * yOff} height="2" fill="#999" rx="1" />
      <rect x={10 + yOff} y={38 + yOff} width={w - 20 - 2 * yOff} height="2" fill="#999" rx="1" />
      <rect x={10 + yOff} y={44 + yOff} width={w - 40 - 2 * yOff} height="2" fill="#999" rx="1" />
      <rect x={10 + yOff} y={58 + yOff} width="60" height="3" fill="#333" rx="1.5" />
      <rect x={10 + yOff} y={66 + yOff} width={w - 20 - 2 * yOff} height="2" fill="#999" rx="1" />
      <rect x={10 + yOff} y={72 + yOff} width={w - 30 - 2 * yOff} height="2" fill="#999" rx="1" />
      <rect x={10 + yOff} y={86 + yOff} width="60" height="3" fill="#333" rx="1.5" />
      <rect x={10 + yOff} y={94 + yOff} width={w - 20 - 2 * yOff} height="2" fill="#999" rx="1" />
    </svg>
  );
}

function DarkPreview() {
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
      <rect x="0" y="0" width={w} height={h} fill="#1a1a2e" rx="2" />
      <rect x="50" y="10" width="100" height="4" fill="#e94560" rx="2" />
      <rect x="20" y="18" width="160" height="1.5" fill="#533483" rx="0.75" />
      <rect x="10" y="30" width="60" height="3" fill="#e94560" rx="1.5" />
      <rect x="10" y="38" width="180" height="2" fill="#aaa" rx="1" />
      <rect x="10" y="44" width="170" height="2" fill="#aaa" rx="1" />
      <rect x="10" y="50" width="150" height="2" fill="#aaa" rx="1" />
      <rect x="10" y="64" width="60" height="3" fill="#e94560" rx="1.5" />
      <rect x="10" y="72" width="180" height="2" fill="#aaa" rx="1" />
      <rect x="10" y="78" width="160" height="2" fill="#aaa" rx="1" />
      <rect x="10" y="92" width="60" height="3" fill="#e94560" rx="1.5" />
      <rect x="10" y="100" width="170" height="2" fill="#aaa" rx="1" />
    </svg>
  );
}

function renderPreview(id: string) {
  switch (id) {
    case "kakuna": return <SingleColumnPreview accentColor="#1976d2" density="compact" />;
    case "bronzor": return <SidebarPreview color="#e8e0d4" />;
    case "onyx": return <SidebarPreview color="#2c3e50" leftPct={28} />;
    case "ditto": return <SingleColumnPreview accentColor="#555" density="spacious" />;
    case "azurill": return <SidebarPreview color="#e8f4f8" leftPct={25} />;
    case "chikorita": return <SingleColumnPreview accentColor="#4caf50" density="medium" />;
    case "leafish": return <SingleColumnPreview accentColor="#66bb6a" density="medium" />;
    case "gengar": return <DarkPreview />;
    case "pikachu": return <SingleColumnPreview accentColor="#f5a623" density="compact" />;
    case "lapras": return <SingleColumnPreview accentColor="#5c6bc0" density="spacious" />;
    case "glalie": return <SidebarPreview color="#e3f2fd" leftPct={28} />;
    case "rhyhorn": return <SingleColumnPreview accentColor="#8d6e63" density="compact" />;
    case "meowth": return <SingleColumnPreview accentColor="#ffb300" density="compact" />;
    case "scizor": return <SidebarPreview color="#1b5e20" leftPct={30} />;
    case "ditgar": return <SingleColumnPreview accentColor="#7b1fa2" density="medium" />;
    default: return <SingleColumnPreview accentColor="#999" density="medium" />;
  }
}

export default function RxTemplateCard({ template, selected, onClick }: Props) {
  return (
    <Card
      sx={{
        width: 220,
        border: selected ? "2px solid #1976d2" : "2px solid transparent",
        bgcolor: selected ? "action.selected" : "background.paper",
        transition: "border-color 0.2s, box-shadow 0.2s",
        ...(selected ? { boxShadow: "0 0 8px rgba(25,118,210,0.3)" } : {}),
      }}
    >
      <CardActionArea onClick={onClick}>
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
          {renderPreview(template.id)}
        </Box>
        <CardContent sx={{ py: 1.5, "&:last-child": { pb: 1.5 } }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
            {template.name}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.5 }}>
            {template.best_for}
          </Typography>
        </CardContent>
      </CardActionArea>
    </Card>
  );
}
