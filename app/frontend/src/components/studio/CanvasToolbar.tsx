'use client';

import React, { useState } from 'react';
import { Fade, ToggleButton } from '@mui/material';
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
  ExpandLessIcon
} from '@/components/ui/icons';
import MouseMui from '@mui/icons-material/Mouse';
import PanToolMui from '@mui/icons-material/PanTool';
import CropFreeMui from '@mui/icons-material/CropFree';

export type ToolMode = 'select' | 'hand';

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
          sx={{
            bgcolor: colors.background.paper,
            border: `1px solid ${colors.border.default}`,
            boxShadow: shadows.sm,
          }}
        >
          {isCollapsed ? <ExpandMoreIcon size={18} /> : <ExpandLessIcon size={18} />}
        </IconButton>
      </Tooltip>

      <Fade in={!isCollapsed} unmountOnExit>
        <Stack direction="column" gap={2} align="center">

          {/* 2. Operation Mode Capsule */}
          <Surface elevation={1} radius="xl" bordered>
            <Stack direction="column" align="center">
              <Tooltip title="Select (V)" placement="right">
                <IconButton
                  size="md"
                  variant={activeTool === 'select' ? 'default' : 'ghost'}
                  active={activeTool === 'select'}
                  onClick={() => onChange('select')}
                  sx={{ borderRadius: 0 }}
                >
                  <MouseMui sx={{ fontSize: 18 }} />
                </IconButton>
              </Tooltip>

              <Tooltip title="Hand (H) - Pan" placement="right">
                <IconButton
                  size="md"
                  variant={activeTool === 'hand' ? 'default' : 'ghost'}
                  active={activeTool === 'hand'}
                  onClick={() => onChange('hand')}
                  sx={{ borderRadius: 0 }}
                >
                  <PanToolMui sx={{ fontSize: 18 }} />
                </IconButton>
              </Tooltip>
            </Stack>
          </Surface>

          {/* 3. View Controls Capsule */}
          <Surface elevation={1} radius="xl" bordered>
            <Stack direction="column" align="center">
              <Tooltip title="Insert Node" placement="right">
                <IconButton size="md" variant="ghost" onClick={onInsert} sx={{ borderRadius: 0 }}>
                  <AddIcon size="md" />
                </IconButton>
              </Tooltip>

              <Tooltip title="Zoom In" placement="right">
                <IconButton size="md" variant="ghost" onClick={onZoomIn} sx={{ borderRadius: 0 }}>
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
                  <Text variant="caption" sx={{ fontWeight: 'bold', fontSize: '0.7rem' }}>
                    {Math.round(zoom * 100)}%
                  </Text>
                </div>
              </Tooltip>

              <Tooltip title="Zoom Out" placement="right">
                <IconButton size="md" variant="ghost" onClick={onZoomOut} sx={{ borderRadius: 0 }}>
                  <ZoomOutIcon size={18} />
                </IconButton>
              </Tooltip>

              <Tooltip title="Fit to Screen" placement="right">
                <IconButton size="md" variant="ghost" onClick={onFitView} sx={{ borderRadius: 0 }}>
                  <CropFreeMui sx={{ fontSize: 18 }} />
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
              sx={{
                bgcolor: hasSelection ? colors.error[50] : colors.background.paper,
                border: `1px solid ${hasSelection ? colors.error[300] : colors.border.default}`,
                color: hasSelection ? colors.error[600] : colors.text.disabled,
                boxShadow: shadows.sm,
                '&:hover': {
                  bgcolor: hasSelection ? colors.error[100] : colors.background.paper
                }
              }}
            >
              <DeleteIcon size={18} />
            </IconButton>
          </Tooltip>

        </Stack>
      </Fade>
    </div>
  );
}
