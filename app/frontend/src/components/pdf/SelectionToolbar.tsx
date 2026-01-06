'use client';

import { ContentCopyIcon, CloseIcon, DescriptionIcon } from '@/components/ui/icons';
import { HighlightColor } from './types';
import { IconButton, Tooltip, Surface } from '@/components/ui/primitives';
import { colors } from '@/components/ui/tokens';

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
    <Surface
      elevation={0} // Using custom shadow via style
      style={{
        position: 'fixed',
        left: `${position.x}px`,
        top: `${position.y - 56}px`,
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        gap: 4,
        padding: 6,
        borderRadius: 12,
        backgroundColor: '#FFFFFF',
        boxShadow: '0 2px 8px rgba(0,0,0,0.12), 0 4px 16px rgba(0,0,0,0.08)',
        border: `1px solid ${colors.border.default}`,
        transform: 'translateX(-50%)',
        backdropFilter: 'blur(8px)',
      }}
      onClick={(e) => e.stopPropagation()}
    >
      {/* 颜色选择按钮 */}
      {colorOptions.map((option) => (
        <Tooltip key={option.color} content={option.label}>
          <button
            onClick={() => onColorSelect(option.color)}
            style={{
              width: 28,
              height: 28,
              minWidth: 28,
              backgroundColor: option.bgColor,
              border: '1.5px solid transparent',
              borderRadius: 6,
              cursor: 'pointer',
              transition: 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = option.hoverColor;
              e.currentTarget.style.transform = 'scale(1.08)';
              e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = option.bgColor;
              e.currentTarget.style.transform = 'scale(1)';
              e.currentTarget.style.boxShadow = 'none';
            }}
          />
        </Tooltip>
      ))}

      {/* 分隔线 */}
      <div style={{ width: 1, height: 20, backgroundColor: colors.border.default, margin: '0 4px' }} />

      {/* 添加批注按钮 */}
      <Tooltip content="添加批注">
        <IconButton
          size="sm"
          variant="ghost"
          onClick={onAddNote}
          style={{ width: 28, height: 28, minWidth: 28 }}
        >
          <DescriptionIcon size={14} />
        </IconButton>
      </Tooltip>

      {/* 复制按钮 */}
      <Tooltip content="复制">
        <IconButton
          size="sm"
          variant="ghost"
          onClick={onCopy}
          style={{ width: 28, height: 28, minWidth: 28 }}
        >
          <ContentCopyIcon size={14} />
        </IconButton>
      </Tooltip>

      {/* 关闭按钮 */}
      <Tooltip content="关闭">
        <IconButton
          size="sm"
          variant="ghost"
          onClick={onClose}
          style={{ width: 28, height: 28, minWidth: 28 }}
        >
          <CloseIcon size={14} />
        </IconButton>
      </Tooltip>
    </Surface>
  );
}
