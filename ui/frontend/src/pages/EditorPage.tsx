import { useCallback, useEffect, useRef, useState } from "react";
import {
  Box,
  Button,
  IconButton,
  Paper,
  Snackbar,
  Alert,
  Tooltip,
} from "@mui/material";
import SaveIcon from "@mui/icons-material/Save";
import RefreshIcon from "@mui/icons-material/Refresh";
import { basicSetup } from "codemirror";
import { EditorView, keymap } from "@codemirror/view";
import { EditorState } from "@codemirror/state";
import { yaml } from "@codemirror/lang-yaml";
import { oneDark } from "@codemirror/theme-one-dark";
import * as yamlParser from "js-yaml";
import { api } from "../api/client";
import YamlSelector from "../components/YamlSelector";
import { DEFAULT_YAML_PATH } from "../types";

export default function EditorPage() {
  const editorRef = useRef<HTMLDivElement>(null);
  const viewRef = useRef<EditorView | null>(null);

  const [yamlPath, setYamlPath] = useState(DEFAULT_YAML_PATH);
  const [content, setContent] = useState("");
  const [originalContent, setOriginalContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  const isDirty = content !== originalContent;

  // Unsaved changes guard
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (isDirty) e.preventDefault();
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [isDirty]);

  // Load YAML content
  const loadYaml = useCallback(async (path: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getYaml(path);
      setContent(res.content);
      setOriginalContent(res.content);
      setLastSaved(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load file";
      if (msg.includes("404")) {
        setContent("");
        setOriginalContent("");
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadYaml(yamlPath);
  }, [yamlPath, loadYaml]);

  // Sync editor content when content changes from load/save
  useEffect(() => {
    if (!viewRef.current || !editorRef.current) return;
    const view = viewRef.current;
    const currentText = view.state.doc.toString();
    if (currentText !== content) {
      view.dispatch({
        changes: { from: 0, to: view.state.doc.length, insert: content },
      });
    }
  }, [content]);

  // Set up CodeMirror
  useEffect(() => {
    if (!editorRef.current) return;

    const updateListener = EditorView.updateListener.of((update) => {
      if (update.docChanged) {
        setContent(update.state.doc.toString());
      }
    });

    // Ctrl+S — read from viewRef to avoid stale closure
    const saveKeybinding = keymap.of([
      {
        key: "Mod-s",
        run: () => {
          const text = viewRef.current?.state.doc.toString() ?? "";
          handleSave(text);
          return true;
        },
      },
    ]);

    const state = EditorState.create({
      doc: content,
      extensions: [
        basicSetup,
        yaml(),
        oneDark,
        updateListener,
        saveKeybinding,
        EditorView.lineWrapping,
      ],
    });

    const view = new EditorView({
      state,
      parent: editorRef.current,
    });
    viewRef.current = view;

    return () => {
      view.destroy();
      viewRef.current = null;
    };
    // Only run this effect once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update editor content when yamlPath changes (recreate editor)
  useEffect(() => {
    if (!viewRef.current) return;
    const view = viewRef.current;
    view.dispatch({
      changes: { from: 0, to: view.state.doc.length, insert: content },
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [yamlPath]);

  const handleSave = async (text?: string) => {
    const currentContent = text ?? content;
    // Client-side YAML validation
    try {
      yamlParser.load(currentContent);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Invalid YAML";
      setError(`YAML error: ${msg}`);
      return;
    }

    setSaving(true);
    setError(null);
    try {
      await api.saveYaml(yamlPath, currentContent);
      setOriginalContent(currentContent);
      setContent(currentContent);
      setLastSaved(new Date());
      setSuccessMsg("Saved successfully");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Save failed";
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleReload = async () => {
    if (isDirty) {
      const ok = window.confirm(
        "You have unsaved changes. Reloading will discard them. Continue?"
      );
      if (!ok) return;
    }
    await loadYaml(yamlPath);
  };

  const handleYamlChange = (newPath: string) => {
    if (isDirty) {
      const ok = window.confirm(
        "You have unsaved changes. Switch files and discard changes?"
      );
      if (!ok) return;
    }
    setYamlPath(newPath);
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", height: "75vh" }}>
      {/* Toolbar */}
      <Paper
        elevation={0}
        sx={{
          p: 1,
          mb: 1,
          display: "flex",
          alignItems: "center",
          gap: 1,
          bgcolor: "background.default",
          border: 1,
          borderColor: "divider",
          borderRadius: 1,
        }}
      >
        <YamlSelector value={yamlPath} onChange={handleYamlChange} />

        <Box sx={{ flex: 1 }} />

        <Tooltip title="Reload from disk (discards changes)">
          <span>
            <IconButton onClick={handleReload} size="small" disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </span>
        </Tooltip>

        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={() => handleSave()}
          disabled={!isDirty || saving || loading}
          color={isDirty ? "warning" : "primary"}
        >
          {saving ? "Saving..." : "Save"}
        </Button>
      </Paper>

      {/* Editor — div always mounted to keep CodeMirror alive */}
      <Paper
        elevation={0}
        sx={{
          flex: 1,
          overflow: "hidden",
          position: "relative",
          border: 1,
          borderColor: "divider",
          borderRadius: 1,
          "& .cm-editor": { height: "100%" },
          "& .cm-scroller": { overflow: "auto" },
        }}
      >
        <div ref={editorRef} style={{ height: "100%" }} />
        {loading && (
          <Box
            sx={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              bgcolor: "rgba(0, 0, 0, 0.4)",
              color: "text.secondary",
              zIndex: 1,
            }}
          >
            Loading...
          </Box>
        )}
      </Paper>

      {/* Status bar */}
      <Box
        sx={{
          mt: 1,
          display: "flex",
          alignItems: "center",
          gap: 2,
          color: "text.secondary",
          fontSize: "0.8rem",
        }}
      >
        <Box
          sx={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            bgcolor: isDirty ? "warning.main" : "success.main",
          }}
        />
        <span>{isDirty ? "Unsaved changes" : "Saved"}</span>
        {lastSaved && (
          <span>
            Last saved: {lastSaved.toLocaleTimeString()}
          </span>
        )}
        {yamlPath && (
          <span>
            File: {yamlPath}
          </span>
        )}
      </Box>

      {/* Error snackbar */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>

      {/* Success snackbar */}
      <Snackbar
        open={!!successMsg}
        autoHideDuration={3000}
        onClose={() => setSuccessMsg(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity="success" onClose={() => setSuccessMsg(null)}>
          {successMsg}
        </Alert>
      </Snackbar>
    </Box>
  );
}
