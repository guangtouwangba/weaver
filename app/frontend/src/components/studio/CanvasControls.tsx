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
  ImageSearchIcon,
  MousePointerIcon,
  HandIcon,
  LinkIcon,
  AccountTreeIcon
} from '@/components/ui/icons';
import { Minus } from 'lucide-react';

interface CanvasControlsProps {
  zoom: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFitView: () => void;
  interactionMode?: 'select' | 'pan' | 'connect' | 'logic_connect';
  onModeChange?: (mode: 'select' | 'pan' | 'connect' | 'logic_connect') => void;
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
          style={{
            display: 'flex',
            flexDirection: 'row',
            padding: 4,
          }}
        >
          <Tooltip title="Select Mode (V)" placement="bottom">
            <IconButton
              size="sm"
              variant={interactionMode === 'select' ? 'default' : 'ghost'}
              active={interactionMode === 'select'}
              onClick={() => onModeChange?.('select')}
            >
              <MousePointerIcon size={20} />
            </IconButton>
          </Tooltip>
          <Tooltip title="Pan Mode (H)" placement="bottom">
            <IconButton
              size="sm"
              variant={interactionMode === 'pan' ? 'default' : 'ghost'}
              active={interactionMode === 'pan'}
              onClick={() => onModeChange?.('pan')}
            >
              <HandIcon size={20} />
            </IconButton>
          </Tooltip>
          <Tooltip title="Connect (L)" placement="bottom">
            <IconButton
              size="sm"
              variant={interactionMode === 'connect' ? 'default' : 'ghost'}
              active={interactionMode === 'connect'}
              onClick={() => onModeChange?.('connect')}
            >
              <LinkIcon size={20} />
            </IconButton>
          </Tooltip>
          <Tooltip title="Logic Connect (K)" placement="bottom">
            <IconButton
              size="sm"
              variant={interactionMode === 'logic_connect' ? 'default' : 'ghost'}
              active={interactionMode === 'logic_connect'}
              onClick={() => onModeChange?.('logic_connect')}
            >
              <AccountTreeIcon size={20} />
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
          style={{
            width: 42,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <Stack direction="column" gap={0} align="center" style={{ padding: 4 }}>
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
              style={{
                paddingTop: 4,
                paddingBottom: 4,
                paddingLeft: 8,
                paddingRight: 8,
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
                <Minus size={16} />
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
