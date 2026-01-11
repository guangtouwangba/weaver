# Design: Split View Workspace (UI/UX Pro Max)

## Layout Architecture

### 1. Resizable Panel System
We will use `react-resizable-panels` to create a robust, persistent 3-pane layout. This replaces the current absolute positioning and modal overlays.

**Structure (`StudioPageContent`):**
```tsx
<ResizablePanelGroup direction="horizontal">
  {/* Left: Resources (Collapsible) */}
  <ResizablePanel defaultSize={20} minSize={15} collapsible>
    <ResourceSidebar />
  </ResizablePanel>
  
  <ResizableHandle />

  {/* Center: Content Docker (Dynamic) */}
  {activeContent && (
    <>
      <ResizablePanel defaultSize={40} minSize={30}>
         <ContentDocker 
           activeDocument={activeContent} 
           onClose={() => setActiveContent(null)}
         />
      </ResizablePanel>
      <ResizableHandle />
    </>
  )}

  {/* Right: Canvas (Main Workspace) */}
  <ResizablePanel defaultSize={40}>
    <KonvaCanvas />
    {/* Assistant is now an overlay *inside* this panel or a 4th panel? 
        Decision: Overlay inside Canvas is cleaner for "floating assistant" feel, 
        but a 4th panel is better for robust chat. 
        Current Decision: Keep Assistant as Overlay for now to minimize refactor scope. */}
    <AssistantPanelOverlay /> 
  </ResizablePanel>
</ResizablePanelGroup>
```

### 2. The `ContentDocker` Component
Features:
- **Tabs/Header**: Title, Close Button, "Open in New Tab" (external).
- **Toolbar**: Context-aware tools (PDF text selection, Video transcript toggle).
- **Viewer Container**: 
    - `PDFViewerPanel` (migrated from Modal).
    - `VideoPlayerPanel` (new).

### 3. Video Transformation
Replace `YouTubePlayerModal` with `VideoPlayerPanel`.
- **Top**: YouTube/Bilibili iframe (16:9 aspect ratio maintained).
- **Bottom**: `TranscriptViewer` (scrollable list).
- **Interaction**:
    - `onTranscriptClick(timestamp)` -> Seek video.
    - `onVideoProgress(time)` -> Auto-scroll transcript.
    - `onDragStart(transcriptSegment)` -> Create Mindmap Node.

## Interaction Design (Pro Max)

### Bi-directional Linking Flow
1. **Source -> Canvas (Creation)**:
   - **User**: Selects text in PDF or Transcript -> Drags to Canvas.
   - **System**: Renders "Ghost Card" under cursor.
   - **Drop**: Creates `NoteNode` with `sourceId` and `quote`. Canvas pans to center the new node.

2. **Canvas -> Source (Recall)**:
   - **User**: Clicks "Source Link" icon on a Node.
   - **System**: 
     - Checks if Content Panel is open? If no, opens it.
     - Loads correct document/video.
     - Scrolls PDF to highlight rect OR Seeks Video to timestamp.
     - Flashes the target content (yellow fade-out) for visual cue.

3. **Sync Highlight**:
   - **User**: Selects a Node.
   - **System**: If source matches open document, specific text/segment turns "Active Blue".

## Visual Polish (Tailwind)
- **Handles**: Thin `w-px bg-border hover:bg-primary/50 transition-colors` handles with grab cursor.
- **Active State**: Active panel gets subtle `ring-1 ring-primary/20` or distinct shadow.
- **Typography**: `Inter` for UI, `Merriweather` for PDF reading mode (if we control rendering).
