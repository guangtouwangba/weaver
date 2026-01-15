'use client';

import { useState, useRef, useEffect, useCallback } from 'react';

import { EditIcon, DeleteIcon } from '@/components/ui/icons';
import { highlightsApi } from '@/lib/api';
import dynamic from 'next/dynamic';
import { SelectionManager } from './SelectionManager';
import { HighlightOverlay } from './HighlightOverlay';
import { SelectionToolbar } from './SelectionToolbar';
import { createDragHandler } from './DragHandler';
import { TextSelection, Highlight, HighlightColor, ToolMode, AnnotationColor, AnnotationType } from './types';
import '@/styles/pdf-viewer.css';

// Design System Imports
import { Button, IconButton, Surface, Text } from '@/components/ui/primitives';
import { Menu, MenuItem, TextField } from '@/components/ui/composites';
import { colors } from '@/components/ui/tokens';

const PDFViewerWrapper = dynamic(
  () => import('./PDFViewerWrapper').then((mod) => mod.PDFViewerWrapper),
  { ssr: false }
);

interface PDFViewerProps {
  documentId: string;
  fileUrl: string;
  pageNumber: number;
  onPageChange: (page: number) => void;
  onDocumentLoad: (numPages: number) => void;
  onHighlightCreate?: (highlight: Highlight) => void;
  onHighlightUpdate?: (highlight: Highlight) => void;
  onHighlightDelete?: (highlightId: string) => void;
  highlightText?: string;
  activeTool?: ToolMode;
  activeColor?: AnnotationColor;
  highlights?: Highlight[];
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
  const [width, setWidth] = useState(800);
  const [internalHighlights, setInternalHighlights] = useState<Highlight[]>([]);

  const highlights = controlledHighlights || internalHighlights;

  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setWidth(entry.contentRect.width);
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  const [textSelection, setTextSelection] = useState<TextSelection | null>(null);

  const [toolbarPosition, setToolbarPosition] = useState<{ x: number; y: number } | null>(null);
  const [highlightMenuAnchor, setHighlightMenuAnchor] = useState<{ x: number; y: number } | null>(null);
  const [selectedHighlight, setSelectedHighlight] = useState<Highlight | null>(null);
  const [noteDialogOpen, setNoteDialogOpen] = useState(false);
  const [noteText, setNoteText] = useState('');
  const [isCreatingHighlight, setIsCreatingHighlight] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [pendingNoteSelection, setPendingNoteSelection] = useState<{
    text: string;
    position: TextSelection;
  } | null>(null);

  // Drag handler ref (unused in render but kept for logic)
  const dragHandler = useRef(createDragHandler(documentId, "PDF Document"));

  // Initialize SelectionManager
  useEffect(() => {
    if (!containerRef.current) return;

    const manager = new SelectionManager(containerRef.current, (selection) => {
      setTextSelection(selection);

      if (selection) {
        const firstRect = selection.rects[0];
        const lastRect = selection.rects[selection.rects.length - 1];
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
            type: h.type as AnnotationType | undefined,
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

      const tempId = `local-${Date.now()}`;
      const highlightWithRects: Highlight = {
        id: tempId,
        documentId,
        pageNumber: textSelection.pageNumber,
        startOffset: 0,
        endOffset: 0,
        color,
        type: ((activeTool === 'underline' || activeTool === 'strike') ? activeTool : 'highlight') as AnnotationType,
        textContent: textSelection.text,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        rects: relativeRects,
      };

      if (!controlledHighlights) {
        setInternalHighlights((prev) => [...prev, highlightWithRects]);
      }

      window.getSelection()?.removeAllRanges();
      setTextSelection(null);
      setToolbarPosition(null);
      setIsCreatingHighlight(false);

      try {
        const newHighlight = await highlightsApi.create(documentId, {
          pageNumber: highlightWithRects.pageNumber,
          startOffset: highlightWithRects.startOffset || 0,
          endOffset: highlightWithRects.endOffset || 0,
          color: color as 'yellow' | 'green' | 'blue' | 'pink',
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

  const handleAddNote = useCallback(() => {
    if (!textSelection) return;
    setPendingNoteSelection({
      text: textSelection.text,
      position: textSelection
    });
    setNoteDialogOpen(true);
  }, [textSelection]);

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
      type: 'note' as AnnotationType,
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
        type: 'note' as AnnotationType,
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
  }, [pendingNoteSelection, noteText, documentId, onHighlightCreate, controlledHighlights]);

  const handleCopy = useCallback(() => {
    if (textSelection) {
      navigator.clipboard.writeText(textSelection.text);
      window.getSelection()?.removeAllRanges();
      setTextSelection(null);
      setToolbarPosition(null);
    }
  }, [textSelection]);

  const handleHighlightClick = useCallback((highlight: Highlight, event?: React.MouseEvent | MouseEvent) => {
    setSelectedHighlight(highlight);
    if (event) {
      const mouseEvent = event as MouseEvent;
      setHighlightMenuAnchor({ x: mouseEvent.clientX, y: mouseEvent.clientY - 10 });
    } else if (highlight.rects && highlight.rects.length > 0 && containerRef.current) {
      const containerRect = containerRef.current.getBoundingClientRect();
      const firstRect = highlight.rects[0];
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
  }, [selectedHighlight, documentId, onHighlightDelete, controlledHighlights]);

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
  }, [selectedHighlight, noteText, documentId, onHighlightUpdate, controlledHighlights]);

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
      await highlightsApi.update(documentId, original.id, { color: color as 'yellow' | 'green' | 'blue' | 'pink' });
      onHighlightUpdate?.(updated);
    } catch (e) {
      if (!controlledHighlights) {
        setInternalHighlights(prev => prev.map(h => h.id === original.id ? original : h));
      }
      setErrorMessage('Failed to update color');
    }
  }, [selectedHighlight, documentId, onHighlightUpdate, controlledHighlights]);

  return (
    <div ref={containerRef} style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden' }}>
      <PDFViewerWrapper
        fileUrl={fileUrl}
        pageNumber={pageNumber}
        width={width}
        onPageChange={onPageChange}
        onDocumentLoad={onDocumentLoad}
        onTextSelect={() => { }}
        highlightText={highlightText}
      />

      <HighlightOverlay
        highlights={highlights.filter(h => h.pageNumber === pageNumber)}
        selection={textSelection}
        searchHighlight={null}
        containerRef={containerRef as React.RefObject<HTMLElement>}
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

      {/* Highlighting Menu */}
      <Menu
        open={Boolean(highlightMenuAnchor)}
        onClose={() => { setHighlightMenuAnchor(null); setSelectedHighlight(null); }}
        anchorReference="anchorPosition"
        anchorPosition={highlightMenuAnchor ? { top: highlightMenuAnchor.y, left: highlightMenuAnchor.x } : undefined}
      >
        <div style={{ display: 'flex', gap: 4, padding: 4 }}>
          {(['yellow', 'green', 'blue', 'pink'] as HighlightColor[]).map((color) => (
            <button
              key={color}
              onClick={() => handleChangeColor(color)}
              style={{
                width: 28, height: 28,
                borderRadius: 4,
                backgroundColor: color === 'yellow' ? '#FFEB3B' : color === 'green' ? '#4CAF50' : color === 'blue' ? '#2196F3' : '#E91E63',
                border: 'none', cursor: 'pointer'
              }}
            />
          ))}
          <IconButton size="sm" variant="ghost" onClick={handleEditHighlight}>
            <EditIcon size="sm" />
          </IconButton>
          <IconButton size="sm" variant="ghost" onClick={handleDeleteHighlight} style={{ color: colors.error[500] }}>
            <DeleteIcon size="sm" />
          </IconButton>
        </div>
      </Menu>

      {/* Note Dialog */}
      {noteDialogOpen && (
        <div
          onClick={() => setNoteDialogOpen(false)}
          style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 2000,
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}
        >
          <Surface
            elevation={2}
            onClick={e => e.stopPropagation()}
            style={{ width: 500, padding: 24, borderRadius: 12 }}
          >
            <Text variant="h6" style={{ marginBottom: 16 }}>{selectedHighlight ? 'Edit Note' : 'Add Note'}</Text>
            <TextField
              multiline rows={5} fullWidth
              value={noteText} onChange={e => setNoteText(e.target.value)}
              placeholder="Enter note..."
              style={{ marginBottom: 16 }}
            />
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              <Button variant="ghost" onClick={() => setNoteDialogOpen(false)}>Cancel</Button>
              <Button variant="primary" onClick={selectedHighlight ? handleSaveEditNote : handleSaveNote}>Save</Button>
            </div>
          </Surface>
        </div>
      )}

      {/* Error Toast */}
      {errorMessage && (
        <div style={{
          position: 'absolute', bottom: 24, left: '50%', transform: 'translateX(-50%)',
          backgroundColor: colors.error[500], color: 'white',
          padding: '8px 16px', borderRadius: 8, boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
          zIndex: 3000, fontSize: 14, fontWeight: 500
        }}>
          {errorMessage}
          <button
            onClick={() => setErrorMessage(null)}
            style={{ marginLeft: 12, background: 'none', border: 'none', color: 'white', cursor: 'pointer' }}
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
}
