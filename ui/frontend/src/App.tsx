import { useState, useEffect, useCallback } from "react";
import {
  AppBar,
  Box,
  Tab,
  Tabs,
  Toolbar,
  Container,
  CssBaseline,
  ThemeProvider,
  createTheme,
  Typography,
} from "@mui/material";
import DescriptionIcon from "@mui/icons-material/Description";
import CompareArrowsIcon from "@mui/icons-material/CompareArrows";
import HistoryIcon from "@mui/icons-material/History";
import EditIcon from "@mui/icons-material/Edit";
import FolderOpenIcon from "@mui/icons-material/FolderOpen";
import Logo from "./components/Logo";
import ResumePage from "./pages/ResumePage";
import ComparePage from "./pages/ComparePage";
import OutputPage from "./pages/OutputPage";
import HistoryPage from "./pages/HistoryPage";
import EditorPage from "./pages/EditorPage";
import { api } from "./api/client";
import type { ThemeInfo, RunHistoryItem } from "./types";

const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#1F3864" },
    secondary: { main: "#2A5A8C" },
    background: { default: "#F4F6FA", paper: "#FFFFFF" },
  },
  shape: { borderRadius: 10 },
  typography: {
    fontFamily: [
      "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto",
      "Helvetica Neue", "Arial", "sans-serif",
    ].join(","),
  },
  components: {
    MuiCard: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: { border: "1px solid #E3E8F0" },
      },
    },
    MuiCardHeader: {
      styleOverrides: {
        title: { fontWeight: 700, fontSize: "0.95rem" },
        root: { paddingBottom: 0 },
      },
    },
    MuiAppBar: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: { backgroundColor: "#1F3864" },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: { textTransform: "none", fontWeight: 600 },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: { textTransform: "none", fontWeight: 600 },
      },
    },
    MuiToggleButton: {
      styleOverrides: {
        root: { textTransform: "none" },
      },
    },
  },
});

function a11yProps(index: number) {
  return { id: `tab-${index}`, "aria-controls": `tabpanel-${index}` };
}

export default function App() {
  const [tab, setTab] = useState(0);
  const [themes, setThemes] = useState<ThemeInfo[]>([]);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    api.listThemes().then(setThemes).catch(() => {});
  }, []);

  const refreshHistory = useCallback(
    () => setRefreshKey((k) => k + 1),
    []
  );

  const handleReRun = useCallback((_item: RunHistoryItem) => {
    setTab(0);
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppBar position="sticky">
        <Toolbar sx={{ px: { xs: 2, md: 3 } }}>
          <Logo />
          <Box sx={{ flexGrow: 1 }} />
          <Typography
            variant="caption"
            sx={{ color: "rgba(255,255,255,0.65)", display: { xs: "none", sm: "block" } }}
          >
            PDF · DOCX · Cover letter
          </Typography>
        </Toolbar>
      </AppBar>
      <Container maxWidth="xl" sx={{ mt: 3, pb: 6 }}>
        <Box
          sx={{
            bgcolor: "background.paper",
            border: "1px solid #E3E8F0",
            borderRadius: 2,
            mb: 3,
            px: 1,
          }}
        >
          <Tabs
            value={tab}
            onChange={(_, v) => setTab(v)}
            variant="scrollable"
            scrollButtons="auto"
            sx={{ minHeight: 52 }}
          >
            <Tab icon={<DescriptionIcon fontSize="small" />} iconPosition="start" label="Build" {...a11yProps(0)} />
            <Tab icon={<CompareArrowsIcon fontSize="small" />} iconPosition="start" label="Compare" {...a11yProps(1)} />
            <Tab icon={<FolderOpenIcon fontSize="small" />} iconPosition="start" label="Outputs" {...a11yProps(2)} />
            <Tab icon={<HistoryIcon fontSize="small" />} iconPosition="start" label="History" {...a11yProps(3)} />
            <Tab icon={<EditIcon fontSize="small" />} iconPosition="start" label="Editor" {...a11yProps(4)} />
          </Tabs>
        </Box>

        {tab === 0 && (
          <ResumePage themes={themes} onRefreshHistory={refreshHistory} />
        )}
        {tab === 1 && (
          <ComparePage />
        )}
        {tab === 2 && (
          <OutputPage />
        )}
        {tab === 3 && (
          <HistoryPage
            refreshKey={refreshKey}
            onReRun={handleReRun}
          />
        )}
        {tab === 4 && (
          <EditorPage />
        )}
      </Container>
    </ThemeProvider>
  );
}
