'use client';

import React, { useState } from 'react';
import { Paper, ToggleButton, ToggleButtonGroup, Tooltip, IconButton, Stack, Fade, Collapse, Typography, Box } from '@mui/material';
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

  // Common styling for capsules
  const capsuleStyle = {
    borderRadius: 4, // High border radius for capsule shape
    overflow: 'hidden',
    border: '1px solid',
    borderColor: 'divider',
    bgcolor: 'background.paper',
    boxShadow: 3,
  };

  return (
    <Box
      sx={{
        position: 'absolute',
        top: '50%',
        left: 24, // Left aligned vertical toolbar
        transform: 'translateY(-50%)',
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 2,
      }}
    >
      {/* 1. Top Toggle Button */}
      <Tooltip title={isCollapsed ? "Expand Toolbar" : "Collapse Toolbar"} placement="right">
        <IconButton
          onClick={() => setIsCollapsed(!isCollapsed)}
          size="small"
          sx={{
            bgcolor: 'background.paper',
            border: '1px solid',
            borderColor: 'divider',
            boxShadow: 2,
            '&:hover': { bgcolor: 'background.paper' }
          }}
        >
          {isCollapsed ? <ExpandMoreIcon size={18} /> : <ExpandLessIcon size={18} />}
        </IconButton>
      </Tooltip>

      <Fade in={!isCollapsed} unmountOnExit>
        <Stack spacing={2} alignItems="center">
          
          {/* 2. Operation Mode Capsule */}
          <Paper elevation={0} sx={capsuleStyle}>
            <Stack direction="column" alignItems="center">
              <Tooltip title="Select (V)" placement="right" arrow>
                <ToggleButton 
                  value="select" 
                  selected={activeTool === 'select'}
                  onClick={() => onChange('select')}
                  aria-label="select tool" 
                  sx={{ border: 'none', py: 1.5, borderRadius: 0, width: '100%' }}
                >
                  <MouseMui sx={{ fontSize: 18 }} />
                </ToggleButton>
              </Tooltip>
              
              <Tooltip title="Hand (H) - Pan" placement="right" arrow>
                <ToggleButton 
                  value="hand" 
                  selected={activeTool === 'hand'}
                  onClick={() => onChange('hand')}
                  aria-label="hand tool" 
                  sx={{ border: 'none', py: 1.5, borderRadius: 0, width: '100%' }}
                >
                  <PanToolMui sx={{ fontSize: 18 }} />
                </ToggleButton>
              </Tooltip>
            </Stack>
          </Paper>

          {/* 3. View Controls Capsule */}
          <Paper elevation={0} sx={capsuleStyle}>
            <Stack direction="column" alignItems="center">
              <Tooltip title="Insert Node" placement="right" arrow>
                <IconButton onClick={onInsert} sx={{ py: 1.5, borderRadius: 0 }}>
                  <AddIcon size="md" />
                </IconButton>
              </Tooltip>

              <Tooltip title="Zoom In" placement="right" arrow>
                <IconButton onClick={onZoomIn} sx={{ py: 1.5, borderRadius: 0 }}>
                  <ZoomInIcon size={18} />
                </IconButton>
              </Tooltip>

              <Tooltip title="Reset Zoom (100%)" placement="right" arrow>
                <Box 
                  onClick={onResetZoom}
                  sx={{ 
                    py: 1, 
                    width: '100%', 
                    textAlign: 'center', 
                    cursor: 'pointer',
                    '&:hover': { bgcolor: 'action.hover' },
                    userSelect: 'none'
                  }}
                >
                  <Typography variant="caption" sx={{ fontWeight: 'bold', fontSize: '0.7rem' }}>
                    {Math.round(zoom * 100)}%
                  </Typography>
                </Box>
              </Tooltip>

              <Tooltip title="Zoom Out" placement="right" arrow>
                <IconButton onClick={onZoomOut} sx={{ py: 1.5, borderRadius: 0 }}>
                  <ZoomOutIcon size={18} />
                </IconButton>
              </Tooltip>
              
              <Tooltip title="Fit to Screen" placement="right" arrow>
                <IconButton onClick={onFitView} sx={{ py: 1.5, borderRadius: 0 }}>
                  <CropFreeMui sx={{ fontSize: 18 }} />
                </IconButton>
              </Tooltip>
            </Stack>
          </Paper>

          {/* 4. Delete Button */}
          <Tooltip title="Delete Selected (Del)" placement="right" arrow>
            <IconButton
              onClick={onDelete}
              disabled={!hasSelection}
              sx={{
                bgcolor: hasSelection ? '#FEF2F2' : 'background.paper', // Light red if active
                border: '1px solid',
                borderColor: hasSelection ? 'error.light' : 'divider',
                boxShadow: 2,
                color: hasSelection ? 'error.main' : 'action.disabled',
                '&:hover': { 
                  bgcolor: hasSelection ? '#FEE2E2' : 'background.paper' 
                }
              }}
            >
              <DeleteIcon size={18} />
            </IconButton>
          </Tooltip>

        </Stack>
      </Fade>
    </Box>
  );
}
