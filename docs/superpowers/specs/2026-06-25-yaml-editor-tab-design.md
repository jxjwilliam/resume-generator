# YAML Editor Tab — Design Spec

**Date:** 2026-06-25
**Status:** Approved

## Overview

Add a 5th "Editor" tab to the WebUI that lets the user read, edit, and save any `profiles/*.yaml` file (all `base*.yaml` versions) directly from the browser using a CodeMirror 6 code editor with YAML syntax highlighting.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  App.tsx                                            │
│  ┌─────────────────────────────────────────────────┐│
│  │ Tab bar: Resume │ Transform │ Compare │ History │ Editor │
│  └─────────────────────────────────────────────────┘│
│                                                      │
│  tab === 4 → <EditorPage />                          │
└──────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────┐
│  EditorPage.tsx                                      │
│  ┌──────────────────────────────────────────────────┐│
│  │ Toolbar: [YamlSelector ▼]  [💾 Save] [↻ Reload] ││
│  ├──────────────────────────────────────────────────┤│
│  │ CodeMirror 6 YAML editor                        ││
│  │ (syntax highlight, line numbers, code folding)   ││
│  ├──────────────────────────────────────────────────┤│
│  │ Status bar: saved/unsaved │ validation errors    ││
│  └──────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────┘
         │
         ├── GET  /api/yaml?path=profiles/base.yaml
         └── PUT  /api/yaml  { path, content }
```

## Backend Changes

### New endpoint: `GET /api/yaml`

- Query param: `path` (default: `profiles/base.yaml`)
- Reads file from disk, returns `{ path, content }` where content is raw YAML text
- Returns 404 if file doesn't exist
- The path must resolve under `REPO_ROOT / profiles/` (security: prevent directory traversal by resolving against `PROFILES_DIR`)

### New endpoint: `PUT /api/yaml`

- Body: `{ path, content }` via `YamlSaveRequest` model
- Validates content is parseable YAML via `yaml.safe_load()`
- Creates a backup of the original file (`base.yaml~`) before writing
- Writes new content to disk
- Returns `{ status: "saved", path }` on success
- Returns 422 with `{ error, line }` if YAML is invalid (parse error with line number)
- Returns 500 on OS write errors

### New model in `models.py`

```python
class YamlSaveRequest(BaseModel):
    path: str = DEFAULT_YAML
    content: str
```

### Security

- Path is resolved relative to `REPO_ROOT / PROFILES_DIR` to prevent directory traversal
- Only files ending in `.yaml` or `.yml` are accepted
- No authentication (localhost-only, matching existing pattern)

## Frontend Changes

### New file: `ui/frontend/src/pages/EditorPage.tsx`

State management (React hooks):

| State | Type | Purpose |
|---|---|---|
| `yamlPath` | `string` | Currently selected YAML file path |
| `content` | `string` | Current editor content |
| `originalContent` | `string` | Last-saved snapshot (for dirty detection) |
| `saving` | `boolean` | Save-in-progress flag |
| `loading` | `boolean` | Load-in-progress flag |
| `error` | `string \| null` | Error message to display |
| `lastSaved` | `Date \| null` | Timestamp of last successful save |

### Changes to `ui/frontend/src/App.tsx`

- Import `EditIcon` from `@mui/icons-material/Edit`
- Import `EditorPage` from `./pages/EditorPage`
- Add tab index 4 with `EditIcon` + label "Editor"
- Render `<EditorPage />` when `tab === 4`
- Shift existing code: Resume=0, Transform=1, Compare=2, History=3, Editor=4

### Changes to `ui/frontend/src/api/client.ts`

Add methods:
```typescript
getYaml: (path?: string) => get<YamlContent>(`/yaml?path=${encodeURIComponent(path || DEFAULT_YAML_PATH)}`),
saveYaml: (path: string, content: string) => post<YamlSaveResponse>("/yaml", { path, content }),
```

### Changes to `ui/frontend/src/types.ts`

Add types:
```typescript
export interface YamlContent {
  path: string;
  content: string;
}

export interface YamlSaveResponse {
  status: string;
  path: string;
}
```

### New dependencies: `package.json`

```json
{
  "codemirror": "^6.0.0",
  "@codemirror/lang-yaml": "^6.0.0",
  "@codemirror/theme-one-dark": "^6.0.0",
  "@codemirror/view": "^6.0.0",
  "@codemirror/state": "^6.0.0",
  "js-yaml": "^4.1.0"
}
```

## EditorPage UX Detail

### Toolbar

- **YamlSelector** (existing component) — dropdown listing all `profiles/*.yaml` files fetched from `GET /api/yamls`
- **Save button** — MUI `LoadingButton`, enabled only when content is dirty (`content !== originalContent`). Shows spinner during save. Ctrl+S also triggers save.
- **Reload button** — Icon button, re-fetches YAML from server. Confirms if there are unsaved changes.

### CodeMirror Editor

- YAML language mode for syntax highlighting
- Line numbers, active line highlight, bracket matching
- Code folding for top-level YAML keys
- Tab = 2 spaces (YAML convention)
- Dark theme by default (matching the existing app's dark-ish aesthetic)
- Auto-height to fill available viewport

### Status Bar

- MUI `Alert` or styled box at the bottom
- States:
  - Green: "Saved at 12:34 PM"
  - Yellow: "Unsaved changes"
  - Red inline: YAML parse error with line number (client-side via `js-yaml`)
- Shows error flash on save failure

### Unsaved Changes Guard

- `window.addEventListener('beforeunload')` warns when navigating away with dirty content
- On YAML file switch via dropdown, confirm dialog if content is dirty

## Error Handling

| Scenario | Handling |
|---|---|
| File not found | Show empty editor with banner "File not found. Save to create it." |
| Invalid YAML on save | Backend returns 422; frontend shows error with line number |
| Write permission error | Backend returns 500; frontend shows "Could not write file: {message}" |
| Network error | Show MUI Snackbar error toast |

## Files Changed

| File | Change |
|---|---|
| `ui/backend/main.py` | Add `GET /api/yaml` and `PUT /api/yaml` endpoints |
| `ui/backend/models.py` | Add `YamlSaveRequest` model |
| `ui/frontend/src/App.tsx` | Add Editor tab (index 4), import `EditorPage` |
| `ui/frontend/src/pages/EditorPage.tsx` | **New file** — full editor page |
| `ui/frontend/src/api/client.ts` | Add `getYaml()` and `saveYaml()` methods |
| `ui/frontend/src/types.ts` | Add `YamlContent` and `YamlSaveResponse` types |
| `ui/frontend/package.json` | Add CodeMirror 6 + js-yaml deps |
| `ui/frontend/package-lock.json` | Updated via npm install |

## Out of Scope

- Diff view / version history (beyond the `~` backup file)
- Form-based field editing (intentionally raw YAML)
- Multi-user / locking (single-user local tool)
- Schema-aware autocomplete (future enhancement)
