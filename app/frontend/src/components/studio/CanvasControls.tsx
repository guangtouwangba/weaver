'use client';

import {
  Stack,
  Surface,
  IconButton,
  Tooltip,
  Text,
} from '@/components/ui';
import { colors, radii, shadows } from '@/components/ui/tokens';
import {
  AddIcon,
  AddCircleIcon,
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
}: CanvasControlsProps) {

  return (
    <>
      {/* Top Center: Interaction Tools */}
      <div
        style={{
          position: 'absolute',
          top: 24,
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 1000,
          display: 'flex',
          gap: 8,
        }}
      >
        <Surface
          elevation={1}
          radius="lg"
          bordered
          sx={{
            display: 'flex',
            flexDirection: 'row',
            p: 0.5,
          }}
        >
          <Tooltip title="Select Mode (V)" placement="bottom">
            <IconButton
              size="sm"
              variant={interactionMode === 'select' ? 'default' : 'ghost'}
              active={interactionMode === 'select'}
              onClick={() => onModeChange?.('select')}
            >
              <MouseMui sx={{ fontSize: 20 }} />
            </IconButton>
          </Tooltip>
          <Tooltip title="Pan Mode (H)" placement="bottom">
            <IconButton
              size="sm"
              variant={interactionMode === 'pan' ? 'default' : 'ghost'}
              active={interactionMode === 'pan'}
              onClick={() => onModeChange?.('pan')}
            >
              <PanToolMui sx={{ fontSize: 20 }} />
            </IconButton>
          </Tooltip>
        </Surface>
      </div>

      {/* Bottom Right: Zoom & View Controls */}
      <div
        style={{
          position: 'absolute',
          bottom: 32,
          right: 32,
          zIndex: 1000,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
        }}
      >
        <Surface
          elevation={1}
          radius="xl"
          bordered
          sx={{
            width: 42,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <Stack direction="column" gap={0} align="center" sx={{ p: 0.5 }}>
            {/* Add Node Button */}
            <Tooltip title="Add Node" placement="left">
              <IconButton size="sm" variant="ghost">
                <AddCircleIcon size="sm" />
              </IconButton>
            </Tooltip>

            {/* Zoom In */}
            <Tooltip title="Zoom In" placement="left">
              <IconButton size="sm" variant="ghost" onClick={onZoomIn}>
                <AddIcon size="sm" />
              </IconButton>
            </Tooltip>

            {/* Zoom Percentage */}
            <Text
              variant="caption"
              color="secondary"
              sx={{
                py: 0.5,
                px: 1,
                fontWeight: 600,
                userSelect: 'none',
                fontSize: '0.7rem'
              }}
            >
              {Math.round(zoom * 100)}%
            </Text>

            {/* Zoom Out */}
            <Tooltip title="Zoom Out" placement="left">
              <IconButton size="sm" variant="ghost" onClick={onZoomOut}>
                <RemoveMui sx={{ fontSize: 16 }} />
              </IconButton>
            </Tooltip>

            {/* Fit View */}
            <Tooltip title="Fit View" placement="left">
              <IconButton size="sm" variant="ghost" onClick={onFitView}>
                <ImageSearchIcon size="sm" />
              </IconButton>
            </Tooltip>
          </Stack>
        </Surface>
      </div>
    </>
  );
}
