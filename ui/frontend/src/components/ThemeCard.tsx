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
}

export default function ThemeCard({ theme, selected, onClick }: Props) {
  return (
    <Card
      sx={{
        width: 220,
        border: selected ? "2px solid #1976d2" : "2px solid transparent",
        bgcolor: selected ? "action.selected" : "background.paper",
      }}
    >
      <CardActionArea onClick={onClick}>
        <Box sx={{ height: 120, bgcolor: "#f5f5f5", display: "flex",
          alignItems: "center", justifyContent: "center", color: "#999" }}>
          <Typography variant="body2">{theme.name}</Typography>
        </Box>
        <CardContent>
          <Typography variant="subtitle2">{theme.name}</Typography>
          <Typography variant="caption" color="text.secondary">
            {theme.best_for}
          </Typography>
        </CardContent>
      </CardActionArea>
    </Card>
  );
}
