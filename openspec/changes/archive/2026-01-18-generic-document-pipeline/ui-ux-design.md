# Unified Document Experience: UI/UX Design & Architecture

## 1. Problem Statement
Currently, the system treats PDF files as "first-class citizens" with specialized UI handling (icons, colors, drag behavior), while other formats (TXT) are second-class or unsupported. Adding support for new formats (Video, DOCX) requires modifying core UI components, leading to brittle code and inconsistent UX.

## 2. Product Vision (L9 Perspective)
**"Everything is a Resource."**
The user shouldn't care about file formats. They interaction model should be consistent:
1.  **Import**: Drag & drop any supported file.
2.  **Visualize**: See a beautiful, recognizable card with a preview.
3.  **Interact**: Drag the card onto the Canvas to "open" it.
4.  **Preview**: Click to see content instantly.

## 3. Core Concepts

### 3.1 The "File DNA" Registry
Instead of hardcoding checks (`if isPdf`), we implement a Frontend Registry that defines the "DNA" of each file type.

| File Type | Color Theme | Icon | Canvas Node | Previewer |
|-----------|-------------|------|-------------|-----------|
| **PDF** | Red-500 | `PdfIcon` | `PdfNode` | `PdfViewer` |
| **TXT** | Gray-500 | `FileTextIcon` | `TextNode` | `TextPreviewer` |
| **DOCX** | Blue-500 | `WordIcon` | `DocNode` | `DocViewer` (or PDF convert) |
| **Video** | Purple-500 | `VideoIcon` | `VideoNode` | `VideoPlayer` |
| **Image** | Green-500 | `ImageIcon` | `ImageNode` | `ImageViewer` |

### 3.2 Unified Drag & Drop Workflow
1.  User drags file (TXT/PDF) into **Inbox**.
2.  Backend generates **Thumbnail** (already implemented in Phase 1).
3.  **DocumentCard** renders generic UI using "File DNA" (Icon + Color).
4.  User drags **DocumentCard** onto **Canvas**.
5.  Canvas detects `dragData.type` and renders appropriate Node.

## 4. Implementation Plan

### Phase 1: Frontend Registry & Component Refactor
1.  **Create `FileRegistry.ts`**:
    -   Maps extensions to config (icon, color, label).
    -   Helper functions: `getFileConfig(filename)`, `isSupported(filename)`.
2.  **Refactor `DocumentPreviewCard.tsx`**:
    -   Remove `isPdf` logic.
    -   Use `FileRegistry` to determine Icon and Color.
    -   Enable `draggable` for all supported types.
    -   Pass generic `dragData` (e.g., `type: 'resource'`, `mimeType: ...`).

### Phase 2: Canvas Integration
1.  **Update Canvas Drop Handler**:
    -   Handle generic `resource` drop events.
    -   Switch on `mimeType` or `fileType` to create nodes.
    -   **TXT**: Create a `TextNode` (shows scrollable text preview).
    -   **Video**: Create a `VideoNode` (shows player).
2.  **Add `TextNode` to Canvas**:
    -   Simple node rendering text content or rich markdown.

### Phase 3: Unified Preview Modal
1.  **Create `ResourcePreviewModal.tsx`**:
    -   Replaces `PDFPreviewModal`.
    -   Takes `resource` as prop.
    -   Renders `Registry.getPreviewComponent(resource)`.
2.  **Implement `TextPreviewer`**:
    -   Simple ScrollView for `.txt` content.
    -   Markdown renderer for `.md`.

## 5. UI/UX Details

### Document Card (Sidebar)
-   **Icon**: Dynamic based on type.
-   **Color**: Subtle background tint based on type color (e.g., Red-50 for PDF, Blue-50 for DOC).
-   **Thumbnail**: If backend provides `thumbnail_url`, show it on hover or as a small cover.

### Canvas Drag Preview
-   When dragging, show a "Ghost Card" with the file icon/thumbnail.
-   On drop, animate the expansion into the full Node.

## 6. Future Proofing
Adding `.docx` support later becomes:
1.  Add `.docx` to Backend `ThumbnailRegistry` (Phase 1 complete).
2.  Add `.docx` to Frontend `FileRegistry` (Icon, Color).
3.  (Optional) Add specialized `DocNode` or reuse `PdfNode` if converted.
