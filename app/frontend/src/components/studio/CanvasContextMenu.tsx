'use client';

import React, { useEffect, useRef, useCallback } from 'react';
import { MenuList, Divider } from '@mui/material';
import { Surface, Stack, Text, Menu, MenuItem, MenuDivider } from '@/components/ui';
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
  viewport?: { x: number; y: number; scale: number };
  canvasContainerRef?: React.RefObject<HTMLElement | null>;
}

export default function CanvasContextMenu({ open, x, y, onClose, onOpenImport, viewport, canvasContainerRef }: CanvasContextMenuProps) {
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
    <Surface
      ref={menuRef}
      elevation={4}
      radius="lg"
      sx={{
        position: 'fixed',
        top: y,
        left: x,
        width: 260,
        zIndex: 1300,
        overflow: 'hidden',
      }}
    >
      <MenuList dense sx={{ py: 1 }}>
        <MenuItem onClick={() => handleAction(() => handleAddNode('default', { x, y }))} icon={<AddIcon size={18} />}>
          Add Node
        </MenuItem>

        <MenuItem onClick={() => handleAction(() => handleAddNode('sticky', { x, y }))} icon={<StickyNote2Icon size={18} />}>
          Add Sticky Note
        </MenuItem>

        <MenuDivider />

        <Stack sx={{ px: 2, py: 0.5 }}>
          <Text variant="overline" color="secondary">
            GENERATE CONTENT
          </Text>
        </Stack>

        <MenuItem
          onClick={() => handleAction(() => handleGenerateAtPosition('mindmap'))}
          icon={<AccountTreeIcon size={18} sx={{ color: colors.primary[500] }} />}
        >
          Generate Mind Map
        </MenuItem>

        <MenuItem
          onClick={() => handleAction(() => handleGenerateAtPosition('flashcards'))}
          icon={<CreditCardIcon size={18} sx={{ color: colors.warning[500] }} />}
        >
          Generate Flashcards
        </MenuItem>

        <MenuItem
          onClick={() => handleAction(() => handleGenerateAtPosition('summary'))}
          icon={<DescriptionIcon size={18} sx={{ color: colors.info[500] }} />}
        >
          Generate Summary
        </MenuItem>

        <MenuDivider />

        <MenuItem onClick={() => handleAction(handleImportSource)} icon={<UploadFileIcon size={18} />}>
          Import Source...
        </MenuItem>
      </MenuList>
    </Surface>
  );
}
