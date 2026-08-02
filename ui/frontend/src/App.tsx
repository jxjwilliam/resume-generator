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

const theme = createTheme();

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
      <AppBar position="static">
        <Toolbar>
          <Logo />
        </Toolbar>
      </AppBar>
      <Container maxWidth="xl" sx={{ mt: 3 }}>
        <Box sx={{ borderBottom: 1, borderColor: "divider", mb: 2 }}>
          <Tabs value={tab} onChange={(_, v) => setTab(v)}>
            <Tab icon={<DescriptionIcon />} label="Resume" {...a11yProps(0)} />
            <Tab icon={<CompareArrowsIcon />} label="Compare" {...a11yProps(1)} />
            <Tab icon={<FolderOpenIcon />} label="Outputs" {...a11yProps(2)} />
            <Tab icon={<HistoryIcon />} label="History" {...a11yProps(3)} />
            <Tab icon={<EditIcon />} label="Editor" {...a11yProps(4)} />
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
