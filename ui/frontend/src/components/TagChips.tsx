import { Box, Chip } from "@mui/material";

interface Props {
  keywords: string[];
}

const colors = ["#1976d2", "#388e3c", "#d32f2f", "#f57c00",
                "#7b1fa2", "#00796b", "#c2185b", "#546e7a"];

export default function TagChips({ keywords }: Props) {
  return (
    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5, my: 1 }}>
      {keywords.map((kw, i) => (
        <Chip
          key={kw}
          label={kw}
          size="small"
          sx={{ bgcolor: colors[i % colors.length], color: "#fff" }}
        />
      ))}
    </Box>
  );
}
