'use client';

import { useState } from 'react';
import { Box, Paper, Typography } from '@mui/material';
import { FileText } from 'lucide-react';

export interface HighlightPosition {
  pageNumber: number;
  startOffset: number;
  endOffset: number;
  rects: DOMRect[]; // 用于渲染
}

export interface Highlight {
  id: string;
  documentId: string;
  pageNumber: number;
  startOffset: number;
  endOffset: number;
  color: 'yellow' | 'green' | 'blue' | 'pink';
  note?: string; // 批注内容
  createdAt: string;
  updatedAt: string;
  rects?: DOMRect[]; // 客户端计算的位置信息
}

interface HighlightOverlayProps {
  highlights: Highlight[];
  containerRef: React.RefObject<HTMLElement>;
  onHighlightClick?: (highlight: Highlight, event?: React.MouseEvent | MouseEvent) => void;
}

const colorMap: Record<string, string> = {
  yellow: '#FFEB3B40', // 40 = 25% opacity
  green: '#4CAF5040',
  blue: '#2196F340',
  pink: '#E91E6340',
};

// containerRef 目前未在组件内部直接使用，但保留参数以便未来扩展（例如按页裁剪高亮）
export default function HighlightOverlay({
  highlights,
  // containerRef 保留以兼容调用方，但当前未在组件内部直接使用
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  containerRef,
  onHighlightClick,
}: HighlightOverlayProps) {
  // 过滤出有 rects 的高亮
  const highlightsWithRects = highlights.filter((h) => h.rects && h.rects.length > 0);

  const [hoveredHighlightId, setHoveredHighlightId] = useState<string | null>(null);

  return (
    <>
      {highlightsWithRects.map((highlight) => {
        return highlight.rects!.map((rect, index) => {
          const isFirstRect = index === 0;
          const hasNote = highlight.note && highlight.note.trim().length > 0;
          
          return (
            <Box
              key={`${highlight.id}-${index}`}
              onClick={(e) => {
                e.stopPropagation();
                e.preventDefault();
                // 传递原生事件对象
                onHighlightClick?.(highlight, e.nativeEvent);
              }}
              onMouseDown={(e) => {
                // 阻止文本选择
                e.stopPropagation();
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
                // rect 本身是相对于容器内容（包含滚动偏移）的坐标，
                // 在滚动容器中使用 position:absolute 直接使用该坐标即可，
                // 元素会随内容一起滚动，而不是固定在视口上。
                left: `${rect.left}px`,
                top: `${rect.top}px`,
                width: `${rect.width}px`,
                height: `${rect.height}px`,
                backgroundColor: colorMap[highlight.color] || colorMap.yellow,
                pointerEvents: 'auto',
                cursor: 'pointer',
                transition: 'background-color 0.2s',
                zIndex: 10,
                '&:hover': {
                  backgroundColor: colorMap[highlight.color]?.replace('40', '60') || colorMap.yellow.replace('40', '60'),
                },
              }}
            >
              {/* 批注图标：只在第一个rect上显示，位于右上角 */}
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
                  <FileText size={8} style={{ color: '#6B7280' }} />
                </Box>
              )}
            </Box>
          );
        });
      })}
      
      {/* 批注预览卡片：悬停时显示 */}
      {highlightsWithRects.map((highlight) => {
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
            onMouseEnter={() => {
              setHoveredHighlightId(highlight.id);
            }}
            onMouseLeave={() => {
              setHoveredHighlightId(null);
            }}
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
              <FileText size={14} style={{ color: '#6B7280', marginTop: 2, flexShrink: 0 }} />
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
    </>
  );
}

