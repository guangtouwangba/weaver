'use client';

import { Box, Paper, IconButton, Tooltip } from '@mui/material';
import { ContentCopyIcon, CloseIcon, DescriptionIcon } from '@/components/ui/icons';
import { HighlightColor } from './types';

interface SelectionToolbarProps {
  position: { x: number; y: number };
  selectedText: string;
  onColorSelect: (color: HighlightColor) => void;
  onAddNote: () => void;
  onCopy: () => void;
  onClose: () => void;
}

const colorOptions: { color: HighlightColor; label: string; bgColor: string; hoverColor: string }[] = [
  { color: 'yellow', label: '黄色高亮', bgColor: '#FFEB3B', hoverColor: '#FFD700' },
  { color: 'green', label: '绿色高亮', bgColor: '#4CAF50', hoverColor: '#45A049' },
  { color: 'blue', label: '蓝色高亮', bgColor: '#2196F3', hoverColor: '#1976D2' },
  { color: 'pink', label: '粉色高亮', bgColor: '#E91E63', hoverColor: '#C2185B' },
];

export function SelectionToolbar({
  position,
  selectedText,
  onColorSelect,
  onAddNote,
  onCopy,
  onClose,
}: SelectionToolbarProps) {
  return (
    <Paper
      elevation={0}
      sx={{
        position: 'fixed',
        left: `${position.x}px`,
        top: `${position.y - 56}px`, // 显示在选中区域上方
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        gap: 0.5,
        p: 0.75,
        borderRadius: 3,
        bgcolor: '#FFFFFF',
        boxShadow: '0 2px 8px rgba(0,0,0,0.12), 0 4px 16px rgba(0,0,0,0.08)',
        border: '1px solid',
        borderColor: '#E5E7EB',
        transform: 'translateX(-50%)', // 居中显示
        backdropFilter: 'blur(8px)',
      }}
      onClick={(e) => e.stopPropagation()}
    >
      {/* 颜色选择按钮 */}
      {colorOptions.map((option) => (
        <Tooltip key={option.color} title={option.label} placement="top" arrow>
          <IconButton
            size="small"
            onClick={() => onColorSelect(option.color)}
            sx={{
              width: 28,
              height: 28,
              minWidth: 28,
              bgcolor: option.bgColor,
              border: '1.5px solid',
              borderColor: 'transparent',
              borderRadius: 1.5,
              transition: 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)',
              '&:hover': {
                bgcolor: option.hoverColor,
                borderColor: '#171717',
                transform: 'scale(1.08)',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              },
              '&:active': {
                transform: 'scale(0.95)',
              },
            }}
          />
        </Tooltip>
      ))}

      {/* 分隔线 */}
      <Box
        sx={{
          width: 1,
          height: 20,
          bgcolor: '#E5E7EB',
          mx: 0.5,
        }}
      />

      {/* 添加批注按钮 */}
      <Tooltip title="添加批注" placement="top" arrow>
        <IconButton
          size="small"
          onClick={onAddNote}
          sx={{
            width: 28,
            height: 28,
            minWidth: 28,
            color: 'text.secondary',
            borderRadius: 1.5,
            transition: 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)',
            '&:hover': {
              bgcolor: '#F3F4F6',
              color: 'text.primary',
              transform: 'scale(1.05)',
            },
          }}
        >
          <DescriptionIcon size={14} />
        </IconButton>
      </Tooltip>

      {/* 复制按钮 */}
      <Tooltip title="复制" placement="top" arrow>
        <IconButton
          size="small"
          onClick={onCopy}
          sx={{
            width: 28,
            height: 28,
            minWidth: 28,
            color: 'text.secondary',
            borderRadius: 1.5,
            transition: 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)',
            '&:hover': {
              bgcolor: '#F3F4F6',
              color: 'text.primary',
              transform: 'scale(1.05)',
            },
          }}
        >
          <ContentCopyIcon size={14} />
        </IconButton>
      </Tooltip>

      {/* 关闭按钮 */}
      <Tooltip title="关闭" placement="top" arrow>
        <IconButton
          size="small"
          onClick={onClose}
          sx={{
            width: 28,
            height: 28,
            minWidth: 28,
            color: 'text.secondary',
            borderRadius: 1.5,
            transition: 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)',
            '&:hover': {
              bgcolor: '#F3F4F6',
              color: 'text.primary',
              transform: 'scale(1.05)',
            },
          }}
        >
          <X size={14} />
        </IconButton>
      </Tooltip>
    </Paper>
  );
}
