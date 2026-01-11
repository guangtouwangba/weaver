# Design: Knowledge Export Module

## Architecture

We will implement a client-side `ClipboardService` (or `lib/clipboard.ts`) that handles the transformation of selected Canvas Nodes into clipboard-friendly formats (Markdown/HTML).

### Spatial-to-Linear Mapping Protocol

The core challenge is flattening a 2D spatial arrangement into a 1D text stream.

#### 1. Grouping & Sorting
- **Algorithm**:
    1.  **Row grouping**: Nodes with Y-coordinates within a threshold (e.g., 50px) are grouped into a "row".
    2.  **Row sorting**: Sort rows by Y-coordinate.
    3.  **Column sorting**: Within each row, sort nodes by X-coordinate.
- **Exception (Mindmaps)**:
    - Mindmap nodes should be treated as a single coherent structure if a root or branch is selected.
    - If multiple disconnected mindmap nodes are selected, they follow spatial sorting, but their children (if selected) are nested under them.

#### 2. Content Conversion Strategy

| Node Type | Markdown Output | Notes |
| :--- | :--- | :--- |
| **Note/Text** | Text content | Headers if bolded/large? |
| **Mindmap Root** | `# Title` | |
| **Mindmap Branch** | `## Subtitle` or `- Item` | Depth determines header level or indentation |
| **Source (Video)** | `### 🎥 Title (timestamp)`<br>`> URL` | Embeds deep link if available |
| **Source (PDF)** | `### 📕 Filename`<br>`> Citation...` | |
| **Image** | `![Title](url)` | |

### API Design (`src/lib/clipboard.ts`)

```typescript
interface ClipboardItem {
  text: string; // Markdown
  html?: string; // Rich text for Word/Email (Future)
}

export function generateClipboardContent(nodes: CanvasNode[]): ClipboardItem {
  // 1. Sort nodes
  const sorted = sortNodesSpatially(nodes);
  
  // 2. Map to text
  const parts = sorted.map(node => convertNodeToMarkdown(node));
  
  return {
    text: parts.join('\n\n')
  };
}
```

### UX / Interaction
- **Shortcut**: `Ctrl+C` / `Cmd+C` in `KonvaCanvas`.
- **Feedback**: Immediate "Copied to clipboard" toast.
- **Visuals**: (Optional MVP) Transient numbers showing order on nodes.

## Constraints & Trade-offs
- **Images**: S3 signed URLs expire. For MVP, we use the URL as-is. Users might need to re-download if pasting into a local doc, creates broken links if pasted into public docs after expiration.
    - *Mitigation*: Use permanent URLs if available, or just accept this limitation for MVP. PRD suggests "Base64" for small files, but that bloats clipboard. 
- **Mindmap Selection**: What if a user selects a child node but not the parent?
    - *Decision*: Export as top-level list item/header. Context is lost but content is preserved.

