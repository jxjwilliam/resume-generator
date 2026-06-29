import { useEffect, useState, useCallback } from "react";
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Collapse,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  Skeleton,
  Stack,
  Typography,
  Alert,
  Chip,
} from "@mui/material";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";
import DescriptionIcon from "@mui/icons-material/Description";
import TextSnippetIcon from "@mui/icons-material/TextSnippet";
import AssessmentIcon from "@mui/icons-material/Assessment";
import LanguageIcon from "@mui/icons-material/Language";
import InsertDriveFileIcon from "@mui/icons-material/InsertDriveFile";
import ImageIcon from "@mui/icons-material/Image";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import CloseIcon from "@mui/icons-material/Close";
import { api } from "../api/client";
import type { OutputDirInfo } from "../types";

const RECRUITER_FILE_TYPES = new Set(["pdf", "docx", "cover-letter"]);

function fileIcon(type: string) {
  switch (type) {
    case "pdf":
      return <PictureAsPdfIcon fontSize="small" sx={{ color: "error.main" }} />;
    case "docx":
      return <DescriptionIcon fontSize="small" sx={{ color: "primary.main" }} />;
    case "html":
      return <LanguageIcon fontSize="small" sx={{ color: "success.main" }} />;
    case "cover-letter":
      return <TextSnippetIcon fontSize="small" sx={{ color: "info.main" }} />;
    case "ats-report":
    case "bullet-diff":
    case "json":
      return <AssessmentIcon fontSize="small" sx={{ color: "warning.main" }} />;
    case "jpg":
    case "png":
      return <ImageIcon fontSize="small" sx={{ color: "text.secondary" }} />;
    default:
      return <InsertDriveFileIcon fontSize="small" sx={{ color: "text.secondary" }} />;
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatSlug(slug: string): string {
  return slug.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function needsHtmlPreview(type: string): boolean {
  return type === "docx" || type === "txt" || type === "json" || type === "other";
}

function previewUrl(slug: string, name: string, type: string): string {
  const encoded = encodeURIComponent(name);
  return needsHtmlPreview(type)
    ? `/api/outputs/html-preview/${encodeURIComponent(slug)}?name=${encoded}`
    : `/api/outputs/view/${encodeURIComponent(slug)}?name=${encoded}`;
}

interface PreviewDialogProps {
  open: boolean;
  title: string;
  url: string;
  onClose: () => void;
}

function PreviewDialog({ open, title, url, onClose }: PreviewDialogProps) {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="xl" fullWidth>
      <DialogTitle sx={{ pr: 6 }}>
        {title}
        <IconButton onClick={onClose} sx={{ position: "absolute", right: 8, top: 8 }}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent sx={{ height: "85vh", p: 0 }}>
        <iframe
          src={url}
          title={title}
          style={{ width: "100%", height: "100%", border: "none" }}
        />
      </DialogContent>
    </Dialog>
  );
}

interface OutputCardProps {
  dir: OutputDirInfo;
}

function OutputCard({ dir }: OutputCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [preview, setPreview] = useState<{ name: string; url: string } | null>(null);

  const recruiterFiles = dir.files.filter((f) => RECRUITER_FILE_TYPES.has(f.type));
  const configCount = dir.files.length - recruiterFiles.length;

  const downloadUrl = (name: string) =>
    `/api/output/${encodeURIComponent(dir.slug)}/download?name=${encodeURIComponent(name)}`;

  return (
    <>
      <Card variant="outlined">
        <CardHeader
          title={
            <Typography variant="subtitle1" fontWeight={600}>
              {formatSlug(dir.slug)}
            </Typography>
          }
          subheader={
            <Typography variant="caption" color="text.secondary">
              {recruiterFiles.length} file{recruiterFiles.length !== 1 ? "s" : ""}
              {configCount > 0 ? ` (+${configCount} config)` : ""}
            </Typography>
          }
          action={
            <IconButton onClick={() => setExpanded(!expanded)} size="small" sx={{ mr: 1, mt: 1 }}>
              {expanded ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
            </IconButton>
          }
        />
        <Collapse in={expanded}>
          <CardContent sx={{ pt: 0 }}>
            {recruiterFiles.length === 0 ? (
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: "italic" }}>
                No recruiter-ready files
              </Typography>
            ) : (
              <Stack spacing={0.5}>
                {recruiterFiles.map((f) => (
                  <Box
                    key={f.name}
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 1,
                      py: 0.5,
                      px: 1,
                      borderRadius: 1,
                      cursor: "pointer",
                      "&:hover": { bgcolor: "action.hover" },
                    }}
                    onClick={() =>
                      setPreview({ name: f.name, url: previewUrl(dir.slug, f.name, f.type) })
                    }
                  >
                    {fileIcon(f.type)}
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Typography variant="body2" noWrap>
                        {f.name}
                      </Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary" sx={{ whiteSpace: "nowrap" }}>
                      {formatSize(f.size)}
                    </Typography>
                    <Chip
                      label={f.type}
                      size="small"
                      variant="outlined"
                      sx={{ height: 20, "& .MuiChip-label": { fontSize: "0.65rem", px: 0.5 } }}
                    />
                    <IconButton
                      size="small"
                      component="a"
                      href={downloadUrl(f.name)}
                      target="_blank"
                      onClick={(e: React.MouseEvent) => e.stopPropagation()}
                      title="Download"
                    >
                      <OpenInNewIcon fontSize="small" />
                    </IconButton>
                  </Box>
                ))}
              </Stack>
            )}
          </CardContent>
        </Collapse>
      </Card>

      {preview && (
        <PreviewDialog
          open={!!preview}
          title={preview.name}
          url={preview.url}
          onClose={() => setPreview(null)}
        />
      )}
    </>
  );
}

function CardSkeleton() {
  return (
    <Card variant="outlined">
      <CardHeader
        title={<Skeleton width="60%" />}
        subheader={<Skeleton width="30%" />}
      />
    </Card>
  );
}

export default function OutputPage() {
  const [dirs, setDirs] = useState<OutputDirInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const resp = await api.listOutputs();
      setDirs(resp.directories);
    } catch (e: any) {
      setError(e.message || "Failed to load outputs");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <Box>
        <Typography variant="h6" gutterBottom>Generated Outputs</Typography>
        <Box sx={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: 2 }}>
          {[1, 2, 3].map((i) => <CardSkeleton key={i} />)}
        </Box>
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Typography variant="h6" gutterBottom>Generated Outputs</Typography>
        <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
      </Box>
    );
  }

  if (dirs.length === 0) {
    return (
      <Box>
        <Typography variant="h6" gutterBottom>Generated Outputs</Typography>
        <Alert severity="info">
          No output files found. Run a build from the Resume tab first.
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Generated Outputs
        <Typography variant="body2" color="text.secondary" component="span" sx={{ ml: 1 }}>
          ({dirs.length} build{dirs.length !== 1 ? "s" : ""})
        </Typography>
      </Typography>

      <Box sx={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: 2 }}>
        {dirs.map((d) => (
          <OutputCard key={d.slug} dir={d} />
        ))}
      </Box>
    </Box>
  );
}
