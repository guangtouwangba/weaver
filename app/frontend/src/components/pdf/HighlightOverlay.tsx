import React, { useState, useEffect } from 'react';
import { DescriptionIcon } from '@/components/ui/icons';
import { TextAnnotation, Highlight, TextSelection } from './types';

interface HighlightOverlayProps {
  highlights?: (Highlight | TextAnnotation)[];
  selection: TextSelection | null;
  searchHighlight?: {
    text: string;
    pageNumber: number;
    rects: DOMRect[];
  } | null;
  containerRef: React.RefObject<HTMLElement>;
  onHighlightClick?: (highlight: Highlight, event?: React.MouseEvent | MouseEvent) => void;
}

const colorMap: Record<string, string> = {
  yellow: '#FFEB3B40', // 40 = 25% opacity
  green: '#4CAF5040',
  blue: '#2196F340',
  pink: '#E91E6340',
  red: '#EF444440',
  orange: '#F9731640',
  purple: '#A855F740',
  black: '#1F293740',
};

const solidColorMap: Record<string, string> = {
  yellow: '#FFEB3B',
  green: '#4CAF50',
  blue: '#2196F3',
  pink: '#E91E63',
  red: '#EF4444',
  orange: '#F97316',
  purple: '#A855F7',
  black: '#1F2937',
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

    const adjustedRects = selection.rects.map(rect => {
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
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        pointerEvents: 'none',
        zIndex: 10,
      }}
    >
      {/* Current Selection Highlight (temporary) */}
      {highlightRects.map((rect, index) => (
        <div
          key={`selection-${index}`}
          style={{
            position: 'absolute',
            left: rect.left,
            top: rect.top,
            width: rect.width,
            height: rect.height,
            backgroundColor: 'rgba(59, 130, 246, 0.3)', // Blueish
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

          const type = (highlight as TextAnnotation).type;
          const color = highlight.color;

          let style: React.CSSProperties = {
            position: 'absolute',
            left: rect.left,
            top: rect.top,
            width: rect.width,
            height: rect.height,
          };

          if (type === 'underline') {
            style.borderBottom = `2px solid ${solidColorMap[color] || solidColorMap.yellow}`;
            style.backgroundColor = 'transparent';
          } else if (type === 'strike') {
            style.background = `linear-gradient(to bottom, transparent 45%, ${solidColorMap[color] || solidColorMap.yellow} 45%, ${solidColorMap[color] || solidColorMap.yellow} 55%, transparent 55%)`;
          } else {
            // Default Highlight
            style.backgroundColor = colorMap[color] || colorMap.yellow;
          }

          return (
            <div
              key={`${highlight.id}-${index}`}
              onClick={(e) => {
                e.stopPropagation();
                e.preventDefault();
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
              className={type === 'highlight' ? 'hover:bg-opacity-60 cursor-pointer' : 'cursor-pointer'}
              style={{
                ...style,
                pointerEvents: 'auto', // Capture clicks
              }}
            >
              {/* Note Icon */}
              {isFirstRect && hasNote && (
                <div
                  style={{
                    position: 'absolute',
                    top: -2,
                    right: -2,
                    width: 14,
                    height: 14,
                    borderRadius: '50%',
                    backgroundColor: '#FFFFFF',
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
                </div>
              )}
            </div>
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
          <div
            key={`note-${highlight.id}`}
            onMouseEnter={() => setHoveredHighlightId(highlight.id)}
            onMouseLeave={() => setHoveredHighlightId(null)}
            style={{
              position: 'absolute',
              left: `${firstRect.left + firstRect.width + 8}px`,
              top: `${firstRect.top}px`,
              maxWidth: 280,
              padding: 12,
              borderRadius: 8,
              backgroundColor: '#FFFFFF',
              border: '1px solid #E5E7EB',
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
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 4 }}>
              <DescriptionIcon size={14} style={{ color: '#6B7280', marginTop: 2, flexShrink: 0 }} />
              <span
                style={{
                  fontSize: 12,
                  lineHeight: 1.5,
                  color: '#111827', // text.primary
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {notePreview}
              </span>
            </div>
          </div>
        );
      })}

      {/* Search Highlight */}
      {searchHighlight && searchHighlight.rects && searchHighlight.rects.map((rect, index) => (
        <div
          key={`search-${index}`}
          className="search-highlight"
          style={{
            position: 'absolute',
            left: rect.left,
            top: rect.top,
            width: rect.width,
            height: rect.height,
            backgroundColor: 'rgba(255, 235, 59, 0.4)',
            borderRadius: '2px',
            pointerEvents: 'none',
          }}
        />
      ))}
    </div>
  );
}
