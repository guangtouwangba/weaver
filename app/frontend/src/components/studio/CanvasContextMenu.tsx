'use client';

import React, { useEffect, useRef, useCallback } from 'react';
import { colors, radii, shadows, fontSize, fontWeight } from '@/components/ui/tokens';
import { AddIcon, StickyNote2Icon, AccountTreeIcon, DescriptionIcon, UploadFileIcon, CreditCardIcon } from '@/components/ui/icons';
import { useCanvasActions } from '@/hooks/useCanvasActions';
import { GenerationType } from '@/contexts/StudioContext';

interface CanvasContextMenuProps {
  open: boolean;
  x: number;
  y: number;
  onClose: () => void;
  onOpenImport: () => void;
  onAddStickyNote?: (position: { x: number; y: number }) => void;
  viewport?: { x: number; y: number; scale: number };
  canvasContainerRef?: React.RefObject<HTMLElement | null>;
}

const MenuItem = ({
  onClick,
  icon,
  children
}: {
  onClick: () => void;
  icon?: React.ReactNode;
  children: React.ReactNode;
}) => {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        width: '100%',
        padding: '8px 16px',
        border: 'none',
        background: 'transparent',
        cursor: 'pointer',
        textAlign: 'left',
        fontSize: fontSize.sm,
        fontWeight: fontWeight.medium,
        color: colors.text.primary,
        transition: 'background-color 0.15s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = colors.neutral[100];
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = 'transparent';
      }}
    >
      {icon && (
        <span style={{ display: 'flex', marginRight: 12, color: colors.text.secondary }}>
          {icon}
        </span>
      )}
      {children}
    </button>
  );
};

const MenuDivider = () => (
  <div style={{ height: 1, backgroundColor: colors.border.default, margin: '4px 0' }} />
);

export default function CanvasContextMenu({ open, x, y, onClose, onOpenImport, onAddStickyNote, viewport, canvasContainerRef }: CanvasContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);
  const { handleAddNode, handleGenerateContentConcurrent, handleImportSource } = useCanvasActions({ onOpenImport });

  /**
   * Convert screen coordinates to canvas coordinates
   */
  const screenToCanvasCoords = useCallback((screenX: number, screenY: number): { x: number; y: number } => {
    if (!viewport) {
      return { x: screenX, y: screenY };
    }

    let containerOffsetX = 0;
    let containerOffsetY = 0;
    if (canvasContainerRef?.current) {
      const rect = canvasContainerRef.current.getBoundingClientRect();
      containerOffsetX = rect.left;
      containerOffsetY = rect.top;
    }

    const canvasX = (screenX - containerOffsetX - viewport.x) / viewport.scale;
    const canvasY = (screenY - containerOffsetY - viewport.y) / viewport.scale;

    return { x: canvasX, y: canvasY };
  }, [viewport, canvasContainerRef]);

  /**
   * Handle content generation at the right-click position
   */
  const handleGenerateAtPosition = useCallback((type: GenerationType) => {
    const canvasPosition = screenToCanvasCoords(x, y);
    handleGenerateContentConcurrent(type, canvasPosition);
  }, [x, y, screenToCanvasCoords, handleGenerateContentConcurrent]);

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (open) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [open, onClose]);

  if (!open) return null;

  const handleAction = (action: () => void) => {
    action();
    onClose();
  };

  return (
    <div
      ref={menuRef}
      style={{
        position: 'fixed',
        top: y,
        left: x,
        width: 260,
        zIndex: 1300,
        overflow: 'hidden',
        backgroundColor: colors.background.paper,
        borderRadius: radii.lg,
        boxShadow: shadows.lg,
        border: `1px solid ${colors.border.default}`,
      }}
    >
      <div style={{ paddingTop: 8, paddingBottom: 8 }}>
        <MenuItem onClick={() => handleAction(() => {
          if (onAddStickyNote) {
            const pos = screenToCanvasCoords(x, y);
            onAddStickyNote(pos);
          } else {
            handleAddNode('sticky', { x, y });
          }
        })} icon={<StickyNote2Icon size={18} />}>
          Add Sticky Note
        </MenuItem>

        <MenuDivider />

        <div style={{ padding: '4px 16px' }}>
          <span style={{
            fontSize: 11,
            fontWeight: fontWeight.bold,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: colors.text.secondary
          }}>
            GENERATE CONTENT
          </span>
        </div>

        <MenuItem
          onClick={() => handleAction(() => handleGenerateAtPosition('mindmap'))}
          icon={<AccountTreeIcon size={18} style={{ color: colors.primary[500] }} />}
        >
          Generate Mind Map
        </MenuItem>

        <MenuItem
          onClick={() => handleAction(() => handleGenerateAtPosition('flashcards'))}
          icon={<CreditCardIcon size={18} style={{ color: colors.warning[500] }} />}
        >
          Generate Flashcards
        </MenuItem>

        <MenuItem
          onClick={() => handleAction(() => handleGenerateAtPosition('summary'))}
          icon={<DescriptionIcon size={18} style={{ color: colors.info[500] }} />}
        >
          Generate Summary
        </MenuItem>

        <MenuDivider />

        <MenuItem onClick={() => handleAction(handleImportSource)} icon={<UploadFileIcon size={18} />}>
          Import Source...
        </MenuItem>
      </div>
    </div>
  );
}
