# Output Preview Tab — Design Spec

**Date**: 2026-06-29
**Feature**: New "Outputs" tab in the WebUI for browsing and previewing generated documents (PDF, DOCX, HTML) from the `output/` directory.

## Motivation

Currently, generated output files are only visible per-run from the History tab's expanded rows. Users want a dedicated space to browse **all** generated outputs at once — independent of build history — with inline preview of PDFs/HTML and easy download of DOCX/reports.

## Design

### Approach: Cards + Inline Preview

All output directories listed as expandable cards in a responsive grid. Expanding a card reveals file groups with inline preview (PDF/HTML via `<iframe>`) or download buttons (DOCX/JSON).

### Backend: New API Endpoint

**`GET /api/outputs`** — filesystem scan of `output/*/` directories, sorted newest-first.

```python
@app.get("/api/outputs")
async def list_outputs():
    """List all output subdirectories and their file contents."""
```

Response shape:
```json
{
  "directories": [
    {
      "slug": "acme-senior-backend-engineer-202606",
      "files": [
        {"name": "William_Jiang_CV.pdf", "type": "pdf", "size": 231383},
        {"name": "resume.docx", "type": "docx", "size": 39404},
        {"name": "William_Jiang_CV.html", "type": "html", "size": 50000},
        {"name": "ats-report.json", "type": "json", "size": 4802}
      ]
    }
  ]
}
```

File types are inferred from extension: `pdf`, `docx`, `html`, `json`, `txt`, `jpg`, `png`, `typ`. The existing `_mime_for_file()` utility is reused for download headers.

Existing `/api/output/{job_id}` and `/api/output/{job_id}/download?name=X` endpoints already serve individual files. The new endpoint provides the directory listing; file serving reuses existing endpoints — though the new Outputs tab will construct direct download URLs to `api/output/{slug}/download?name=X` using the slug as a job_id surrogate for file resolution. (The backend `_resolve_output_path` already falls back to scanning all output subdirectories by name, so it resolves files via slug.)

### Frontend: New OutputPage Component

**File**: `ui/frontend/src/pages/OutputPage.tsx`

**States**:
- **Loading**: MUI `Skeleton` placeholders for 3-4 cards
- **Empty**: Alert "No output files found. Run a build first."
- **Error**: Alert with error message
- **Data**: Grid of cards, one per output directory

**Card layout** (MUI `Card`):
- Header: slug name, count of files
- Expandable section (MUI `Collapse`):
  - PDF files → click opens inline `<iframe>` preview in a dialog or expanded section
  - DOCX files → download link (opens in new tab)
  - HTML files → inline iframe preview
  - JSON/text files → download link
  - Other → generic download link

**File type icons** (reuse from HistoryTable):
- PDF → `PictureAsPdfIcon` (red)
- DOCX → `DescriptionIcon` (blue)
- HTML → `LanguageIcon`
- JSON → `AssessmentIcon`

**Responsive grid**: `Grid2` with `lg={4} md={6} xs={12}` breakpoints.

### Frontend: Tab Navigation Update

Insert "Outputs" tab between Compare (index 2) and History (index 3) in `App.tsx`:

| Index | Tab | Icon | Page |
|-------|-----|------|------|
| 0 | Resume | DescriptionIcon | ResumePage |
| 1 | Transform | AutoFixHighIcon | TransformPage |
| 2 | Compare | CompareArrowsIcon | ComparePage |
| **3** | **Outputs** | **FolderOpenIcon** | **OutputPage** |
| 4 | History | HistoryIcon | HistoryPage |
| 5 | Editor | EditIcon | EditorPage |

Import `FolderOpenIcon` from `@mui/icons-material/FolderOpen`.

### Frontend: API Client + Types

**Types** (`types.ts`):
```typescript
export interface OutputsResponse {
  directories: OutputDirInfo[];
}

export interface OutputDirInfo {
  slug: string;
  files: OutputFile[];
}
```

Existing `OutputFile` type already has `name`, `type`, `slug`, `size`.

**API client** (`client.ts`):
```typescript
listOutputs: () => get<OutputsResponse>("/outputs"),
```

## Implementation Order

1. Backend: add `GET /api/outputs` endpoint
2. Frontend: add types + API client method
3. Frontend: create `OutputPage.tsx` component
4. Frontend: add tab to `App.tsx` navigation
5. Verify: `lsp_diagnostics` + `npm run build`

## Open Questions

None — design approved inline during brainstorming.
