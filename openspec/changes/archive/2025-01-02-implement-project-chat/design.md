# Design: Project Chat & Drag-and-Drop

## Architecture

### Frontend
- **Components**:
    - `CanvasChatButton`: Floating action button at bottom center.
    - `CanvasChatPanel`: The main chat container.
    - `ChatMessage`: Individual message bubble.
    - `ChatInput`: Text area + Drop zone.
- **State Management**:
    - Manage chat history in `StudioContext` or a new `ChatContext`.
    - Handle `isChatOpen` state.
- **Drag & Drop**:
    - **Inbound (to Chat)**: Use `react-dnd` or HTML5 native DnD. Since Konva handles its own drag, we might need a bridge.
        - *Challenge*: Konva nodes are inside the canvas. We need to detect when a Konva node is dragged *over* the DOM overlay of the chat.
    - **Outbound (to Canvas)**: Dragging a message bubble needs to trigger a "node creation" on drop upon the canvas.

### Backend
- Re-use `research_agent.application.use_cases` logic.
- Ensure `comments` or `annotations` repositories are not mixed up, but `documents` are used.
- Response format:
    ```json
    {
      "text": "The market trend is...",
      "sources": [
        { "doc_id": "...", "page": 1, "text": "...", "score": 0.9, "quote": "exact text snippet" }
      ]
    }
    ```

### Citation Highlighting Strategy
- **Frontend**:
    - `PDFViewerWrapper` already uses `pdfjs-dist`'s `PDFFindController`.
    - We will use the `highlightText` prop on `PDFViewer` (and `SourcePanel`) to pass the citation quote.
    - When a citation is clicked, update `StudioContext` to not only set `activeDocumentId` and `pageNumber` (via `sourceNavigation`) but also a new `highlightQuote` state.
    - `SourcePanel` will pass this `highlightQuote` to `PDFViewer` -> `PDFViewerWrapper`, which will trigger `findController.executeCommand('find', ...)` to highlight the text.


## Unknowns / Risks
- **Konva vs DOM Drag**: Dragging from Konva canvas to a DOM element (Chat Input) can be tricky.
    - *Plan*: When dragging a node in Konva, we can track the global pointer. If released over the Chat Input area (calculated by client bounds), trigger the "Add Context" action.

