'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { Box, Menu, MenuItem, TextField, Button, IconButton, Paper, Snackbar, Alert, Slide, Tooltip } from '@mui/material';
import { EditIcon, DeleteIcon, CloseIcon, ErrorIcon } from '@/components/ui/icons';
import { highlightsApi } from '@/lib/api'; // Removed HighlightResponse from import as we use local type extending it
import dynamic from 'next/dynamic';
import { SelectionManager } from './SelectionManager';
import { HighlightOverlay } from './HighlightOverlay';
import { SelectionToolbar } from './SelectionToolbar';
import { createDragHandler } from './DragHandler';
import { TextSelection, Highlight, HighlightColor, ToolMode, AnnotationColor } from './types';
import '@/styles/pdf-viewer.css';

const PDFViewerWrapper = dynamic(
  () => import('./PDFViewerWrapper').then((mod) => mod.PDFViewerWrapper),
  { ssr: false }
);

interface PDFViewerProps {
  documentId: string;
  fileUrl: string; // Changed from content: React.ReactNode
  pageNumber: number;
  onPageChange: (page: number) => void;
  onDocumentLoad: (numPages: number) => void;
  onHighlightCreate?: (highlight: Highlight) => void;
  onHighlightUpdate?: (highlight: Highlight) => void;
  onHighlightDelete?: (highlightId: string) => void;
  highlightText?: string; // For search highlighting
  activeTool?: ToolMode;
  activeColor?: AnnotationColor;
  highlights?: Highlight[]; // Controlled mode
}

export function PDFViewer({
  documentId,
  fileUrl,
  pageNumber,
  onPageChange,
  onDocumentLoad,
  onHighlightCreate,
  onHighlightUpdate,
  onHighlightDelete,
  highlightText,
  activeTool,
  activeColor,
  highlights: controlledHighlights,
}: PDFViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [internalHighlights, setInternalHighlights] = useState<Highlight[]>([]);

  // Use controlled highlights if provided, otherwise internal
  const highlights = controlledHighlights || internalHighlights;

  const [textSelection, setTextSelection] = useState<TextSelection | null>(null);

  const [toolbarPosition, setToolbarPosition] = useState<{ x: number; y: number } | null>(null);
  const [highlightMenuAnchor, setHighlightMenuAnchor] = useState<{ x: number; y: number } | null>(null);
  const [selectedHighlight, setSelectedHighlight] = useState<Highlight | null>(null);
  const [noteDialogOpen, setNoteDialogOpen] = useState(false);
  const [noteText, setNoteText] = useState('');
  const [isCreatingHighlight, setIsCreatingHighlight] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [pendingHighlights, setPendingHighlights] = useState<Map<string, { highlight: Highlight; retryCount: number }>>(new Map());

  const [pendingNoteSelection, setPendingNoteSelection] = useState<{
    text: string;
    position: TextSelection;
  } | null>(null);

  // Drag Handler
  const dragHandler = useRef(createDragHandler(documentId, "PDF Document")); // We might want actual title

  // Initialize SelectionManager
  useEffect(() => {
    if (!containerRef.current) return;

    const manager = new SelectionManager(containerRef.current, (selection) => {
      setTextSelection(selection);

      if (selection) {
        // Calculate toolbar position (centered above selection)
        const firstRect = selection.rects[0];
        const lastRect = selection.rects[selection.rects.length - 1];
        // Rects are client rects
        const centerX = (firstRect.left + lastRect.right) / 2;
        const topY = Math.min(...selection.rects.map(r => r.top));

        setToolbarPosition({ x: centerX, y: topY });
      } else {
        setToolbarPosition(null);
      }
    });

    return () => manager.destroy();
  }, []);

  // Load Highlights (Only if not controlled)
  useEffect(() => {
    if (controlledHighlights || !documentId) return;

    const loadHighlights = async () => {
      try {
        const highlightsList = await highlightsApi.list(documentId);
        setInternalHighlights(
          highlightsList.map((h) => ({
            ...h,
            rects: h.rects
              ? h.rects.map(
                (rect) =>
                  new DOMRect(
                    rect.left,
                    rect.top,
                    rect.width,
                    rect.height
                  )
              )
              : [],
          }))
        );
      } catch (error) {
        console.error('Failed to load highlights:', error);
        setInternalHighlights([]);
      }
    };

    loadHighlights();
  }, [documentId]);

  // Handle color select
  const handleColorSelect = useCallback(
    async (color: HighlightColor) => {
      if (!textSelection || !toolbarPosition || isCreatingHighlight) return;

      setIsCreatingHighlight(true);

      // Calculate relative rects for saving
      if (!containerRef.current) return;
      const containerRect = containerRef.current.getBoundingClientRect();
      const scrollLeft = containerRef.current.scrollLeft;
      const scrollTop = containerRef.current.scrollTop;

      const relativeRects = textSelection.rects.map(rect =>
        new DOMRect(
          rect.left - containerRect.left + scrollLeft,
          rect.top - containerRect.top + scrollTop,
          rect.width,
          rect.height
        )
      );

      // Optimistic update
      const tempId = `local-${Date.now()}`;
      const highlightWithRects: Highlight = {
        id: tempId,
        documentId,
        pageNumber: textSelection.pageNumber,
        // offset calculation is tricky with just rects, skipping specific offset logic for now or deriving it if needed.
        // The API might expect startOffset/endOffset. 
        // For now, we'll try to guess or just send 0 if backend allows, or we need to map rects to text offsets using PDFJS text layer.
        // Given complexity, let's assume we send 0 and rely on rects for rendering if backend supports it.
        startOffset: 0,
        endOffset: 0,
        color,
        type: (activeTool === 'underline' || activeTool === 'strike') ? activeTool : 'highlight',
        textContent: textSelection.text,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        rects: relativeRects,
      };

      if (!controlledHighlights) {
        setInternalHighlights((prev) => [...prev, highlightWithRects]);
      }

      // Clear selection
      window.getSelection()?.removeAllRanges();
      setTextSelection(null);
      setToolbarPosition(null);
      setIsCreatingHighlight(false);

      // API call logic (simplified from original)
      try {
        const newHighlight = await highlightsApi.create(documentId, {
          pageNumber: highlightWithRects.pageNumber,
          startOffset: highlightWithRects.startOffset || 0,
          endOffset: highlightWithRects.endOffset || 0,
          color,
          type: highlightWithRects.type,
          textContent: highlightWithRects.textContent,
          rects: relativeRects.map((rect) => ({
            left: rect.left,
            top: rect.top,
            width: rect.width,
            height: rect.height,
            right: rect.right,
            bottom: rect.bottom,
          })),
        });

        if (!controlledHighlights) {
          setInternalHighlights((prev) =>
            prev.map((h) => (h.id === tempId ? { ...newHighlight, rects: relativeRects } : h))
          );
        }
        onHighlightCreate?.({ ...newHighlight, rects: relativeRects });
      } catch (error) {
        console.error('Failed to create highlight', error);
        if (!controlledHighlights) {
          setInternalHighlights(prev => prev.filter(h => h.id !== tempId)); // Revert
        }
        setErrorMessage('Failed to create highlight');
      }
    },
    [textSelection, toolbarPosition, documentId, onHighlightCreate, isCreatingHighlight, activeTool, controlledHighlights]
  );

  // Handle Add Note
  const handleAddNote = useCallback(() => {
    if (!textSelection) return;
    setPendingNoteSelection({
      text: textSelection.text,
      position: textSelection
    });
    setNoteDialogOpen(true);
  }, [textSelection]);

  // Handle Save Note
  const handleSaveNote = useCallback(async () => {
    if (!pendingNoteSelection || !containerRef.current) return;
    const { position } = pendingNoteSelection;

    const containerRect = containerRef.current.getBoundingClientRect();
    const scrollLeft = containerRef.current.scrollLeft;
    const scrollTop = containerRef.current.scrollTop;

    const relativeRects = position.rects.map(rect =>
      new DOMRect(
        rect.left - containerRect.left + scrollLeft,
        rect.top - containerRect.top + scrollTop,
        rect.width,
        rect.height
      )
    );

    const tempId = `local-${Date.now()}`;
    const highlightWithRects: Highlight = {
      id: tempId,
      documentId,
      pageNumber: position.pageNumber,
      startOffset: 0,
      endOffset: 0,
      color: 'yellow',
      note: noteText,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      rects: relativeRects,
    };

    if (!controlledHighlights) {
      setInternalHighlights((prev) => [...prev, highlightWithRects]);
    }
    setNoteDialogOpen(false);
    setNoteText('');
    setPendingNoteSelection(null);
    window.getSelection()?.removeAllRanges();
    setTextSelection(null);

    try {
      const newHighlight = await highlightsApi.create(documentId, {
        pageNumber: position.pageNumber,
        startOffset: 0,
        endOffset: 0,
        color: 'yellow',
        note: noteText,
        rects: relativeRects.map((rect) => ({
          left: rect.left,
          top: rect.top,
          width: rect.width,
          height: rect.height,
          right: rect.right,
          bottom: rect.bottom,
        })),
      });

      if (!controlledHighlights) {
        setInternalHighlights((prev) =>
          prev.map((h) => (h.id === tempId ? { ...newHighlight, rects: relativeRects } : h))
        );
      }
      onHighlightCreate?.({ ...newHighlight, rects: relativeRects });
    } catch (error) {
      console.error('Failed to create highlight with note', error);
      if (!controlledHighlights) {
        setInternalHighlights(prev => prev.filter(h => h.id !== tempId));
      }
      setErrorMessage('Failed to create highlight');
    }
  }, [pendingNoteSelection, noteText, documentId, onHighlightCreate]);

  // Handle Copy
  const handleCopy = useCallback(() => {
    if (textSelection) {
      navigator.clipboard.writeText(textSelection.text);
      window.getSelection()?.removeAllRanges();
      setTextSelection(null);
      setToolbarPosition(null);
    }
  }, [textSelection]);

  // Handle Highlight Click
  const handleHighlightClick = useCallback((highlight: Highlight, event?: React.MouseEvent | MouseEvent) => {
    setSelectedHighlight(highlight);
    if (event) {
      // If we have event, use it for positioning menu
      const mouseEvent = event as MouseEvent; // or React.MouseEvent
      setHighlightMenuAnchor({ x: mouseEvent.clientX, y: mouseEvent.clientY - 10 });
    } else if (highlight.rects && highlight.rects.length > 0 && containerRef.current) {
      // Fallback to rect calculation if no event
      // Note: highlight.rects are relative to container content
      // We need to convert to client coordinates for menu positioning
      const containerRect = containerRef.current.getBoundingClientRect();
      const firstRect = highlight.rects[0];
      // relative left + container left - scrollLeft
      const clientLeft = firstRect.left + containerRect.left - containerRef.current.scrollLeft;
      const clientTop = firstRect.top + containerRect.top - containerRef.current.scrollTop;

      setHighlightMenuAnchor({ x: clientLeft + firstRect.width / 2, y: clientTop });
    }
  }, []);

  const handleDeleteHighlight = useCallback(async () => {
    if (!selectedHighlight) return;
    const deleted = selectedHighlight;
    if (!controlledHighlights) {
      setInternalHighlights(prev => prev.filter(h => h.id !== deleted.id));
    }
    setHighlightMenuAnchor(null);
    setSelectedHighlight(null);

    try {
      await highlightsApi.delete(documentId, deleted.id);
      onHighlightDelete?.(deleted.id);
    } catch (e) {
      if (!controlledHighlights) {
        setInternalHighlights(prev => [...prev, deleted]);
      }
      setErrorMessage('Failed to delete highlight');
    }
  }, [selectedHighlight, documentId, onHighlightDelete]);

  // Handle Edit Note (simplified)
  const handleEditHighlight = useCallback(() => {
    if (!selectedHighlight) return;
    setNoteText(selectedHighlight.note || '');
    setNoteDialogOpen(true);
    setHighlightMenuAnchor(null);
  }, [selectedHighlight]);

  const handleSaveEditNote = useCallback(async () => {
    if (!selectedHighlight) return;
    const original = selectedHighlight;
    const updated = { ...original, note: noteText };

    if (!controlledHighlights) {
      setInternalHighlights(prev => prev.map(h => h.id === original.id ? updated : h));
    }
    setNoteDialogOpen(false);
    setNoteText('');
    setSelectedHighlight(null);

    try {
      await highlightsApi.update(documentId, original.id, { note: noteText });
      onHighlightUpdate?.(updated);
    } catch (e) {
      if (!controlledHighlights) {
        setInternalHighlights(prev => prev.map(h => h.id === original.id ? original : h));
      }
      setErrorMessage('Failed to update note');
    }
  }, [selectedHighlight, noteText, documentId, onHighlightUpdate]);

  const handleChangeColor = useCallback(async (color: HighlightColor) => {
    if (!selectedHighlight) return;
    const original = selectedHighlight;
    const updated = { ...original, color };

    if (!controlledHighlights) {
      setInternalHighlights(prev => prev.map(h => h.id === original.id ? updated : h));
    }
    setHighlightMenuAnchor(null);
    setSelectedHighlight(null);

    try {
      await highlightsApi.update(documentId, original.id, { color });
      onHighlightUpdate?.(updated);
    } catch (e) {
      if (!controlledHighlights) {
        setInternalHighlights(prev => prev.map(h => h.id === original.id ? original : h));
      }
      setErrorMessage('Failed to update color');
    }
  }, [selectedHighlight, documentId, onHighlightUpdate]);


  return (
    <Box ref={containerRef} sx={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden' }}>
      <PDFViewerWrapper
        fileUrl={fileUrl}
        pageNumber={pageNumber}
        width={containerRef.current?.clientWidth || 800}
        onPageChange={onPageChange}
        onDocumentLoad={onDocumentLoad}
        onTextSelect={() => { }} // Handled by SelectionManager
        highlightText={highlightText}
      />

      <HighlightOverlay
        highlights={highlights.filter(h => h.pageNumber === pageNumber)}
        selection={textSelection}
        searchHighlight={null} // TODO: Implement search highlight mapping if needed
        containerRef={containerRef}
        onHighlightClick={handleHighlightClick}
      />

      {toolbarPosition && textSelection && (
        <SelectionToolbar
          position={toolbarPosition}
          selectedText={textSelection.text}
          onColorSelect={handleColorSelect}
          onAddNote={handleAddNote}
          onCopy={handleCopy}
          onClose={() => {
            window.getSelection()?.removeAllRanges();
            setTextSelection(null);
            setToolbarPosition(null);
          }}
        />
      )}

      {/* Draggable Handle for selection - Optional, dragging usually works on text selection natively 
          but plan mentioned custom drag handler. 
          SelectionManager detects selection, we can attach drag event listener to the container.
          Actually, native drag works if we select text.
          If we want "DraggableSelectionHandle" as in plan:
          
          <DraggableSelectionHandle
             selection={textSelection}
             onDragStart={(e) => dragHandler.current.handleDragStart(e, textSelection)}
           />
           
           I'll skip explicit handle for now as native text drag is often preferred, 
           BUT the plan had `DragHandler` which sets custom data.
           We can add a draggable element over the selection or just intercept dragstart on container (which we do in SourcePanel).
           
           In SourcePanel:
           document.addEventListener('dragstart', handleDragStart);
           
           Here we can rely on that or move it here. 
           The plan has `DragHandler.ts` which provides `handleDragStart`.
           The plan's `SourcePanel` refactor section adds:
           <DraggableSelectionHandle ... />
           
           Since I am inside `PDFViewer`, I can just ensure `dragstart` is handled.
           I'll stick to native behavior for now or add a listener to container.
      */}

      {/* Highlighting Menu */}
      <Menu
        open={Boolean(highlightMenuAnchor)}
        onClose={() => { setHighlightMenuAnchor(null); setSelectedHighlight(null); }}
        anchorReference="anchorPosition"
        anchorPosition={highlightMenuAnchor ? { top: highlightMenuAnchor.y, left: highlightMenuAnchor.x } : undefined}
        PaperProps={{ sx: { borderRadius: 3, p: 0.5 } }}
        MenuListProps={{ sx: { display: 'flex', gap: 0.5, p: 0 } }}
      >
        {(['yellow', 'green', 'blue', 'pink'] as HighlightColor[]).map((color) => (
          <MenuItem key={color} onClick={() => handleChangeColor(color)} sx={{ p: 0, minWidth: 0, borderRadius: 2 }}>
            <Box sx={{ width: 28, height: 28, bgcolor: color === 'yellow' ? '#FFEB3B' : color === 'green' ? '#4CAF50' : color === 'blue' ? '#2196F3' : '#E91E63', borderRadius: 1.5 }} />
          </MenuItem>
        ))}
        <MenuItem onClick={handleEditHighlight} sx={{ p: 0.5, minWidth: 0, borderRadius: 2 }}><EditIcon size="sm" /></MenuItem>
        <MenuItem onClick={handleDeleteHighlight} sx={{ p: 0.5, minWidth: 0, borderRadius: 2, color: 'error.main' }}><DeleteIcon size="sm" /></MenuItem>
      </Menu>

      {/* Note Dialog */}
      {noteDialogOpen && (
        <Box sx={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, bgcolor: 'rgba(0,0,0,0.5)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center' }} onClick={() => setNoteDialogOpen(false)}>
          <Paper sx={{ width: 500, p: 3, borderRadius: 3 }} onClick={e => e.stopPropagation()}>
            <Typography variant="h6" mb={2}>{selectedHighlight ? 'Edit Note' : 'Add Note'}</Typography>
            <TextField
              multiline rows={5} fullWidth
              value={noteText} onChange={e => setNoteText(e.target.value)}
              placeholder="Enter note..."
            />
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1, mt: 2 }}>
              <Button onClick={() => setNoteDialogOpen(false)}>Cancel</Button>
              <Button variant="contained" onClick={selectedHighlight ? handleSaveEditNote : handleSaveNote}>Save</Button>
            </Box>
          </Paper>
        </Box>
      )}

      <Snackbar open={Boolean(errorMessage)} autoHideDuration={6000} onClose={() => setErrorMessage(null)}>
        <Alert severity="error">{errorMessage}</Alert>
      </Snackbar>
    </Box>
  );
}
