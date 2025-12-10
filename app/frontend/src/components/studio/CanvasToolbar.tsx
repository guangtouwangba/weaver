'use client';

import { Paper, ToggleButton, ToggleButtonGroup, Tooltip } from '@mui/material';
import { MousePointer2, Hand } from 'lucide-react';

export type ToolMode = 'select' | 'hand';

interface CanvasToolbarProps {
  activeTool: ToolMode;
  onChange: (tool: ToolMode) => void;
}

export default function CanvasToolbar({ activeTool, onChange }: CanvasToolbarProps) {
  return (
    <Paper
      elevation={3}
      sx={{
        position: 'absolute',
        bottom: 24,
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 1000,
        borderRadius: 2,
        overflow: 'hidden',
        border: '1px solid',
        borderColor: 'divider',
        bgcolor: 'background.paper',
      }}
    >
      <ToggleButtonGroup
        value={activeTool}
        exclusive
        onChange={(_, newTool) => {
          if (newTool) onChange(newTool);
        }}
        size="small"
        aria-label="canvas tool"
      >
        <Tooltip title="Select (V)" arrow placement="top">
          <ToggleButton value="select" aria-label="select tool">
            <MousePointer2 size={18} />
          </ToggleButton>
        </Tooltip>
        
        <Tooltip title="Hand (H)" arrow placement="top">
          <ToggleButton value="hand" aria-label="hand tool">
            <Hand size={18} />
          </ToggleButton>
        </Tooltip>
      </ToggleButtonGroup>
    </Paper>
  );
}
