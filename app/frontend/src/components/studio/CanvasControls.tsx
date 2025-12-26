'use client';

import { useState } from 'react';
import { 
  Box, 
  Paper, 
  IconButton, 
  Tooltip,
  Typography,
  Collapse
} from "@mui/material";
import { 
  AddIcon, 
  AddCircleIcon,
  ExpandMoreIcon, 
  ExpandLessIcon,
  DeleteIcon,
  ImageSearchIcon
} from '@/components/ui/icons';
import RemoveMui from '@mui/icons-material/Remove';
import MouseMui from '@mui/icons-material/Mouse';
import PanToolMui from '@mui/icons-material/PanTool';

interface CanvasControlsProps {
  zoom: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFitView: () => void;
  interactionMode?: 'select' | 'pan';
  onModeChange?: (mode: 'select' | 'pan') => void;
  onDelete?: () => void;
  hasSelection?: boolean;
}

export default function CanvasControls({ 
  zoom, 
  onZoomIn, 
  onZoomOut, 
  onFitView,
  interactionMode = 'select',
  onModeChange,
  onDelete,
  hasSelection = false
}: CanvasControlsProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Common paper style - pill-shaped with full rounded corners
  const paperStyle = {
    width: 42, // Fixed width to ensure consistency across all groups
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    borderRadius: '20px', // Full pill-shaped rounded corners
    overflow: 'hidden',
    bgcolor: 'background.paper',
    boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
    border: '1px solid',
    borderColor: 'divider',
  };

  // Mode button style with circular highlight for active state
  const getModeButtonStyle = (isActive: boolean) => ({
    width: 32,
    height: 32,
    borderRadius: '50%',
    bgcolor: isActive ? '#EFF6FF' : 'transparent',
    color: isActive ? '#3B82F6' : 'text.secondary',
    transition: 'all 0.2s ease',
    '&:hover': {
      bgcolor: isActive ? '#DBEAFE' : 'action.hover',
    },
  });

  return (
    <Box
      sx={{
        position: 'absolute',
        bottom: 32,
        right: 32,
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 1.5,
      }}
    >
      {/* Collapse Toggle - circular button */}
      <Tooltip title={isCollapsed ? "Expand toolbar" : "Collapse toolbar"} placement="left">
        <IconButton
          onClick={() => setIsCollapsed(!isCollapsed)}
          size="small"
          sx={{
            width: 32,
            height: 32,
            borderRadius: '50%',
            bgcolor: 'background.paper',
            border: '1px solid',
            borderColor: 'divider',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
            '&:hover': {
              bgcolor: 'action.hover',
            },
          }}
        >
          {isCollapsed ? <ExpandLessIcon size="sm" /> : <ExpandMoreIcon size="sm" />}
        </IconButton>
      </Tooltip>

      {/* Collapsible Content */}
      <Collapse in={!isCollapsed} timeout={200}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1.5 }}>
          {/* Mode Tools Group */}
          <Paper elevation={0} sx={paperStyle}>
            <Box sx={{ p: 0.5, display: 'flex', flexDirection: 'column', gap: 0.5 }}>
              <Tooltip title="Select Mode (V)" placement="left">
                <IconButton 
                  onClick={() => onModeChange?.('select')}
                  sx={getModeButtonStyle(interactionMode === 'select')}
                >
                  <MouseMui sx={{ fontSize: 16 }} />
                </IconButton>
              </Tooltip>
              <Tooltip title="Pan Mode (H)" placement="left">
                <IconButton 
                  onClick={() => onModeChange?.('pan')}
                  sx={getModeButtonStyle(interactionMode === 'pan')}
                >
                  <PanToolMui sx={{ fontSize: 16 }} />
                </IconButton>
              </Tooltip>
            </Box>
          </Paper>

          {/* Zoom Controls Group */}
          <Paper elevation={0} sx={paperStyle}>
            <Box sx={{ p: 0.5, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.25 }}>
              {/* Add Node Button */}
              <Tooltip title="Add Node" placement="left">
                <IconButton 
                  sx={{ 
                    width: 32, 
                    height: 32, 
                    color: 'text.secondary',
                    '&:hover': { bgcolor: 'action.hover' }
                  }}
                >
                  <AddCircleIcon size="sm" />
                </IconButton>
              </Tooltip>

              {/* Zoom In */}
              <Tooltip title="Zoom In" placement="left">
                <IconButton 
                  onClick={onZoomIn} 
                  sx={{ 
                    width: 32, 
                    height: 32, 
                    color: 'text.secondary',
                    '&:hover': { bgcolor: 'action.hover' }
                  }}
                >
                  <AddIcon size="sm" />
                </IconButton>
              </Tooltip>

              {/* Zoom Percentage */}
              <Typography 
                variant="caption" 
                sx={{ 
                  py: 0.5,
                  px: 1,
                  fontWeight: 600, 
                  color: 'text.secondary', 
                  userSelect: 'none',
                  fontSize: '0.7rem'
                }}
              >
                {Math.round(zoom * 100)}%
              </Typography>

              {/* Zoom Out */}
              <Tooltip title="Zoom Out" placement="left">
                <IconButton 
                  onClick={onZoomOut} 
                  sx={{ 
                    width: 32, 
                    height: 32, 
                    color: 'text.secondary',
                    '&:hover': { bgcolor: 'action.hover' }
                  }}
                >
                  <RemoveMui sx={{ fontSize: 16 }} />
                </IconButton>
              </Tooltip>

              {/* Fit View */}
              <Tooltip title="Fit View" placement="left">
                <IconButton 
                  onClick={onFitView} 
                  sx={{ 
                    width: 32, 
                    height: 32, 
                    color: 'text.secondary',
                    '&:hover': { bgcolor: 'action.hover' }
                  }}
                >
                  <ImageSearchIcon size="sm" />
                </IconButton>
              </Tooltip>
            </Box>
          </Paper>

          {/* Delete Button - always visible with red border style */}
          <Paper 
            elevation={0} 
            sx={{
              ...paperStyle,
              border: '1px solid',
              borderColor: '#FECACA',
              bgcolor: '#FEF2F2',
            }}
          >
            <Box sx={{ p: 0.5 }}>
              <Tooltip title="Delete Selected" placement="left">
                <IconButton 
                  onClick={onDelete}
                  disabled={!hasSelection}
                  sx={{ 
                    width: 32, 
                    height: 32, 
                    color: hasSelection ? '#DC2626' : '#FCA5A5',
                    '&:hover': { 
                      bgcolor: hasSelection ? '#FEE2E2' : 'transparent',
                    },
                    '&.Mui-disabled': {
                      color: '#FCA5A5',
                    }
                  }}
                >
                  <DeleteIcon size="sm" />
                </IconButton>
              </Tooltip>
            </Box>
          </Paper>
        </Box>
      </Collapse>
    </Box>
  );
}
