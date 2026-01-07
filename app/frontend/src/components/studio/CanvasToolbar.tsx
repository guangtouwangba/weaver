'use client';

import React, { useState } from 'react';
import {
  Stack,
  Surface,
  Text,
  IconButton,
  Tooltip,
  Collapse,
} from '@/components/ui';
import { colors, radii, shadows } from '@/components/ui/tokens';
import {
  AddIcon,
  ZoomInIcon,
  ZoomOutIcon,
  DeleteIcon,
  ExpandMoreIcon,
  ExpandLessIcon,
  MousePointerIcon,
  HandIcon,
  ScanIcon,
  LinkIcon,
  AccountTreeIcon
} from '@/components/ui/icons';

export type ToolMode = 'select' | 'hand' | 'connect' | 'logic_connect';

interface CanvasToolbarProps {
  activeTool: ToolMode;
  onChange: (tool: ToolMode) => void;
  zoom: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetZoom: () => void;
  onFitView: () => void;
  onInsert: () => void;
  onDelete: () => void;
  hasSelection?: boolean;
}

export default function CanvasToolbar({
  activeTool,
  onChange,
  zoom,
  onZoomIn,
  onZoomOut,
  onResetZoom,
  onFitView,
  onInsert,
  onDelete,
  hasSelection = false
}: CanvasToolbarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Debug log
  console.log('[CanvasToolbar] Rendering with activeTool:', activeTool, 'isCollapsed:', isCollapsed);

  return (
    <div
      style={{
        position: 'absolute',
        top: '50%',
        left: 24,
        transform: 'translateY(-50%)',
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 16,
      }}
    >
      {/* 1. Top Toggle Button */}
      <Tooltip title={isCollapsed ? "Expand Toolbar" : "Collapse Toolbar"} placement="right">
        <IconButton
          size="sm"
          onClick={() => setIsCollapsed(!isCollapsed)}
          style={{
            backgroundColor: colors.background.paper,
            border: `1px solid ${colors.border.default}`,
            boxShadow: shadows.sm,
          }}
        >
          {isCollapsed ? <ExpandMoreIcon size={18} /> : <ExpandLessIcon size={18} />}
        </IconButton>
      </Tooltip>

      {!isCollapsed && (
        <Stack direction="column" gap={2} align="center">

          {/* 2. Operation Mode Capsule - Contains 4 tools */}
          <Surface elevation={1} radius="xl" bordered>
            <Stack direction="column" align="center">
              <Tooltip title="Select (V)" placement="right">
                <IconButton
                  size="md"
                  variant={activeTool === 'select' ? 'default' : 'ghost'}
                  active={activeTool === 'select'}
                  onClick={() => onChange('select')}
                  style={{ borderRadius: 0 }}
                >
                  <MousePointerIcon size={18} />
                </IconButton>
              </Tooltip>

              <Tooltip title="Hand (H) - Pan" placement="right">
                <IconButton
                  size="md"
                  variant={activeTool === 'hand' ? 'default' : 'ghost'}
                  active={activeTool === 'hand'}
                  onClick={() => onChange('hand')}
                  style={{ borderRadius: 0 }}
                >
                  <HandIcon size={18} />
                </IconButton>
              </Tooltip>

              <Tooltip title="Connect (L)" placement="right">
                <IconButton
                  size="md"
                  variant={activeTool === 'connect' ? 'default' : 'ghost'}
                  active={activeTool === 'connect'}
                  onClick={() => onChange('connect')}
                  style={{ borderRadius: 0 }}
                >
                  <LinkIcon size={18} />
                </IconButton>
              </Tooltip>

              <Tooltip title="Logic Connect (K)" placement="right">
                <IconButton
                  size="md"
                  variant={activeTool === 'logic_connect' ? 'default' : 'ghost'}
                  active={activeTool === 'logic_connect'}
                  onClick={() => onChange('logic_connect')}
                  style={{ borderRadius: 0 }}
                >
                  <AccountTreeIcon size={18} />
                </IconButton>
              </Tooltip>
            </Stack>
          </Surface>

          {/* 3. View Controls Capsule */}
          <Surface elevation={1} radius="xl" bordered>
            <Stack direction="column" align="center">
              <Tooltip title="Insert Node" placement="right">
                <IconButton size="md" variant="ghost" onClick={onInsert} style={{ borderRadius: 0 }}>
                  <AddIcon size="md" />
                </IconButton>
              </Tooltip>

              <Tooltip title="Zoom In" placement="right">
                <IconButton size="md" variant="ghost" onClick={onZoomIn} style={{ borderRadius: 0 }}>
                  <ZoomInIcon size={18} />
                </IconButton>
              </Tooltip>

              <Tooltip title="Reset Zoom (100%)" placement="right">
                <div
                  onClick={onResetZoom}
                  style={{
                    padding: '8px 0',
                    width: '100%',
                    textAlign: 'center',
                    cursor: 'pointer',
                    userSelect: 'none',
                  }}
                >
                  <Text variant="caption" style={{ fontWeight: 'bold', fontSize: '0.7rem' }}>
                    {Math.round(zoom * 100)}%
                  </Text>
                </div>
              </Tooltip>

              <Tooltip title="Zoom Out" placement="right">
                <IconButton size="md" variant="ghost" onClick={onZoomOut} style={{ borderRadius: 0 }}>
                  <ZoomOutIcon size={18} />
                </IconButton>
              </Tooltip>

              <Tooltip title="Fit to Screen" placement="right">
                <IconButton size="md" variant="ghost" onClick={onFitView} style={{ borderRadius: 0 }}>
                  <ScanIcon size={18} />
                </IconButton>
              </Tooltip>
            </Stack>
          </Surface>

          {/* 4. Delete Button */}
          <Tooltip title="Delete Selected (Del)" placement="right">
            <IconButton
              size="sm"
              onClick={onDelete}
              disabled={!hasSelection}
              style={{
                backgroundColor: hasSelection ? colors.error[50] : colors.background.paper,
                border: `1px solid ${hasSelection ? colors.error[300] : colors.border.default}`,
                color: hasSelection ? colors.error[600] : colors.text.disabled,
                boxShadow: shadows.sm,
              }}
            >
              <DeleteIcon size={18} />
            </IconButton>
          </Tooltip>

        </Stack>
      )}
    </div>
  );
}
