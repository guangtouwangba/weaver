import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography } from '@mui/material';
import { DescriptionIcon } from '@/components/ui/icons';
import { TextSelection, Highlight } from './types';

interface HighlightOverlayProps {
  highlights?: Highlight[];
  selection: TextSelection | null;
  searchHighlight?: {
    text: string;
    pageNumber: number;
    rects: DOMRect[]; // We will assume search computes rects or we handle it
  } | null;
  containerRef: React.RefObject<HTMLElement>;
  onHighlightClick?: (highlight: Highlight, event?: React.MouseEvent | MouseEvent) => void;
}

const colorMap: Record<string, string> = {
  yellow: '#FFEB3B40', // 40 = 25% opacity
  green: '#4CAF5040',
  blue: '#2196F340',
  pink: '#E91E6340',
};

export function HighlightOverlay({
  highlights = [],
  selection,
  searchHighlight,
  containerRef,
  onHighlightClick,
}: HighlightOverlayProps) {
  const [highlightRects, setHighlightRects] = useState<DOMRect[]>([]);
  const [hoveredHighlightId, setHoveredHighlightId] = useState<string | null>(null);

  // Calculate selection highlight position
  useEffect(() => {
    if (!selection || !containerRef.current) {
      setHighlightRects([]);
      return;
    }

    const containerRect = containerRef.current.getBoundingClientRect();
    const scrollLeft = containerRef.current.scrollLeft;
    const scrollTop = containerRef.current.scrollTop;

    // The rects in TextSelection (from SelectionManager) are likely client rects (viewport relative)
    // We need to convert them to be relative to the container *content* (including scroll) if the overlay is inside the scrollable area.
    // However, usually the overlay is position:absolute inside a relative container.
    // If the container scrolls, and the overlay is inside, we just need coords relative to the container's top-left.
    
    // SelectionManager returns client rects.
    const adjustedRects = selection.rects.map(rect => {
       // Convert client rect to offset relative to container
       return new DOMRect(
         rect.left - containerRect.left + scrollLeft,
         rect.top - containerRect.top + scrollTop,
         rect.width,
         rect.height
       );
    });
    setHighlightRects(adjustedRects);
  }, [selection, containerRef]);


  return (
    <Box
      sx={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        pointerEvents: 'none', // Allow clicks to pass through to text layer unless hitting a pointer-events:auto element
        zIndex: 10,
      }}
    >
      {/* Current Selection Highlight (temporary) */}
      {highlightRects.map((rect, index) => (
        <Box
          key={`selection-${index}`}
          sx={{
            position: 'absolute',
            left: rect.left,
            top: rect.top,
            width: rect.width,
            height: rect.height,
            bgcolor: 'rgba(59, 130, 246, 0.3)', // Blueish for selection
            borderRadius: '2px',
          }}
        />
      ))}

      {/* Saved Highlights */}
      {highlights.map((highlight) => {
        if (!highlight.rects || highlight.rects.length === 0) return null;
        
        return highlight.rects.map((rect, index) => {
           const isFirstRect = index === 0;
           const hasNote = highlight.note && highlight.note.trim().length > 0;
           
           return (
            <Box
              key={`${highlight.id}-${index}`}
              onClick={(e) => {
                e.stopPropagation();
                e.preventDefault();
                // We need pointerEvents: auto on the highlight box to capture clicks
                onHighlightClick?.(highlight, e.nativeEvent);
              }}
              onMouseEnter={() => {
                if (hasNote) {
                  setHoveredHighlightId(highlight.id);
                }
              }}
              onMouseLeave={() => {
                setHoveredHighlightId(null);
              }}
              sx={{
                position: 'absolute',
                left: rect.left,
                top: rect.top,
                width: rect.width,
                height: rect.height,
                backgroundColor: colorMap[highlight.color] || colorMap.yellow,
                borderRadius: '2px',
                pointerEvents: 'auto', // Important for click handling
                cursor: 'pointer',
                transition: 'background-color 0.2s',
                '&:hover': {
                  backgroundColor: colorMap[highlight.color]?.replace('40', '60') || colorMap.yellow.replace('40', '60'),
                },
              }}
            >
              {/* Note Icon */}
              {isFirstRect && hasNote && (
                <Box
                  sx={{
                    position: 'absolute',
                    top: -2,
                    right: -2,
                    width: 14,
                    height: 14,
                    borderRadius: '50%',
                    bgcolor: '#FFFFFF',
                    border: '1.5px solid',
                    borderColor: colorMap[highlight.color]?.replace('40', 'FF') || '#FFEB3B',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.15)',
                    zIndex: 11,
                    pointerEvents: 'none',
                  }}
                >
                  <DescriptionIcon size={8} style={{ color: '#6B7280' }} />
                </Box>
              )}
            </Box>
           );
        });
      })}

       {/* Note Preview Cards */}
      {highlights.map((highlight) => {
        const hasNote = highlight.note && highlight.note.trim().length > 0;
        const isHovered = hoveredHighlightId === highlight.id;
        
        if (!hasNote || !isHovered || !highlight.rects || highlight.rects.length === 0) {
          return null;
        }
        
        const firstRect = highlight.rects[0];
        const noteText = highlight.note || '';
        const notePreview = noteText.length > 100 
          ? `${noteText.substring(0, 100)}...` 
          : noteText;
        
        return (
          <Paper
            key={`note-${highlight.id}`}
            elevation={0}
            onMouseEnter={() => setHoveredHighlightId(highlight.id)}
            onMouseLeave={() => setHoveredHighlightId(null)}
            sx={{
              position: 'absolute',
              left: `${firstRect.left + firstRect.width + 8}px`,
              top: `${firstRect.top}px`,
              maxWidth: 280,
              p: 1.5,
              borderRadius: 2,
              bgcolor: '#FFFFFF',
              border: '1px solid',
              borderColor: '#E5E7EB',
              boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
              zIndex: 1000,
              pointerEvents: 'auto',
              cursor: 'default',
            }}
            onClick={(e) => {
                e.stopPropagation();
                onHighlightClick?.(highlight, e.nativeEvent);
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
              <DescriptionIcon size={14} style={{ color: '#6B7280', marginTop: 2, flexShrink: 0 }} />
              <Typography
                variant="caption"
                sx={{
                  fontSize: 12,
                  lineHeight: 1.5,
                  color: 'text.primary',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {notePreview}
              </Typography>
            </Box>
          </Paper>
        );
      })}

      {/* Search Highlight */}
      {searchHighlight && searchHighlight.rects && searchHighlight.rects.map((rect, index) => (
          <Box
            key={`search-${index}`}
            className="search-highlight" // Use CSS animation defined in global css
            sx={{
                position: 'absolute',
                left: rect.left,
                top: rect.top,
                width: rect.width,
                height: rect.height,
                bgcolor: 'rgba(255, 235, 59, 0.4)',
                borderRadius: '2px',
                pointerEvents: 'none',
            }}
          />
      ))}
    </Box>
  );
}
